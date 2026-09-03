import { AppShell, PageHead } from "../components/layout/AppShell";
import { useAuth } from "../hooks/useAuth";

export function Members() {
  return (
    <AppShell>
      <PageHead title="Members" />
      <div style={{ padding: "24px 36px", maxWidth: 640 }}>
        <p style={{ color: "var(--ink-2)", marginTop: 0 }}>
          Invite people to your organisation and set what they can do — view reports, run checks, or manage sources.
        </p>
        <div style={{ border: "1px solid var(--line)", borderRadius: "var(--radius)", background: "var(--sheet)",
          padding: "40px 24px", textAlign: "center", color: "var(--ink-3)", marginTop: 16 }}>
          Member management arrives with team plans.
        </div>
      </div>
    </AppShell>
  );
}

export function Settings() {
  const { user } = useAuth();
  return (
    <AppShell>
      <PageHead title="Settings" />
      <div style={{ padding: "24px 36px", maxWidth: 560 }}>
        <Section title="Profile">
          <Row label="Email" value={user?.email || "—"} />
        </Section>
        <Section title="Plan">
          <Row label="Current plan" value="Free" />
          <Row label="Checks this month" value="—" />
        </Section>
        <Section title="API keys">
          <p style={{ color: "var(--ink-3)", fontSize: 14, margin: 0 }}>
            Create a key to run checks from scripts or an LMS integration.
          </p>
        </Section>
      </div>
    </AppShell>
  );
}
function Section({ title, children }: any) {
  return <div style={{ marginBottom: 28 }}>
    <h3 style={{ fontSize: 13, color: "var(--ink-3)", fontWeight: 600, margin: "0 0 10px" }}>{title}</h3>
    <div style={{ border: "1px solid var(--line)", borderRadius: "var(--radius)", background: "var(--sheet)" }}>{children}</div>
  </div>;
}
function Row({ label, value }: { label: string; value: string }) {
  return <div style={{ display: "flex", justifyContent: "space-between", padding: "14px 18px",
    borderBottom: "1px solid var(--line)", fontSize: 14 }}>
    <span style={{ color: "var(--ink-2)" }}>{label}</span><span style={{ fontWeight: 500 }}>{value}</span>
  </div>;
}
