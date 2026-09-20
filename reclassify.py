# reclassify.py
# Re-run the Classifier Agent on findings already stored in the database.
#
# This is used instead of running the full pipeline again because new runs
# would create new finding IDs and would no longer match the labels in my_labels.


import sys
from collections import Counter

import db
from agents.classifier_agent import classify


DEFAULT_RUNS = [11, 12, 13, 14, 15]


def ensure_column():
    conn = db.get_conn()
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(findings)")
    columns = [row[1] for row in cur.fetchall()]

    if "severity_initial" not in columns:
        cur.execute(
            "ALTER TABLE findings ADD COLUMN severity_initial TEXT"
        )
        conn.commit()
        print("Added severity_initial column")

    conn.close()


def load(run_ids):
    conn = db.get_conn()

    placeholders = ",".join("?" for _ in run_ids)

    rows = conn.execute(
        f"""
        SELECT id, issue_type, description, severity
        FROM findings
        WHERE run_id IN ({placeholders})
        ORDER BY id
        """,
        run_ids
    ).fetchall()

    conn.close()

    return [
        {
            "id": finding_id,
            "issue_type": issue_type,
            "description": description,
            "severity": severity,
        }
        for finding_id, issue_type, description, severity in rows
    ]


def save(findings):
    conn = db.get_conn()
    cur = conn.cursor()

    for finding in findings:
        # Keep the first severity value so running this file again does not
        # replace the original severity with the classified one.
        cur.execute(
            """
            UPDATE findings
            SET severity_initial = COALESCE(severity_initial, ?),
                severity = ?
            WHERE id = ?
            """,
            (
                finding["severity_initial"],
                finding["severity"],
                finding["id"],
            )
        )

    conn.commit()
    conn.close()


def agreement(column, run_ids):
    # Compare the selected severity column with the human labels.
    conn = db.get_conn()

    placeholders = ",".join("?" for _ in run_ids)

    rows = conn.execute(
        f"""
        SELECT f.{column}, m.severity
        FROM my_labels m
        JOIN findings f ON f.id = m.finding_id
        WHERE f.run_id IN ({placeholders})
        AND f.{column} IS NOT NULL
        """,
        run_ids
    ).fetchall()

    conn.close()

    pairs = [
        (str(predicted or "").lower(), str(label or "").lower())
        for predicted, label in rows
    ]

    scored = [
        (predicted, label)
        for predicted, label in pairs
        if label in ("critical", "major", "minor", "not_a_bug")
    ]

    if not scored:
        return None

    correct = sum(
        1 for predicted, label in scored
        if predicted == label
    )

    high = {"critical", "major"}

    correct_two_class = sum(
        1 for predicted, label in scored
        if (predicted in high) == (label in high)
    )

    per_class = {}

    for severity in ("critical", "major", "minor", "not_a_bug"):
        predicted = [
            (p, label)
            for p, label in scored
            if p == severity
        ]

        actual = [
            (p, label)
            for p, label in scored
            if label == severity
        ]

        true_positive = sum(
            1 for p, label in predicted
            if label == severity
        )

        per_class[severity] = {
            "predicted": len(predicted),
            "actual": len(actual),
            "correct": true_positive,
            "precision": true_positive / len(predicted) if predicted else 0.0,
            "recall": true_positive / len(actual) if actual else 0.0,
        }

    return {
        "n": len(scored),
        "agree": correct,
        "acc": correct / len(scored),
        "acc2": correct_two_class / len(scored),
        "per_class": per_class,
        "not_a_bug_excluded": len(pairs) - len(scored),
    }


def show(name, result):
    if result is None:
        print(f"\n{name}: no data")
        return

    print(
        f"\n{name} "
        f"(n={result['n']}, "
        f"not_a_bug excluded: {result['not_a_bug_excluded']})"
    )

    print(
        f"  3-class agreement: "
        f"{result['agree']}/{result['n']} = "
        f"{100 * result['acc']:.0f}%"
    )

    print(
        f"  2-class agreement (high/low): "
        f"{100 * result['acc2']:.0f}%"
    )

    print(
        f"  {'class':<10}"
        f"{'predicted':>10}"
        f"{'actual':>8}"
        f"{'correct':>9}"
        f"{'prec':>7}"
        f"{'recall':>8}"
    )

    for severity, values in result["per_class"].items():
        print(
            f"  {severity:<10}"
            f"{values['predicted']:>10}"
            f"{values['actual']:>8}"
            f"{values['correct']:>9}"
            f"{100 * values['precision']:>6.0f}%"
            f"{100 * values['recall']:>7.0f}%"
        )


def main():
    runs = DEFAULT_RUNS

    if "--runs" in sys.argv:
        value = sys.argv[sys.argv.index("--runs") + 1]
        runs = [int(run_id) for run_id in value.split(",")]

    if "--compare" in sys.argv:
        before = agreement("severity_initial", runs)
        after = agreement("severity", runs)

        show(
            "BEFORE - severity from analysis agents",
            before
        )

        show(
            "AFTER - severity from Classifier Agent",
            after
        )

        if before and after:
            change = 100 * (after["acc"] - before["acc"])
            change_two_class = 100 * (
                after["acc2"] - before["acc2"]
            )

            print(
                f"\nChange: {change:+.0f} points (3-class), "
                f"{change_two_class:+.0f} points (2-class)"
            )

        return

    ensure_column()

    findings = load(runs)

    print(
        f"Loaded {len(findings)} findings "
        f"from runs {runs}"
    )

    print(
        "Current distribution:",
        dict(Counter(
            finding["severity"]
            for finding in findings
        ))
    )

    classify(findings)

    print(
        "New distribution:",
        dict(Counter(
            finding["severity"]
            for finding in findings
        ))
    )

    changed = [
        finding
        for finding in findings
        if finding["severity"] != finding["severity_initial"]
    ]

    print(
        f"{len(changed)} of {len(findings)} "
        f"findings changed severity"
    )

    if "--dry-run" in sys.argv:
        print("\nDry run, nothing written. Sample of changes:")

        for finding in changed[:15]:
            print(
                f"  [{finding['severity_initial']} -> "
                f"{finding['severity']}] "
                f"{finding['description'][:90]}"
            )

        return

    save(findings)

    print(
        "Written. Run with --compare "
        "to compare the results."
    )


if __name__ == "__main__":
    main()