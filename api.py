import sqlite3
import db
from fastapi import FastAPI, HTTPException

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