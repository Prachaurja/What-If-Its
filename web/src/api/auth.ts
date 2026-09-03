import { api, setAuth } from "./client";
import type { AuthResponse, User } from "./types";

export async function register(email: string, password: string, name?: string) {
  const r = await api.post<AuthResponse>("/auth/register", { email, password, name });
  setAuth(r.access_token, r.org_id ?? null);
  return r;
}
export async function login(email: string, password: string) {
  const r = await api.post<AuthResponse>("/auth/login", { email, password });
  setAuth(r.access_token, r.org_id ?? null);
  return r;
}
export async function me() { return api.get<{ user: User; orgs: any[] }>("/auth/me"); }
export function logout() { setAuth(null, null); }
