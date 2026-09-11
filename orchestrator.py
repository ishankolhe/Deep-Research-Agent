import os
import uuid

from agents.planner import plan_subquestions
from agents.researcher import research_subquestion
from agents.reflector import find_gaps
from agents.synthesizer import write_report
from agents.chart_agent import extract_chartable_data, render_charts, find_supporting_images
from utils.export_docx import export_docx
from utils.export_pdf import export_pdf
from utils import db

OUTPUT_ROOT = os.path.join(os.path.dirname(__file__), "outputs")

# In-memory job store for live progress polling. Completed reports are also
# persisted to SQLite (utils/db.py) so history survives server restarts.
JOBS: dict[str, dict] = {}


def _log(job_id: str, status: str, progress: int, message: str):
    job = JOBS[job_id]
    job["status"] = status
    job["progress"] = progress
    job["log"].append(message)


def start_job(query: str, owner_name: str = "guest") -> str:
    job_id = str(uuid.uuid4())[:8]
    JOBS[job_id] = {
        "query": query,
        "owner_name": owner_name,
        "status": "queued",
        "progress": 0,
        "log": [],
        "report": None,
        "error": None,
    }
    return job_id


def run_job(job_id: str, max_reflection_rounds: int = 1):
    """
    The core agent loop. Call this in a background thread/task from the API layer.
    """
    query = JOBS[job_id]["query"]
    owner_name = JOBS[job_id].get("owner_name", "guest")
    job_dir = os.path.join(OUTPUT_ROOT, job_id)
    os.makedirs(job_dir, exist_ok=True)

    try:
        _log(job_id, "planning", 5, f"Planning sub-questions for: {query}")
        subquestions = plan_subquestions(query)
        _log(job_id, "planning", 15, f"Planned {len(subquestions)} sub-questions")

        research_results = []
        _log(job_id, "researching", 20, "Researching sub-questions")
        for i, sq in enumerate(subquestions, start=1):
            _log(job_id, "researching", 20 + int(20 * i / max(len(subquestions), 1)),
                 f"[{i}/{len(subquestions)}] Researching: {sq}")
            result = research_subquestion(sq)
            _log(job_id, "researching", 20 + int(20 * i / max(len(subquestions), 1)),
                 f"[{i}/{len(subquestions)}] Found {len(result['facts'])} facts")
            research_results.append(result)
        _log(job_id, "researching", 45, "Initial research pass complete")

        for round_i in range(max_reflection_rounds):
            _log(job_id, "reflecting", 50, "Checking for coverage gaps")
            gaps = find_gaps(query, research_results)
            if not gaps:
                break
            _log(job_id, "researching", 55, f"Filling gaps: {gaps}")
            for gq in gaps:
                research_results.append(research_subquestion(gq))

        _log(job_id, "writing", 65, "Synthesizing report")
        report_md = write_report(query, research_results)

        _log(job_id, "visualizing", 75, "Extracting chartable data")
        chart_specs = extract_chartable_data(research_results)
        chart_paths = render_charts(chart_specs, os.path.join(job_dir, "charts"))

        _log(job_id, "visualizing", 82, "Finding supporting images")
        image_paths = find_supporting_images(query, subquestions, os.path.join(job_dir, "images"))

        _log(job_id, "exporting", 90, "Exporting PDF and DOCX")
        pdf_path = export_pdf(query, report_md, chart_paths, image_paths,
                               os.path.join(job_dir, "report.pdf"))
        docx_path = export_docx(query, report_md, chart_paths, image_paths,
                                 os.path.join(job_dir, "report.docx"))

        JOBS[job_id]["report"] = {
            "markdown": report_md,
            "charts": chart_paths,
            "images": image_paths,
            "pdf_path": pdf_path,
            "docx_path": docx_path,
            "research_results": research_results,  # kept for follow-up Q&A, no re-search needed
        }
        _log(job_id, "done", 100, "Report ready")

        db.save_report(
            job_id=job_id, owner_name=owner_name, query=query, status="done",
            markdown=report_md, charts=chart_paths, images=image_paths,
            pdf_path=pdf_path, docx_path=docx_path, research_results=research_results,
        )

    except Exception as e:
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error"] = str(e)
        JOBS[job_id]["log"].append(f"Error: {e}")
