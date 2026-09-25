# Score saved runs against the reference bugs

# Imports
import sys
import csv

import db


# Reference bugs used to score problem_user runs
# Each entry contains the ID, category, title, term groups and exclusions
# A description needs at least one term from every group to match
SCORED = [
    (
        "BG_04",
        "consistency",
        "Product 1 description wrong",
        [
            ["description", "text"],
            [
                "allthethings", "carry.all", "function call",
                "code snippet", "out of context", "out of place",
            ],
        ],
        ["accessible name", "alt text"],
    ),
    (
        "BG_05",
        "consistency",
        "Product 6 name wrong",
        [
            ["product titled", "product name", "product title"],
            [
                "out of context", "out of place", "code",
                "function call", "wrong", "incorrect", "mismatch",
                "inappropriate", "confuse",
            ],
        ],
        [
            "first name", "last name", "postal", "checkout",
            "accessible name", "alignment", "spacing", "two lines",
            "separation", "description '", "product description",
        ],
    ),
    (
        "BG_08",
        "functional",
        "Incorrect sort Z to A",
        [
            ["sort", "sorting", "sorted"],
            [
                "no effect", "no change", "not working", "does not",
                "did not", "unchanged", "incorrect", "wrong",
                "fails", "failed",
            ],
        ],
        [],
    ),
    (
        "BG_09",
        "functional",
        "Sort button not working",
        [
            ["sort", "sorting", "sorted", "product-sort"],
            [
                "no effect", "no change", "not working", "does not",
                "did not", "unchanged", "fails", "failed",
            ],
        ],
        [],
    ),

    # These rules also count general sorting failures for the price modes
    (
        "BG_10",
        "functional",
        "Incorrect sort price low to high",
        [
            ["sort", "sorting", "sorted", "product-sort"],
            [
                "no effect", "no change", "not working", "does not",
                "did not", "unchanged", "incorrect", "wrong",
                "fails", "failed",
            ],
        ],
        [],
    ),
    (
        "BG_11",
        "functional",
        "Incorrect sort price high to low",
        [
            ["sort", "sorting", "sorted", "product-sort"],
            [
                "no effect", "no change", "not working", "does not",
                "did not", "unchanged", "incorrect", "wrong",
                "fails", "failed",
            ],
        ],
        [],
    ),
    (
        "BG_12",
        "visual",
        "Incorrect product images",
        [
            ["image", "images", "picture", "photo"],
            [
                "identical", "same", "wrong", "incorrect", "duplicate",
                "dog", "does not match", "not match", "unrelated",
            ],
        ],
        [],
    ),
    (
        "BG_13",
        "functional",
        "Add to cart buttons 3, 4, 6 not working",
        [
            ["add to cart", "add-to-cart", "add_to_cart"],
            [
                "no effect", "no change", "not working", "does not",
                "did not", "unchanged", "fails", "failed",
            ],
        ],
        [],
    ),
    (
        "BG_14",
        "functional",
        "Remove buttons not displayed",
        [
            ["remove"],
            [
                "not displayed", "missing", "not shown", "absent",
                "does not appear", "no effect", "no change",
                "not working",
            ],
        ],
        [],
    ),
    (
        "BG_15",
        "functional",
        "Incorrect navigation in full product view",
        [
            ["product", "item"],
            ["navigat", "detail page", "full view", "product page"],
            [
                "incorrect", "wrong", "unexpected", "does not",
                "did not", "fails", "failed", "mismatch",
            ],
        ],
        [
            "sidebar", "menu", "burger", "about", "logout",
            "all items", "all-items", "href",
        ],
    ),
    (
        "BG_16",
        "functional",
        "Fail to add products 3, 4, 6 to cart",
        [
            ["add to cart", "add-to-cart", "add_to_cart"],
            ["cart"],
            [
                "not added", "fail", "failed", "no effect", "no change",
                "not working", "does not", "did not", "empty",
            ],
        ],
        [],
    ),
    (
        "BG_17",
        "functional",
        "Fail to remove products 3, 4, 6 from cart",
        [
            ["remove", "removal"],
            ["cart"],
            [
                "fail", "failed", "no effect", "no change",
                "not working", "does not", "did not",
            ],
        ],
        [],
    ),
]


# Also score related bugs as groups
# A group counts as detected when at least one of its bugs matches
CLASSES = [
    ("Wrong product data", ["BG_04", "BG_05"]),
    ("Sort control broken", ["BG_08", "BG_09", "BG_10", "BG_11"]),
    ("Wrong product images", ["BG_12"]),
    ("Add to cart broken", ["BG_13", "BG_16"]),
    ("Remove from cart broken", ["BG_14", "BG_17"]),
    ("Product navigation", ["BG_15"]),
]


# Get the findings saved for one run
def load_findings(run_id):
    conn = db.get_conn()

    try:
        rows = conn.execute(
            """
            SELECT description, source, severity
            FROM findings
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchall()
    finally:
        conn.close()

    # Lowercase descriptions so matching ignores capital letters
    return [
        (
            str(description or "").lower(),
            source or "",
            severity or "",
        )
        for description, source, severity in rows
    ]


# Check a description against one reference bug
def matches(description, groups, exclude):
    if any(term in description for term in exclude):
        return False

    for group in groups:
        if not any(term in description for term in group):
            return False

    return True


# Score one run using the same rules as the other runs
def score_run(run_id):
    findings = load_findings(run_id)
    results = {}

    for bug_id, category, title, groups, exclude in SCORED:
        matched_findings = []

        for description, source, severity in findings:
            if matches(description, groups, exclude):
                matched_findings.append((description, source))

        sources = sorted({
            source for description, source in matched_findings
        })

        results[bug_id] = {
            "caught": bool(matched_findings),
            "sources": sources,
            "n": len(matched_findings),
            "example": (
                matched_findings[0][0][:110]
                if matched_findings else ""
            ),
            "all_hits": matched_findings,
        }

    return results, len(findings)


def main():
    args = sys.argv[1:]

    # Remove the CSV option and filename before reading run IDs
    if "--csv" in args:
        csv_index = args.index("--csv")
        args = args[:csv_index] + args[csv_index + 2:]

    run_args = [
        arg for arg in args
        if not arg.startswith("--")
    ]

    runs = [int(arg) for arg in run_args] if run_args else [7, 8, 10]

    scores = {}
    totals = {}

    for run_id in runs:
        scores[run_id], totals[run_id] = score_run(run_id)

    # Table showing which reference bugs were detected
    width = 46
    header = f"{'Bug':<7}{'Category':<13}{'Description':<{width}}"
    header += "".join(
        f"{'Run ' + str(run_id):>10}" for run_id in runs
    )

    print(header)
    print("-" * len(header))

    for bug_id, category, title, _, _ in SCORED:
        line = f"{bug_id:<7}{category:<13}{title[:width - 2]:<{width}}"

        for run_id in runs:
            detected = "YES" if scores[run_id][bug_id]["caught"] else "no"
            line += f"{detected:>10}"

        print(line)

    print("-" * len(header))

    # Count matched reference bugs, not individual findings
    bug_count = len(SCORED)
    detected_counts = {}

    for run_id in runs:
        detected_counts[run_id] = sum(
            1 for result in scores[run_id].values()
            if result["caught"]
        )

    line = f"{'':<7}{'':<13}{'Detected of ' + str(bug_count):<{width}}"

    for run_id in runs:
        count = f"{detected_counts[run_id]}/{bug_count}"
        line += f"{count:>10}"

    print(line)

    line = f"{'':<7}{'':<13}{'Recall':<{width}}"

    for run_id in runs:
        recall = 100 * detected_counts[run_id] / bug_count
        line += f"{recall:>9.0f}%"

    print(line)

    line = f"{'':<7}{'':<13}{'Total findings in run':<{width}}"

    for run_id in runs:
        line += f"{totals[run_id]:>10}"

    print(line)

    # Show the same results grouped by defect class
    print()
    class_header = f"{'Defect class':<28}{'Bug ids':<26}"
    class_header += "".join(
        f"{'Run ' + str(run_id):>10}" for run_id in runs
    )

    print(class_header)
    print("-" * len(class_header))

    for name, bug_ids in CLASSES:
        line = f"{name:<28}{', '.join(bug_ids):<26}"

        for run_id in runs:
            detected = any(
                scores[run_id][bug_id]["caught"]
                for bug_id in bug_ids
            )
            label = "YES" if detected else "no"
            line += f"{label:>10}"

        print(line)

    print("-" * len(class_header))

    class_count = len(CLASSES)
    class_counts = {}

    for run_id in runs:
        class_counts[run_id] = sum(
            1 for name, bug_ids in CLASSES
            if any(
                scores[run_id][bug_id]["caught"]
                for bug_id in bug_ids
            )
        )

    line = f"{'':<28}{'Classes detected':<26}"

    for run_id in runs:
        count = f"{class_counts[run_id]}/{class_count}"
        line += f"{count:>10}"

    print(line)

    line = f"{'':<28}{'Class-level recall':<26}"

    for run_id in runs:
        recall = 100 * class_counts[run_id] / class_count
        line += f"{recall:>9.0f}%"

    print(line)

    # Show which agents produced the matching findings
    print("\nDetecting source per bug:")

    for run_id in runs:
        detected_sources = []

        for bug_id, result in scores[run_id].items():
            if result["caught"]:
                sources = "/".join(result["sources"])
                detected_sources.append(f"{bug_id}={sources}")

        summary = ", ".join(detected_sources) or "none"
        print(f"  run {run_id}: {summary}")

    last_run = runs[-1]

    # Check all matches from the last run manually
    if "--verify" in sys.argv:
        print(f"\nAll matches for run {last_run}. Check each match:")

        for bug_id, _, title, _, _ in SCORED:
            result = scores[last_run][bug_id]
            print(f"\n  {bug_id}  {title}")

            if not result["caught"]:
                print("    (not detected)")
                continue

            for description, source in result["all_hits"]:
                print(f"    [{source}] {description[:150]}")

        return

    print("\nExample matched finding (last run scored):")

    for bug_id, _, _, _, _ in SCORED:
        result = scores[last_run][bug_id]

        if result["caught"]:
            print(f"  {bug_id}: {result['example']}")

    # Save the per-bug table if a CSV filename was provided
    if "--csv" in sys.argv:
        csv_path = sys.argv[sys.argv.index("--csv") + 1]

        with open(csv_path, "w", newline="") as file:
            writer = csv.writer(file)

            writer.writerow(
                ["Bug", "Category", "Description"]
                + [f"Run {run_id}" for run_id in runs]
                + ["Detected by (final run)"]
            )

            for bug_id, category, title, _, _ in SCORED:
                detections = [
                    "YES" if scores[run_id][bug_id]["caught"] else "no"
                    for run_id in runs
                ]

                sources = "/".join(
                    scores[last_run][bug_id]["sources"]
                )

                writer.writerow(
                    [bug_id, category, title]
                    + detections
                    + [sources]
                )

        print(f"\nWritten to {csv_path}")


if __name__ == "__main__":
    main()