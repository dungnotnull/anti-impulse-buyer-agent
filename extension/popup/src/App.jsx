import React, { useEffect, useState } from "react";
import Dashboard from "./Dashboard";
import EssentialItems from "./EssentialItems";
import Settings from "./Settings";
import WishList from "./WishList";

const BACKEND = "http://localhost:7432";

const TAB_KEYS = ["dashboard", "essentials", "wishlist", "settings"];
const TAB_LABELS = {
  dashboard: "📊 Dashboard",
  essentials: "✅ Essentials",
  wishlist: "📋 Wish List",
  settings: "⚙️ Settings",
};

export default function App() {
  const [tab, setTab] = useState("dashboard");
  const [backendOk, setBackendOk] = useState(null);
  const [summary, setSummary] = useState(null);
  const [essentials, setEssentials] = useState([]);

  useEffect(() => {
    checkHealth();
  }, []);

  useEffect(() => {
    if (tab === "dashboard") fetchSummary();
    if (tab === "essentials") fetchEssentials();
  }, [tab]);

  async function checkHealth() {
    try {
      const r = await fetch(`${BACKEND}/api/health`);
      if (r.ok) setBackendOk(true);
      else setBackendOk(false);
    } catch {
      setBackendOk(false);
    }
  }

  async function fetchSummary() {
    try {
      const r = await fetch(`${BACKEND}/api/summary?days=30`);
      if (r.ok) setSummary(await r.json());
    } catch {}
  }

  async function fetchEssentials() {
    try {
      const r = await fetch(`${BACKEND}/api/essentials`);
      if (r.ok) setEssentials(await r.json());
    } catch {}
  }

  const styles = {
    container: { width: 380, fontFamily: "-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif", padding: 16, background: "#fff", color: "#1a1a2e" },
    tabs: { display: "flex", gap: 2, marginBottom: 16, borderBottom: "2px solid #eee", paddingBottom: 8 },
    tab: (isActive) => ({
      flex: 1, padding: "8px 2px", textAlign: "center", cursor: "pointer", fontSize: 11,
      fontWeight: 600, border: "none", background: "none",
      color: isActive ? "#1a1a2e" : "#999",
      borderBottom: isActive ? "2px solid #1a1a2e" : "2px solid transparent", marginBottom: -10,
    }),
    status: { textAlign: "center", fontSize: 11, color: backendOk ? "#2ecc71" : "#e74c3c", marginBottom: 12 },
  };

  return (
    <div style={styles.container}>
      <h1 style={{ fontSize: 18, fontWeight: 700, marginBottom: 2 }}>anti-impulse-buyer</h1>
      <p style={{ fontSize: 10, color: "#999", margin: "0 0 8px 0" }}>Your wallet's guardian</p>
      <div style={styles.status}>
        {backendOk === null ? "⏳ Connecting..." : backendOk ? "🟢 Backend online" : "🔴 Backend offline"}
      </div>
      <div style={styles.tabs}>
        {TAB_KEYS.map((k) => (
          <button key={k} style={styles.tab(tab === k)} onClick={() => setTab(k)}>
            {TAB_LABELS[k]}
          </button>
        ))}
      </div>
      {tab === "dashboard" && <Dashboard summary={summary} onRefresh={fetchSummary} />}
      {tab === "essentials" && <EssentialItems items={essentials} onRefresh={fetchEssentials} />}
      {tab === "wishlist" && <WishList />}
      {tab === "settings" && <Settings onBackendCheck={checkHealth} />}
    </div>
  );
}
