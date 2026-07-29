# test_execute.py — verify _execute() can drive a real form, no LLM involved.
# Flow: log in -> go to checkout-step-one -> fill 3 fields -> click Continue
#       -> confirm the page advanced to checkout-step-two.


import asyncio
from playwright.async_api import async_playwright
from agents.crawl_agent import _execute, _login

SAUCEDEMO_LOGIN = {
    "url": "https://www.saucedemo.com",
    "username": "standard_user",
    "password": "secret_sauce",
    "username_selector": "#user-name",
    "password_selector": "#password",
    "submit_selector": "#login-button",
}

# A hardcoded scenario: what the LLM will eventually produce on its own.
DECISIONS = [
    {"action": "fill",  "selector": "[data-test='firstName']",  "value": "Sofia"},
    {"action": "fill",  "selector": "[data-test='lastName']",   "value": "Test"},
    {"action": "fill",  "selector": "[data-test='postalCode']", "value": "12345"},
    {"action": "click", "selector": "[data-test='continue']"},
    {"action": "done"},
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Log in, then a cart item is needed to reach checkout, so add one first.
        await _login(page, SAUCEDEMO_LOGIN)
        await page.goto("https://www.saucedemo.com/inventory.html")
        await page.click("[data-test='add-to-cart-sauce-labs-backpack']")

        # Go to checkout step one (the form we want to drive).
        await page.goto("https://www.saucedemo.com/checkout-step-one.html")
        await page.wait_for_load_state("networkidle")
        print(f"Start URL: {page.url}")

        # Run each hardcoded decision through _execute and print the result.
        for d in DECISIONS:
            ok, msg = await _execute(page, d)
            print(f"  {'OK ' if ok else 'ERR'} {d['action']:5} -> {msg}")

        # Did we advance to step two?
        print(f"End URL:   {page.url}")
        if "checkout-step-two" in page.url:
            print("SUCCESS: form filled and submitted, advanced to step two.")
        else:
            print("DID NOT ADVANCE — check the messages above.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())