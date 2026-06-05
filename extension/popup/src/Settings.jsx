import React, { useState, useEffect } from "react";

const BACKEND = "http://localhost:7432";

export default function Settings({ onBackendCheck }) {
  const [claudeKey, setClaudeKey] = useState("");
  const [openaiKey, setOpenaiKey] = useState("");
  const [llmMode, setLlmMode] = useState("local");
  const [income, setIncome] = useState("");
  const [avgSpend, setAvgSpend] = useState("");
  const [saved, setSaved] = useState(false);
  const [dataRetention, setDataRetention] = useState(90);
  const [status, setStatus] = useState("");

  // Load from backend
  useEffect(() => {
    fetch(`${BACKEND}/api/profile`)
      .then((r) => r.json())
      .then((data) => {
        if (data.monthly_income) setIncome(String(data.monthly_income));
        if (data.monthly_avg_spend) setAvgSpend(String(data.monthly_avg_spend));
        setLlmMode(data.llm_mode || "local");
        setDataRetention(data.data_retention_days || 90);
      })
      .catch(() => {});
    // Load API keys from local storage
    chrome.storage?.local?.get(["claude_api_key", "openai_api_key"], (data) => {
      if (data.claude_api_key) setClaudeKey(data.claude_api_key);
      if (data.openai_api_key) setOpenaiKey(data.openai_api_key);
    });
  }, []);

  async function handleSave() {
    setStatus("Saving...");
    try {
      const r = await fetch(`${BACKEND}/api/profile`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          monthly_income: parseFloat(income) || 0,
          monthly_avg_spend: parseFloat(avgSpend) || 0,
          data_retention_days: dataRetention,
          llm_mode: llmMode,
        }),
      });
      if (r.ok) {
        // Save API keys to local storage
        chrome.storage?.local?.set({
          claude_api_key: claudeKey,
          openai_api_key: openaiKey,
        });
        setSaved(true);
        setStatus("✅ Settings saved!");
        setTimeout(() => setSaved(false), 2000);
      } else {
        setStatus("❌ Failed to save");
      }
    } catch {
      setStatus("❌ Backend unreachable");
    }
  }

  async function handlePurge() {
    if (!confirm("Delete ALL spending data? This cannot be undone.")) return;
    try {
      const r = await fetch(`${BACKEND}/api/export/purge`, { method: "POST" });
      if (r.ok) setStatus("✅ All data purged");
    } catch {
      setStatus("❌ Purge failed");
    }
  }

  async function handleExport() {
    window.open(`${BACKEND}/api/export/events-csv`, "_blank");
  }

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <p style={{ fontSize: 11, fontWeight: 600, marginBottom: 6 }}>LLM Mode</p>
        <div style={{ display: "flex", gap: 6 }}>
          {["local", "cloud"].map((mode) => (
            <button key={mode} onClick={() => setLlmMode(mode)}
              style={{
                flex: 1, padding: "8px 0", border: `2px solid ${llmMode === mode ? "#1a1a2e" : "#dee2e6"}`,
                borderRadius: 6, background: llmMode === mode ? "#1a1a2e" : "#fff",
                color: llmMode === mode ? "#fff" : "#333", fontSize: 11, fontWeight: 600, cursor: "pointer",
              }}
            >{mode === "local" ? "🏠 Local Only" : "☁️ Cloud (Opt-in)"}</button>
          ))}
        </div>
        <p style={{ fontSize: 9, color: "#999", marginTop: 4 }}>
          {llmMode === "local" ? "All data stays on your machine." : "Enables richer narratives via Claude/GPT-4."}
        </p>
      </div>

      {llmMode === "cloud" && (
        <>
          <Field label="Claude API Key" value={claudeKey} onChange={setClaudeKey} placeholder="sk-ant-..." />
          <Field label="OpenAI API Key" value={openaiKey} onChange={setOpenaiKey} placeholder="sk-proj-..." />
        </>
      )}

      <Field label="Monthly Net Income ($)" value={income} onChange={setIncome} placeholder="e.g. 4500" type="number" />
      <Field label="Monthly Average Spend ($)" value={avgSpend} onChange={setAvgSpend} placeholder="e.g. 3200" type="number" />
      <Field label="Data Retention (days)" value={String(dataRetention)} onChange={(v) => setDataRetention(parseInt(v) || 90)} placeholder="90" type="number" />

      <button onClick={handleSave}
        style={{ width: "100%", padding: 10, background: "#1a1a2e", color: "#fff", border: "none", borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: "pointer", marginTop: 8 }}>
        {saved ? "✅ Saved!" : "💾 Save Settings"}
      </button>

      <div style={{ marginTop: 16, paddingTop: 12, borderTop: "1px solid #eee" }}>
        <p style={{ fontSize: 11, fontWeight: 600, marginBottom: 6 }}>Data Management</p>
        <button onClick={handleExport}
          style={{ width: "100%", padding: 8, background: "#e9ecef", color: "#333", border: "none", borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: "pointer", marginBottom: 6 }}>
          📥 Export as CSV
        </button>
        <button onClick={handlePurge}
          style={{ width: "100%", padding: 8, background: "#fce4e4", color: "#e74c3c", border: "none", borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: "pointer" }}>
          🗑️ Purge All Data
        </button>
      </div>

      {status && <p style={{ textAlign: "center", fontSize: 11, marginTop: 8, fontWeight: 600, color: status.startsWith("✅") ? "#2ecc71" : "#e74c3c" }}>{status}</p>}
    </div>
  );
}

function Field({ label, value, onChange, placeholder, type = "text" }) {
  return (
    <div style={{ marginBottom: 8 }}>
      <label style={{ fontSize: 10, fontWeight: 600, color: "#666", display: "block", marginBottom: 3 }}>{label}</label>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
        style={{ width: "100%", padding: "7px 10px", border: "1px solid #dee2e6", borderRadius: 6, fontSize: 11, outline: "none", boxSizing: "border-box" }} />
    </div>
  );
}
