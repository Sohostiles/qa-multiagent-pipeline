# The Orchestrator
import asyncio

import db
from agents.crawl_agent import crawl, LoginFailed
from agents.vision_agent import analyse as vision_analyse
from agents.reason_agent import analyse as reason_analyse, analyse_transitions
from agents.report_agent import generate_markdown, consolidate
from agents.classifier_agent import classify, split_reportable
from utils.html_report import generate_html

# SauceDemo login, expressed as a generic login_config for the crawler
# For a different site, swap this dict or pass login_config=None to skip login
SAUCEDEMO_LOGIN = {
    "url": "https://www.saucedemo.com",
    "username": "standard_user",
    "password": "secret_sauce",
    "username_selector": "#user-name",
    "password_selector": "#password",
    "submit_selector": "#login-button",
}

def run_pipeline(url, login_config, run_id=None):
    username = login_config.get("username", "anonymous") if login_config else "anonymous"

    print(f"\n{'='*50}")
    print(f"Pipeline starting")
    print(f"Target: {url}")
    print(f"User: {username}")
    print(f"{'='*50}\n")

    # Step 1, prepare the database
    db.init_db()

    # Create a run unless the API already created it
    if run_id is None:
        run_id = db.create_run(url, username)

    print(f"Run ID: {run_id}\n")

    # Step 2, crawl
    db.update_run_status(run_id, "crawling")
    try:
        pages, traces, no_change_findings = asyncio.run(crawl(url, run_id,
                                                              login_config=login_config))
    except LoginFailed as e:
        print(f"\n  {e}")
        db.update_run_status(run_id, "login_failed")
        return {"run_id": run_id, "findings": [], "login_failed": True, "reason": str(e)}
    db.save_pages(run_id, pages)
    db.save_traces(run_id, traces)

    # Step 3, analysis, Vision plus Reason per state plus Reason transitions
    db.update_run_status(run_id, "analysing")

    vision_findings = vision_analyse(pages)
    for f in vision_findings:
        f["source"] = "vision"

    reason_findings = reason_analyse(pages)          # tagged source=reason
    transition_findings = analyse_transitions(pages) # tagged source=reason_transition

    findings = vision_findings + reason_findings + transition_findings + no_change_findings

    # Step 3b, classify all findings using the same rubric.
    db.update_run_status(run_id, "classifying")
    findings = classify(findings)

    # Save all findings, including those marked as not_a_bug.
    db.save_findings(run_id, findings)

    # Separate findings to include in the reports
    findings, suppressed = split_reportable(findings)

    # Step 4, group repeated findings and generate both reports
    db.update_run_status(run_id, "reporting")
    findings = consolidate(findings)

    report_content = generate_markdown(
    findings, run_id, username, target_url=url
    )
    html_path = generate_html(
        findings, report_content, run_id, username, pages, target_url=url
    )

    # Step 5, mark complete
    db.save_report(run_id, report_content)
    db.update_run_status(run_id, "completed")

    print(f"\n{'='*50}")
    print(f"Pipeline complete")
    print(f"Run ID: {run_id}")
    print(f"Findings: {len(findings)} reported, {len(suppressed)} suppressed "
          f"(vision {len(vision_findings)}, reason {len(reason_findings)}, "
          f"transition {len(transition_findings)}, "
          f"interaction_check {len(no_change_findings)})")
    print(f"HTML report: {html_path}")
    print(f"{'='*50}\n")

    return {
        "run_id": run_id,
        "pages": pages,
        "findings": findings,
        "report": report_content,
        "html_path": html_path,
    }


if __name__ == "__main__":
    result = run_pipeline(
        url="https://www.saucedemo.com",
        login_config={**SAUCEDEMO_LOGIN, "username": "problem_user"},
    )