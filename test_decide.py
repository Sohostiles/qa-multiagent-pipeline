# test_decide.py
# Watch the LLM drive a real page, step by step
# Manually runs the loop, get elements, LLM decides, execute, repeat
# Verifies decide_next_action before assembling the full run_scenario loop

import asyncio
from playwright.async_api import async_playwright
from agents.crawl_agent import (
    _login,
    _get_interactive_elements,
    decide_next_action,
    _execute,
)

SAUCEDEMO_LOGIN = {
    "url": "https://www.saucedemo.com",
    "username": "standard_user",
    "password": "secret_sauce",
    "username_selector": "#user-name",
    "password_selector": "#password",
    "submit_selector": "#login-button",
}

MAX_STEPS = 12

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Set up, log in, add an item, land on the checkout form
        await _login(page, SAUCEDEMO_LOGIN)
        await page.goto("https://www.saucedemo.com/inventory.html")
        await page.click("[data-test='add-to-cart-sauce-labs-backpack']")
        await page.goto("https://www.saucedemo.com/checkout-step-one.html")
        await page.wait_for_load_state("networkidle")

        print(f"Starting on: {page.url}\n")
        history = []

        for step in range(MAX_STEPS):
            elements = await _get_interactive_elements(page)
            decision = await decide_next_action(page.url, elements, history)
            print(f"STEP {step+1}")
            print(f"  URL:      {page.url}")
            print(f"  DECISION: {decision}")

            if decision.get("action") == "done":
                print("  LLM signalled DONE.\n")
                break

            ok, msg = await _execute(page, decision)
            print(f"  RESULT:   {'OK ' if ok else 'ERR'} {msg}\n")

            # Record what happened so the next decision has context
            history.append({
                "action": decision.get("action"),
                "selector": decision.get("selector"),
                "value": decision.get("value", ""),
                "result": msg,
            })

        print("=" * 50)
        print(f"Final URL: {page.url}")
        print(f"Steps taken: {len(history)}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())