import { motion } from "framer-motion";
import type { ReactNode, ButtonHTMLAttributes, InputHTMLAttributes } from "react";

export function Button({ variant = "primary", children, ...p }:
  { variant?: "primary" | "ghost" | "quiet" } & ButtonHTMLAttributes<HTMLButtonElement>) {
  const base: any = {
    border: "none", borderRadius: "var(--radius-sm)", fontWeight: 600, fontSize: 14,
    padding: "10px 18px", transition: "transform .12s var(--ease), background .15s, box-shadow .15s",
  };
  const styles: Record<string, any> = {
    primary: { ...base, background: "var(--cobalt)", color: "#fff" },
    ghost: { ...base, background: "transparent", color: "var(--ink)", border: "1px solid var(--line-strong)" },
    quiet: { ...base, background: "transparent", color: "var(--ink-2)", padding: "6px 10px" },
  };
  return (
    <motion.button whileHover={{ y: -1 }} whileTap={{ y: 0, scale: 0.98 }}
      style={styles[variant]} {...(p as any)}>
      {children}
    </motion.button>
  );
}

export function Input(p: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...p} style={{
    width: "100%", padding: "11px 13px", border: "1px solid var(--line-strong)",
    borderRadius: "var(--radius-sm)", fontSize: 15, fontFamily: "var(--sans)",
    background: "var(--sheet)", color: "var(--ink)", ...(p.style || {}),
  }} onFocus={(e) => (e.target.style.borderColor = "var(--cobalt)")}
     onBlur={(e) => (e.target.style.borderColor = "var(--line-strong)")} />;
}

export function Card({ children, style }: { children: ReactNode; style?: any }) {
  return <div style={{ background: "var(--sheet)", border: "1px solid var(--line)",
    borderRadius: "var(--radius)", boxShadow: "var(--shadow)", ...style }}>{children}</div>;
}

export function Pill({ status }: { status: string }) {
  const map: Record<string, [string, string, string]> = {
    done: ["var(--ok)", "#EAF7F0", "Done"],
    running: ["var(--cobalt)", "var(--cobalt-wash)", "Running"],
    queued: ["var(--ink-2)", "var(--sheet-2)", "Queued"],
    failed: ["var(--redpen)", "#FDECEA", "Failed"],
  };
  const [fg, bg, label] = map[status] || map.queued;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6, color: fg, background: bg,
      padding: "3px 10px", borderRadius: 20, fontSize: 12, fontWeight: 600 }}>
      {(status === "running" || status === "queued") && (
        <motion.span animate={{ opacity: [1, 0.3, 1] }} transition={{ duration: 1.4, repeat: Infinity }}
          style={{ width: 6, height: 6, borderRadius: 3, background: fg }} />
      )}
      {label}
    </span>
  );
}

export function Spinner() {
  return <motion.div animate={{ rotate: 360 }} transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
    style={{ width: 18, height: 18, border: "2px solid var(--line)", borderTopColor: "var(--cobalt)", borderRadius: "50%" }} />;
}
