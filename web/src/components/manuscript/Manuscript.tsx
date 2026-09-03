import { useMemo } from "react";
import { motion, useReducedMotion } from "framer-motion";
import type { ReportPayload } from "../../api/types";

// The hero. Renders the submission as a document, sweeping highlighter across
// matched passages and underlining AI-flagged sentences. The one orchestrated
// motion moment in the whole app.
export function Manuscript({ report, activeSource }:
  { report: ReportPayload; activeSource: number | null }) {
  const reduce = useReducedMotion();
  const words = useMemo(() => report.text.split(/\s+/).filter(Boolean), [report.text]);

  // per-word: which source matched (or null)
  const wordSource = useMemo(() => {
    const arr: (number | null)[] = new Array(words.length).fill(null);
    for (const m of report.matches)
      for (let i = m.start_word; i < m.end_word && i < words.length; i++)
        if (arr[i] == null) arr[i] = m.source_id;
    return arr;
  }, [report.matches, words.length]);

  // AI-flagged sentences (from deberta windows, if scored)
  const aiFlag = useMemo(() => {
    const flags = new Set<string>();
    const w = report.ai?.windows;
    if (w) for (const win of w) if (win.ai + win.ai_paraphrased > 0.6) flags.add(win.text.slice(0, 40));
    return flags;
  }, [report.ai]);

  // build paragraph → sentence → word spans
  let wi = 0;
  const paras = report.text.split(/\n\s*\n/);
  let matchIndex = 0;

  return (
    <div style={{ fontFamily: "var(--serif)", fontSize: 18, lineHeight: 1.75, color: "var(--ink)",
      maxWidth: "68ch", fontOpticalSizing: "auto" }}>
      <div style={{ fontFamily: "var(--sans)", fontSize: 12, color: "var(--ink-3)", marginBottom: 28,
        letterSpacing: 0.3 }}>{report.word_count.toLocaleString()} words</div>
      {paras.map((para, pi) => (
        <p key={pi} style={{ margin: "0 0 1.15em" }}>
          {para.split(/(?<=[.!?])\s+/).map((sent, si) => {
            const flagged = [...aiFlag].some((f) => sent.startsWith(f));
            return (
              <span key={si} style={flagged ? {
                textDecoration: "underline wavy var(--redpen)", textDecorationThickness: 1.5,
                textUnderlineOffset: 5,
              } : undefined}>
                {sent.split(/\s+/).filter(Boolean).map((word) => {
                  const src = wordSource[wi];
                  const isMatch = src != null;
                  const dim = activeSource != null && src !== activeSource;
                  const idx = wi++;
                  if (!isMatch) return <span key={idx}>{word} </span>;
                  const mi = matchIndex++;
                  return (
                    <motion.span key={idx}
                      initial={reduce ? false : { backgroundSize: "0% 100%" }}
                      animate={{ backgroundSize: "100% 100%" }}
                      transition={{ delay: reduce ? 0 : 0.25 + mi * 0.012, duration: 0.28, ease: "easeOut" }}
                      style={{
                        backgroundImage: "linear-gradient(var(--match),var(--match))",
                        backgroundRepeat: "no-repeat", backgroundPosition: "left center",
                        borderRadius: 2, opacity: dim ? 0.35 : 1, transition: "opacity .2s",
                        boxDecorationBreak: "clone", WebkitBoxDecorationBreak: "clone",
                      }}>{word} </motion.span>
                  );
                })}
              </span>
            );
          })}
        </p>
      ))}
    </div>
  );
}
