# test_storage.py
# Cheap test of the DB storage and merge logic, no crawl and no agents
# Feeds fake pages, findings, and traces straight into the db functions
# Confirms the schema, save functions, and source tagging all work
# Reads the rows back and prints them, so no API calls and no cost

import db


# Fake pages, one passive and one interaction state
FAKE_PAGES = [
    {
        "url": "https://example.com/form",
        "screenshot": "screenshots/fake_1.png",
        "dom_path": "dom/fake_1.html",
    },
    {
        "url": "https://example.com/form",
        "screenshot": "screenshots/fake_1_step2.png",
        "dom_path": "dom/fake_1_step2.html",
        "interaction": True,
        "step": 2,
        "action": "click [data-test='submit']",
    },
]

# Fake findings from the three sources, tagged like the orchestrator would
FAKE_FINDINGS = [
    {
        "page_url": "https://example.com/form",
        "issue_type": "visual", "description": "Low contrast footer",
        "severity": "minor", "confidence": "high",
        "location": "footer", "recommended_fix": "Increase contrast",
        "source": "vision",
    },
    {
        "page_url": "https://example.com/form",
        "issue_type": "functional", "description": "Input missing label",
        "severity": "major", "confidence": "high",
        "location": "first name field", "recommended_fix": "Add a label",
        "source": "reason",
    },
    {
        "page_url": "https://example.com/form",
        "issue_type": "functional", "description": "Empty submit showed no message",
        "severity": "major", "confidence": "medium",
        "location": "form", "recommended_fix": "Show per field errors",
        "source": "reason_transition",
    },
]

# Fake traces, shaped like the crawler now produces them
FAKE_TRACES = [
    {
        "page_url": "https://example.com/form", "step": 1,
        "action": "fill", "selector": "[data-test='firstName']",
        "value": "", "reason": "test empty submit", "result": "filled with ''",
    },
    {
        "page_url": "https://example.com/form", "step": 2,
        "action": "click", "selector": "[data-test='submit']",
        "value": "", "reason": "submit the empty form", "result": "clicked",
    },
]


def _dump(table):
    conn = db.get_conn()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table} WHERE run_id = ?", (RUN_ID,))
    rows = cursor.fetchall()
    names = [d[0] for d in cursor.description]
    conn.close()
    print(f"\n{table} ({len(rows)} rows)")
    for r in rows:
        print("  " + ", ".join(f"{n}={v!r}" for n, v in zip(names, r)))


if __name__ == "__main__":
    db.init_db()
    RUN_ID = db.create_run("https://example.com/form", "test_user")
    print(f"Run ID: {RUN_ID}")

    db.save_pages(RUN_ID, FAKE_PAGES)
    db.save_findings(RUN_ID, FAKE_FINDINGS)
    db.save_traces(RUN_ID, FAKE_TRACES)
    db.update_run_status(RUN_ID, "completed")

    # Read everything back to confirm it stored correctly
    _dump("pages")
    _dump("findings")
    _dump("traces")

    # Confirm the three sources are distinguishable
    conn = db.get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT source, COUNT(*) FROM findings WHERE run_id = ? GROUP BY source",
        (RUN_ID,)
    )
    print("\nfindings by source:")
    for source, count in cursor.fetchall():
        print(f"  {source}: {count}")
    conn.close()