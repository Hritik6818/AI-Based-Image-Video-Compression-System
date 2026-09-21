import sqlite3
import os

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT, kind TEXT, method TEXT,
  orig_size INTEGER, new_size INTEGER,
  saving_pct REAL, psnr REAL, ssim REAL,
  score_10 REAL, verdict TEXT,
  time_ms INTEGER, params TEXT, created_at INTEGER
);
"""

def get_db(path="db/jobs.db"):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    con = sqlite3.connect(path)
    con.execute(SCHEMA)
    return con

def log_job(path, row: dict):
    con = get_db(path)
    cols = ",".join(row.keys())
    q = f"INSERT INTO jobs({cols}) VALUES({','.join('?'*len(row))})"
    cur = con.execute(q, list(row.values()))
    con.commit()
    jid = cur.lastrowid
    con.close()
    return jid
