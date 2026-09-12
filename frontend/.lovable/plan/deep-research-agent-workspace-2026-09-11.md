# Deep Research Agent workspace

## Goal
Build a polished research workspace that feels like an editorial analysis tool rather than a chat app, using the supplied research API and browser-stored owner identity.

## Experience
- Add a persistent dark sidebar with Dashboard, New Research, History, owner profile, and Change name; use a compact drawer on mobile.
- Show first-visit and change-name dialogs backed by `owner_name` in local storage.
- Use a light paper-like workspace, deep indigo and teal accents, sans-serif interface text, and serif report prose.
- Add clear loading, empty, offline/CORS, retry, and API error states throughout.

## Pages and flows
- **Dashboard `/`**: load owner stats, show three metric cards, quick-start prompt chips, a new-research composer, and recent topics linking to available reports/history.
- **New Research `/new-research`**: focused research composer with the same quick prompts; submit `{ query, owner_name }` and navigate to the created job.
- **Research `/research/$jobId`**: poll status every two seconds, visualize all workflow stages, auto-scroll the audit log, retry failures, and switch automatically into the completed report.
- **Report view**: rich Markdown article, date and export links, inline citation badges with smooth source highlighting, sticky sources rail, chart/image galleries, and a non-chat “Explore Further” Q&A stack.
- **History `/history`**: owner-scoped report table/list with dates, status, source/sub-question counts, report navigation, retry, and an empty-state research link.

## Technical details
- Create a typed API client for the supplied base URL, including relative asset URL resolution, response validation, and readable network/CORS errors.
- Use TanStack Query for API reads and mutations; keep polling active only while a research job is unfinished.
- Add Markdown/GFM rendering with custom citation parsing and accessible report tables, links, headings, and lists.
- Keep data and UI state client-safe: local storage is read after hydration, while shareable report IDs live in route parameters.
- Add route-specific titles, descriptions, Open Graph metadata, and responsive layouts for every page.
- Verify the dashboard, onboarding, mobile navigation, job progress, failure handling, and representative completed-report rendering in the browser; use mocked API responses only for deterministic verification if the live service is unavailable.

## Scope boundary
No authentication or database will be added; identity remains browser-local exactly as requested.
