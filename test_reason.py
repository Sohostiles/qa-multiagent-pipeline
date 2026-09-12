# test_reason.py
# Test the Reason Agent cheaply on a few saved DOM files
# No crawl, no full pipeline, just a few API calls
# Covers both passes, per state analysis and before/after transition analysis

from agents.reason_agent import analyse, analyse_transitions

# For the transition test we need a before and after DOM pair
# before is the passive checkout form, after is the empty submit state
CHECKOUT_BEFORE = "dom/999_3_checkout-step-one.html"
CHECKOUT_AFTER = "dom/999_3_checkout-step-one_step4.html"


def _load_dom(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return ""


# Per state test, one passive page and one interaction state
PER_STATE_PAGES = [
    {
        "url": "https://www.saucedemo.com/checkout-step-one.html",
        "dom_path": CHECKOUT_BEFORE,
    },
    {
        "url": "https://www.saucedemo.com/checkout-step-one.html",
        "dom_path": CHECKOUT_AFTER,
        "interaction": True,
        "step": 4,
        "action": "click [data-test='continue']",
        "action_reason": "test validation by submitting the form empty",
    },
]

# Transition test, one interaction state carrying a dom_before
TRANSITION_PAGES = [
    {
        "url": "https://www.saucedemo.com/checkout-step-one.html",
        "dom_path": CHECKOUT_AFTER,
        "interaction": True,
        "step": 4,
        "action": "click [data-test='continue']",
        "action_reason": "test validation by submitting the form empty",
        "dom_before_path": CHECKOUT_BEFORE,
    },
]


def _print_findings(title, findings):
    print("\n" + "=" * 50)
    print(f"{title}, {len(findings)} findings")
    print("=" * 50)
    for i, f in enumerate(findings, 1):
        print(f"\n[{i}] {f.get('issue_type')} / {f.get('severity')} "
              f"/ confidence={f.get('confidence','?')} / source={f.get('source','?')}")
        print(f"    page:  {f.get('page_url')}")
        print(f"    desc:  {f.get('description')}")
        print(f"    fix:   {f.get('recommended_fix')}")


if __name__ == "__main__":
    # Load DOM text for the per state pages
    for p in PER_STATE_PAGES:
        p["dom"] = _load_dom(p["dom_path"])

    # Load both DOMs for the transition pages
    for p in TRANSITION_PAGES:
        p["dom"] = _load_dom(p["dom_path"])
        p["dom_before"] = _load_dom(p["dom_before_path"])

    per_state = analyse(PER_STATE_PAGES)
    _print_findings("PER STATE RESULT", per_state)

    transitions = analyse_transitions(TRANSITION_PAGES)
    _print_findings("TRANSITION RESULT", transitions)