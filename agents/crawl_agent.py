# Crawl Agent

# agents/crawl_agent.py
import asyncio
from playwright.async_api import async_playwright
from config import SCREENSHOTS_DIR

async def crawl(url, username, password, run_id):
    print(f"Crawl Agent starting for {url} as '{username}'...")
    pages_crawled = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Login
        await page.goto(url)
        await page.fill("#user-name", username)
        await page.fill("#password", password)
        await page.click("#login-button")
        await page.wait_for_load_state("networkidle")
        print(f"  Logged in as {username}")

        # Inventory page
        screenshot_path = str(SCREENSHOTS_DIR / f"{run_id}_inventory.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        pages_crawled.append({"url": page.url, "screenshot": screenshot_path})
        print(f"  Captured inventory page")

        # Product detail page
        await page.click(".inventory_item_name >> nth=0")
        await page.wait_for_load_state("networkidle")
        screenshot_path = str(SCREENSHOTS_DIR / f"{run_id}_product.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        pages_crawled.append({"url": page.url, "screenshot": screenshot_path})
        print(f"  Captured product page")

        # Cart page
        await page.go_back()
        await page.wait_for_load_state("networkidle")
        await page.click(".btn_inventory >> nth=0")
        await page.click(".shopping_cart_link")
        await page.wait_for_load_state("networkidle")
        screenshot_path = str(SCREENSHOTS_DIR / f"{run_id}_cart.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        pages_crawled.append({"url": page.url, "screenshot": screenshot_path})
        print(f"  Captured cart page")

        # Checkout page
        await page.click("#checkout")
        await page.wait_for_load_state("networkidle")
        screenshot_path = str(SCREENSHOTS_DIR / f"{run_id}_checkout.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        pages_crawled.append({"url": page.url, "screenshot": screenshot_path})
        print(f"  Captured checkout page")

        await browser.close()

    print(f"Crawl Agent complete — {len(pages_crawled)} pages captured")
    return pages_crawled