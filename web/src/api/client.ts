// Thin fetch wrapper: attaches the JWT, sends X-Org-Id, normalises errors.
const BASE = import.meta.env.VITE_API_URL || "/api/v1";

let accessToken: string | null = localStorage.getItem("swipe_token");
let orgId: string | null = localStorage.getItem("swipe_org");

export function setAuth(token: string | null, org?: number | null) {
  accessToken = token;
  if (token) localStorage.setItem("swipe_token", token);
  else localStorage.removeItem("swipe_token");
  if (org !== undefined) {
    orgId = org != null ? String(org) : null;
    if (orgId) localStorage.setItem("swipe_org", orgId);
    else localStorage.removeItem("swipe_org");
  }
}
export const getToken = () => accessToken;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) { super(message); this.status = status; }
}

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { ...(opts.headers as any) };
  if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;
  if (orgId) headers["X-Org-Id"] = orgId;
  if (opts.body && !(opts.body instanceof FormData)) headers["Content-Type"] = "application/json";

  const res = await fetch(BASE + path, { ...opts, headers });
  if (!res.ok) {
    let msg = res.statusText;
    try { const j = await res.json(); msg = j.detail || j.error?.message || msg; } catch {}
    throw new ApiError(res.status, msg);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T>(p: string) => req<T>(p),
  post: <T>(p: string, body?: any) => req<T>(p, { method: "POST", body: body instanceof FormData ? body : JSON.stringify(body) }),
  del: <T>(p: string) => req<T>(p, { method: "DELETE" }),
};
