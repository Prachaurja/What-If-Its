import { api } from "./client";
import type { SourceDoc } from "./types";
export const listSources = () => api.get<SourceDoc[]>("/sources").catch(() => [] as SourceDoc[]);
export function addSource(file: File) {
  const fd = new FormData(); fd.append("file", file);
  return api.post<SourceDoc>("/sources", fd);
}
