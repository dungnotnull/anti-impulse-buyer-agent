/**
 * anti-impulse-buyer — Service Worker (Background)
 *
 * Manifest V3 service worker — may be killed when idle.
 * - Uses chrome.alarms to keep alive and periodically check backend health
 * - Routes messages between content scripts and local Python backend
 * - All async responses use return true to keep the message channel open
 */

const BACKEND_URL = "http://localhost:7432";
const KEEPALIVE_INTERVAL = 4; // minutes (MV3 idle timeout is ~30s-5min)

// ─── Keep service worker alive ───
chrome.runtime.onStartup.addListener(() => {
  setupKeepalive();
});
chrome.runtime.onInstalled.addListener(() => {
  setupKeepalive();
});

function setupKeepalive() {
  chrome.alarms.create("aib-keepalive", { periodInMinutes: KEEPALIVE_INTERVAL });
}

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "aib-keepalive") {
    // Warm up the backend connection and keep SW alive
    fetch(`${BACKEND_URL}/api/health`).catch(() => {});
  }
});

// ─── Message router ───

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  try {
    switch (message.type) {
      case "CHECKOUT_INTERCEPT":
        handleIntercept(message.payload, sender, sendResponse);
        return true; // keep channel open for async response

      case "LOG_EVENT":
        handleLogEvent(message.payload, sendResponse);
        return true;

      case "WISHLIST_ITEM":
        handleWishlist(message.payload, sendResponse);
        return true;

      case "CHECK_HEALTH":
        handleHealth(sendResponse);
        return true;

      case "GET_DARK_PATTERNS":
        handleGetDarkPatterns(message.payload, sendResponse);
        return true;

      default:
        console.warn("[aib] Unknown message type:", message.type);
        sendResponse({ error: "Unknown message type" });
        return false;
    }
  } catch (err) {
    console.error("[aib] Message handler error:", err);
    sendResponse({ success: false, error: err.message });
    return false;
  }
});

// ─── Handlers ───

async function handleIntercept(payload, sender, sendResponse) {
  try {
    const resp = await fetch(`${BACKEND_URL}/api/intercept`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_name: payload.product_name,
        price: payload.price,
        category: payload.category || "",
        url: payload.url || sender?.tab?.url || "",
        page_title: payload.page_title || "",
        timestamp: new Date().toISOString(),
      }),
      signal: AbortSignal.timeout(10000), // 10s timeout
    });

    if (!resp.ok) {
      throw new Error(`Backend returned ${resp.status}`);
    }

    const data = await resp.json();

    // Tell content script to show overlay
    if (sender?.tab?.id) {
      chrome.tabs.sendMessage(sender.tab.id, {
        type: "SHOW_OVERLAY",
        payload: data,
      }).catch(() => {
        // Tab may have navigated away — safe to ignore
      });
    }

    sendResponse({ success: true, data });
  } catch (err) {
    console.error("[aib] Intercept error:", err);
    // Still try to send an error response so the overlay shows with fallback data
    if (sender?.tab?.id) {
      chrome.tabs.sendMessage(sender.tab.id, {
        type: "SHOW_OVERLAY",
        payload: {
          impulsivity_score: 0.5,
          score_tier: "medium",
          narrative: "⚠️ Backend unreachable. Take a moment to think before you buy.",
          challenge_difficulty: "medium",
          similar_owned_count: 0,
          dark_pattern_warnings: [],
        },
      }).catch(() => {});
    }
    sendResponse({ success: false, error: err.message });
  }
}

async function handleLogEvent(payload, sendResponse) {
  try {
    const resp = await fetch(`${BACKEND_URL}/api/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(5000),
    });
    const data = await resp.json();
    sendResponse({ success: true, data });
  } catch (err) {
    console.error("[aib] Log event error:", err);
    sendResponse({ success: false, error: err.message });
  }
}

async function handleWishlist(payload, sendResponse) {
  try {
    const params = new URLSearchParams({
      product_name: payload.product_name,
      price: String(payload.price),
      category: payload.category || "",
      url: payload.url || "",
    });
    const resp = await fetch(`${BACKEND_URL}/api/wishlist?${params}`, {
      method: "POST",
      signal: AbortSignal.timeout(5000),
    });
    const data = await resp.json();
    sendResponse({ success: true, data });
  } catch (err) {
    console.error("[aib] Wishlist error:", err);
    sendResponse({ success: false, error: err.message });
  }
}

async function handleGetDarkPatterns(payload, sendResponse) {
  try {
    const resp = await fetch(`${BACKEND_URL}/api/detect-dark-patterns`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: payload.text || "" }),
      signal: AbortSignal.timeout(5000),
    });
    const data = await resp.json();
    sendResponse({ success: true, data });
  } catch (err) {
    sendResponse({ success: false, error: err.message });
  }
}

async function handleHealth(sendResponse) {
  try {
    const resp = await fetch(`${BACKEND_URL}/api/health`, {
      signal: AbortSignal.timeout(3000),
    });
    const data = await resp.json();
    sendResponse({ success: true, data });
  } catch {
    sendResponse({ success: false, error: "Backend unreachable" });
  }
}
