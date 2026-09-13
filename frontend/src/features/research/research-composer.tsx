import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { ArrowRight, LoaderCircle, Sparkles, GraduationCap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { api } from "./api";
import { useOwner } from "./owner-context";

export const QUICK_PROMPTS = [
  "Compare the top 3 EV battery technologies",
  "State of renewable energy adoption in India",
  "GenAI vs Agentic AI for enterprises",
];

export function ResearchComposer({ initialQuery = "", focused = false }: { initialQuery?: string; focused?: boolean }) {
  const [query, setQuery] = useState(initialQuery);
  const [deepMode, setDeepMode] = useState(false);
  const { ownerName } = useOwner();
  const navigate = useNavigate();
  const mutation = useMutation({
    mutationFn: () => api.startResearch(query.trim(), ownerName, deepMode),
    onSuccess: ({ job_id }) => navigate({
      to: "/research/$jobId",
      params: { jobId: job_id },
      search: { query: query.trim() },
    }),
  });

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (query.trim() && ownerName) mutation.mutate();
  };

  return (
    <div className={focused ? "research-composer research-composer--focused" : "research-composer"}>
      <div className="mb-5 flex items-start gap-3">
        <span className="icon-tile"><Sparkles /></span>
        <div><h2 className="text-xl font-semibold text-foreground">Start new research</h2><p className="mt-1 text-sm text-muted-foreground">Frame a question worth investigating deeply.</p></div>
      </div>
      <form onSubmit={submit}>
        <Textarea autoFocus={focused} value={query} onChange={(e) => setQuery(e.target.value)} placeholder="What would you like to understand?" className="min-h-32 resize-none border-border bg-background p-4 text-base shadow-none" />
        <div className="mt-3 flex flex-wrap gap-2">
          {QUICK_PROMPTS.map((prompt) => <Button className="prompt-chip" variant="outline" size="sm" type="button" key={prompt} onClick={() => setQuery(prompt)}>{prompt}</Button>)}
        </div>
        <div className="mt-4 flex items-start gap-3 rounded-lg border border-border bg-muted/40 p-3">
          <GraduationCap className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
          <div className="flex-1">
            <div className="flex items-center justify-between gap-3">
              <Label htmlFor="deep-mode" className="text-sm font-medium">Deep / Academic mode</Label>
              <Switch id="deep-mode" checked={deepMode} onCheckedChange={setDeepMode} />
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              Prioritizes peer-reviewed papers (arXiv, Semantic Scholar), adds a system comparison table and rigorous evidence analysis. Slower — takes several minutes.
            </p>
          </div>
        </div>
        {mutation.error && <p role="alert" className="mt-4 text-sm text-destructive">{mutation.error.message}</p>}
        <div className="mt-5 flex justify-end">
          <Button type="submit" size="lg" disabled={!query.trim() || !ownerName || mutation.isPending}>
            {mutation.isPending ? <LoaderCircle className="animate-spin" /> : <ArrowRight />} Research
          </Button>
        </div>
      </form>
    </div>
  );
}