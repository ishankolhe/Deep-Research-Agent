# Deep Research Studio

Build the Deep Research Agent workspace application.

Key requirements and architecture:
1. Architecture & Design:
   - Analytical, editorial research workspace (NOT a chatbot or messaging interface). Think Notion / BI tool crossed with an academic paper.
   - Dark persistent left sidebar (app logo/name, navigation: Dashboard, New Research, History, and bottom user profile with initial avatar & "Change name").
   - Light background main content area with deep indigo / teal accents.
   - Typography: Serif font (like Merriweather, Georgia, or Playfair) for report body text; clean sans-serif for all UI chrome.
   - Fully mobile-responsive (collapsible sidebar / drawer, sources panel stacking below on small screens).

2. Identity & Onboarding:
   - No auth backend. On first visit, check localStorage for `owner_name`. If absent, show centered modal/dialog: "What should we call you?" with input and "Continue".
   - Persist in localStorage as `owner_name`. Allow modifying via "Change name" in the sidebar footer.
   - Pass `owner_name` in all relevant API calls.

3. Backend API Integration (Base URL: https://deep-research-agent-91oq.onrender.com):
   - POST /research with body { query, owner_name } -> returns { job_id }
   - GET /research/{job_id}/status -> returns { status, progress, log, error }. Poll every 2s while status is not 'done' or 'error'.
   - GET /research/{job_id}/report -> returns { markdown, charts, images, pdf_url, docx_url, citations } (relative URLs prefixed with API_BASE_URL).
   - POST /research/{job_id}/ask with body { question } -> returns { answer, supported }.
   - GET /history?owner_name={owner_name} -> returns { reports: [{ job_id, query, status, created_at, num_sources, num_subquestions }] }.
   - GET /stats?owner_name={owner_name} -> returns { total_reports, total_sources_analyzed, total_subquestions_researched, recent_topics }.

4. Pages & Views:
   - Dashboard:
     * 3 Stat cards from GET /stats (Reports generated, Sources analyzed, Sub-questions researched) with large numbers and subtle accent icons.
     * "Start new research" panel with textarea, "Research" button, and quick-start prompt chips ("Compare the top 3 EV battery technologies", "State of renewable energy adoption in India", "GenAI vs Agentic AI for enterprises") that pre-fill the input.
     * "Recent topics" list from stats navigating to the report or history.
     * Submitting triggers POST /research and transitions to Progress view.
   - Progress View:
     * Query heading.
     * Horizontal stage stepper: Planning → Researching → Reflecting → Writing → Visualizing → Exporting → Done with active stage highlighted in accent and completed checkmarks.
     * Live auto-scrolling terminal/audit log box showing entries from `log` array.
     * On 'done', transitions automatically to Report view. On 'error', shows plain message with retry button.
   - Report Page:
     * Header with query title, date, and "Download PDF" / "Download DOCX" links (prefixing relative urls with API_BASE_URL).
     * Main editorial column: Render markdown with rich headings, lists, tables, and serif typography. Inline citation numbers like [1] rendered as superscript accent badges.
     * Right-hand sticky "Sources" sidebar (moves below main column on mobile) listing citations with number, title, and external link icon. Clicking an inline [X] badge smoothly scrolls to and temporarily highlights the matching citation item.
     * Visuals section: Clean grid with borders for `charts` and thumbnail gallery for `images`.
     * "Explore Further" section (strictly non-chat): Single question input + "Ask" button. Calls POST /research/{job_id}/ask. Stacks Q&A cards (newest on top) with clear "Q" and "A" indicators in clean cards.
   - History Page:
     * Table/list from GET /history with query, date, status badge, sources & subquestions counts.
     * Clicking a row navigates directly to that report's page.
     * Friendly empty state with quick link to start research.

Ensure all loading, polling, error handling (including CORS or network failure fallback), and empty states are polished and robust.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/62587b5d-fb9f-4d35-b539-f44a941dd176).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
