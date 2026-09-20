import sqlite3
import db
from pathlib import Path
from fastapi.responses import FileResponse, Response
from config import SCREENSHOTS_DIR
from schemas import RunRequest
from pipeline_runner import run_test

from fastapi import FastAPI, HTTPException, BackgroundTasks

app = FastAPI(title="QA Multi-Agent API")

@app.get("/")
def home():
    return {"message": "QA API is running"}

@app.get("/runs")
def get_runs():
    conn = db.get_conn()
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute(
            "SELECT id, url, username, status, created_at "
            "FROM runs ORDER BY id DESC"
        ).fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()

@app.get("/runs/{run_id}")
def get_run(run_id: int):
    conn = db.get_conn()
    conn.row_factory = sqlite3.Row

    try:
        row = conn.execute(
            "SELECT id, url, username, status, created_at "
            "FROM runs WHERE id = ?",
            (run_id,)
        ).fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="Run not found")

        return dict(row)
    finally:
        conn.close()

@app.get("/runs/{run_id}/findings")
def get_findings(run_id: int):
    conn = db.get_conn()
    conn.row_factory = sqlite3.Row

    try:
        run = conn.execute(
            "SELECT id FROM runs WHERE id = ?",
            (run_id,)
        ).fetchone()

        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")

        rows = conn.execute(
            """
            SELECT id, run_id, page_url, issue_type, description,
                   severity, confidence, location, recommended_fix, source
            FROM findings
            WHERE run_id = ?
            ORDER BY id
            """,
            (run_id,)
        ).fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()

@app.get("/findings/{finding_id}")
def get_finding(finding_id: int):
    conn = db.get_conn()
    conn.row_factory = sqlite3.Row

    try:
        row = conn.execute(
            """
            SELECT id, run_id, page_url, issue_type, description,
                   severity, confidence, location, recommended_fix, source
            FROM findings
            WHERE id = ?
            """,
            (finding_id,)
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Finding not found"
            )

        return dict(row)
    finally:
        conn.close()

# Get the pages captured during a run
@app.get("/runs/{run_id}/pages")
def get_pages(run_id: int):
    conn = db.get_conn()
    conn.row_factory = sqlite3.Row

    try:
        # Check that the run exists
        run = conn.execute(
            "SELECT id FROM runs WHERE id = ?",
            (run_id,)
        ).fetchone()

        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")

        # Get the captured pages and interaction details
        rows = conn.execute(
            """
            SELECT id, run_id, url, screenshot_path,
                   interaction, action, step
            FROM pages
            WHERE run_id = ?
            ORDER BY id
            """,
            (run_id,)
        ).fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()

# Return the screenshot for a captured page
@app.get("/pages/{page_id}/screenshot")
def get_screenshot(page_id: int):
    conn = db.get_conn()
    conn.row_factory = sqlite3.Row

    try:
        page = conn.execute(
            "SELECT screenshot_path FROM pages WHERE id = ?",
            (page_id,)
        ).fetchone()
    finally:
        conn.close()

    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")

    if not page["screenshot_path"]:
        raise HTTPException(status_code=404, detail="No screenshot saved")

    # Look for the saved filename in the current screenshots folder
    filename = Path(page["screenshot_path"]).name
    folder = SCREENSHOTS_DIR.resolve()
    screenshot = (folder / filename).resolve()

    # Only serve files inside the screenshots folder
    if screenshot.parent != folder:
        raise HTTPException(status_code=404, detail="Screenshot not found")

    if not screenshot.is_file():
        raise HTTPException(status_code=404, detail="Screenshot not found")

    return FileResponse(screenshot, media_type="image/png")

# Download the saved Markdown report for a run
@app.get("/runs/{run_id}/report")
def download_report(run_id: int):
    conn = db.get_conn()
    conn.row_factory = sqlite3.Row

    try:
        # Check that the run exists
        run = conn.execute(
            "SELECT id FROM runs WHERE id = ?",
            (run_id,)
        ).fetchone()

        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")

        # Get the latest saved report for this run
        report = conn.execute(
            """
            SELECT content FROM reports
            WHERE run_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (run_id,)
        ).fetchone()
    finally:
        conn.close()

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="No report saved for this run"
        )

    return Response(
        content=report["content"],
        media_type="text/markdown",
        headers={
            "Content-Disposition":
                f'attachment; filename="report_{run_id}.md"'
        }
    )

# Create a run using the URL and optional login details
@app.post("/runs", status_code=202)
def start_run(request: RunRequest, background_tasks: BackgroundTasks):
    db.init_db()

    url = str(request.url)
    username = "anonymous"
    login_config = None

    # Prepare login details in the format the crawler expects
    if request.login is not None:
        login = request.login
        username = login.username

        login_config = {
            "url": str(login.url),
            "username": login.username,
            "password": login.password.get_secret_value(),
            "username_selector": login.username_selector,
            "password_selector": login.password_selector,
            "submit_selector": login.submit_selector
        }

        if login.success_url is not None:
            login_config["success_url"] = str(login.success_url)

    # Save the run before starting the assessment
    run_id = db.create_run(url, username)

    background_tasks.add_task(
        run_test,
        run_id=run_id,
        url=url,
        login_config=login_config
    )

    return {
        "run_id": run_id,
        "status": "pending"
    }