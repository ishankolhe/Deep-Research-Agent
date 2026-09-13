export const API_BASE_URL = "https://deep-research-agent-91oq.onrender.com";

export type ResearchStatus = {
  status: string;
  progress?: number;
  log?: string[];
  error?: string | null;
};
export type Citation = { title?: string; url?: string; source?: string; name?: string } | string;
export type ResearchReport = {
  markdown: string;
  charts?: Array<string | { url?: string; title?: string }>;
  images?: Array<string | { url?: string; title?: string; alt?: string }>;
  pdf_url?: string | null;
  docx_url?: string | null;
  citations?: Citation[];
};
export type HistoryReport = {
  job_id: string;
  query: string;
  status: string;
  created_at: string;
  num_sources?: number;
  num_subquestions?: number;
};
export type Stats = {
  total_reports: number;
  total_sources_analyzed: number;
  total_subquestions_researched: number;
  recent_topics?: Array<string | { job_id?: string; query: string }>;
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...options?.headers },
    });
    if (!response.ok) {
      const detail = await response.text().catch(() => "");
      throw new Error(detail || `The research service returned ${response.status}.`);
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error("The research service could not be reached. Check your connection and try again.");
    }
    throw error;
  }
}

export const api = {
  startResearch: (query: string, ownerName: string, deepMode = false) =>
    request<{ job_id: string }>("/research", {
      method: "POST",
      body: JSON.stringify({ query, owner_name: ownerName, deep_mode: deepMode }),
    }),
  status: (jobId: string) => request<ResearchStatus>(`/research/${encodeURIComponent(jobId)}/status`),
  report: (jobId: string) => request<ResearchReport>(`/research/${encodeURIComponent(jobId)}/report`),
  ask: (jobId: string, question: string) =>
    request<{ answer: string; supported: boolean }>(`/research/${encodeURIComponent(jobId)}/ask`, {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
  history: (ownerName: string) =>
    request<{ reports: HistoryReport[] }>(`/history?owner_name=${encodeURIComponent(ownerName)}`),
  stats: (ownerName: string) =>
    request<Stats>(`/stats?owner_name=${encodeURIComponent(ownerName)}`),
};

export function assetUrl(value?: string | null) {
  if (!value) return "";
  try {
    return new URL(value, API_BASE_URL).toString();
  } catch {
    return "";
  }
}

export function citationDetails(citation: Citation) {
  if (typeof citation === "string") return { title: citation, url: citation.startsWith("http") ? citation : "" };
  return {
    title: citation.title ?? citation.source ?? citation.name ?? "Source",
    url: citation.url ?? "",
  };
}
