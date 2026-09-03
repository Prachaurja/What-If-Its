import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import { AuthPage } from "./pages/Auth";
import { Dashboard } from "./pages/Dashboard";
import { NewCheck } from "./pages/NewCheck";
import { Report } from "./pages/Report";
import { Sources } from "./pages/Sources";
import { Members, Settings } from "./pages/Simple";

function Protected({ children }: { children: React.ReactNode }) {
  const { user, ready } = useAuth();
  if (!ready) return <div style={{ display: "grid", placeItems: "center", height: "100vh", color: "var(--ink-3)" }}>…</div>;
  return user ? <>{children}</> : <Navigate to="/signin" replace />;
}

function Page({ children }: { children: React.ReactNode }) {
  return <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
    transition={{ duration: 0.2 }}>{children}</motion.div>;
}

function Router() {
  const loc = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={loc} key={loc.pathname.split("/")[1] || "root"}>
        <Route path="/signin" element={<Page><AuthPage mode="signin" /></Page>} />
        <Route path="/signup" element={<Page><AuthPage mode="signup" /></Page>} />
        <Route path="/" element={<Protected><Page><Dashboard /></Page></Protected>} />
        <Route path="/new" element={<Protected><Page><NewCheck /></Page></Protected>} />
        <Route path="/report/:id" element={<Protected><Page><Report /></Page></Protected>} />
        <Route path="/sources" element={<Protected><Page><Sources /></Page></Protected>} />
        <Route path="/members" element={<Protected><Page><Members /></Page></Protected>} />
        <Route path="/settings" element={<Protected><Page><Settings /></Page></Protected>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AnimatePresence>
  );
}

export default function App() {
  return <AuthProvider><Router /></AuthProvider>;
}
