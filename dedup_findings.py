# dedup_findings.py
# Collapse duplicate findings for a run into distinct issues, using one LLM call
# Same underlying bug reported on many pages becomes one entry
# Works on stored findings only
# The model only groups ids, descriptions come from the stored findings

import sys
import json
import db
from config import chat_with_retry, MODEL


def load_findings(run_id):
    conn = db.get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, page_url, issue_type, description, severity,
               confidence, location, recommended_fix, source
        FROM findings WHERE run_id = ?
    """, (run_id,))
    cols = ["id", "page_url", "issue_type", "description", "severity",
            "confidence", "location", "recommended_fix", "source"]
    findings = [dict(zip(cols, r)) for r in cursor.fetchall()]
    conn.close()
    return findings


def cluster_findings(findings):
    # Build a compact numbered list for the model
    lines = []
    for f in findings:
        lines.append(
            f"{f['id']}: [{f['issue_type']}/{f['severity']}] "
            f"{f['description']} (page: {f['page_url']})"
        )
    listing = "\n".join(lines)

    system = """You are a QA lead consolidating automated test findings.
Many findings describe the SAME underlying bug reported on different pages.
Group the finding ids that describe the same underlying issue.

Respond ONLY with JSON:
{"clusters": [[id, id, ...], [id], ...]}

Each inner list is one cluster of ids describing the same issue.
Every id must appear in exactly one cluster. A unique finding is its own
single-element cluster. Do not invent ids."""

    user = f"Consolidate these findings:\n\n{listing}"

    response = chat_with_retry(
        model=MODEL,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        temperature=0,
        max_tokens=2000,
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("Could not parse clustering response, returning each finding as its own cluster")
        return {"clusters": [[f["id"]] for f in findings]}


if __name__ == "__main__":
    run_id = int(sys.argv[1]) if len(sys.argv) > 1 else 10

    findings = load_findings(run_id)
    print(f"Loaded {len(findings)} findings for run {run_id}")

    result = cluster_findings(findings)
    clusters = result.get("clusters", [])
    by_id = {f["id"]: f for f in findings}

    print(f"\nConsolidated into {len(clusters)} distinct issues\n")
    print("=" * 60)
    for i, cluster_ids in enumerate(clusters, 1):
        members = [by_id[cid] for cid in cluster_ids if cid in by_id]
        if not members:
            continue
        rep = members[0]  # representative finding, description comes from stored data
        pages = sorted({m["page_url"] for m in members})
        print(f"\n[{i}] [{rep['issue_type']}/{rep['severity']}] "
              f"(seen on {len(pages)} page(s), {len(members)} raw findings)")
        print(f"    {rep['description']}")
        print(f"    Fix: {rep['recommended_fix']}")
        if len(pages) > 1:
            shown = ', '.join(p.split('/')[-1] or 'home' for p in pages)
            print(f"    Pages: {shown}")

    total_raw = len(findings)
    total_distinct = len(clusters)
    print("\n" + "=" * 60)
    print(f"Raw findings:      {total_raw}")
    print(f"Distinct issues:   {total_distinct}")
    if total_distinct:
        print(f"Duplication ratio: {total_raw / total_distinct:.1f}x")