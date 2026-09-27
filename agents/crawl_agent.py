# Crawl Agent
# Find pages, save screenshots and DOM, and try interactions
# Uses a queue to follow links up to the page and depth limits

import json
import asyncio
import re
from urllib.parse import urlparse, urljoin

from playwright.async_api import async_playwright
from config import SCREENSHOTS_DIR, DOM_DIR, client, CRAWL_MODEL, chat_with_retry


# Hide controls with these words from the model's element list
DESTRUCTIVE_KEYWORDS = [
    "logout", "log out", "sign out", "signout",
    "remove", "delete", "reset", "clear",
    "buy", "purchase", "pay", "order",
]

DEFAULT_MAX_PAGES = 30
DEFAULT_MAX_DEPTH = 5

CREDENTIALS = {
    "username", "user-name", "user_name", "password",
    "pass", "email", "login", "pwd", "signing",
    "signin", "emailme",
}

DEFAULT_ERROR_SELECTORS = (
    "[data-test='error'], .error-message-container, [role='alert']"
)


class LoginFailed(Exception):
    pass


# Make a filename using the page path and capture number
def _safe_name(url, index):
    path = urlparse(url).path.strip("/").replace("/", "_")

    if not path:
        path = "home"

    path = re.sub(r"\.[a-zA-Z0-9]+$", "", path)
    return f"{index}_{path}"[:80]


# Save the current screenshot and HTML
async def _capture(page, run_id, name):
    screenshot_path = str(SCREENSHOTS_DIR / f"{run_id}_{name}.png")
    await page.screenshot(path=screenshot_path, full_page=True)

    dom = await page.content()
    dom_path = str(DOM_DIR / f"{run_id}_{name}.html")

    with open(dom_path, "w", encoding="utf-8") as file:
        file.write(dom)

    return {
        "url": page.url,
        "screenshot": screenshot_path,
        "dom": dom,
        "dom_path": dom_path,
    }


# Check whether the text contains a blocked word
def _is_destructive(text):
    text = (text or "").lower()
    return any(word in text for word in DESTRUCTIVE_KEYWORDS)


# Find links on the same domain that haven't been queued or visited
async def _discover_links(page, base_domain, visited, queued):
    new_links = []
    anchors = await page.query_selector_all("a[href]")

    for anchor in anchors:
        href = await anchor.get_attribute("href")

        if not href:
            continue

        # Ignore links that don't lead to another page
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        full_url = await page.evaluate(
            "(h) => new URL(h, location.href).href",
            href,
        )

        if urlparse(full_url).netloc != base_domain:
            continue

        if full_url in visited or full_url in queued:
            continue

        new_links.append(full_url)

    return new_links


# Find product pages opened through JavaScript rather than href links
# This selector covers the title links used by SauceDemo
async def _discover_by_clicking(
    page, current_url, base_domain, visited, queued
):
    found = []
    selectors = []

    elements = await page.query_selector_all("[data-test$='-title-link']")

    # Save selectors before clicking anything
    for element in elements:
        data_test = await element.get_attribute("data-test")

        if data_test:
            selectors.append(f"[data-test='{data_test}']")

    for selector in selectors:
        # Return to the starting page if the last click navigated away
        if page.url != current_url:
            await page.goto(current_url)
            await page.wait_for_load_state("networkidle")

        element = await page.query_selector(selector)

        if element is None:
            continue

        before_url = page.url

        try:
            await element.click(timeout=2000)
            await page.wait_for_load_state("networkidle")
        except Exception:
            continue

        after_url = page.url

        if (
            after_url != before_url
            and urlparse(after_url).netloc == base_domain
            and after_url not in visited
            and after_url not in queued
            and after_url not in found
        ):
            found.append(after_url)

    # Leave the browser back on the crawl page
    if page.url != current_url:
        await page.goto(current_url)
        await page.wait_for_load_state("networkidle")

    # Keep product pages ordered by their numeric ID
    def _id_key(url):
        match = re.search(r"id=(\d+)", url)
        return int(match.group(1)) if match else -1

    return sorted(found, key=_id_key)


# Collect controls the model can use
async def _get_interactive_elements(page, max_elements=30):
    elements = []
    selector = "input, textarea, select, button, a[href], [role=button]"
    handles = await page.query_selector_all(selector)

    for index, element in enumerate(handles):
        if index >= max_elements:
            break

        tag = await element.evaluate("el => el.tagName.toLowerCase()")
        element_type = await element.get_attribute("type")
        name = await element.get_attribute("name")
        placeholder = await element.get_attribute("placeholder")
        data_test = await element.get_attribute("data-test")
        text = (await element.inner_text() or "").strip()[:50]
        aria_label = await element.get_attribute("aria-label")
        element_id = await element.get_attribute("id")

        # Prefer data-test, then name, then ID
        if data_test:
            css = f"[data-test='{data_test}']"
        elif name:
            css = f"{tag}[name='{name}']"
        elif element_id:
            css = f"#{element_id}"
        else:
            css = None

        elements.append({
            "index": index,
            "tag": tag,
            "type": element_type,
            "name": name or aria_label or placeholder or text or data_test,
            "placeholder": placeholder,
            "text": text,
            "selector": css,
        })

    return elements


# Carry out one action and return its result for the trace
async def _execute(page, decision):
    action = decision.get("action")
    selector = decision.get("selector")

    if action == "done":
        return True, "done"

    if not selector:
        return False, "no selector provided"

    element = await page.query_selector(selector)

    if element is None:
        return False, f"element not found: {selector}"

    try:
        if action == "fill":
            value = decision.get("value", "")
            await element.fill(value)
            return True, f"filled {selector} with {value!r}"

        elif action == "click":
            await element.click(timeout=3000)
            await page.wait_for_load_state("networkidle")
            return True, f"clicked {selector}"

        elif action == "select":
            value = decision.get("value", "")
            await element.select_option(label=value)
            return True, f"selected {value!r} in {selector}"

        else:
            return False, f"unknown action: {action}"

    except Exception as error:
        return False, f"action failed on {selector}: {error}"


# Check whether a control looks like a login field
def _is_credential_field(element):
    text = " ".join(
        str(element.get(key, ""))
        for key in ["name", "placeholder", "text", "selector", "type"]
    ).lower()

    if element.get("type") == "password":
        return True

    return any(term in text for term in CREDENTIALS)


# Remove blocked controls before sending the list to the model
def _filter_safe_elements(elements, block_credentials=False):
    safe_elements = []

    for element in elements:
        label = (
            f"{element.get('name', '')} {element.get('text', '')}"
        ).lower()

        if _is_destructive(label):
            continue

        if block_credentials and _is_credential_field(element):
            continue

        if element.get("selector") is None:
            continue

        safe_elements.append(element)

    return safe_elements


# Ask the model which action to try next
async def decide_next_action(page_url, elements, history):
    safe_elements = _filter_safe_elements(
        elements,
        block_credentials=True,
    )

    element_lines = "\n".join(
        f"{element['index']}: <{element['tag']}> "
        f"{element.get('name', '')!r} selector={element['selector']}"
        for element in safe_elements
    )

    history_lines = "\n".join(
        f"- {step['action']} {step.get('selector', '')} "
        f"{step.get('value', '')} => {step.get('result', '')}"
        for step in history
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
        model=CRAWL_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0,
        max_tokens=200,
    )

    raw = response.choices[0].message.content.strip()

    # Remove Markdown fences if the model included them
    if raw.startswith("```"):
        raw = raw.split("```")[1]

        if raw.startswith("json"):
            raw = raw[4:]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "action": "done",
            "reason": "could not parse LLM response",
        }


# Only start a scenario if the page has input controls
def _is_interactive_page(elements):
    for element in elements:
        if element.get("tag") in ("input", "textarea", "select"):
            return True

    return False


# Try actions, capture changed states and record what happened
# Returns captures, trace steps and possible no-change findings
async def run_scenario(page, run_id, base_name, max_steps=12):
    captured_pages = []
    trace = []
    no_change_findings = []

    last_dom = await page.content()

    for step in range(max_steps):
        elements = await _get_interactive_elements(page)
        decision = await decide_next_action(page.url, elements, trace)

        print(
            f"    [scenario] step {step + 1}: {decision.get('action')} "
            f"{decision.get('selector', '')} {decision.get('reason', '')}"
        )

        if decision.get("action") == "done":
            break

        ok, message = await _execute(page, decision)
        new_dom = await page.content()

        # Save another capture if the HTML changed
        if new_dom != last_dom:
            capture = await _capture(
                page,
                run_id,
                f"{base_name}_step{step + 1}",
            )

            capture["interaction"] = True
            capture["step"] = step + 1
            capture["action"] = (
                f"{decision.get('action')} "
                f"{decision.get('selector', '')} "
                f"{decision.get('value', '')}"
            ).strip()
            capture["action_reason"] = decision.get("reason", "")
            capture["dom_before"] = last_dom

            captured_pages.append(capture)
            last_dom = new_dom

        else:
            # An unchanged DOM is treated as a possible defect signal
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
                        f"{decision.get('selector', '')} produced no change "
                        f"in the page, though a change was expected. "
                        f"Intent: {decision.get('reason', '')}"
                    ),
                    "severity": "major",
                    "confidence": "medium",
                    "location": decision.get("selector", ""),
                    "recommended_fix": (
                        "Ensure this control performs its intended action."
                    ),
                    "source": "interaction_check",
                })

                print(
                    f"      (no DOM change on {action}, "
                    "recorded as potential defect)"
                )
            else:
                print("      (no DOM change, expected, skipped)")

        # Keep the action and result for later analysis
        trace.append({
            "action": decision.get("action"),
            "selector": decision.get("selector"),
            "value": decision.get("value", ""),
            "reason": decision.get("reason", ""),
            "result": message,
            "url_after": page.url,
        })

        if not ok:
            print(f"      (action failed: {message})")

    print(
        f"    [scenario] complete, {len(captured_pages)} states captured, "
        f"{len(trace)} steps"
    )

    return captured_pages, trace, no_change_findings


# Log in using the details provided by the user
async def _login(page, login_config):
    login_url = login_config["url"]

    await page.goto(login_url)
    await page.fill(
        login_config["username_selector"],
        login_config["username"],
    )
    await page.fill(
        login_config["password_selector"],
        login_config["password"],
    )
    await page.click(login_config["submit_selector"])
    await page.wait_for_load_state("networkidle")

    # Look for a login error message
    error_text = ""
    selectors = login_config.get(
        "error_selectors",
        DEFAULT_ERROR_SELECTORS,
    )

    try:
        element = await page.query_selector(selectors)

        if element:
            error_text = (await element.inner_text() or "").strip()
    except Exception:
        pass

    expected_url = login_config.get("success_url")

    if expected_url:
        navigated = expected_url in page.url
    else:
        navigated = page.url.rstrip("/") != login_url.rstrip("/")

    if error_text or not navigated:
        reason = (
            error_text
            or f"did not navigate away from login page: {page.url}"
        )
        raise LoginFailed(f"Login failed: {reason}")

    print(f"  Logged in as {login_config.get('username', '(unknown)')}")


# Crawl the target and collect captures, traces and interaction findings
# Login is optional and uses the same browser session
# Scenario captures can take the total beyond max_pages
async def crawl(
    url,
    run_id,
    login_config=None,
    seed_paths=None,
    max_pages=DEFAULT_MAX_PAGES,
    max_depth=DEFAULT_MAX_DEPTH,
):
    print(f"Crawl Agent starting for {url}...")

    pages_crawled = []
    all_traces = []
    all_no_change = []

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page()

        if login_config:
            await _login(page, login_config)

        # Open the target after login
        await page.goto(url)
        await page.wait_for_load_state("networkidle")

        # Use the final address if the target redirected
        start_url = page.url
        parsed_start = urlparse(start_url)
        base_domain = parsed_start.netloc
        origin = f"{parsed_start.scheme}://{parsed_start.netloc}"

        queue = [(start_url, 0)]
        queued = {start_url}
        visited = set()
        index = 0

        # Add any extra starting paths
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

            if page.url != current_url:
                await page.goto(current_url)
                await page.wait_for_load_state("networkidle")

            visited.add(current_url)

            # Capture the page before trying interactions
            index += 1
            name = _safe_name(current_url, index)

            pages_crawled.append(
                await _capture(page, run_id, name)
            )

            print(
                f"  Captured [{len(pages_crawled)}/{max_pages}] "
                f"depth={depth}: {current_url}"
            )

            elements = await _get_interactive_elements(page)

            if _is_interactive_page(elements):
                print(
                    f"    [scenario] interactive page detected: {current_url}"
                )

                scenario_pages, scenario_trace, scenario_findings = (
                    await run_scenario(page, run_id, name)
                )

                pages_crawled.extend(scenario_pages)

                # Attach the starting page and step number to each trace
                for step_number, trace_step in enumerate(scenario_trace, 1):
                    trace_step["page_url"] = current_url
                    trace_step["step"] = step_number
                    all_traces.append(trace_step)

                all_no_change.extend(scenario_findings)

                # The scenario may have navigated to another page
                if page.url != current_url:
                    await page.goto(current_url)
                    await page.wait_for_load_state("networkidle")

            if depth < max_depth:
                # Add normal links to the queue
                links = await _discover_links(
                    page,
                    base_domain,
                    visited,
                    queued,
                )

                for link in links:
                    queue.append((link, depth + 1))
                    queued.add(link)

                # Also check title links opened through JavaScript
                click_links = await _discover_by_clicking(
                    page,
                    current_url,
                    base_domain,
                    visited,
                    queued,
                )

                for link in click_links:
                    queue.append((link, depth + 1))
                    queued.add(link)

        await browser.close()

    print(
        f"Crawl Agent complete, {len(pages_crawled)} pages captured, "
        f"{len(all_traces)} trace steps, "
        f"{len(all_no_change)} no-change findings"
    )

    return pages_crawled, all_traces, all_no_change