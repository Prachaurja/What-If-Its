import { NavLink, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import type { ReactNode } from "react";
import { useAuth } from "../../hooks/useAuth";

const nav = [
  ["/", "Checks"], ["/new", "New check"], ["/sources", "Sources"],
  ["/members", "Members"], ["/settings", "Settings"],
];

export function AppShell({ children }: { children: ReactNode }) {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  return (
    <div style={{ display: "grid", gridTemplateColumns: "232px 1fr", minHeight: "100vh" }}>
      <aside style={{ background: "var(--sheet)", borderRight: "1px solid var(--line)",
        padding: "22px 16px", display: "flex", flexDirection: "column", position: "sticky", top: 0, height: "100vh" }}>
        <div style={{ fontFamily: "var(--serif)", fontSize: 21, fontWeight: 600, padding: "0 8px 20px",
          letterSpacing: -0.4 }}>Swipe</div>
        <nav style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {nav.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === "/"} style={({ isActive }) => ({
              position: "relative", padding: "9px 12px", borderRadius: "var(--radius-sm)", fontSize: 14,
              fontWeight: 500, color: isActive ? "var(--ink)" : "var(--ink-2)",
              background: isActive ? "var(--sheet-2)" : "transparent",
            })}>
              {({ isActive }) => (<>
                {isActive && <motion.span layoutId="navdot" style={{ position: "absolute", left: 0, top: 10,
                  bottom: 10, width: 3, borderRadius: 3, background: "var(--cobalt)" }} />}
                {label}
              </>)}
            </NavLink>
          ))}
        </nav>
        <div style={{ marginTop: "auto", padding: "0 8px" }}>
          <div style={{ fontSize: 13, color: "var(--ink-2)" }}>{user?.email}</div>
          <button onClick={() => { signOut(); navigate("/signin"); }}
            style={{ background: "none", border: "none", color: "var(--ink-3)", fontSize: 13, padding: "6px 0" }}>
            Sign out
          </button>
        </div>
      </aside>
      <main>{children}</main>
    </div>
  );
}

export function PageHead({ title, action }: { title: string; action?: ReactNode }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
      padding: "26px 36px", borderBottom: "1px solid var(--line)" }}>
      <h1 style={{ fontFamily: "var(--serif)", fontSize: 24, fontWeight: 600, margin: 0, letterSpacing: -0.4 }}>{title}</h1>
      {action}
    </div>
  );
}
