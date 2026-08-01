# test_vision.py
# Test the Vision Agent cheaply on a few saved screenshots
# No crawl, no full pipeline, just a couple of API calls
# Point PAGES at DOM and screenshot files already on disk from a past crawl

import asyncio
from agents.vision_agent import analyse

# One normal page and one interaction state
PAGES = [
    {
        "url": "https://www.saucedemo.com/inventory.html",
        "screenshot": "screenshots/999_1_inventory.png",
        "dom_path": "dom/999_1_inventory.html",
    },
    {
        "url": "https://www.saucedemo.com/checkout-step-one.html",
        "screenshot": "screenshots/999_3_checkout-step-one_step4.png",
        "dom_path": "dom/999_3_checkout-step-one_step4.html",
        "interaction": True,
        "step": 4,
        "action": "click [data-test='continue']",
        "action_reason": "test validation by submitting the form empty",
    },
]


def _load_dom(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    # Load the saved DOM text into each page dict, like the crawler would provide
    for p in PAGES:
        p["dom"] = _load_dom(p["dom_path"])

    findings = analyse(PAGES)

    print("\n" + "=" * 50)
    print(f"VISION TEST RESULT, {len(findings)} findings")
    print("=" * 50)
    for i, f in enumerate(findings, 1):
        print(f"\n[{i}] {f.get('issue_type')} / {f.get('severity')} "
              f"/ confidence={f.get('confidence','?')}")
        print(f"    page:  {f.get('page_url')}")
        print(f"    desc:  {f.get('description')}")
        print(f"    where: {f.get('location')}")