# test_crawl.py — run ONLY the Crawl Agent, in isolation.
# Usage:  python test_crawl.py
#
# This does not touch the database, the Vision/Reason agents, or reports.
# It just runs the crawler and prints what it captured, so you can confirm
# the generic crawler discovers pages correctly before wiring it deeper.

import asyncio
from agents.crawl_agent import crawl

# SauceDemo login as a generic login_config (same shape the orchestrator uses).
SAUCEDEMO_LOGIN = {
    "url": "https://www.saucedemo.com",
    "username": "standard_user",
    "password": "secret_sauce",
    "username_selector": "#user-name",
    "password_selector": "#password",
    "submit_selector": "#login-button",
}

if __name__ == "__main__":
    # run_id is just a label for the screenshot/DOM filenames here.
    run_id = 999

    pages = asyncio.run(
        crawl(
            url="https://www.saucedemo.com",
            run_id=run_id,
            login_config=SAUCEDEMO_LOGIN,
            seed_paths=["/cart.html", "/checkout-step-one.html"],
            max_pages=20,
            max_depth=5,
        )
    )

    print("\n" + "=" * 50)
    print(f"CRAWL TEST RESULT — {len(pages)} pages captured")
    print("=" * 50)
    for i, p in enumerate(pages, 1):
        dom_len = len(p.get("dom", ""))
        print(f"\n[{i}] {p['url']}")
        print(f"    screenshot: {p['screenshot']}")
        print(f"    dom_path  : {p['dom_path']}")
        print(f"    dom size  : {dom_len} chars")