import sqlite3
import json
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            job_id TEXT PRIMARY KEY,
            owner_name TEXT NOT NULL,
            query TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            markdown TEXT,
            charts_json TEXT,
            images_json TEXT,
            pdf_path TEXT,
            docx_path TEXT,
            research_json TEXT,
            num_sources INTEGER DEFAULT 0,
            num_subquestions INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def save_report(job_id, owner_name, query, status, markdown, charts, images,
                 pdf_path, docx_path, research_results):
    unique_sources = set()
    for r in (research_results or []):
        for f in r.get("facts", []):
            unique_sources.add(f.get("source_url"))
    num_sources = len(unique_sources)
    num_subquestions = len(research_results or [])

    conn = _connect()
    conn.execute("""
        INSERT INTO reports (job_id, owner_name, query, status, created_at, markdown,
                              charts_json, images_json, pdf_path, docx_path, research_json,
                              num_sources, num_subquestions)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(job_id) DO UPDATE SET
            status=excluded.status, markdown=excluded.markdown, charts_json=excluded.charts_json,
            images_json=excluded.images_json, pdf_path=excluded.pdf_path, docx_path=excluded.docx_path,
            research_json=excluded.research_json, num_sources=excluded.num_sources,
            num_subquestions=excluded.num_subquestions
    """, (job_id, owner_name, query, status, datetime.now(timezone.utc).isoformat(), markdown,
          json.dumps(charts), json.dumps(images), pdf_path, docx_path,
          json.dumps(research_results or []), num_sources, num_subquestions))
    conn.commit()
    conn.close()


def get_report(job_id):
    conn = _connect()
    row = conn.execute("SELECT * FROM reports WHERE job_id = ?", (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_reports(owner_name):
    conn = _connect()
    rows = conn.execute(
        "SELECT job_id, query, status, created_at, num_sources, num_subquestions "
        "FROM reports WHERE owner_name = ? ORDER BY created_at DESC",
        (owner_name,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats(owner_name):
    conn = _connect()
    row = conn.execute(
        "SELECT COUNT(*) as total, SUM(num_sources) as total_sources, "
        "SUM(num_subquestions) as total_subquestions FROM reports "
        "WHERE owner_name = ? AND status = 'done'",
        (owner_name,),
    ).fetchone()
    recent = conn.execute(
        "SELECT query, created_at FROM reports WHERE owner_name = ? "
        "ORDER BY created_at DESC LIMIT 5",
        (owner_name,),
    ).fetchall()
    conn.close()
    return {
        "total_reports": row["total"] or 0,
        "total_sources_analyzed": row["total_sources"] or 0,
        "total_subquestions_researched": row["total_subquestions"] or 0,
        "recent_topics": [dict(r) for r in recent],
    }
