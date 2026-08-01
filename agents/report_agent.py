# Report Agent 

from datetime import datetime
from config import chat_with_retry, client, MODEL, OUTPUTS_DIR

def generate_markdown(findings, run_id, username):
    print("Report Agent generating markdown report...")

    critical = [f for f in findings if f["severity"] == "critical"]
    major = [f for f in findings if f["severity"] == "major"]
    minor = [f for f in findings if f["severity"] == "minor"]

    findings_text = ""
    for f in findings:
        findings_text += f"""
- [{f['severity'].upper()}] {f['issue_type'].upper()} on {f['page_url']}
  Description: {f['description']}
  Location: {f.get('location', 'Not specified')}
  Recommended Fix: {f.get('recommended_fix', 'Not specified')}
"""

    response = chat_with_retry(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """You are a senior QA engineer writing a formal bug report. 
                                Generate a clear, structured incident report from the provided findings.

                                Use this exact structure:

                                # QA Automated Test Report

                                ## Summary
                                Brief overview of the test run and key findings.

                                ## Test Details
                                - Target Application: 
                                - User Role Tested:
                                - Pages Analysed:
                                - Total Issues Found:
                                - Critical: X | Major: X | Minor: X

                                ## Critical & Major Findings
                                For each critical/major issue, include:
                                ### [SEVERITY] Issue Title
                                - **Type:** visual/functional/ux
                                - **Page:** url
                                - **Description:** full description
                                - **Recommended Fix:** your suggestion

                                ## Minor Findings
                                Brief list of minor issues.

                                ## Conclusion
                                Overall assessment and recommended next steps.

                                Be professional, specific and actionable."""
                                            },
                                            {
                                                "role": "user",
                                                "content": f"""Generate a QA report for the following test run:

                                Target: https://www.saucedemo.com
                                User Role: {username}
                                Total Findings: {len(findings)} ({len(critical)} critical, {len(major)} major, {len(minor)} minor)

                                Findings:
                                {findings_text}"""
                                            }
                                        ],
                                        max_tokens=2000
                                    )

    report_content = response.choices[0].message.content.strip()

    report_path = OUTPUTS_DIR / f"report_{run_id}_{username}.md"
    with open(report_path, "w", encoding="utf-8") as file:
        file.write(report_content)

    print(f"Markdown report saved to {report_path}")
    return report_content