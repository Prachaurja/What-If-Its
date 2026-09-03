import { useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { checkFile, checkText } from "../api/checks";
import { AppShell, PageHead } from "../components/layout/AppShell";
import { Button } from "../components/ui/ui";

export function NewCheck() {
  const nav = useNavigate();
  const [drag, setDrag] = useState(false);
  const [paste, setPaste] = useState(false);
  const [text, setText] = useState(""); const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false); const [err, setErr] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const run = useCallback(async (fn: () => Promise<{ id: number }>) => {
    setBusy(true); setErr("");
    try { const r = await fn(); nav(`/report/${r.id}`); }
    catch (e: any) { setErr(e.message); setBusy(false); }
  }, [nav]);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDrag(false);
    const f = e.dataTransfer.files[0]; if (f) run(() => checkFile(f));
  };

  return (
    <AppShell>
      <PageHead title="New check" />
      <div style={{ padding: "28px 36px", maxWidth: 720 }}>
        <AnimatePresence mode="wait">
          {!paste ? (
            <motion.div key="drop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
                onDragLeave={() => setDrag(false)} onDrop={onDrop}
                onClick={() => fileRef.current?.click()}
                style={{ border: `2px dashed ${drag ? "var(--cobalt)" : "var(--line-strong)"}`,
                  borderRadius: "var(--radius)", padding: "64px 32px", textAlign: "center", cursor: "pointer",
                  background: drag ? "var(--cobalt-wash)" : "var(--sheet)", transition: "all .18s" }}>
                <motion.div animate={{ y: drag ? -4 : 0 }} style={{ fontFamily: "var(--serif)", fontSize: 22, marginBottom: 8 }}>
                  {busy ? "Uploading…" : "Drop a document here"}
                </motion.div>
                <p style={{ color: "var(--ink-2)", margin: "0 0 18px" }}>Word, PDF, or plain text — up to 10&nbsp;MB</p>
                <Button variant="ghost" type="button">Choose a file</Button>
              </div>
              <input ref={fileRef} type="file" accept=".docx,.pdf,.txt,.md" hidden
                onChange={(e) => e.target.files?.[0] && run(() => checkFile(e.target.files![0]))} />
              <div style={{ textAlign: "center", margin: "18px 0" }}>
                <button onClick={() => setPaste(true)} style={{ background: "none", border: "none", color: "var(--cobalt)", fontSize: 14, fontWeight: 500 }}>
                  or paste text instead
                </button>
              </div>
            </motion.div>
          ) : (
            <motion.div key="paste" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <input placeholder="Title (optional)" value={title} onChange={(e) => setTitle(e.target.value)}
                style={{ width: "100%", padding: "11px 13px", border: "1px solid var(--line-strong)",
                  borderRadius: "var(--radius-sm)", fontSize: 15, marginBottom: 10, fontFamily: "var(--sans)" }} />
              <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste the document text…"
                style={{ width: "100%", minHeight: 280, padding: 14, border: "1px solid var(--line-strong)",
                  borderRadius: "var(--radius-sm)", fontSize: 16, fontFamily: "var(--serif)", lineHeight: 1.7, resize: "vertical" }} />
              <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
                <Button disabled={busy || text.split(/\s+/).length < 20}
                  onClick={() => run(() => checkText(title || "Pasted text", text))}>
                  {busy ? "Checking…" : "Run check"}
                </Button>
                <Button variant="ghost" onClick={() => setPaste(false)}>Back</Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        {err && <div style={{ color: "var(--redpen)", fontSize: 14, marginTop: 16 }}>{err}</div>}
      </div>
    </AppShell>
  );
}
