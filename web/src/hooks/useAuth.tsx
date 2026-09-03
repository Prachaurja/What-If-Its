import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import { getToken, setAuth } from "../api/client";
import * as auth from "../api/auth";
import type { User } from "../api/types";

interface AuthCtx { user: User | null; ready: boolean;
  signIn: (e: string, p: string) => Promise<void>;
  signUp: (e: string, p: string, n?: string) => Promise<void>;
  signOut: () => void; }
const Ctx = createContext<AuthCtx>(null!);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (getToken()) auth.me().then((r) => setUser(r.user)).catch(() => setAuth(null)).finally(() => setReady(true));
    else setReady(true);
  }, []);
  const signIn = async (e: string, p: string) => { const r = await auth.login(e, p); setUser(r.user); };
  const signUp = async (e: string, p: string, n?: string) => { const r = await auth.register(e, p, n); setUser(r.user); };
  const signOut = () => { auth.logout(); setUser(null); };
  return <Ctx.Provider value={{ user, ready, signIn, signUp, signOut }}>{children}</Ctx.Provider>;
}
export const useAuth = () => useContext(Ctx);
