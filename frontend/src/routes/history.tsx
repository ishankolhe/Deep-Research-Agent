import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Clock3, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/features/research/api";
import { useOwner } from "@/features/research/owner-context";
import { ErrorState, LoadingState } from "@/features/research/states";

export const Route = createFileRoute("/history")({ head: () => ({ meta: [
  { title: "Research History — Deep Research Agent" }, { name: "description", content: "Browse previous deep research reports and their evidence counts." },
  { property: "og:title", content: "Deep Research History" }, { property: "og:description", content: "Browse previous deep research reports and their evidence counts." },
  { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" },
] }), component: HistoryPage });
function HistoryPage() {
  const { ownerName } = useOwner();
  const history = useQuery({ queryKey: ["history", ownerName], queryFn: () => api.history(ownerName), enabled: Boolean(ownerName), retry: 1 });
  return <div className="page-wrap"><header className="page-heading"><p className="eyebrow">Archive</p><h1>Research history</h1><p>Every investigation, together in one place.</p></header>
    {history.isLoading ? <LoadingState label="Opening your research archive…" /> : history.isError ? <ErrorState error={history.error} retry={() => history.refetch()} /> : history.data?.reports.length ? <div className="history-list"><div className="history-head"><span>Topic</span><span>Date</span><span>Sources</span><span>Sub-questions</span><span>Status</span><span /></div>{history.data.reports.map((item) => <Link to="/research/$jobId" params={{ jobId: item.job_id }} search={{ query: item.query, createdAt: item.created_at }} className="history-row" key={item.job_id}><span className="history-topic">{item.query}</span><span><Clock3 />{formatDate(item.created_at)}</span><span>{item.num_sources ?? "—"}</span><span>{item.num_subquestions ?? "—"}</span><span><i data-status={item.status}>{item.status}</i></span><ArrowRight /></Link>)}</div> : <div className="empty-state"><Search /><h2>No research yet</h2><p>Start with a question and your reports will collect here.</p><Button asChild><Link to="/new-research">Start research <ArrowRight /></Link></Button></div>}
  </div>;
}
function formatDate(value: string) { const date = new Date(value); return Number.isNaN(date.getTime()) ? "Unknown date" : new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(date); }
