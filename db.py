#  Database Setup 
## References:  https://sqlite.org/docs.html

# db.py
import sqlite3
from config import DB_PATH

def get_conn():
    return sqlite3.connect(DB_PATH)

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

    # Store each page crawled
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            url TEXT,
            screenshot_path TEXT,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
    """)

    # Store each finding from the Vision Agent
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            page_url TEXT,
            issue_type TEXT,
            description TEXT,
            severity TEXT,
            recommended_fix TEXT,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
    """)
    
    # Stores the final generated report 
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            content TEXT,
            created_at TEXT,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
    """)

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
            "INSERT INTO pages (run_id, url, screenshot_path) VALUES (?, ?, ?)",
            (run_id, page["url"], page["screenshot"])
        )
    conn.commit()
    conn.close()

def save_findings(run_id, findings):
    conn = get_conn()
    cursor = conn.cursor()
    for f in findings:
        cursor.execute(
            """INSERT INTO findings
               (run_id, page_url, issue_type, description, severity, recommended_fix)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (run_id, f["page_url"], f["issue_type"], f["description"],
             f["severity"], f.get("recommended_fix", ""))
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