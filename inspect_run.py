# inspect_run.py
# Pull a stored run out of the database into a clean, saveable summary
# No crawl, no agents, no API calls, just reads what is already stored
# Usage: python inspect_run.py <run_id>
#        python inspect_run.py <run_id> > run5_summary.txt   to save it

import sys
import db


def inspect(run_id):
    conn = db.get_conn()
    cursor = conn.cursor()

    # Run metadata
    cursor.execute("SELECT url, username, status, created_at FROM runs WHERE id = ?", (run_id,))
    run = cursor.fetchone()
    if not run:
        print(f"No run with id {run_id}")
        conn.close()
        return
    url, username, status, created_at = run

    print("=" * 60)
    print(f"RUN {run_id} SUMMARY")
    print("=" * 60)
    print(f"Target:   {url}")
    print(f"User:     {username}")
    print(f"Status:   {status}")
    print(f"Created:  {created_at}")

    # Pages
    cursor.execute("""
        SELECT COUNT(*), SUM(interaction) FROM pages WHERE run_id = ?
    """, (run_id,))
    total_pages, interaction_pages = cursor.fetchone()
    interaction_pages = interaction_pages or 0
    print(f"\nPages captured: {total_pages} "
          f"({interaction_pages} interaction, {total_pages - interaction_pages} passive)")

    # Findings totals
    cursor.execute("SELECT COUNT(*) FROM findings WHERE run_id = ?", (run_id,))
    total_findings = cursor.fetchone()[0]
    print(f"Total findings: {total_findings}")

    # By source
    print("\nFindings by source:")
    cursor.execute("""
        SELECT source, COUNT(*) FROM findings WHERE run_id = ?
        GROUP BY source ORDER BY source
    """, (run_id,))
    for source, count in cursor.fetchall():
        print(f"  {source or '(none)':<20} {count}")

    # By severity
    print("\nFindings by severity:")
    cursor.execute("""
        SELECT severity, COUNT(*) FROM findings WHERE run_id = ?
        GROUP BY severity ORDER BY severity
    """, (run_id,))
    for severity, count in cursor.fetchall():
        print(f"  {severity or '(none)':<20} {count}")

    # By issue type
    print("\nFindings by issue type:")
    cursor.execute("""
        SELECT issue_type, COUNT(*) FROM findings WHERE run_id = ?
        GROUP BY issue_type ORDER BY issue_type
    """, (run_id,))
    for issue_type, count in cursor.fetchall():
        print(f"  {issue_type or '(none)':<20} {count}")

    # Full findings list
    print("\n" + "=" * 60)
    print("ALL FINDINGS")
    print("=" * 60)
    cursor.execute("""
        SELECT severity, issue_type, source, confidence, page_url, description, recommended_fix
        FROM findings WHERE run_id = ?
        ORDER BY
          CASE severity WHEN 'critical' THEN 0 WHEN 'major' THEN 1 ELSE 2 END,
          source
    """, (run_id,))
    for i, row in enumerate(cursor.fetchall(), 1):
        severity, issue_type, source, confidence, page_url, description, fix = row
        print(f"\n[{i}] {severity} / {issue_type} / {source} / confidence={confidence}")
        print(f"    page: {page_url}")
        print(f"    desc: {description}")
        print(f"    fix:  {fix}")

    # Interaction trace count
    cursor.execute("SELECT COUNT(*) FROM traces WHERE run_id = ?", (run_id,))
    trace_count = cursor.fetchone()[0]
    print(f"\n\nInteraction trace steps stored: {trace_count}")

    conn.close()


if __name__ == "__main__":
    run_id = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    inspect(run_id)