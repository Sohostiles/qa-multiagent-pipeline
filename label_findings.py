# label_findings.py
# Hand-label findings with severity to train DISTILBERT

import sys
import db

# Runs to label.
DEFAULT_RUNS = [11, 12, 13, 14, 15]

VALID = {"c": "critical", "m": "major", "n": "minor", "x": "not_a_bug", "s": "skip"}

def ensure_label_table():
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS my_labels (
            finding_id INTEGER PRIMARY KEY,
            severity TEXT,
            FOREIGN KEY (finding_id) REFERENCES findings(id)
        )
    """)
    conn.commit()
    conn.close()

def load_unlablled(run_ids):
    conn = db.get_conn()
    cur = conn.cursor()
    placeholders = ",".join("?" for _ in run_ids)
    # Findings in the chosen runs that have not yet been labeled
    cur.execute(f"""
        SELECT f.id, f.issue_type, f.description, f.recommended_fix
        FROM findings f
        LEFT JOIN my_labels h ON h.finding_id = f.id
        WHERE f.run_id IN ({placeholders}) AND h.finding_id IS NULL
        ORDER BY f.id
    """, run_ids)
    rows = cur.fetchall()
    conn.close()
    return rows

def save_label(finding_id, severity):
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO my_labels (finding_id, severity) VALUES (?, ?)",
                (finding_id, severity))
    conn.commit()
    conn.close()

def progress(run_ids):
    conn = db.get_conn()
    cur = conn.cursor()
    placeholders = ",".join("?" for _ in run_ids)
    cur.execute(f"SELECT COUNT(*) FROM findings WHERE run_id IN ({placeholders})", run_ids)
    total = cur.fetchone()[0]
    cur.execute(f"""
        SELECT COUNT(*) FROM findings f
        JOIN my_labels h ON h.finding_id = f.id
        WHERE f.run_id IN ({placeholders})
    """, run_ids)
    done = cur.fetchone()[0]
    conn.close()
    return done, total 

if __name__ == "__main__":
    run_ids = DEFAULT_RUNS
    if "--runs" in sys.argv:
        run_ids = [int(x) for x in sys.argv[sys.argv.index("--runs")+1].split(",")]

    ensure_label_table()
    rows = load_unlablled(run_ids)
    done, total = progress(run_ids)

    print(f"Labeling runs {run_ids}")
    print(f"Progress: {done}/{total} already labelled, {len(rows)} to go")
    print("Keys:  [c]ritical   [m]ajor   [n]inor(minor) [x]not_a_bug [s]kip   [q]uit\n")

    for i, (fid, issue_type, desc, fix) in enumerate(rows, 1):
        print ("=" * 60)
        print(f"({i}/{len(rows)})  finding #{fid}   type: {issue_type}")
        print(f"\n  {desc}\n")
        if fix:
            print(f"  suggested fix: {fix}\n")

        while True:
            choice = input("Enter severity (c/m/n/x/s/q): ").strip().lower()
            if choice == "q":
                print("\nStopped. Progress saved, run again to continue.")
                sys.exit(0)
            if choice in VALID:
                break
            print(" invalid, use one of c/m/n/x/s/q")

        if VALID[choice] == "skip":
            print (" skipped\n")
            continue
        save_label(fid, VALID[choice])
        print (f" saved as {VALID[choice]}\n")

    done, total = progress(run_ids)
    print(f"\nDone for now. {done}/{total} labelled.")

            