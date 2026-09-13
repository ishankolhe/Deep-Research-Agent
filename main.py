import os
import json
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from orchestrator import start_job, run_job, JOBS, OUTPUT_ROOT
from agents.synthesizer import build_citation_map
from agents.qa_agent import answer_followup
from utils import db

db.init_db()

app = FastAPI(title="Deep Research Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(OUTPUT_ROOT, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=OUTPUT_ROOT), name="outputs")


class ResearchRequest(BaseModel):
    query: str
    owner_name: str = "guest"
    deep_mode: bool = False


class AskRequest(BaseModel):
    question: str


def _get_research_results(job_id: str) -> list:
    """Live jobs keep results in memory; completed jobs from a prior server run
    are read back from SQLite so history/Q&A survive restarts."""
    job = JOBS.get(job_id)
    if job and job.get("report"):
        return job["report"].get("research_results", [])
    row = db.get_report(job_id)
    if row and row.get("research_json"):
        return json.loads(row["research_json"])
    return []


@app.post("/research")
def create_research(req: ResearchRequest, background_tasks: BackgroundTasks):
    if not req.query or not req.query.strip():
        raise HTTPException(400, "query must not be empty")
    job_id = start_job(req.query.strip(), owner_name=(req.owner_name or "guest").strip(),
                        deep_mode=req.deep_mode)
    background_tasks.add_task(run_job, job_id)
    return {"job_id": job_id}


@app.get("/research/{job_id}/status")
def get_status(job_id: str):
    job = JOBS.get(job_id)
    if job:
        return {
            "status": job["status"],
            "progress": job["progress"],
            "log": job["log"],
            "error": job.get("error"),
        }
    row = db.get_report(job_id)
    if not row:
        raise HTTPException(404, "job not found")
    return {"status": row["status"], "progress": 100 if row["status"] == "done" else 0,
             "log": [], "error": None}


@app.get("/research/{job_id}/report")
def get_report(job_id: str):
    job = JOBS.get(job_id)
    report = job["report"] if job and job.get("status") == "done" else None
    row = None
    if not report:
        row = db.get_report(job_id)
        if not row or row["status"] != "done":
            raise HTTPException(409, "job not found or not finished yet")

    if report:
        markdown = report["markdown"]
        charts = [f"/outputs/{job_id}/charts/{os.path.basename(p)}" for p in report["charts"]]
        images = [f"/outputs/{job_id}/images/{os.path.basename(p)}" for p in report["images"]]
        pdf_url = f"/outputs/{job_id}/report.pdf"
        docx_url = f"/outputs/{job_id}/report.docx"
        research_results = report.get("research_results", [])
    else:
        markdown = row["markdown"]
        charts = [f"/outputs/{job_id}/charts/{os.path.basename(p)}"
                  for p in json.loads(row["charts_json"] or "[]")]
        images = [f"/outputs/{job_id}/images/{os.path.basename(p)}"
                  for p in json.loads(row["images_json"] or "[]")]
        pdf_url = f"/outputs/{job_id}/report.pdf"
        docx_url = f"/outputs/{job_id}/report.docx"
        research_results = json.loads(row["research_json"] or "[]")

    citation_map = build_citation_map(research_results)
    citations = sorted(
        [{"number": c["number"], "title": c["title"], "url": url,
          "authors": c.get("authors", []), "year": c.get("year", ""),
          "venue": c.get("venue", ""), "source_type": c.get("source_type", "web")}
         for url, c in citation_map.items()],
        key=lambda c: c["number"],
    )

    return {
        "markdown": markdown,
        "charts": charts,
        "images": images,
        "pdf_url": pdf_url,
        "docx_url": docx_url,
        "citations": citations,
    }


@app.post("/research/{job_id}/ask")
def ask_followup(job_id: str, req: AskRequest):
    research_results = _get_research_results(job_id)
    if not research_results:
        raise HTTPException(404, "no research data found for this job")
    if not req.question or not req.question.strip():
        raise HTTPException(400, "question must not be empty")
    return answer_followup(req.question.strip(), research_results)


@app.get("/history")
def get_history(owner_name: str = "guest"):
    return {"reports": db.list_reports(owner_name)}


@app.get("/stats")
def get_stats_endpoint(owner_name: str = "guest"):
    return db.get_stats(owner_name)
