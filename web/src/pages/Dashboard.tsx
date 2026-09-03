import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { listChecks } from "../api/checks";
import { AppShell, PageHead } from "../components/layout/AppShell";
import { Button, Pill } from "../components/ui/ui";

function Bar({ value, color }: { value: number | null; color: string }) {
  if (value == null) return <span style={{ color: "var(--ink-3)", fontSize: 13 }}>—</span>;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{ width: 54, height: 6, background: "var(--sheet-2)", borderRadius: 3, overflow: "hidden" }}>
        <motion.div initial={{ width: 0 }} animate={{ width: `${value}%` }} transition={{ duration: 0.6, ease: "easeOut" }}
          style={{ height: "100%", background: color, borderRadius: 3 }} />
      </div>
      <span style={{ fontSize: 13, color: "var(--ink-2)", fontVariantNumeric: "tabular-nums" }}>{Math.round(value)}%</span>
    </div>
  );
}

export function Dashboard() {
  const nav = useNavigate();
  const { data: checks = [], isLoading } = useQuery({
    queryKey: ["checks"], queryFn: listChecks,
    refetchInterval: (q) => (q.state.data?.some((c) => c.status === "queued" || c.status === "running") ? 2500 : false),
  });

  return (
    <AppShell>
      <PageHead title="Checks" action={<Button onClick={() => nav("/new")}>New check</Button>} />
      <div style={{ padding: "24px 36px" }}>
        {isLoading ? <Empty text="Loading…" /> : checks.length === 0 ? (
          <div style={{ textAlign: "center", padding: "80px 0" }}>
            <div style={{ fontFamily: "var(--serif)", fontSize: 22, marginBottom: 8 }}>No checks yet</div>
            <p style={{ color: "var(--ink-2)", marginBottom: 20 }}>Upload a document to see it checked for matches and AI writing.</p>
            <Button onClick={() => nav("/new")}>Run your first check</Button>
          </div>
        ) : (
          <div style={{ border: "1px solid var(--line)", borderRadius: "var(--radius)", overflow: "hidden", background: "var(--sheet)" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 130px 130px 120px", padding: "12px 18px",
              fontSize: 12, color: "var(--ink-3)", fontWeight: 600, borderBottom: "1px solid var(--line)" }}>
              <span>Title</span><span>Similarity</span><span>AI writing</span><span>Status</span>
            </div>
            {checks.map((c, i) => (
              <motion.div key={c.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03 }} onClick={() => c.status === "done" && nav(`/report/${c.id}`)}
                style={{ display: "grid", gridTemplateColumns: "1fr 130px 130px 120px", padding: "14px 18px",
                  alignItems: "center", borderBottom: "1px solid var(--line)", cursor: c.status === "done" ? "pointer" : "default",
                  transition: "background .12s" }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "var(--sheet-2)")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
                <span style={{ fontWeight: 500 }}>{c.title}</span>
                <Bar value={c.similarity_pct} color="var(--match-ink)" />
                <Bar value={c.ai_prob != null ? c.ai_prob * 100 : null} color="var(--redpen)" />
                <Pill status={c.status} />
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
function Empty({ text }: { text: string }) {
  return <div style={{ padding: "80px 0", textAlign: "center", color: "var(--ink-3)" }}>{text}</div>;
}
