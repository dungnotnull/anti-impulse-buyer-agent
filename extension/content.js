/**
 * anti-impulse-buyer — Content Script
 *
 * Injected into every page. Responsibilities:
 * 1. Detect e-commerce sites via site_profiles.json (with inline fallback)
 * 2. Attach click interceptors on checkout/buy-now buttons
 * 3. Extract product metadata from the page DOM
 * 4. Send CHECKOUT_INTERCEPT message to service worker
 * 5. Listen for SHOW_OVERLAY command and inject the freeze overlay
 * 6. On "proceeded": re-trigger the original checkout action
 * 7. On "wishlisted" / timeout: close overlay
 */

let overlayFrame = null;
let interceptedButton = null;
let isProcessing = false;
const SITE_PROFILES_URL = chrome.runtime.getURL("site_profiles.json");

// ─── Inline fallback profiles (used when fetch fails) ───
const FALLBACK_PROFILES = [
  {
    site: "Generic",
    domain_patterns: ["*://*/*"],
    buy_button_selectors: [
      // Text-based heuristic selectors
      'a[href*="checkout"]', 'a[href*="buy"]', 'a[href*="purchase"]',
      'button:not([disabled])', 'input[type="submit"]',
      '[class*="buy"]', '[class*="checkout"]', '[class*="purchase"]',
      '[id*="buy"]', '[id*="checkout"]', '[id*="purchase"]',
      '[data-testid*="buy"]', '[data-testid*="checkout"]',
    ],
    product_name_selectors: [
      'h1', '[class*="title"]', '[class*="name"]', '[class*="product"]',
      '[itemprop="name"]', 'meta[property="og:title"]',
    ],
    price_selectors: [
      '[class*="price"]', '[itemprop="price"]', '[class*="Price"]',
      'meta[property="product:price:amount"]',
    ],
    checkout_url_pattern: ["/checkout", "/cart", "/buy", "/order"],
  },
];

// ─── Load site profiles (with fallback) ───

let profiles = [];
fetch(SITE_PROFILES_URL)
  .then((r) => {
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  })
  .then((data) => {
    profiles = data.profiles || [];
    start();
  })
  .catch((err) => {
    console.warn("[aib] Could not fetch site_profiles.json (" + err.message + "). Using generic fallback.");
    profiles = FALLBACK_PROFILES;
    start();
  });

// ─── Timeout: if fetch hangs, use fallback after 3 seconds ───
setTimeout(() => {
  if (profiles.length === 0) {
    console.warn("[aib] site_profiles.json fetch timed out. Using generic fallback.");
    profiles = FALLBACK_PROFILES;
    start();
  }
}, 3000);

function start() {
  scanAndIntercept();
  // Also always try generic scanning alongside profile matching
  scanGenericButtons();
}

// ─── Site detection ───

function getMatchingProfile() {
  const hostname = window.location.hostname;
  return profiles.find((p) =>
    p.domain_patterns.some((pattern) => {
      const re = new RegExp(
        "^" + pattern.replace(/\*/g, ".*").replace(/\./g, "\\.") + "$"
      );
      return re.test(hostname);
    })
  );
}

// ─── Scanner: find & intercept buy buttons via profile selectors ───

function scanAndIntercept() {
  const profile = getMatchingProfile();
  if (!profile) return;

  const selectors = profile.buy_button_selectors || [];
  for (const sel of selectors) {
    const buttons = document.querySelectorAll(sel);
    buttons.forEach((btn) => attachIntercept(btn, profile));
  }

  const observer = new MutationObserver(() => {
    for (const sel of selectors) {
      const buttons = document.querySelectorAll(sel);
      buttons.forEach((btn) => attachIntercept(btn, profile));
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
}

// ─── Generic fallback scanner: find ANY button that says "buy now" / "checkout" ───

function scanGenericButtons() {
  // Text-based scanning as a safety net
  const buyKeywords = ["buy now", "checkout", "place order", "purchase", "complete order", "pay now", "confirm order"];
  const buttons = document.querySelectorAll("button, a, input[type='submit'], [role='button']");
  buttons.forEach((btn) => {
    if (btn.dataset.aibIntercepted) return;
    const text = (btn.textContent || btn.value || "").trim().toLowerCase();
    const href = (btn.href || "").toLowerCase();
    const cls = (btn.className || "").toLowerCase();
    const id = (btn.id || "").toLowerCase();

    const matchesKeyword = buyKeywords.some((kw) => text.includes(kw));
    const matchesHref = href.includes("/checkout") || href.includes("/buy") || href.includes("/order");
    const matchesClass = cls.includes("buy") || cls.includes("checkout") || id.includes("buy") || id.includes("checkout");

    if (matchesKeyword || matchesHref || matchesClass) {
      attachIntercept(btn, FALLBACK_PROFILES[0]);
    }
  });
}

// ─── Attach click interceptor ───

function attachIntercept(button, profile) {
  if (button.dataset.aibIntercepted) return;
  button.dataset.aibIntercepted = "true";

  button.addEventListener("click", (event) => {
    if (isProcessing) return;
    event.preventDefault();
    event.stopImmediatePropagation();

    interceptedButton = button;
    const { product_name, price, category } = extractProductMeta(profile);

    chrome.runtime.sendMessage(
      {
        type: "CHECKOUT_INTERCEPT",
        payload: {
          product_name,
          price,
          category,
          url: window.location.href,
          page_title: document.title,
        },
      },
      (response) => {
        if (chrome.runtime.lastError) {
          console.warn("[aib] Intercept error:", chrome.runtime.lastError);
          isProcessing = false;
        }
      }
    );
  });
}

// ─── Extract product metadata from DOM ───

function extractProductMeta(profile) {
  let product_name = "";
  let price = 0;

  for (const sel of profile.product_name_selectors || []) {
    const el = document.querySelector(sel);
    if (el) {
      if (el.tagName === "META") {
        product_name = el.getAttribute("content") || "";
      } else {
        product_name = el.textContent.trim();
      }
      if (product_name) break;
    }
  }
  if (!product_name) {
    product_name =
      document.querySelector("h1")?.textContent?.trim() ||
      document.title?.replace(/ - .*$/, "").trim() ||
      "Unknown Product";
  }

  for (const sel of profile.price_selectors || []) {
    const el = document.querySelector(sel);
    if (el) {
      if (el.tagName === "META") {
        const content = el.getAttribute("content") || "";
        price = parseFloat(content) || 0;
      } else {
        const text = el.textContent.trim();
        const match = text.replace(/[^0-9.,]/g, "").match(/[\d,]+\.?\d*/);
        if (match) {
          price = parseFloat(match[0].replace(/,/g, ""));
        }
      }
      if (price) break;
    }
  }
  if (!price) {
    const priceEl = document.querySelector(
      '[class*="price"] span, [class*="Price"] span, [itemprop="price"], meta[property="product:price:amount"]'
    );
    if (priceEl) {
      if (priceEl.tagName === "META") {
        price = parseFloat(priceEl.getAttribute("content") || "") || 0;
      } else {
        const match = priceEl.textContent
          .trim()
          .replace(/[^0-9.,]/g, "")
          .match(/[\d,]+\.?\d*/);
        if (match) price = parseFloat(match[0].replace(/,/g, ""));
      }
    }
  }

  return { product_name, price, category: "" };
}

// ─── Listen for SHOW_OVERLAY from service worker ───

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "SHOW_OVERLAY") {
    showOverlay(message.payload);
    sendResponse({ success: true });
  }
  return true;
});

// ─── Inject freeze overlay iframe ───

function showOverlay(interceptData) {
  if (overlayFrame) return;
  isProcessing = true;

  overlayFrame = document.createElement("iframe");
  overlayFrame.id = "aib-overlay-frame";
  overlayFrame.style.cssText = `
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    z-index: 2147483647;
    border: none;
    background: rgba(0,0,0,0.6);
  `;

  const encoded = encodeURIComponent(JSON.stringify(interceptData));
  overlayFrame.src = chrome.runtime.getURL(
    `overlay/overlay.html?data=${encoded}`
  );

  document.body.appendChild(overlayFrame);
  window.addEventListener("message", handleOverlayDecision);
}

function handleOverlayDecision(event) {
  if (event.data?.type !== "AIB_OVERLAY_DECISION") return;
  window.removeEventListener("message", handleOverlayDecision);

  const decision = event.data.decision;
  closeOverlay();

  if (decision === "proceeded" && interceptedButton) {
    // Re-trigger original checkout: remove interceptor flag, click, restore
    isProcessing = false;
    interceptedButton.dataset.aibIntercepted = "";
    // Dispatch a new click event (more reliable than .click() for some frameworks)
    const clickEvent = new MouseEvent("click", { bubbles: true, cancelable: true });
    interceptedButton.dispatchEvent(clickEvent);
    // Re-apply interceptor after a short delay
    setTimeout(() => {
      if (interceptedButton) interceptedButton.dataset.aibIntercepted = "true";
    }, 500);
  } else {
    isProcessing = false;
  }
}

function closeOverlay() {
  if (overlayFrame) {
    overlayFrame.remove();
    overlayFrame = null;
  }
}
