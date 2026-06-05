import React, { useState } from "react";

const BACKEND = "http://localhost:7432";

export default function EssentialItems({ items, onRefresh }) {
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function addItem() {
    if (!name.trim()) return;
    setSaving(true);
    setError("");
    try {
      const r = await fetch(`${BACKEND}/api/essentials`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim(), category, notes }),
      });
      if (r.ok) {
        setName("");
        setCategory("");
        setNotes("");
        onRefresh();
      } else {
        const d = await r.json();
        setError(d.detail || "Failed to add");
      }
    } catch {
      setError("Backend unreachable");
    }
    setSaving(false);
  }

  async function deleteItem(id) {
    try {
      await fetch(`${BACKEND}/api/essentials/${id}`, { method: "DELETE" });
      onRefresh();
    } catch {}
  }

  return (
    <div>
      {/* Add form */}
      <div style={{ background: "#f8f9fa", borderRadius: 8, padding: 12, marginBottom: 12 }}>
        <p style={{ fontSize: 12, fontWeight: 600, marginBottom: 8 }}>Add Essential Item</p>
        <input
          placeholder="Item name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={inputStyle}
        />
        <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
          <input
            placeholder="Category (optional)"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            style={{ ...inputStyle, flex: 1 }}
          />
          <input
            placeholder="Notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            style={{ ...inputStyle, flex: 1 }}
          />
        </div>
        {error && <p style={{ fontSize: 11, color: "#e74c3c", margin: "4px 0 0 0" }}>{error}</p>}
        <button
          onClick={addItem}
          disabled={saving || !name.trim()}
          style={{
            marginTop: 8,
            padding: "6px 16px",
            background: "#1a1a2e",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            fontSize: 12,
            fontWeight: 600,
            cursor: "pointer",
            opacity: saving || !name.trim() ? 0.6 : 1,
          }}
        >
          {saving ? "Adding..." : "Add Item"}
        </button>
      </div>

      {/* List */}
      {items.length === 0 && (
        <p style={{ fontSize: 12, color: "#999", textAlign: "center", padding: 20 }}>
          No essential items yet. Add items that should bypass impulse checks (groceries, bills, etc.).
        </p>
      )}

      {items.map((item) => (
        <div
          key={item.id}
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "8px 0",
            borderBottom: "1px solid #f0f0f0",
          }}
        >
          <div style={{ flex: 1 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>{item.name}</span>
            {item.category && (
              <span style={{ fontSize: 11, color: "#999", marginLeft: 8 }}>{item.category}</span>
            )}
          </div>
          <button
            onClick={() => deleteItem(item.id)}
            style={{
              background: "none",
              border: "none",
              color: "#e74c3c",
              cursor: "pointer",
              fontSize: 16,
              padding: 4,
            }}
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}

const inputStyle = {
  width: "100%",
  padding: "8px 10px",
  border: "1px solid #dee2e6",
  borderRadius: 6,
  fontSize: 12,
  outline: "none",
  boxSizing: "border-box",
};
