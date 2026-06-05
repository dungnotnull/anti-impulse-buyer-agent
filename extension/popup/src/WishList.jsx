import React, { useEffect, useState } from "react";

const BACKEND = "http://localhost:7432";

export default function WishList() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [digest, setDigest] = useState(null);

  useEffect(() => {
    fetchWishlist();
  }, []);

  async function fetchWishlist() {
    setLoading(true);
    try {
      const r = await fetch(`${BACKEND}/api/wishlist/digest`);
      if (r.ok) setDigest(await r.json());
    } catch {}
    setLoading(false);
  }

  async function markReviewed() {
    try {
      await fetch(`${BACKEND}/api/wishlist/digest/review`, { method: "POST" });
      fetchWishlist();
    } catch {}
  }

  if (loading) return <p style={{ fontSize: 12, color: "#999" }}>Loading wish list...</p>;

  if (!digest || digest.item_count === 0) {
    return (
      <div style={{ textAlign: "center", padding: 30 }}>
        <p style={{ fontSize: 32, marginBottom: 8 }}>🎉</p>
        <p style={{ fontSize: 13, color: "#666" }}>No items in wish list!</p>
        <p style={{ fontSize: 11, color: "#999", marginTop: 4 }}>When you resist an impulse purchase, it'll appear here for weekly review.</p>
      </div>
    );
  }

  return (
    <div>
      <div style={{ background: "#f8f9fa", borderRadius: 8, padding: 12, marginBottom: 12 }}>
        <p style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>📋 Wish List Summary</p>
        <p style={{ fontSize: 11, color: "#555", lineHeight: 1.5 }}>{digest.summary}</p>
      </div>

      {digest.items?.map((item, i) => (
        <div key={i} style={{ padding: "8px 0", borderBottom: "1px solid #f0f0f0" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span style={{ fontSize: 12, fontWeight: 600, flex: 1 }}>{item.product_name}</span>
            <span style={{ fontSize: 12, color: "#e74c3c", fontWeight: 700 }}>${item.price?.toFixed(2)}</span>
          </div>
          <p style={{ fontSize: 10, color: "#666", lineHeight: 1.4 }}>{item.narrative}</p>
          {item.category && <span style={{ fontSize: 9, color: "#999" }}>{item.category}</span>}
        </div>
      ))}

      <button onClick={markReviewed}
        style={{ width: "100%", marginTop: 12, padding: 10, background: "#1a1a2e", color: "#fff", border: "none", borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: "pointer" }}>
        ✅ Mark All Reviewed
      </button>
    </div>
  );
}
