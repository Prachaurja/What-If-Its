import { motion, useReducedMotion, animate } from "framer-motion";
import { useEffect, useState } from "react";

export function ScoreRing({ value, color, label, sublabel, suffix = "%" }:
  { value: number; color: string; label: string; sublabel?: string; suffix?: string }) {
  const reduce = useReducedMotion();
  const [display, setDisplay] = useState(reduce ? value : 0);
  const R = 30, C = 2 * Math.PI * R;
  useEffect(() => {
    if (reduce) { setDisplay(value); return; }
    const controls = animate(0, value, { duration: 0.9, ease: "easeOut", onUpdate: (v) => setDisplay(v) });
    return () => controls.stop();
  }, [value, reduce]);
  return (
    <div style={{ display: "flex", gap: 14, alignItems: "center" }}>
      <svg width="72" height="72" viewBox="0 0 72 72" style={{ flex: "none" }}>
        <circle cx="36" cy="36" r={R} fill="none" stroke="var(--sheet-2)" strokeWidth="6.5" />
        <motion.circle cx="36" cy="36" r={R} fill="none" stroke={color} strokeWidth="6.5"
          strokeLinecap="round" strokeDasharray={C}
          initial={{ strokeDashoffset: C }}
          animate={{ strokeDashoffset: C * (1 - display / 100) }}
          transform="rotate(-90 36 36)" />
      </svg>
      <div>
        <div style={{ fontFamily: "var(--serif)", fontSize: 30, fontWeight: 600, lineHeight: 1 }}>
          {Math.round(display)}{suffix}
        </div>
        <div style={{ fontSize: 13, color: "var(--ink-2)", marginTop: 3 }}>{label}</div>
        {sublabel && <div style={{ fontSize: 12, color: "var(--ink-3)", marginTop: 2 }}>{sublabel}</div>}
      </div>
    </div>
  );
}
