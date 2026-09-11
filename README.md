# Deep Research Agent

An AI agent system that takes a research question, plans sub-questions, searches and
reads the web, reflects on gaps, and produces a structured report with citations,
charts, and images — exported as Markdown/PDF/DOCX.

## Architecture

```
User query
   │
   ▼
Planner agent          → splits query into 4-6 focused sub-questions (Gemini)
   │
   ▼
Research agents (loop)  → for each sub-question: Tavily search → Gemini summarizer
   │                       extracts facts + keeps source URLs for citation
   ▼
Reflection / gap-check  → Gemini checks: "are there unanswered sub-questions?"
   │                       if yes → loop back to Research agents with new queries
   │                       if no  → continue
   ▼
Synthesis / writer      → Gemini drafts report sections (intro, findings, conclusion)
   │                       as structured Markdown with inline citations
   ▼
Chart / image agent     → Gemini extracts numeric tables from the facts → matplotlib
   │                       charts; Pexels/Unsplash pulls supporting images
   ▼
Exporter                → assembles Markdown + charts + images → PDF / DOCX
```

This is a **hand-rolled orchestration loop** (no LangChain/LangGraph) — the state
machine (plan → research → reflect → write → visualize → export) is implemented
directly in `orchestrator.py` so every step is easy to explain in a viva/demo.

Completed reports are persisted to a local SQLite database (`utils/db.py`, file at
`data/reports.db` / `research.db`) so history, stats, and follow-up Q&A survive
server restarts — no separate database service needed.

## Stack (all free-tier)

| Component        | Service                                  | Free tier                                   |
|-------------------|--------------------------------------------|----------------------------------------------|
| LLM               | Gemini API (`gemini-3.5-flash-lite`)      | higher daily cap than standard Flash, no card needed |
| Web search        | Tavily API                                | 1,000 credits/month, no card needed          |
| Images            | Pexels API                                | 200 req/hour                                  |
| Charts            | matplotlib (local, no key)                | free                                          |
| PDF/DOCX export   | reportlab / python-docx (local)           | free                                          |
| History/stats DB  | SQLite (local file, stdlib, no key)       | free                                          |
| Backend           | FastAPI                                    | self-hosted                                   |
| Frontend          | Lovable (see `LOVABLE_PROMPT.md`)          | —                                              |

## Setup

```bash
cd deep-research-agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in GEMINI_API_KEY, TAVILY_API_KEY, PEXELS_API_KEY
uvicorn main:app --port 8000
```

## API

- `POST /research` `{ "query": "...", "owner_name": "..." }` → `{ "job_id": "..." }` — starts a job in the background
- `GET /research/{job_id}/status` → `{ "status": "planning|researching|reflecting|writing|visualizing|exporting|done|error", "progress": 0-100, "log": [...], "error": null }`
- `GET /research/{job_id}/report` → `{ "markdown", "charts": [...], "images": [...], "pdf_url", "docx_url", "citations": [{"number","title","url"}, ...] }`
- `POST /research/{job_id}/ask` `{ "question": "..." }` → `{ "answer": "...", "supported": true }` — answers using only that report's already-gathered facts, no new search
- `GET /history?owner_name=...` → `{ "reports": [{"job_id","query","status","created_at","num_sources","num_subquestions"}, ...] }`
- `GET /stats?owner_name=...` → `{ "total_reports", "total_sources_analyzed", "total_subquestions_researched", "recent_topics": [...] }`

See `LOVABLE_PROMPT.md` for the ready-to-paste prompt to generate the frontend in Lovable
against this API contract — built as a research dashboard/workspace (sidebar, history
table, report pages), deliberately not a chatbot UI.
