import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Check, Circle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/features/research/api";
import { ReportView } from "@/features/research/report-view";
import { ErrorState, LoadingState } from "@/features/research/states";

const stages = ["Planning", "Researching", "Reflecting", "Writing", "Visualizing", "Exporting", "Done"];
const statusAliases: Record<string, number> = { pending: 0, queued: 0, planning: 0, researching: 1, research: 1, reflecting: 2, reflection: 2, writing: 3, visualizing: 4, visualization: 4, exporting: 5, done: 6, completed: 6 };

export const Route = createFileRoute("/research/$jobId")({
  validateSearch: (search: Record<string, unknown>) => ({
    query: typeof search.query === "string" ? search.query : undefined,
    createdAt: typeof search.createdAt === "string" ? search.createdAt : undefined,
  }),
  head: () => ({ meta: [
    { title: "Research Report — Deep Research Agent" }, { name: "description", content: "Follow research progress and read the completed evidence-led report." },
    { property: "og:title", content: "Deep Research Report" }, { property: "og:description", content: "Follow research progress and read the completed evidence-led report." },
    { property: "og:type", content: "article" }, { name: "twitter:card", content: "summary_large_image" },
  ] }), component: ResearchJob,
});

function ResearchJob() {
  const { jobId } = Route.useParams();
  const search = Route.useSearch();
  const statusQuery = useQuery({
    queryKey: ["research-status", jobId], queryFn: () => api.status(jobId), retry: 1,
    refetchInterval: (query) => { const status = String(query.state.data?.status ?? "").toLowerCase(); return status === "done" || status === "completed" || status === "error" || status === "failed" ? false : 2000; },
  });
  const status = statusQuery.data;
  const normalized = String(status?.status ?? "").toLowerCase();
  const done = normalized === "done" || normalized === "completed";
  const failed = normalized === "error" || normalized === "failed";
  const reportQuery = useQuery({ queryKey: ["research-report", jobId], queryFn: () => api.report(jobId), enabled: done, retry: 1 });
  const query = search.query || extractQuery(status?.log) || "Research in progress";

  if (statusQuery.isLoading) return <LoadingState label="Connecting to your research…" />;
  if (statusQuery.isError) return <ErrorState error={statusQuery.error} retry={() => statusQuery.refetch()} />;
  if (failed) return <div className="page-wrap"><div className="empty-state"><Circle className="text-destructive" /><h1>Research stopped</h1><p>{status?.error || "The research service could not complete this request."}</p><Button asChild><Link to="/new-research"><RotateCcw />Try another query</Link></Button></div></div>;
  if (done) {
    if (reportQuery.isLoading) return <LoadingState label="Preparing the completed report…" />;
    if (reportQuery.isError) return <ErrorState error={reportQuery.error} retry={() => reportQuery.refetch()} />;
    if (reportQuery.data) return <ReportView jobId={jobId} query={query === "Research in progress" ? "Completed research" : query} report={reportQuery.data} createdAt={search.createdAt} />;
  }
  return <ProgressView query={query} status={normalized} progress={status?.progress} logs={status?.log ?? []} />;
}

function ProgressView({ query, status, progress, logs }: { query: string; status: string; progress: number | undefined; logs: string[] }) {
  const stageIndex = statusAliases[status] ?? Math.min(5, Math.floor(((progress ?? 0) / 100) * 6));
  return <div className="page-wrap progress-page"><header className="page-heading"><p className="eyebrow">Live investigation</p><h1>{query}</h1><p>The research agent is gathering, testing, and synthesizing evidence.</p></header>
    <section className="stage-panel" aria-label="Research progress"><div className="stage-meter"><span style={{ width: `${Math.max(progress ?? (stageIndex / 6) * 100, 2)}%` }} /></div><div className="stage-grid">{stages.map((stage, index) => <div key={stage} data-state={index < stageIndex ? "complete" : index === stageIndex ? "active" : "upcoming"}><span>{index < stageIndex ? <Check /> : index + 1}</span><p>{stage}</p></div>)}</div></section>
    <section className="terminal"><div className="terminal-top"><span /><span /><span /><p>Research audit log</p></div><div className="terminal-body" ref={(node) => { if (node) node.scrollTop = node.scrollHeight; }}>{logs.length ? logs.map((log, index) => <p key={`${log}-${index}`}><span>{String(index + 1).padStart(2, "0")}</span>{log}</p>) : <p><span>01</span>Initializing research plan…</p>}</div></section>
  </div>;
}
function extractQuery(log?: string[]) { const first = log?.find((item) => /query|topic/i.test(item)); return first?.replace(/^(query|topic)\s*:?\s*/i, "") ?? ""; }
