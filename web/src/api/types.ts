export interface AuthResponse { access_token: string; user: User; org_id?: number; }
export interface User { id: number; email: string; name?: string | null; }

export interface CheckSummary {
  id: number; title: string; status: "queued" | "running" | "done" | "failed";
  similarity_pct: number | null; ai_prob: number | null; created_at?: string; created_by?: string;
}
export interface Match { source_id: number; source_title: string; start_word: number; end_word: number; }
export interface SourceRow { id: number; title: string; percent: number; url?: string | null; }
export interface AiResult {
  scored: boolean; reason?: string; prob: number | null; band: [number, number] | null;
  verdict: string; note?: string; caveat?: string; detectors?: Record<string, number | null>;
  windows?: { text: string; ai: number; ai_paraphrased: number }[];
}
export interface ReportPayload {
  document_id: number; title: string; text: string;
  similarity_percent: number; word_count: number;
  sources: SourceRow[]; matches: Match[]; ai: AiResult | null;
}
export interface CheckDetail {
  id: number; status: CheckSummary["status"];
  similarity_pct: number | null; payload: ReportPayload | null;
}
export interface SourceDoc { id: number; title: string; word_count: number; }
