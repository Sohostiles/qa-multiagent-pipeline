# generate_report_from_db.py
# Regenerate the report for an existing run from findings already in the DB
# Avoids re-crawling and re-analysing, so it costs only the report calls
# Usage: python generate_report_from_db.py <run_id>

import sys
import db
from agents.report_agent import generate_markdown
from utils.html_report import generate_html


def load_run(run_id):
    conn = db.get_conn()
    cursor = conn.cursor()

    # Load the run's username
    cursor.execute("SELECT username FROM runs WHERE id = ?", (run_id,))
    row = cursor.fetchone()
    username = row[0] if row else "unknown"

    # Load findings, rebuilt into the dict shape the report agent expects
    cursor.execute("""
        SELECT page_url, issue_type, description, severity,
               confidence, location, recommended_fix, source
        FROM findings WHERE run_id = ?
    """, (run_id,))
    cols = ["page_url", "issue_type", "description", "severity",
            "confidence", "location", "recommended_fix", "source"]
    findings = [dict(zip(cols, r)) for r in cursor.fetchall()]

    # Load pages for the HTML report (url and screenshot are enough)
    cursor.execute("SELECT url, screenshot_path FROM pages WHERE run_id = ?", (run_id,))
    pages = [{"url": r[0], "screenshot": r[1]} for r in cursor.fetchall()]

    conn.close()
    return username, findings, pages


if __name__ == "__main__":
    run_id = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    username, findings, pages = load_run(run_id)
    print(f"Loaded run {run_id}: {len(findings)} findings, {len(pages)} pages, user={username}")

    # Show the source breakdown so we can see the merged result
    by_source = {}
    for f in findings:
        by_source[f.get("source", "?")] = by_source.get(f.get("source", "?"), 0) + 1
    print(f"By source: {by_source}")

    report_content = generate_markdown(findings, run_id, username)
    html_path = generate_html(findings, report_content, run_id, username, pages)

    db.save_report(run_id, report_content)
    print(f"\nReport regenerated for run {run_id}")
    print(f"HTML report: {html_path}")