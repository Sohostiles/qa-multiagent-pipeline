# Report Agent

import json

from config import chat_with_retry, REPORT_MODEL, OUTPUTS_DIR


# Group findings that describe the same defect.
# Keep the description from the first finding in each group.
def consolidate(findings):
    if len(findings) < 2:
        return findings

    print(f"Consolidating {len(findings)} findings...")

    listing = ""

    for i, finding in enumerate(findings):
        listing += (
            f"{i}: [{finding.get('issue_type', '?')}/"
            f"{finding.get('severity', '?')}] "
            f"{finding.get('description', '')} "
            f"(page: {finding.get('page_url', '')})\n"
        )

    system = """You are a QA lead grouping automated test findings.
Group findings that describe the same underlying defect observed on different
pages or in different states. Keep different defects in separate groups.

Respond ONLY with JSON:
{"clusters": [[index, index, ...], [index], ...]}

Every index must appear exactly once.
A unique finding should have its own group.
Do not invent indices."""

    response = chat_with_retry(
        model=REPORT_MODEL,
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": f"Group these findings:\n\n{listing}"
            }
        ],
        temperature=0,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content.strip()

    # Remove markdown formatting if the response uses a code block.
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        print("  Could not parse consolidation response, keeping all findings")
        return findings

    if not isinstance(result, dict):
        print("  Invalid consolidation response, keeping all findings")
        return findings

    clusters = result.get("clusters")

    if not isinstance(clusters, list):
        print("  Invalid groups, keeping all findings")
        return findings

    # Check that every finding appears exactly once.
    indices = []

    for cluster in clusters:
        if not isinstance(cluster, list) or not cluster:
            print("  Invalid group, keeping all findings")
            return findings

        for index in cluster:
            if type(index) is not int:
                print("  Invalid finding index, keeping all findings")
                return findings

            indices.append(index)

    if sorted(indices) != list(range(len(findings))):
        print("  Missing or repeated findings, keeping all findings")
        return findings

    consolidated = []
    severity_order = {"critical": 3, "major": 2, "minor": 1}

    for cluster in clusters:
        representative = findings[cluster[0]].copy()
        pages = []
        severity = representative.get("severity", "")

        for index in cluster:
            finding = findings[index]
            page = finding.get("page_url", "")

            if page and page not in pages:
                pages.append(page)

            # Keep the highest severity in the group.
            current_severity = finding.get("severity", "")

            if severity_order.get(current_severity, 0) > severity_order.get(
                severity, 0
            ):
                severity = current_severity

        representative["severity"] = severity
        representative["occurrences"] = len(cluster)
        representative["pages_affected"] = sorted(pages)
        consolidated.append(representative)

    print(
        f"  {len(findings)} findings grouped into "
        f"{len(consolidated)} distinct issues"
    )

    return consolidated


def generate_markdown(findings, run_id, username, target_url):
    print("Report Agent generating markdown report...")

    critical = [f for f in findings if f["severity"] == "critical"]
    major = [f for f in findings if f["severity"] == "major"]
    minor = [f for f in findings if f["severity"] == "minor"]

    findings_text = ""

    for finding in findings:
        pages = finding.get("pages_affected")

        if not pages:
            pages = [finding.get("page_url", "Not specified")]

        findings_text += f"""
- [{finding['severity'].upper()}] {finding['issue_type'].upper()}
  Pages affected: {', '.join(pages)}
  Occurrences: {finding.get('occurrences', 1)}
  Description: {finding['description']}
  Location: {finding.get('location', 'Not specified')}
  Recommended Fix: {finding.get('recommended_fix', 'Not specified')}
"""

    response = chat_with_retry(
        model=REPORT_MODEL,
        messages=[
            {
                "role": "system",
                "content": """You are a senior QA engineer writing a formal bug report.
Generate a clear, structured report from the provided findings.

Use this exact structure:

# QA Automated Test Report

## Summary
Brief overview of the test run and key findings.

## Test Details
- Target Application:
- User Role Tested:
- Total Issues Found:
- Critical: X | Major: X | Minor: X

## Critical & Major Findings
For each critical or major issue, include:

### [SEVERITY] Issue Title
- **Type:** visual/functional/ux
- **Pages affected:** URLs
- **Occurrences:** number of observations
- **Description:** full description
- **Recommended Fix:** your suggestion

## Minor Findings
Brief list of minor issues, including affected pages and occurrences.

## Conclusion
Overall assessment and recommended next steps.

Each finding represents one distinct issue.
Occurrences show how many findings were grouped into that issue.
Use the supplied severities and counts.
Do not invent defects or claim that unreported behaviour was tested.
If there are no findings, say no issues were reported.
Be professional, specific and actionable."""
            },
            {
                "role": "user",
                "content": f"""Generate a QA report for the following test run:

Target: {target_url}
Run ID: {run_id}
User Role: {username}
Total Issues: {len(findings)}
Critical: {len(critical)} | Major: {len(major)} | Minor: {len(minor)}

Findings:
{findings_text}"""
            }
        ],
        max_tokens=2000,
    )

    report_content = response.choices[0].message.content.strip()

    report_path = OUTPUTS_DIR / f"report_{run_id}.md"

    with open(report_path, "w", encoding="utf-8") as file:
        file.write(report_content)

    print(f"Markdown report saved to {report_path}")

    return report_content