# Crawl Agent
# Generic Playwright crawler
# Discovers pages at runtime instead of following a hardcoded path
# Queue of links to visit, with depth and page limits

import json
import asyncio
import re
from playwright.async_api import async_playwright
from config import SCREENSHOTS_DIR, DOM_DIR, client, MODEL, chat_with_retry
from urllib.parse import urlparse, urljoin

# Buttons whose text matches these are never clicked
DESTRUCTIVE_KEYWORDS = [
    "logout", "log out", "sign out", "signout",
    "remove", "delete", "reset", "clear",
    "buy", "purchase", "pay", "order",
]

# Default crawl bounds
DEFAULT_MAX_PAGES = 30
DEFAULT_MAX_DEPTH = 5


# Build a safe filename from a URL and index
def _safe_name(url, index):
    path = urlparse(url).path.strip("/").replace("/", "_")
    if not path:
        path = "home"
    path = re.sub(r"\.[a-zA-Z0-9]+$", "", path)
    return f"{index}_{path}"[:80]


# Capture screenshot and DOM for the current page state
async def _capture(page, run_id, name):
    screenshot_path = str(SCREENSHOTS_DIR / f"{run_id}_{name}.png")
    await page.screenshot(path=screenshot_path, full_page=True)

    dom = await page.content()
    dom_path = str(DOM_DIR / f"{run_id}_{name}.html")
    with open(dom_path, "w", encoding="utf-8") as fh:
        fh.write(dom)

    return {
        "url": page.url,
        "screenshot": screenshot_path,
        "dom": dom,
        "dom_path": dom_path,
    }


# True if text matches a destructive keyword
def _is_destructive(text):
    t = (text or "").lower()
    return any(word in t for word in DESTRUCTIVE_KEYWORDS)


# Collect same domain, unseen link URLs on the current page
async def _discover_links(page, base_domain, visited, queued):
    new_links = []
    anchors = await page.query_selector_all("a[href]")
    for a in anchors:
        href = await a.get_attribute("href")
        if not href:
            continue
        # Skip non navigational hrefs like "#", "javascript:", "mailto:", "tel:"
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        # Resolve relative URLs against the current page
        abs_url = await page.evaluate("(h) => new URL(h, location.href).href", href)
        if urlparse(abs_url).netloc != base_domain:
            continue
        if abs_url in visited or abs_url in queued:
            continue
        new_links.append(abs_url)
    return new_links


# Discover JS only navigation targets that expose a stable identifier
# SauceDemo tiles carry data-test="item-N-title-link" but no href
# We click each by its own selector, so state drift cannot misalign them
async def _discover_by_clicking(page, current_url, base_domain, visited, queued):
    found = []

    # Read all stable target selectors from one page snapshot
    handles = await page.query_selector_all("[data-test$='-title-link']")
    selectors = []
    for h in handles:
        dt = await h.get_attribute("data-test")
        if dt:
            selectors.append(f"[data-test='{dt}']")

    # Visit each target by its own selector, reloading fresh each time
    for sel in selectors:
        if page.url != current_url:
            await page.goto(current_url)
            await page.wait_for_load_state("networkidle")

        el = await page.query_selector(sel)
        if el is None:
            continue

        before = page.url
        try:
            await el.click(timeout=2000)
            await page.wait_for_load_state("networkidle")
        except Exception:
            continue

        after = page.url
        if (after != before
                and urlparse(after).netloc == base_domain
                and after not in visited
                and after not in queued
                and after not in found):
            found.append(after)

    # Leave the browser on the crawl page for the caller
    if page.url != current_url:
        await page.goto(current_url)
        await page.wait_for_load_state("networkidle")

    # Sort by numeric id so item pages come back in order
    def _id_key(url):
        m = re.search(r'id=(\d+)', url)
        return int(m.group(1)) if m else -1
    found = sorted(found, key=_id_key)

    return found


# List the interactive elements on the page for the LLM
# Each element gets an index and a selector we can act on later
async def _get_interactive_elements(page, max_elements=30):
    elements = []
    selector = "input, textarea, select, button, a[href], [role=button]"
    handles = await page.query_selector_all(selector)

    for i, h in enumerate(handles):
        if i >= max_elements:
            break
        # Gather descriptive attributes, any may be None
        tag = await h.evaluate("el => el.tagName.toLowerCase()")
        el_type = await h.get_attribute("type")
        name = await h.get_attribute("name")
        placeholder = await h.get_attribute("placeholder")
        data_test = await h.get_attribute("data-test")
        text = (await h.inner_text() or "").strip()[:50]
        aria = await h.get_attribute("aria-label")

        # Prefer data-test, then name, then id
        el_id = await h.get_attribute("id")
        if data_test:
            css = f"[data-test='{data_test}']"
        elif name:
            css = f"{tag}[name='{name}']"
        elif el_id:
            css = f"#{el_id}"
        else:
            css = None

        elements.append({
            "index": i,
            "tag": tag,
            "type": el_type,
            "name": name or aria or placeholder or text or data_test,
            "placeholder": placeholder,
            "text": text,
            "selector": css,
        })

    return elements


# Run a single decision against the page
# decision looks like {"action": "click"/"fill", "selector": ..., "value": ...}
# Returns (ok, message) so the trace can record what happened
async def _execute(page, decision):
    action = decision.get("action")
    selector = decision.get("selector")

    if action == "done":
        return True, "done"

    if not selector:
        return False, "no selector provided"

    el = await page.query_selector(selector)
    if el is None:
        return False, f"element not found: {selector}"
    
    try:
        if action == "fill":
            value = decision.get("value", "")
            await el.fill(value)
            return True, f"filled {selector} with {value!r}"

        elif action == "click":
            await el.click(timeout=3000)
            await page.wait_for_load_state("networkidle")
            return True, f"clicked {selector}"

        elif action == "select":
            value = decision.get("value", "")
            await el.select_option(label=value)
            return True, f"selected {value!r} in {selector}"

        else:
            return False, f"unknown action: {action}"

    except Exception as e:
        return False, f"action failed on {selector}: {e}"


# Drop elements the LLM must never pick, like logout or reset
def _filter_safe_elements(elements):
    safe = []
    for e in elements:
        label = f"{e.get('name','')} {e.get('text','')}".lower()
        if _is_destructive(label):
            continue
        if e.get("selector") is None:
            continue
        safe.append(e)
    return safe


# Ask the LLM for the next step
# It acts as a QA tester, infers a goal for the page, and drives toward bugs
async def decide_next_action(page_url, elements, history):
    safe = _filter_safe_elements(elements)

    # Compact element list for the prompt
    element_lines = "\n".join(
        f"{e['index']}: <{e['tag']}> {e.get('name','')!r} selector={e['selector']}"
        for e in safe
    )
    history_lines = "\n".join(
        f"- {h['action']} {h.get('selector','')} {h.get('value','')} => {h.get('result','')}"
        for h in history
    ) or "(nothing yet)"

    system = """You are a QA test engineer interacting with a live web page to
surface FUNCTIONAL bugs. Infer a realistic testing goal for THIS page (e.g.
complete a checkout, submit a form, test validation with empty or invalid input)
and work toward it one step at a time.

Choose the SINGLE next action from the provided elements. Respond ONLY with JSON:
{"action": "fill"|"click"|"select"|"done", "selector": "<selector from the list>",
 "value": "<text if filling, else omit>", "reason": "<one short sentence>"}

Rules:
- Use only selectors that appear in the element list.
- Prioritise testing input controls such as dropdowns, sort menus, and form fields over repeatedly clicking similar buttons.
- To test validation, you may deliberately submit empty or invalid values.
- After an action that should change the page, prefer verifying the result over repeating similar actions.
- Return {"action": "done"} when the goal is reached or no useful action remains.
- Prefer completing a realistic user flow before declaring done."""
    user = f"""Page: {page_url}

Available elements:
{element_lines}

Actions so far:
{history_lines}

What is the single next action?"""

    response = chat_with_retry(
        model=MODEL,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        temperature=0,
        max_tokens=200,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"action": "done", "reason": "could not parse LLM response"}


# True if a page has form fields, not just navigation buttons
def _is_interactive_page(elements):
    for e in elements:
        if e.get("tag") in ("input", "textarea", "select"):
            return True
    return False


# Run one LLM guided interaction scenario on the current page
# Loop: read elements, LLM decides, execute, capture the new state, record trace
# Returns (captured_pages, trace)
async def run_scenario(page, run_id, base_name, max_steps=12):
    captured_pages = []
    trace = []
    no_change_findings = []
    last_dom = await page.content()   # baseline before any action

    for step in range(max_steps):
        elements = await _get_interactive_elements(page)
        decision = await decide_next_action(page.url, elements, trace)
        print(f"    [scenario] step {step+1}: {decision.get('action')} "
              f"{decision.get('selector','')} {decision.get('reason','')}")

        if decision.get("action") == "done":
            break

        ok, msg = await _execute(page, decision)

        # Capture only if the DOM meaningfully changed since the last capture
        new_dom = await page.content()
        if new_dom != last_dom:
            capture = await _capture(page, run_id, f"{base_name}_step{step+1}")
            capture["interaction"] = True
            capture["step"] = step + 1
            capture["action"] = f"{decision.get('action')} {decision.get('selector','')} {decision.get('value','')}".strip()
            capture["action_reason"] = decision.get("reason", "")
            capture["dom_before"] = last_dom   # the DOM as it was before this action
            captured_pages.append(capture)
            last_dom = new_dom
        else:
            # No DOM change. For actions that SHOULD cause a change (clicking a
            # button/link, selecting an option), no change is itself a defect
            # signal, the control did nothing.
            action = decision.get("action")
            value = decision.get("value", "")
            expected_change = (
                action == "click"
                or action == "select"
                or (action == "fill" and value != "")
            )
            if expected_change:
                no_change_findings.append({
                    "page_url": page.url,
                    "issue_type": "functional",
                    "description": (
                        f"Interaction had no effect: '{action}' on "
                        f"{decision.get('selector','')} produced no change in the page, "
                        f"though a change was expected. Intent: {decision.get('reason','')}"
                    ),
                    "severity": "major",
                    "confidence": "medium",
                    "location": decision.get("selector", ""),
                    "recommended_fix": "Ensure this control performs its intended action.",
                    "source": "interaction_check",
                })
                print(f"      (no DOM change on {action}, recorded as potential defect)")
            else:
                print(f"      (no DOM change, expected, skipped)")

        # Record the trace step for reproducibility
        trace.append({
            "action": decision.get("action"),
            "selector": decision.get("selector"),
            "value": decision.get("value", ""),
            "reason": decision.get("reason", ""),
            "result": msg,
            "url_after": page.url,
        })

        if not ok:
            print(f"      (action failed: {msg})")

    print(f"    [scenario] complete, {len(captured_pages)} states captured, "
          f"{len(trace)} steps")
    return captured_pages, trace, no_change_findings

# Optional configurable login
async def _login(page, login_config):
    await page.goto(login_config["url"])
    await page.fill(login_config["username_selector"], login_config["username"])
    await page.fill(login_config["password_selector"], login_config["password"])
    await page.click(login_config["submit_selector"])
    await page.wait_for_load_state("networkidle")
    print(f"  Logged in as {login_config.get('username', '(unknown)')}")


# Generic crawl, returns a list of page dicts
# url is where to start crawling, post login for SauceDemo
# login_config logs in first if provided
# max_pages caps total pages, max_depth caps how far links are followed
async def crawl(url, run_id, login_config=None, seed_paths=None,
                max_pages=DEFAULT_MAX_PAGES, max_depth=DEFAULT_MAX_DEPTH):

    print(f"Crawl Agent starting for {url}...")
    pages_crawled = []
    all_traces = []
    all_no_change = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Optional login
        if login_config:
            await _login(page, login_config)

        start_url = page.url if login_config else url
        parsed_start = urlparse(start_url)
        base_domain = parsed_start.netloc
        origin = f"{parsed_start.scheme}://{parsed_start.netloc}"

        # BFS queue of (url, depth), visited and queued are sets of URLs
        queue = [(start_url, 0)]
        queued = {start_url}
        visited = set()
        index = 0

        # Seed the queue with known entry points, treated like discovered links
        if seed_paths:
            for seed in seed_paths:
                seed_url = urljoin(origin + "/", seed)
                if seed_url not in queued:
                    queue.append((seed_url, 0))
                    queued.add(seed_url)

        while queue and len(pages_crawled) < max_pages:
            current_url, depth = queue.pop(0)
            if current_url in visited:
                continue

            # Navigate, the first item may already be loaded post login
            if page.url != current_url:
                await page.goto(current_url)
                await page.wait_for_load_state("networkidle")
            visited.add(current_url)

            # Capture this page passively
            index += 1
            name = _safe_name(current_url, index)
            pages_crawled.append(await _capture(page, run_id, name))
            print(f"  Captured [{len(pages_crawled)}/{max_pages}] depth={depth}: {current_url}")

            # Interaction phase, run a scenario if the page has a form
            elements = await _get_interactive_elements(page)
            if _is_interactive_page(elements):
                print(f"    [scenario] interactive page detected: {current_url}")
                scenario_pages, scenario_trace, scenario_nc = await run_scenario(page, run_id, name)
                pages_crawled.extend(scenario_pages)

                # Attach page and step context, then collect for storage
                for i, t in enumerate(scenario_trace, 1):
                    t["page_url"] = current_url
                    t["step"] = i
                    all_traces.append(t)

                # Collect no-change interaction findings
                all_no_change.extend(scenario_nc)

                # A scenario moves the browser around, return to the crawl page
                if page.url != current_url:
                    await page.goto(current_url)
                    await page.wait_for_load_state("networkidle")

            # Discover links and queue unseen same domain ones
            if depth < max_depth:
                for link in await _discover_links(page, base_domain, visited, queued):
                    queue.append((link, depth + 1))
                    queued.add(link)

                # JS only navigation, reach pages that have no href by clicking
                for link in await _discover_by_clicking(page, current_url, base_domain, visited, queued):
                    queue.append((link, depth + 1))
                    queued.add(link)

        await browser.close()

    print(f"Crawl Agent complete, {len(pages_crawled)} pages captured, "
          f"{len(all_traces)} trace steps, {len(all_no_change)} no-change findings")
    return pages_crawled, all_traces, all_no_change