import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { BookOpen, FileText, GitBranch, Library, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ResearchComposer } from "@/features/research/research-composer";
import { api } from "@/features/research/api";
import { useOwner } from "@/features/research/owner-context";
import { ErrorState } from "@/features/research/states";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [
    { title: "Dashboard — Deep Research Agent" },
    { name: "description", content: "Launch rigorous research and review recent topics in your analytical workspace." },
    { property: "og:title", content: "Deep Research Agent Dashboard" },
    { property: "og:description", content: "Launch rigorous research and review recent topics in your analytical workspace." },
    { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" },
  ] }),
  component: Dashboard,
});

function Dashboard() {
  const { ownerName } = useOwner();
  const stats = useQuery({ queryKey: ["stats", ownerName], queryFn: () => api.stats(ownerName), enabled: Boolean(ownerName), retry: 1 });
  const cards = [
    { label: "Reports generated", value: stats.data?.total_reports, icon: FileText },
    { label: "Sources analyzed", value: stats.data?.total_sources_analyzed, icon: Library },
    { label: "Sub-questions researched", value: stats.data?.total_subquestions_researched, icon: GitBranch },
  ];
  return <div className="page-wrap dashboard-page">
    <header className="page-heading"><p className="eyebrow">Research workspace</p><h1>Good {timeOfDay()}, {ownerName || "researcher"}.</h1><p>Turn complex questions into sourced, structured analysis.</p></header>
    {stats.isError ? <ErrorState error={stats.error} retry={() => stats.refetch()} /> : <section className="stats-grid" aria-label="Research statistics">{cards.map(({ label, value, icon: Icon }) => <article className="stat-card" key={label}><span><Icon /></span><p>{label}</p>{stats.isLoading ? <Skeleton className="mt-3 h-10 w-20" /> : <strong>{(value ?? 0).toLocaleString()}</strong>}</article>)}</section>}
    <ResearchComposer />
    <section className="recent-section"><div className="section-title"><div><p className="eyebrow">Library</p><h2>Recent topics</h2></div><Button asChild variant="ghost"><Link to="/history">View history <ArrowRight /></Link></Button></div>
      {stats.data?.recent_topics?.length ? <div className="topic-list">{stats.data.recent_topics.map((topic, index) => { const value = typeof topic === "string" ? { query: topic } : topic; return value.job_id ? <Link key={`${value.query}-${index}`} to="/research/$jobId" params={{ jobId: value.job_id }} search={{ query: value.query }}><BookOpen /><span>{value.query}</span><ArrowRight /></Link> : <Link key={`${value.query}-${index}`} to="/history"><BookOpen /><span>{value.query}</span><ArrowRight /></Link>; })}</div> : !stats.isLoading && <div className="empty-inline"><BookOpen /><p>Your completed research topics will appear here.</p></div>}
    </section>
  </div>;
}
function timeOfDay() { const hour = new Date().getHours(); return hour < 12 ? "morning" : hour < 18 ? "afternoon" : "evening"; }
