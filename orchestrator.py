# The Orchastrator

# orchestrator.py
import asyncio
from datetime import datetime

import db
from agents.crawl_agent import crawl
from agents.vision_agent import analyse
from agents.report_agent import generate_markdown
from utils.html_report import generate_html

def run_pipeline(url, username, password):
    print(f"\n{'='*50}")
    print(f"Pipeline starting")
    print(f"Target: {url}")
    print(f"User: {username}")
    print(f"{'='*50}\n")

    # Step 1: Initialise DB and create run record
    db.init_db()
    run_id = db.create_run(url, username)
    print(f"Run ID: {run_id}\n")

    # Step 2: Crawl
    db.update_run_status(run_id, "crawling")
    pages = asyncio.run(crawl(url, username, password, run_id))
    db.save_pages(run_id, pages)

    # Step 3: Vision analysis
    db.update_run_status(run_id, "analysing")
    findings = analyse(pages)
    db.save_findings(run_id, findings)

    # Step 4: Generate reports
    db.update_run_status(run_id, "reporting")
    report_content = generate_markdown(findings, run_id, username)
    html_path = generate_html(findings, report_content, run_id, username, pages)

    # Step 5: Mark complete
    db.save_report(run_id, report_content)
    db.update_run_status(run_id, "completed")

    print(f"\n{'='*50}")
    print(f"Pipeline complete")
    print(f"Run ID: {run_id}")
    print(f"Findings: {len(findings)}")
    print(f"HTML report: {html_path}")
    print(f"{'='*50}\n")

    return {
        "run_id": run_id,
        "pages": pages,
        "findings": findings,
        "report": report_content,
        "html_path": html_path
    }

if __name__ == "__main__":
    # Run 1: standard_user (baseline - should find few or no issues)
    print("RUN 1: standard_user (baseline)")
    result_standard = run_pipeline(
        url="https://www.saucedemo.com",
        username="standard_user",
        password="secret_sauce"
    )

    # Run 2: problem_user (should find significantly more issues)
    print("RUN 2: problem_user (buggy user)")
    result_problem = run_pipeline(
        url="https://www.saucedemo.com",
        username="problem_user",
        password="secret_sauce"
    )

    # Comparison summary
    standard_findings = result_standard["findings"]
    problem_findings = result_problem["findings"]

    print("\n" + "="*50)
    print("COMPARISON SUMMARY")
    print("="*50)
    print(f"{'Metric':<30} {'standard_user':>15} {'problem_user':>15}")
    print("-"*60)
    print(f"{'Total findings':<30} {len(standard_findings):>15} {len(problem_findings):>15}")
    print(f"{'Critical':<30} {len([f for f in standard_findings if f['severity']=='critical']):>15} {len([f for f in problem_findings if f['severity']=='critical']):>15}")
    print(f"{'Major':<30} {len([f for f in standard_findings if f['severity']=='major']):>15} {len([f for f in problem_findings if f['severity']=='major']):>15}")
    print(f"{'Minor':<30} {len([f for f in standard_findings if f['severity']=='minor']):>15} {len([f for f in problem_findings if f['severity']=='minor']):>15}")
    print("="*50)