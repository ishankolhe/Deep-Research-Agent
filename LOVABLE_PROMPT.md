Paste everything below into Lovable to generate the frontend.
Before pasting: deploy the backend (see README.md) somewhere reachable
(Render/Railway free tier, or your own server) and replace API_BASE_URL
in the prompt with that URL.

------------------------------------------------------------------

Build "Deep Research Agent" — a research workspace, NOT a chatbot. There is
no chat thread anywhere in this app. It should feel like a focused analytics/
research tool: a persistent sidebar, a dashboard, a history table, and
document-style report pages. Think Notion or a BI dashboard crossed with a
research paper, not a messaging app.

IDENTITY (no real auth — name only):
On first visit, if no name is saved in local storage, show a small centered
card: "What should we call you?" with a text input and a "Continue" button.
Save the name to local storage as `owner_name` and send it as a field/param
on every relevant API call below. Show the name in the sidebar footer with a
small "Change name" link that re-opens that same card.

BACKEND API (already built — call it directly, do not invent your own backend logic):
Base URL: API_BASE_URL (replace with the deployed FastAPI URL)

1. POST {API_BASE_URL}/research
   Body: { "query": string, "owner_name": string }
   Response: { "job_id": string }

2. GET {API_BASE_URL}/research/{job_id}/status
   Response: {
     "status": "planning" | "researching" | "reflecting" | "writing" | "visualizing" | "exporting" | "done" | "error",
     "progress": number (0-100),
     "log": string[],
     "error": string | null
   }
   Poll every 2 seconds while status is not "done"/"error".

3. GET {API_BASE_URL}/research/{job_id}/report
   Only call once status is "done". Response: {
     "markdown": string,
     "charts": string[]       (relative paths, prefix with API_BASE_URL),
     "images": string[]       (relative paths, prefix with API_BASE_URL),
     "pdf_url": string        (relative path, prefix with API_BASE_URL),
     "docx_url": string       (relative path, prefix with API_BASE_URL),
     "citations": [{ "number": int, "title": string, "url": string }, ...]
   }

4. POST {API_BASE_URL}/research/{job_id}/ask
   Body: { "question": string }
   Response: { "answer": string, "supported": boolean }
   This answers a follow-up question using only that report's already-gathered
   sources (no new search). Render results as growing "Explore Further" cards
   on the report page — see below. NEVER render this as a chat bubble UI.

5. GET {API_BASE_URL}/history?owner_name=string
   Response: { "reports": [{ "job_id", "query", "status", "created_at",
                              "num_sources", "num_subquestions" }, ...] }

6. GET {API_BASE_URL}/stats?owner_name=string
   Response: { "total_reports": int, "total_sources_analyzed": int,
               "total_subquestions_researched": int,
               "recent_topics": [{ "query", "created_at" }, ...] }

LAYOUT (persistent sidebar, all pages):
- Left sidebar, dark theme: app name/logo top, then nav items "Dashboard",
  "New Research", "History"; at the very bottom, the user's name (from local
  storage) with a small avatar-style initial circle and a "Change name" link.
- Main content area to the right, light background, switches per page below.

PAGES:

1. Dashboard (default landing page after the name is set)
   - Row of 3 stat cards across the top, pulled from GET /stats: "Reports
     generated", "Sources analyzed", "Sub-questions researched" — big number,
     small label, subtle accent-colored icon.
   - Below that, a "Start new research" panel: a multiline text input with a
     "Research" button, and beneath it a row of quick-start example chips
     (e.g. "Compare the top 3 EV battery technologies", "State of renewable
     energy adoption in India", "GenAI vs Agentic AI for enterprises") that
     fill the input when clicked.
   - Below that, "Recent topics" — a short list from `recent_topics`, each
     row clickable, navigating to History filtered/scrolled to that report
     (or directly to its report page if you already have its job_id).
   - On submitting the research input: POST /research with the name, store
     job_id, navigate to the Progress view (not a separate route necessarily
     — can be a modal/overlay or a page, your choice, but must show the
     stepper described below).

2. Progress view (shown right after submitting a query)
   - Shows the query as a heading.
   - A horizontal stepper across stages: Planning → Researching → Reflecting
     → Writing → Visualizing → Exporting → Done, current stage highlighted
     in the accent color, completed stages checked off.
   - Below it, a live activity log panel (styled like a clean terminal/audit
     log, not a chat) auto-scrolling as new `log` entries arrive from polling.
   - On "done": automatically transition to the Report page for that job_id.
   - On "error": show the error message plainly with a "Try again" button
     back to the Dashboard.

3. Report page
   - Header: query as the title, generated date, two buttons top-right
     ("Download PDF", "Download DOCX" linking to pdf_url/docx_url).
   - Main column: render `markdown` as formatted rich text — real heading
     hierarchy, bold, bullet/numbered lists, and any tables. Render inline
     citation numbers like [1] as small clickable superscript badges in the
     accent color.
   - Right-hand sidebar panel (collapses below the main column on mobile):
     "Sources" — one row per entry in `citations` (number, title, link icon
     to the url). Clicking a citation badge in the main text scrolls to and
     briefly highlights its matching row in this panel.
   - Below the main content: a "Visuals" section showing chart images in a
     clean grid with light borders, then a small photo gallery row for
     `images`.
   - At the very bottom: an "Explore Further" section — NOT a chat interface.
     A single text input with an "Ask" button. Each submission calls
     POST /research/{job_id}/ask and appends a new card above the input:
     a card with a small "Q" label and the question, then an "A" label and
     the answer text below it, in a clean bordered card (like an FAQ/notes
     list, stacking newest on top). No avatars, no message bubbles, no
     left/right alignment.

4. History page
   - A clean table/list from GET /history: columns for query, date, status,
     and a small badge showing sources/sub-questions count. Sorted newest
     first. Clicking a row navigates straight to that report's Report page
     (skip the progress view — call GET /research/{job_id}/report directly).
   - Empty state: friendly message + a "Start your first research" button
     back to the Dashboard.

DESIGN:
- Overall tone: clean, editorial, analytical — a cross between a research
  paper and a modern BI/analytics dashboard. Generous whitespace.
- Sidebar: dark (near-black or deep indigo). Main content: light background.
- Accent color: deep indigo or teal, used sparingly for the stepper, buttons,
  citation badges, and stat card icons — everything else neutral gray/white.
- Serif font for report body text (the actual research content); sans-serif
  for all UI chrome (nav, buttons, labels, stat cards).
- Mobile responsive: sidebar collapses to a bottom nav or hamburger; the
  report's sources panel moves below the main content instead of beside it.

STATE / DATA:
- No real authentication — the name-only identity described above is enough.
- No frontend database — all state comes from the API and local storage
  (only the `owner_name` string lives in local storage).
- Handle loading and error states gracefully everywhere (network failure,
  404 job not found, empty query submission, empty history).

------------------------------------------------------------------
