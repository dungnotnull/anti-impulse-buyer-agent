import React, { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, AreaChart, Area, CartesianGrid,
} from "recharts";

const BACKEND = "http://localhost:7432";
const PIE_COLORS = ["#e74c3c", "#2ecc71", "#f39c12"];

export default function Dashboard({ summary, onRefresh }) {
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    if (summary?.recent_events) {
      // Build area chart data from events over time
      const byDay = {};
      for (const e of summary.recent_events) {
        const day = e.created_at?.slice(0, 10) || "unknown";
        if (!byDay[day]) byDay[day] = { date: day, blocked: 0, proceeded: 0, wishlisted: 0 };
        byDay[day][e.decision] = (byDay[day][e.decision] || 0) + 1;
      }
      setChartData(Object.values(byDay).sort((a, b) => a.date.localeCompare(b.date)));
    }
  }, [summary]);

  if (!summary) {
    return <p style={{ fontSize: 13, color: "#999" }}>Loading dashboard...</p>;
  }

  const pieData = [
    { name: "Blocked", value: summary.total_blocked },
    { name: "Proceeded", value: summary.total_proceeded },
    { name: "Wishlisted", value: summary.total_wishlisted },
  ].filter((d) => d.value > 0);

  const barData = (summary.recent_events || []).slice(0, 8).reverse().map((e) => ({
    name: e.product_name.length > 12 ? e.product_name.slice(0, 12) + "…" : e.product_name,
    score: +(e.impulsivity_score * 100).toFixed(0),
    fill: e.decision === "proceeded" ? "#2ecc71" : e.decision === "wishlisted" ? "#f39c12" : "#e74c3c",
  }));

  return (
    <div>
      <div style={{ display: "flex", gap: 6, marginBottom: 16, flexWrap: "wrap" }}>
        <StatCard label="Blocked" value={summary.total_blocked} color="#e74c3c" />
        <StatCard label="Proceeded" value={summary.total_proceeded} color="#2ecc71" />
        <StatCard label="Money Saved" value={`$${summary.money_saved?.toFixed(0)}`} color="#27ae60" />
        <StatCard label="Streak" value={`${summary.current_streak_days}d`} color="#2980b9" />
      </div>

      {pieData.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <p style={{ fontSize: 11, fontWeight: 600, marginBottom: 4, color: "#666" }}>Decision Breakdown</p>
          <ResponsiveContainer width="100%" height={150}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={35} outerRadius={55} dataKey="value">
                {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
              </Pie>
              <Legend fontSize={10} />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}

      {chartData.length > 1 && (
        <div style={{ marginBottom: 16 }}>
          <p style={{ fontSize: 11, fontWeight: 600, marginBottom: 4, color: "#666" }}>Daily Trend</p>
          <ResponsiveContainer width="100%" height={120}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" fontSize={8} />
              <YAxis fontSize={8} />
              <Tooltip />
              <Area type="monotone" dataKey="blocked" stroke="#e74c3c" fill="#e74c3c" fillOpacity={0.3} />
              <Area type="monotone" dataKey="proceeded" stroke="#2ecc71" fill="#2ecc71" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {barData.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <p style={{ fontSize: 11, fontWeight: 600, marginBottom: 4, color: "#666" }}>Recent Scores</p>
          <ResponsiveContainer width="100%" height={120}>
            <BarChart data={barData}>
              <XAxis dataKey="name" fontSize={8} />
              <YAxis domain={[0, 100]} fontSize={8} />
              <Tooltip />
              <Bar dataKey="score" radius={[3, 3, 0, 0]}>
                {barData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {(summary.recent_events || []).length > 0 && (
        <div>
          <p style={{ fontSize: 11, fontWeight: 600, marginBottom: 4, color: "#666" }}>Recent Events</p>
          {(summary.recent_events || []).slice(0, 5).map((e) => (
            <div key={e.id} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: "1px solid #f0f0f0", fontSize: 11 }}>
              <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{e.product_name}</span>
              <span style={{ width: 50, textAlign: "right" }}>${e.price?.toFixed(2)}</span>
              <span style={{ width: 60, textAlign: "center", fontWeight: 600, color: { blocked: "#e74c3c", proceeded: "#2ecc71", wishlisted: "#f39c12" }[e.decision] || "#999" }}>
                {e.decision}
              </span>
              <span style={{ width: 30, textAlign: "right", color: "#999" }}>{(e.impulsivity_score * 100).toFixed(0)}</span>
            </div>
          ))}
        </div>
      )}

      <button onClick={onRefresh} style={{ width: "100%", marginTop: 12, padding: 8, background: "#f8f9fa", border: "1px solid #dee2e6", borderRadius: 6, fontSize: 11, cursor: "pointer", color: "#666" }}>
        🔄 Refresh
      </button>
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div style={{ flex: 1, background: "#f8f9fa", borderRadius: 8, padding: "8px 4px", textAlign: "center", minWidth: 60 }}>
      <div style={{ fontSize: 16, fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: 9, color: "#999", marginTop: 1 }}>{label}</div>
    </div>
  );
}
