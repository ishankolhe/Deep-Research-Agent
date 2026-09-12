import { AlertCircle, LoaderCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export function LoadingState({ label = "Loading research…" }: { label?: string }) { return <div className="state-panel"><LoaderCircle className="size-6 animate-spin text-primary" /><p>{label}</p></div>; }
export function ErrorState({ error, retry }: { error: unknown; retry: () => void }) { return <div className="state-panel" role="alert"><AlertCircle className="size-7 text-destructive" /><div><h2 className="font-semibold">We couldn’t load this view</h2><p className="mt-1 max-w-md text-sm text-muted-foreground">{error instanceof Error ? error.message : "Something unexpected happened."}</p></div><Button variant="outline" onClick={retry}><RefreshCw />Try again</Button></div>; }
