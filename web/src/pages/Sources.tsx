import { useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { listSources, addSource } from "../api/sources";
import { AppShell, PageHead } from "../components/layout/AppShell";
import { Button } from "../components/ui/ui";

export function Sources() {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const { data: sources = [] } = useQuery({ queryKey: ["sources"], queryFn: listSources });

  async function upload(files: FileList | null) {
    if (!files) return;
    for (const f of Array.from(files)) await addSource(f).catch(() => {});
    qc.invalidateQueries({ queryKey: ["sources"] });
  }

  return (
    <AppShell>
      <PageHead title="Sources" action={
        <Button onClick={() => fileRef.current?.click()}>Add sources</Button>} />
      <input ref={fileRef} type="file" multiple accept=".docx,.pdf,.txt,.md" hidden
        onChange={(e) => upload(e.target.files)} />
      <div style={{ padding: "24px 36px" }}>
        <p style={{ color: "var(--ink-2)", maxWidth: "60ch", marginTop: 0 }}>
          Reference documents that submissions are compared against. Every check you run is also added here,
          so your repository grows as you use Swipe.
        </p>
        {sources.length === 0 ? (
          <div style={{ padding: "60px 0", textAlign: "center", color: "var(--ink-3)" }}>
            No reference sources yet. Add documents to compare submissions against.
          </div>
        ) : (
          <div style={{ border: "1px solid var(--line)", borderRadius: "var(--radius)", overflow: "hidden",
            background: "var(--sheet)", marginTop: 16 }}>
            {sources.map((s, i) => (
              <motion.div key={s.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}
                style={{ display: "flex", justifyContent: "space-between", padding: "14px 18px",
                  borderBottom: "1px solid var(--line)", fontSize: 14 }}>
                <span style={{ fontWeight: 500 }}>{s.title}</span>
                <span style={{ color: "var(--ink-2)" }}>{s.word_count.toLocaleString()} words</span>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
