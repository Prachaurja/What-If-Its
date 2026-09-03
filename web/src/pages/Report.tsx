import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useCheck } from "../hooks/useCheck";
import { AppShell } from "../components/layout/AppShell";
import { Manuscript } from "../components/manuscript/Manuscript";
import { ScoreRing } from "../components/report/ScoreRing";
import { Spinner } from "../components/ui/ui";
import type { ReportPayload } from "../api/types";

export function Report() {
  const { id } = useParams();
  const nav = useNavigate();
  const { data, isError } = useCheck(id ? Number(id) : null);
  const [tab, setTab] = useState<"sources" | "ai">("sources");
  const [activeSource, setActiveSource] = useState<number | null>(null);

  if (isError) return <AppShell><Center>Couldn't load this check.</Center></AppShell>;
  if (!data) return <AppShell><Center><Spinner /></Center></AppShell>;

  if (data.status !== "done") {
    return <AppShell><Center>
      <motion.div style={{ textAlign: "center" }}>
        <div style={{ display: "inline-flex", marginBottom: 16 }}><Spinner /></div>
        <div style={{ fontFamily: "var(--serif)", fontSize: 22 }}>
          {data.status === "queued" ? "Queued…" : data.status === "failed" ? "Check failed" : "Checking your document…"}
        </div>
        <p style={{ color: "var(--ink-2)" }}>This usually takes under a minute.</p>
      </motion.div>
    </Center></AppShell>;
  }

  const r = data.payload as ReportPayload;
  const ai = r.ai;

  return (
    <AppShell>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "18px 36px", borderBottom: "1px solid var(--line)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <button onClick={() => nav("/")} style={{ background: "none", border: "none", color: "var(--ink-2)", fontSize: 14 }}>← Checks</button>
          <span style={{ fontFamily: "var(--serif)", fontSize: 17, fontWeight: 600 }}>{r.title}</span>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) 360px", gap: 0 }}>
        {/* manuscript */}
        <div style={{ padding: "40px 48px", borderRight: "1px solid var(--line)", minHeight: "calc(100vh - 130px)" }}>
          <Manuscript report={r} activeSource={activeSource} />
        </div>

        {/* margin */}
        <div style={{ padding: "28px 28px", position: "sticky", top: 0, alignSelf: "start" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 20, marginBottom: 24 }}>
            <ScoreRing value={r.similarity_percent} color="var(--match-ink)"
              label="matches a known source"
              sublabel={`${r.sources.length} source${r.sources.length === 1 ? "" : "s"}`} />
            {ai?.scored ? (
              <ScoreRing value={Math.round((ai.prob || 0) * 100)} color="var(--redpen)"
                label={`${ai.verdict} AI-written`}
                sublabel={ai.band ? `range ${Math.round(ai.band[0]*100)}–${Math.round(ai.band[1]*100)}%` : undefined} />
            ) : (
              <div style={{ fontSize: 13, color: "var(--ink-3)", paddingLeft: 4 }}>
                AI writing: not scored{ai?.reason ? ` — ${ai.reason}` : ""}
              </div>
            )}
          </div>

          {/* tabs */}
          <div style={{ display: "flex", gap: 4, borderBottom: "1px solid var(--line)", marginBottom: 14 }}>
            {(["sources", "ai"] as const).map((t) => (
              <button key={t} onClick={() => setTab(t)} style={{ position: "relative", background: "none", border: "none",
                padding: "8px 4px", marginRight: 16, fontSize: 13, fontWeight: 600,
                color: tab === t ? "var(--ink)" : "var(--ink-3)" }}>
                {t === "sources" ? "Sources" : "AI writing"}
                {tab === t && <motion.div layoutId="tab" style={{ position: "absolute", left: 0, right: 0, bottom: -1,
                  height: 2, background: "var(--cobalt)" }} />}
              </button>
            ))}
          </div>

          <AnimatePresence mode="wait">
            {tab === "sources" ? (
              <motion.div key="s" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                {r.sources.length === 0 ? <p style={{ color: "var(--ink-3)", fontSize: 14 }}>No matching sources found.</p> :
                  r.sources.map((s) => (
                    <div key={s.id} onMouseEnter={() => setActiveSource(s.id)} onMouseLeave={() => setActiveSource(null)}
                      style={{ display: "flex", justifyContent: "space-between", padding: "10px 8px", borderRadius: 6,
                        cursor: "default", transition: "background .12s", fontSize: 14 }}
                      onMouseOver={(e) => (e.currentTarget.style.background = "var(--sheet-2)")}
                      onMouseOut={(e) => (e.currentTarget.style.background = "transparent")}>
                      <span style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <span style={{ width: 9, height: 9, borderRadius: 2, background: "var(--match)", flex: "none" }} />
                        {s.title}
                      </span>
                      <span style={{ color: "var(--ink-2)", fontVariantNumeric: "tabular-nums" }}>{s.percent}%</span>
                    </div>
                  ))}
              </motion.div>
            ) : (
              <motion.div key="a" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                {ai?.scored ? (<>
                  <div style={{ fontSize: 14, marginBottom: 12 }}>
                    <b style={{ textTransform: "capitalize" }}>{ai.verdict}</b> to be AI-written.
                    {ai.note && <div style={{ color: "var(--redpen)", fontSize: 13, marginTop: 4 }}>{ai.note}</div>}
                  </div>
                  {ai.detectors && <div style={{ fontSize: 13, color: "var(--ink-2)", lineHeight: 1.9 }}>
                    {Object.entries(ai.detectors).filter(([, v]) => v != null).map(([k, v]) => (
                      <div key={k} style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ textTransform: "capitalize" }}>{k}</span>
                        <span>{Math.round((v as number) * 100)}%</span>
                      </div>
                    ))}
                  </div>}
                </>) : <p style={{ color: "var(--ink-3)", fontSize: 14 }}>{ai?.reason || "Not scored."}</p>}
                <p style={{ fontSize: 12, color: "var(--ink-3)", marginTop: 18, lineHeight: 1.5, fontStyle: "italic" }}>
                  {ai?.caveat || "AI-writing signals are probabilistic. Use them as a prompt for review, not as evidence."}
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </AppShell>
  );
}
function Center({ children }: { children: React.ReactNode }) {
  return <div style={{ display: "grid", placeItems: "center", minHeight: "70vh", color: "var(--ink-2)" }}>{children}</div>;
}
