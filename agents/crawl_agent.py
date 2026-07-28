# Crawl Agent 
# Adjust the crawler into a generic plawright crawler 
# Discovers pages at runtime instead of following a hardcoded path 
# Strategy: queue of links to visit, depth limit, and max pages limit
# Discovery links, buttons and queue the unseen once

import asyncio
import re
from playwright.async_api import async_playwright
# from tornado.web import url
from config import SCREENSHOTS_DIR, DOM_DIR
from urllib.parse import urlparse, urljoin

# Safety: buttons whose text/attrivutes match these are never clicked

DESTRUCTIVE_KEYWORDS = [
    "logout", "log out", "sign out", "signout",
    "remove", "delete", "reset", "clear", 
    "buy", "purchase", "pay", "order",
]

# Defautl crawl bounds
DEFAULT_MAX_PAGES = 20
DEFAULT_MAX_DEPTH = 5

# Build an artefact name from a URL and index.
def _safe_name(url, index):
    path = urlparse(url).path.strip("/").replace("/", "_")
    if not path:
        path = "home"
    path = re.sub(r"\.[a-zA-Z0-9]+$", "", path)
    return f"{index}_{path}"[:80]

 # Capture screenshot and DOM for the current page state.
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

#True if button text/attributes match a destructive keyword.
def _is_destructive(text):
    t = (text or "").lower()
    return any(word in t for word in DESTRUCTIVE_KEYWORDS)

# Collect same-domain, not yet seen link URLs on the current page.
async def _discover_links(page, base_domain, visited, queued):
    new_links = []
    anchors = await page.query_selector_all("a[href]")
    for a in anchors:
        href = await a.get_attribute("href")
        if not href:
            continue
        # Skip non-navigational hrefs
        # "#", "javascript", etc.
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        # Resolve relative URLs against the current page
        abs_url = await page.evaluate("(h) => new URL(h, location.href).href", href)
        print(f"    [debug link] {href} -> {abs_url}") # debug
        if urlparse(abs_url).netloc != base_domain:
            continue  # stay on the same site
        if abs_url in visited or abs_url in queued:
            continue  # loop prevention
        new_links.append(abs_url)
    return new_links

# Discover JS-only navigation targets that expose a stable identifier.
# SauceDemo tiles carry data-test="item-N-title-link" but no href, so we
# click each by its OWN selector (not by list index) — this is immune to
# DOM/state drift, since the selector always points at the same element.
async def _discover_by_clicking(page, current_url, base_domain, visited, queued):
    found = []

    # 1. Enumerate stable target selectors from ONE snapshot of the page.
    handles = await page.query_selector_all("[data-test$='-title-link']")
    selectors = []
    for h in handles:
        dt = await h.get_attribute("data-test")
        if dt:
            selectors.append(f"[data-test='{dt}']")
    print(f"    [debug] JS-click: {len(selectors)} stable targets: {selectors}")

    # 2. Visit each target by its own selector, reloading fresh each time.
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
            print(f"    [debug] {sel} -> {after}")

    # Leave the browser on the crawl page for the caller.
    if page.url != current_url:
        await page.goto(current_url)
        await page.wait_for_load_state("networkidle")


    def _id_key(url):
        m = re.search(r'id=(\d+)', url)
        return int(m.group(1)) if m else -1
    found = sorted(found, key=_id_key)

    return found


# Optional, configurable login keys
async def _login(page, login_config):
    await page.goto(login_config["url"])
    await page.fill(login_config["username_selector"], login_config["username"])
    await page.fill(login_config["password_selector"], login_config["password"])
    await page.click(login_config["submit_selector"])
    await page.wait_for_load_state("networkidle")
    print(f"  Logged in as {login_config.get('username', '(unknown)')}")


# Generic crawl. Returns a list of page dicts (url, screenshot, dom, dom_path).
 
# url: where to start crawling (post-login landing page for SauceDemo)
# login_config: if provided, log in before crawling
# max_pages: hard cap on pages captured (reproducibility + cost control)
# max_depth: how far from the start page to follow links

async def crawl(url, run_id, login_config=None, seed_paths=None,
                max_pages=DEFAULT_MAX_PAGES, max_depth=DEFAULT_MAX_DEPTH):

    print(f"Crawl Agent starting for {url}...")
    pages_crawled = []
 
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
 
        # Optional login
        if login_config:
            await _login(page, login_config)
 
        start_url = page.url if login_config else url
        parsed_start = urlparse(start_url)
        base_domain = parsed_start.netloc
        origin = f"{parsed_start.scheme}://{parsed_start.netloc}"  # e.g. https://www.saucedemo.com

        # BFS queue of (url, depth). visited/queued are sets of URLs.
        queue = [(start_url, 0)]
        queued = {start_url}
        visited = set()
        index = 0

        # Seed the queue with known entry points, resolved to absolute URLs and treated
        # exactly like discovered links, so the crawl logic stays generic.
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
 
            # Navigate (the very first item may already be loaded post-login)
            if page.url != current_url:
                await page.goto(current_url)
                await page.wait_for_load_state("networkidle")
            visited.add(current_url)
 
            # Capture this page
            index += 1
            name = _safe_name(current_url, index)
            pages_crawled.append(await _capture(page, run_id, name))
            print(f"  Captured [{len(pages_crawled)}/{max_pages}] depth={depth}: {current_url}")
 
            # Discover links on this page and queue unseen same-domain ones
            if depth < max_depth:
                # Discover links and queue unseen same-domain ones
                for link in await _discover_links(page, base_domain, visited, queued):
                    queue.append((link, depth + 1))
                    queued.add(link)

                # JS-only navigation: reach pages that have no href by clicking
                for link in await _discover_by_clicking(page, current_url, base_domain, visited, queued):
                    queue.append((link, depth + 1))
                    queued.add(link)
 
        await browser.close()
 
    print(f"Crawl Agent complete - {len(pages_crawled)} pages captured")
    return pages_crawled