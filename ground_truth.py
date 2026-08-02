# ground_truth.py
# Structured ground truth for the SauceDemo evaluation
# Source: github.com/lakshithadil/Test-Automation-for-Swag-Labs bug report (17 bugs)
#
# Each bug has:
#   id          the original BG_ id from the reference
#   user        which SauceDemo account the bug applies to
#   category    functional, visual, text, auth, performance
#   detectable  whether THIS tool can realistically detect it, with a reason
#               (vision/DOM/interaction based, no correctness oracle for text)
#   description the original bug description

GROUND_TRUTH = [
    # Login / auth, not crawled by this tool
    {"id": "BG_01", "user": "locked_out_user", "category": "auth",
     "detectable": False, "reason": "tool does not test locked_out_user login",
     "description": "locked_out_user cannot log in"},

    # Wrong product, detectable as a within-page consistency defect
    # (title / description / image disagree on the same page), not as text-correctness.
    {"id": "BG_02", "user": "standard_user", "category": "consistency",
     "detectable": True, "reason": "title/description/image mismatch visible on the product page",
     "description": "Product 1 description is wrong for standard user"},
    {"id": "BG_03", "user": "standard_user", "category": "consistency",
     "detectable": True, "reason": "title/description/image mismatch visible on the product page",
     "description": "Product 6 name is wrong for standard user"},
    {"id": "BG_04", "user": "problem_user", "category": "consistency",
     "detectable": True, "reason": "title/description/image mismatch visible on the product page",
     "description": "Product 1 description is wrong for problem user"},
    {"id": "BG_05", "user": "problem_user", "category": "consistency",
     "detectable": True, "reason": "title/description/image mismatch visible on the product page",
     "description": "Product 6 name is wrong for problem user"},
    {"id": "BG_06", "user": "problem_user", "category": "consistency",
     "detectable": True, "reason": "title/description/image mismatch visible on the product page",
     "description": "Product 1 description is wrong for problem user (duplicate of BG_04)"},
    {"id": "BG_07", "user": "problem_user", "category": "consistency",
     "detectable": True, "reason": "title/description/image mismatch visible on the product page",
     "description": "Product 6 name is wrong for problem user (duplicate of BG_05)"},

    # Sorting, the tool exercises the sort dropdown and can compare order
    {"id": "BG_08", "user": "problem_user", "category": "functional",
     "detectable": True, "reason": "interaction agent triggers sort, order checkable",
     "description": "Incorrectly sorted Z to A for problem user"},
    {"id": "BG_09", "user": "problem_user", "category": "functional",
     "detectable": True, "reason": "interaction agent triggers sort, effect checkable",
     "description": "Sort A to Z shown but sort option button not working for problem user"},
    {"id": "BG_10", "user": "problem_user", "category": "functional",
     "detectable": True, "reason": "interaction agent triggers sort, order checkable",
     "description": "Incorrectly sorted price low to high for problem user"},
    {"id": "BG_11", "user": "problem_user", "category": "functional",
     "detectable": True, "reason": "interaction agent triggers sort, order checkable",
     "description": "Incorrectly sorted price high to low for problem user"},

    # Wrong images, the Vision agent can see this
    {"id": "BG_12", "user": "problem_user", "category": "visual",
     "detectable": True, "reason": "Vision agent analyses product images",
     "description": "Incorrect product images for problem user"},

    # Cart add/remove, the interaction agent clicks these and can compare states
    {"id": "BG_13", "user": "problem_user", "category": "functional",
     "detectable": True, "reason": "interaction agent clicks add-to-cart, effect checkable",
     "description": "Add to cart buttons 3, 4 and 6 not working for problem user"},
    {"id": "BG_14", "user": "problem_user", "category": "functional",
     "detectable": True, "reason": "interaction agent, remove button state checkable",
     "description": "Remove buttons 3, 4 and 6 not displayed for problem user"},
    {"id": "BG_15", "user": "problem_user", "category": "functional",
     "detectable": True, "reason": "interaction agent navigates product view",
     "description": "Incorrect navigation of product items in full view for problem user"},
    {"id": "BG_16", "user": "problem_user", "category": "functional",
     "detectable": True, "reason": "interaction agent add-to-cart, effect checkable",
     "description": "Fail to add to cart products 3, 4 and 6 for problem user"},
    {"id": "BG_17", "user": "problem_user", "category": "functional",
     "detectable": True, "reason": "interaction agent remove-from-cart, effect checkable",
     "description": "Fail to remove from cart products 3, 4 and 6 for problem user"},
]


def summary():
    total = len(GROUND_TRUTH)
    detectable = [b for b in GROUND_TRUTH if b["detectable"]]
    by_user = {}
    for b in GROUND_TRUTH:
        by_user.setdefault(b["user"], 0)
        by_user[b["user"]] += 1
    by_cat = {}
    for b in GROUND_TRUTH:
        by_cat.setdefault(b["category"], 0)
        by_cat[b["category"]] += 1

    print(f"Total ground-truth bugs: {total}")
    print(f"Detectable by this tool: {len(detectable)}")
    print(f"Out of scope:            {total - len(detectable)}")
    print("\nBy user:")
    for u, c in by_user.items():
        print(f"  {u:<22} {c}")
    print("\nBy category:")
    for cat, c in by_cat.items():
        print(f"  {cat:<12} {c}")
    print("\nDetectable bugs (the scored subset):")
    for b in detectable:
        print(f"  {b['id']} [{b['category']}] {b['description']}")
    print("\nOut-of-scope bugs (reported, not scored):")
    for b in GROUND_TRUTH:
        if not b["detectable"]:
            print(f"  {b['id']} [{b['category']}] {b['reason']}")


if __name__ == "__main__":
    summary()