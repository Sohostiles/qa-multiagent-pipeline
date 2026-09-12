"""
score_runs.py — score pipeline runs against the reference bug set.

Produces the per-bug detection table and recall figures for the Evaluation
chapter. All runs are scored by the SAME matching rules, so the progression
across runs 7, 8 and 10 is a like-for-like measurement rather than a judgement
made separately for each run.

Usage:
    python3 score_runs.py                 # scores runs 7, 8, 10
    python3 score_runs.py 7 8 10 16       # or name the runs
    python3 score_runs.py --csv table.csv # also write the table as CSV

Matching rule: a bug counts as detected if some finding's description contains
at least one term from EVERY term group for that bug. Requiring all groups
avoids matching "sort" alone, which appears in unrelated findings.
"""

import sys
import csv
import db

# Bugs applying to problem_user, duplicates and other-user bugs excluded.
# Term groups: a finding matches if it contains a term from every group.
# Bugs applying to problem_user; duplicates and other-user bugs excluded.
# Each bug has term groups (a finding must contain a term from EVERY group)
# and optional exclude terms (a finding containing any of these cannot match).
# Exclusions were added after inspecting the first pass, where loose terms
# matched unrelated findings.
SCORED = [
    ("BG_04", "consistency", "Product 1 description wrong",
     [["description", "text"],
      ["allthethings", "carry.all", "function call", "code snippet",
       "out of context", "out of place"]],
     ["accessible name", "alt text"]),

    ("BG_05", "consistency", "Product 6 name wrong",
     [["product titled", "product name", "product title"],
      ["out of context", "out of place", "code", "function call",
       "wrong", "incorrect", "mismatch", "inappropriate", "confuse"]],
     ["first name", "last name", "postal", "checkout", "accessible name",
      "alignment", "spacing", "two lines", "separation", "description '",
      "product description"]),

    ("BG_08", "functional", "Incorrect sort Z to A",
     [["sort", "sorting", "sorted"],
      ["no effect", "no change", "not working", "does not", "did not",
       "unchanged", "incorrect", "wrong", "fails", "failed"]],
     []),

    ("BG_09", "functional", "Sort button not working",
     [["sort", "sorting", "sorted", "product-sort"],
      ["no effect", "no change", "not working", "does not", "did not",
       "unchanged", "fails", "failed"]],
     []),

    # A dead sort control evidences every sort mode, so BG_10 and BG_11 use the
    # same rule as BG_08/BG_09. Requiring the word "price" made the score depend
    # on incidental wording rather than on what was detected.
    ("BG_10", "functional", "Incorrect sort price low to high",
     [["sort", "sorting", "sorted", "product-sort"],
      ["no effect", "no change", "not working", "does not", "did not",
       "unchanged", "incorrect", "wrong", "fails", "failed"]],
     []),

    ("BG_11", "functional", "Incorrect sort price high to low",
     [["sort", "sorting", "sorted", "product-sort"],
      ["no effect", "no change", "not working", "does not", "did not",
       "unchanged", "incorrect", "wrong", "fails", "failed"]],
     []),

    ("BG_12", "visual", "Incorrect product images",
     [["image", "images", "picture", "photo"],
      ["identical", "same", "wrong", "incorrect", "duplicate", "dog",
       "does not match", "not match", "unrelated"]],
     []),

    ("BG_13", "functional", "Add to cart buttons 3, 4, 6 not working",
     [["add to cart", "add-to-cart", "add_to_cart"],
      ["no effect", "no change", "not working", "does not", "did not",
       "unchanged", "fails", "failed"]],
     []),

    ("BG_14", "functional", "Remove buttons not displayed",
     [["remove"],
      ["not displayed", "missing", "not shown", "absent", "does not appear",
       "no effect", "no change", "not working"]],
     []),

    ("BG_15", "functional", "Incorrect navigation in full product view",
     [["product", "item"],
      ["navigat", "detail page", "full view", "product page"],
      ["incorrect", "wrong", "unexpected", "does not", "did not", "fails",
       "failed", "mismatch"]],
     ["sidebar", "menu", "burger", "about", "logout", "all items",
      "all-items", "href"]),

    ("BG_16", "functional", "Fail to add products 3, 4, 6 to cart",
     [["add to cart", "add-to-cart", "add_to_cart"],
      ["cart"],
      ["not added", "fail", "failed", "no effect", "no change", "not working",
       "does not", "did not", "empty"]],
     []),

    ("BG_17", "functional", "Fail to remove products 3, 4, 6 from cart",
     [["remove", "removal"],
      ["cart"],
      ["fail", "failed", "no effect", "no change", "not working", "does not",
       "did not"]],
     []),
]


# Several reference ids describe one underlying defect written up more than
# once (four sort modes, one broken dropdown). Class-level scoring reports what
# the tool actually detected, independent of how the reference was subdivided.
CLASSES = [
    ("Wrong product data", ["BG_04", "BG_05"]),
    ("Sort control broken", ["BG_08", "BG_09", "BG_10", "BG_11"]),
    ("Wrong product images", ["BG_12"]),
    ("Add to cart broken", ["BG_13", "BG_16"]),
    ("Remove from cart broken", ["BG_14", "BG_17"]),
    ("Product navigation", ["BG_15"]),
]


def load_findings(run_id):
    conn = db.get_conn()
    rows = conn.execute(
        "SELECT description, source, severity FROM findings WHERE run_id = ?",
        (run_id,)
    ).fetchall()
    conn.close()
    return [(str(d or "").lower(), s or "", sev or "") for d, s, sev in rows]


def matches(desc, groups, exclude):
    if any(term in desc for term in exclude):
        return False
    return all(any(term in desc for term in group) for group in groups)


def score_run(run_id):
    findings = load_findings(run_id)
    result = {}
    for bug_id, cat, title, groups, exclude in SCORED:
        hits = [(d, s) for d, s, _ in findings if matches(d, groups, exclude)]
        if hits:
            sources = sorted({s for _, s in hits})
            result[bug_id] = {"caught": True, "sources": sources,
                              "n": len(hits), "example": hits[0][0][:110],
                              "all_hits": hits}
        else:
            result[bug_id] = {"caught": False, "sources": [], "n": 0,
                              "example": "", "all_hits": []}
    return result, len(findings)


def main():
    argv = sys.argv[1:]
    if "--csv" in argv:
        i = argv.index("--csv")
        argv = argv[:i] + argv[i + 2:]
    args = [a for a in argv if not a.startswith("--")]
    runs = [int(a) for a in args] if args else [7, 8, 10]

    scores, totals = {}, {}
    for r in runs:
        scores[r], totals[r] = score_run(r)

    width = 46
    header = f"{'Bug':<7}{'Category':<13}{'Description':<{width}}"
    header += "".join(f"{'Run ' + str(r):>10}" for r in runs)
    print(header)
    print("-" * len(header))

    for bug_id, cat, title, _, _ in SCORED:
        line = f"{bug_id:<7}{cat:<13}{title[:width-2]:<{width}}"
        for r in runs:
            line += f"{('YES' if scores[r][bug_id]['caught'] else 'no'):>10}"
        print(line)

    print("-" * len(header))
    n = len(SCORED)
    line = f"{'':<7}{'':<13}{'Detected of ' + str(n):<{width}}"
    for r in runs:
        c = sum(1 for b in scores[r].values() if b["caught"])
        line += f"{str(c) + '/' + str(n):>10}"
    print(line)

    line = f"{'':<7}{'':<13}{'Recall':<{width}}"
    for r in runs:
        c = sum(1 for b in scores[r].values() if b["caught"])
        line += f"{f'{100*c/n:.0f}%':>10}"
    print(line)

    line = f"{'':<7}{'':<13}{'Total findings in run':<{width}}"
    for r in runs:
        line += f"{totals[r]:>10}"
    print(line)

    # class-level view
    print()
    ch = f"{'Defect class':<28}{'Bug ids':<26}"
    ch += "".join(f"{'Run ' + str(r):>10}" for r in runs)
    print(ch)
    print("-" * len(ch))
    for name, ids in CLASSES:
        line = f"{name:<28}{', '.join(ids):<26}"
        for r in runs:
            hit = any(scores[r][b]["caught"] for b in ids)
            line += f"{('YES' if hit else 'no'):>10}"
        print(line)
    print("-" * len(ch))
    nc = len(CLASSES)
    line = f"{'':<28}{'Classes detected':<26}"
    for r in runs:
        c = sum(1 for _, ids in CLASSES
                if any(scores[r][b]["caught"] for b in ids))
        line += f"{str(c) + '/' + str(nc):>10}"
    print(line)
    line = f"{'':<28}{'Class-level recall':<26}"
    for r in runs:
        c = sum(1 for _, ids in CLASSES
                if any(scores[r][b]["caught"] for b in ids))
        line += f"{f'{100*c/nc:.0f}%':>10}"
    print(line)

    # which component detected what, for the "by agent" column
    print("\nDetecting source per bug:")
    for r in runs:
        caught = {b: v["sources"] for b, v in scores[r].items() if v["caught"]}
        print(f"  run {r}: " + (", ".join(f"{b}={'/'.join(s)}"
                                          for b, s in caught.items()) or "none"))

    if "--verify" in sys.argv:
        last = runs[-1]
        print(f"\nALL matches for run {last} — check each one is really that bug:")
        for bug_id, _, title, _, _ in SCORED:
            v = scores[last][bug_id]
            print(f"\n  {bug_id}  {title}")
            if not v["caught"]:
                print("    (not detected)")
                continue
            for d, src in v["all_hits"]:
                print(f"    [{src}] {d[:150]}")
        return

    print("\nExample matched finding (last run scored):")
    last = runs[-1]
    for bug_id, _, _, _, _ in SCORED:
        v = scores[last][bug_id]
        if v["caught"]:
            print(f"  {bug_id}: {v['example']}")

    if "--csv" in sys.argv:
        path = sys.argv[sys.argv.index("--csv") + 1]
        with open(path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["Bug", "Category", "Description"] +
                       [f"Run {r}" for r in runs] + ["Detected by (final run)"])
            for bug_id, cat, title, _, _ in SCORED:
                w.writerow([bug_id, cat, title] +
                           ["YES" if scores[r][bug_id]["caught"] else "no"
                            for r in runs] +
                           ["/".join(scores[runs[-1]][bug_id]["sources"])])
        print(f"\nWritten to {path}")


if __name__ == "__main__":
    main()