import { api, setAuth } from "./client";
import type { User } from "./types";

interface TokenOut { access_token: string; token_type: string; }
interface MeOut { id: number; email: string; name?: string | null; orgs: { id: number; role: string }[]; }

// Login/register return only a token. We save it, then fetch /me to get the
// user and the active org, and store both.
async function establish(tok: TokenOut): Promise<User> {
  setAuth(tok.access_token);
  const me = await api.get<MeOut>("/auth/me");
  const org = me.orgs?.[0]?.id ?? null;
  setAuth(tok.access_token, org);
  return { id: me.id, email: me.email, name: me.name };
}

export async function register(email: string, password: string, name?: string) {
  const tok = await api.post<TokenOut>("/auth/register", { email, password, name });
  return establish(tok);
}
export async function login(email: string, password: string) {
  const tok = await api.post<TokenOut>("/auth/login", { email, password });
  return establish(tok);
}
export async function me() {
  const m = await api.get<MeOut>("/auth/me");
  return { user: { id: m.id, email: m.email, name: m.name } as User, orgs: m.orgs };
}
export function logout() { setAuth(null, null); }
