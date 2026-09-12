import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ArrowUpRight, Download, LoaderCircle, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, assetUrl, citationDetails, type ResearchReport } from "./api";

type QA = { question: string; answer: string; supported: boolean };

function CitationText({ text }: { text: string }) {
  const parts = text.split(/(\[\d+\])/g);
  return <>{parts.map((part, index) => {
    const match = part.match(/^\[(\d+)\]$/);
    if (!match) return part;
    const number = Number(match[1]);
    return <button key={`${part}-${index}`} type="button" className="citation-badge" aria-label={`Go to source ${number}`} onClick={() => {
      const target = document.getElementById(`source-${number}`);
      target?.scrollIntoView({ behavior: "smooth", block: "center" });
      target?.classList.add("source-highlight");
      window.setTimeout(() => target?.classList.remove("source-highlight"), 1600);
    }}>{number}</button>;
  })}</>;
}

export function ReportView({ jobId, query, report, createdAt }: { jobId: string; query: string; report: ResearchReport; createdAt?: string }) {
  const [question, setQuestion] = useState("");
  const [answers, setAnswers] = useState<QA[]>([]);
  const ask = useMutation({
    mutationFn: () => api.ask(jobId, question.trim()),
    onSuccess: (result) => { setAnswers((current) => [{ question: question.trim(), ...result }, ...current]); setQuestion(""); },
  });
  const citations = report.citations ?? [];
  const markdownComponents = useMemo(() => ({
    p: ({ children }: { children?: React.ReactNode }) => <p>{typeof children === "string" ? <CitationText text={children} /> : children}</p>,
    li: ({ children }: { children?: React.ReactNode }) => <li>{typeof children === "string" ? <CitationText text={children} /> : children}</li>,
    a: ({ href, children }: React.AnchorHTMLAttributes<HTMLAnchorElement>) => <a href={href} target="_blank" rel="noreferrer">{children}</a>,
  }), []);
  const visuals = [...(report.charts ?? []).map((item) => ({ item, kind: "Chart" })), ...(report.images ?? []).map((item) => ({ item, kind: "Image" }))];
  return <div className="page-wrap report-page">
    <header className="report-header">
      <div><p className="eyebrow">Research report</p><h1>{query}</h1><p className="mt-3 text-sm text-muted-foreground">{createdAt ? new Intl.DateTimeFormat(undefined, { dateStyle: "long" }).format(new Date(createdAt)) : "Completed research"}</p></div>
      <div className="flex flex-wrap gap-2">
        {report.pdf_url && <Button asChild variant="outline"><a href={assetUrl(report.pdf_url)} target="_blank" rel="noreferrer"><Download />PDF</a></Button>}
        {report.docx_url && <Button asChild variant="outline"><a href={assetUrl(report.docx_url)} target="_blank" rel="noreferrer"><Download />DOCX</a></Button>}
      </div>
    </header>
    <div className="report-layout">
      <article className="report-prose"><ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{report.markdown || "No report content was returned."}</ReactMarkdown></article>
      <aside className="sources-rail"><div className="sticky top-8"><h2>Sources</h2>{citations.length ? <ol>{citations.map((citation, index) => { const item = citationDetails(citation); return <li id={`source-${index + 1}`} key={`${item.title}-${index}`}><span>{index + 1}</span><div><p>{item.title}</p>{item.url && <a href={item.url} target="_blank" rel="noreferrer">Open source <ArrowUpRight /></a>}</div></li>; })}</ol> : <p className="text-sm text-muted-foreground">No citations were included.</p>}</div></aside>
    </div>
    {visuals.length > 0 && <section className="report-section"><p className="eyebrow">Evidence</p><h2>Visuals</h2><div className="visual-grid">{visuals.map(({ item, kind }, index) => { const data = typeof item === "string" ? { url: item, title: `${kind} ${index + 1}` } : item; const alt = "alt" in data && typeof data.alt === "string" ? data.alt : data.title ?? `${kind} ${index + 1}`; return <figure key={`${data.url}-${index}`}><img loading="lazy" src={assetUrl(data.url)} alt={alt} /><figcaption>{data.title ?? `${kind} ${index + 1}`}</figcaption></figure>; })}</div></section>}
    <section className="report-section explore-section"><div><p className="eyebrow">Explore further</p><h2>Ask a follow-up question</h2><p>This answer will use the evidence gathered for this report.</p></div><form onSubmit={(e) => { e.preventDefault(); if (question.trim()) ask.mutate(); }} className="ask-form"><Input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="What else should this research clarify?" /><Button disabled={!question.trim() || ask.isPending}>{ask.isPending ? <LoaderCircle className="animate-spin" /> : <Search />}Ask</Button></form>{ask.error && <p role="alert" className="text-sm text-destructive">{ask.error.message}</p>}<div className="qa-stack">{answers.map((item, index) => <article key={`${item.question}-${index}`} className="qa-card"><div><span>Q</span><p>{item.question}</p></div><div><span>A</span><p>{item.answer}</p></div>{!item.supported && <small>Answer may extend beyond the collected sources.</small>}</article>)}</div></section>
  </div>;
}
