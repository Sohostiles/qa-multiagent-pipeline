#  Database Setup 
## References:  https://sqlite.org/docs.html

import sqlite3
from config import DB_PATH

def get_conn():
    return sqlite3.connect(DB_PATH)

# Return True if a column already exists on a table
def _column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())

# Add a column only if it is missing 
def _add_column_if_missing(cursor, table, column, coltype):
    if not _column_exists(cursor, table, column):
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")

def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    # Store each pipeline run
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            username TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    """)

    #Store each page crawled
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            url TEXT,
            screenshot_path TEXT,
            dom_path TEXT,
            interaction INTEGER DEFAULT 0,
            action TEXT,
            step INTEGER,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
    """)

    #Store each finding from the Vision and Reason Agents
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            page_url TEXT,
            issue_type TEXT,
            description TEXT,
            severity TEXT,
            confidence TEXT,
            location TEXT,
            recommended_fix TEXT,
            source TEXT,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
    """)

    #Store interaction traces, one row per scenario step
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            page_url TEXT,
            step INTEGER,
            action TEXT,
            selector TEXT,
            value TEXT,
            reason TEXT,
            result TEXT,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
    """)

    #Store the final generated report 
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            content TEXT,
            created_at TEXT,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
    """)

    # Migrate an existing DB to add any missing columns
    _add_column_if_missing(cursor, "pages", "dom_path", "TEXT")
    _add_column_if_missing(cursor, "pages", "interaction", "INTEGER DEFAULT 0")
    _add_column_if_missing(cursor, "pages", "action", "TEXT")
    _add_column_if_missing(cursor, "pages", "step", "INTEGER")
    _add_column_if_missing(cursor, "findings", "confidence", "TEXT")
    _add_column_if_missing(cursor, "findings", "location", "TEXT")
    _add_column_if_missing(cursor, "findings", "source", "TEXT")

    conn.commit()
    conn.close()
    print("Database initialised")

def create_run(url, username):
    from datetime import datetime
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO runs (url, username, status, created_at) VALUES (?, ?, ?, ?)",
        (url, username, "pending", datetime.now().isoformat())
    )
    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id

def update_run_status(run_id, status):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE runs SET status = ? WHERE id = ?",
        (status, run_id)
    )
    conn.commit()
    conn.close()

def save_pages(run_id, pages):
    conn = get_conn()
    cursor = conn.cursor()
    for page in pages:
        cursor.execute(
            """INSERT INTO pages
               (run_id, url, screenshot_path, dom_path, interaction, action, step)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (run_id, page["url"], page.get("screenshot", ""),
             page.get("dom_path", ""),
             1 if page.get("interaction") else 0,
             page.get("action", ""),
             page.get("step"))
        )
    conn.commit()
    conn.close()

# Store the interaction trace for a run, one row per scenario step
def save_traces(run_id, traces):
    conn = get_conn()
    cursor = conn.cursor()
    for t in traces:
        cursor.execute(
            """INSERT INTO traces
               (run_id, page_url, step, action, selector, value, reason, result)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, t.get("page_url", ""), t.get("step"),
             t.get("action", ""), t.get("selector", ""), t.get("value", ""),
             t.get("reason", ""), t.get("result", ""))
        )
    conn.commit()
    conn.close()

def save_findings(run_id, findings):
    conn = get_conn()
    cursor = conn.cursor()
    for f in findings:
        cursor.execute(
            """INSERT INTO findings
               (run_id, page_url, issue_type, description, severity,
                confidence, location, recommended_fix, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, f.get("page_url", ""), f.get("issue_type", ""),
             f.get("description", ""), f.get("severity", ""),
             f.get("confidence", ""), f.get("location", ""),
             f.get("recommended_fix", ""), f.get("source", ""))
        )
    conn.commit()
    conn.close()

def save_report(run_id, content):
    from datetime import datetime
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reports (run_id, content, created_at) VALUES (?, ?, ?)",
        (run_id, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()