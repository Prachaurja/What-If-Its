import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "../hooks/useAuth";
import { Button, Input } from "../components/ui/ui";

export function AuthPage({ mode }: { mode: "signin" | "signup" }) {
  const { signIn, signUp } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState(""); const [pw, setPw] = useState("");
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  const isUp = mode === "signup";

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr(""); setBusy(true);
    try { isUp ? await signUp(email, pw) : await signIn(email, pw); nav("/"); }
    catch (e: any) { setErr(e.message || "Something went wrong"); } finally { setBusy(false); }
  }

  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: 24 }}>
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }} style={{ width: 380 }}>
        <div style={{ fontFamily: "var(--serif)", fontSize: 34, fontWeight: 600, letterSpacing: -0.8,
          marginBottom: 6 }}>Swipe</div>
        <p style={{ color: "var(--ink-2)", marginTop: 0, marginBottom: 28 }}>
          {isUp ? "Create an account to start checking documents." : "Sign in to your workspace."}
        </p>
        <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <Input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
          <Input type="password" placeholder="Password" value={pw} onChange={(e) => setPw(e.target.value)} required minLength={8} />
          {err && <div style={{ color: "var(--redpen)", fontSize: 13 }}>{err}</div>}
          <Button type="submit" disabled={busy} style={{ marginTop: 4 }}>
            {busy ? "…" : isUp ? "Create account" : "Sign in"}
          </Button>
        </form>
        <p style={{ fontSize: 14, color: "var(--ink-2)", marginTop: 20 }}>
          {isUp ? <>Already have an account? <Link to="/signin">Sign in</Link></>
                : <>New to Swipe? <Link to="/signup">Create an account</Link></>}
        </p>
      </motion.div>
    </div>
  );
}
