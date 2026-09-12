import { createFileRoute } from "@tanstack/react-router";
import { ResearchComposer } from "@/features/research/research-composer";
export const Route = createFileRoute("/new-research")({
  head: () => ({ meta: [
    { title: "New Research — Deep Research Agent" }, { name: "description", content: "Start a new evidence-led deep research project." },
    { property: "og:title", content: "Start New Research" }, { property: "og:description", content: "Start a new evidence-led deep research project." },
    { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" },
  ] }), component: NewResearch,
});
function NewResearch() { return <div className="page-wrap narrow-page"><header className="page-heading"><p className="eyebrow">New inquiry</p><h1>What do you want to know?</h1><p>Be specific about the decision, comparison, or trend you want investigated.</p></header><ResearchComposer focused /></div>; }
