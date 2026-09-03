import { api } from "./client";
import type { CheckSummary, CheckDetail } from "./types";

export const listChecks = () => api.get<CheckSummary[]>("/checks");
export const getCheck = (id: number) => api.get<CheckDetail>(`/checks/${id}`);
export const checkText = (title: string, text: string, options?: any) =>
  api.post<{ id: number; status: string }>("/checks/text", { title, text, ...options });
export function checkFile(file: File) {
  const fd = new FormData(); fd.append("file", file);
  return api.post<{ id: number; status: string }>("/checks", fd);
}
