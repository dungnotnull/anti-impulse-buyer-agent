/**
 * anti-impulse-buyer — Freeze Overlay UI Logic
 *
 * Embedded in an iframe injected by the content script.
 * Communicates with the content script via window.parent.postMessage.
 * Background logging uses chrome.runtime.sendMessage (works because
 * the iframe loads a chrome-extension:// page).
 *
 * SAFETY: chrome.runtime.sendMessage might fail in some Firefox
 * iframe contexts — all errors are caught silently.
 */

// ─── State ───
let freezeDuration = 300;
let timerInterval = null;
let challengeSolved = false;
let challengeDifficulty = "easy";
let correctAnswer = "";
let answerTolerance = 0;
let interceptData = null;
let productMeta = { product_name: "Unknown", price: 0, category: "", url: "" };

// ─── Parse intercept data from URL ───
function parseInterceptData() {
  const params = new URLSearchParams(window.location.search);
  const raw = params.get("data");
  if (raw) {
    try {
      interceptData = JSON.parse(decodeURIComponent(raw));
    } catch {
      interceptData = {
        impulsivity_score: 0.5,
        score_tier: "medium",
        narrative: "Take a moment to think before you buy.",
        challenge_difficulty: "medium",
        similar_owned_count: 0,
      };
    }
  }
}

// ─── Timer ───
function startTimer() {
  const timerEl = document.getElementById("aib-timer");

  timerInterval = setInterval(() => {
    freezeDuration--;
    const mins = String(Math.floor(freezeDuration / 60)).padStart(2, "0");
    const secs = String(freezeDuration % 60).padStart(2, "0");
    timerEl.textContent = `${mins}:${secs}`;

    if (freezeDuration <= 60) {
      timerEl.style.color = "#e63946";
    }

    if (freezeDuration <= 0) {
      clearInterval(timerInterval);
      handleTimeout();
    }
  }, 1000);
}

function handleTimeout() {
  if (!challengeSolved) {
    sendDecision("wishlisted");
  }
}

// ─── Narrative ───
function showNarrative() {
  const el = document.getElementById("aib-narrative");
  el.textContent = interceptData.narrative || "Think before you buy.";
}

// ─── Score bar ───
function showScoreBar() {
  const score = interceptData.importunity_score ?? interceptData.impulsivity_score ?? 0;
  const tier = interceptData.score_tier || "medium";
  const fill = document.getElementById("aib-score-fill");
  const value = document.getElementById("aib-score-value");

  const pct = Math.round(score * 100);
  fill.style.width = `${pct}%`;

  let color = "#2ecc71";
  if (tier === "medium") color = "#f39c12";
  if (tier === "high") color = "#e74c3c";

  fill.style.background = color;
  value.textContent = `${pct}% — ${tier.toUpperCase()}`;
}

// ─── Challenge ───
function loadChallenge() {
  const diff = interceptData.challenge_difficulty || "medium";
  challengeDifficulty = diff;

  const challenges = {
    easy: [
      { q: "What is 12 × 15?", a: "180", tol: 0 },
      { q: "What is 144 ÷ 12?", a: "12", tol: 0 },
      { q: "What is 25 + 37?", a: "62", tol: 0 },
      { q: "What is 100 − 43?", a: "57", tol: 0 },
      { q: "What is 7 × 8?", a: "56", tol: 0 },
      { q: "What is 15% of 200?", a: "30", tol: 0 },
      { q: "What is 3² + 4²?", a: "25", tol: 0 },
      { q: "What is 5³?", a: "125", tol: 0 },
      { q: "If you save $5/day for 30 days, how much do you have?", a: "150", tol: 0 },
      { q: "A $45 item is 20% off. What is the sale price?", a: "36", tol: 0.01 },
      { q: "What is 99 + 99?", a: "198", tol: 0 },
      { q: "What is √49?", a: "7", tol: 0 },
      { q: "How many minutes in 3 hours?", a: "180", tol: 0 },
    ],
    medium: [
      { q: "Next number: 2, 6, 18, 54, ?", a: "162", tol: 0 },
      { q: "Next number: 1, 4, 9, 16, 25, ?", a: "36", tol: 0 },
      { q: "Next number: 3, 8, 15, 24, 35, ?", a: "48", tol: 0 },
      { q: "Next number: 1, 1, 2, 3, 5, 8, ?", a: "13", tol: 0 },
      { q: "Next number: 100, 90, 81, 73, 66, ?", a: "60", tol: 0 },
      { q: "Next number: 2, 3, 5, 7, 11, 13, ?", a: "17", tol: 0 },
      { q: "Complete: Mon, Tue, Wed, Thu, Fri, ?", a: "Sat", tol: 0 },
      { q: "Complete: Jan, Mar, May, Jul, ?", a: "Sep", tol: 0 },
      { q: "Next letter: A, C, E, G, I, ?", a: "K", tol: 0 },
      { q: "Next number: 1, 2, 4, 8, 16, ?", a: "32", tol: 0 },
      { q: "Next number: 99, 88, 77, 66, ?", a: "55", tol: 0 },
    ],
    hard: [
      { q: "You earn $3,200/month. Rent $1,100, food $400, transport $200, utilities $150. You want a $900 TV. After expenses, how many months of saving 100% of remaining money would it take? (Round to nearest tenth)", a: "0.66", tol: 0.05 },
      { q: "You buy coffee $5.50 every workday (Mon-Fri). How much per year (52 weeks)?", a: "1430", tol: 0.01 },
      { q: "$120 item, 15% off coupon, 8% tax. Final price?", a: "110.16", tol: 0.01 },
      { q: "You save $8/day. How much in 90 days? Invest at 5% simple interest for 1 year — how much interest?", a: "36", tol: 0.01 },
      { q: "Skip 2 impulse purchases/week at $35 each. Monthly savings (4 weeks)?", a: "280", tol: 0.01 },
      { q: "$14.99/month subscription. Over 3 years total? (Round to $)", a: "540", tol: 0.01 },
      { q: "Delivery $5. You order 15x/month. If you reduce to 5x/month, yearly delivery savings?", a: "600", tol: 0.01 },
      { q: "$6/day snacks, 5 days/week. Meal prep to $2/day. Yearly savings (52 weeks)?", a: "1040", tol: 0.01 },
    ],
  };

  const pool = challenges[diff] || challenges.easy;
  const picked = pool[Math.floor(Math.random() * pool.length)];

  correctAnswer = String(picked.a);
  answerTolerance = picked.tol;

  document.getElementById("aib-challenge-question").textContent = picked.q;
}

function checkChallenge() {
  const input = document.getElementById("aib-challenge-input");
  const feedback = document.getElementById("aib-challenge-feedback");
  const userAnswer = input.value.trim();

  if (!userAnswer) {
    feedback.textContent = "Please enter an answer.";
    feedback.style.color = "#e74c3c";
    return;
  }

  let correct = false;
  try {
    const userVal = parseFloat(userAnswer.replace(/,/g, "").replace("$", ""));
    const correctVal = parseFloat(correctAnswer);
    if (answerTolerance > 0) {
      correct = Math.abs(userVal - correctVal) <= answerTolerance;
    } else {
      correct = userVal === correctVal;
    }
  } catch {
    correct = userAnswer.toLowerCase() === correctAnswer.toLowerCase();
  }

  if (correct) {
    challengeSolved = true;
    feedback.textContent = "✅ Correct! You may proceed.";
    feedback.style.color = "#2ecc71";
    document.getElementById("aib-challenge-submit").disabled = true;
    input.disabled = true;
    document.getElementById("aib-proceed-btn").disabled = false;
  } else {
    feedback.textContent = "❌ Incorrect. Try again.";
    feedback.style.color = "#e74c3c";
    input.value = "";
    input.focus();
  }
}

// ─── Send decision to parent window ───
function sendDecision(decision) {
  clearInterval(timerInterval);

  // 1. Tell content script to close overlay and proceed/block (primary channel)
  window.parent.postMessage(
    { type: "AIB_OVERLAY_DECISION", decision },
    "*"
  );

  // 2. Try to log event via service worker (may fail in some iframe contexts — safe)
  try {
    chrome.runtime.sendMessage({
      type: "LOG_EVENT",
      payload: {
        product_name: interceptData.product_name || productMeta.product_name || "Unknown",
        price: interceptData.price ?? productMeta.price ?? 0,
        category: interceptData.category || productMeta.category || "",
        url: productMeta.url || (window.parent !== window ? document.referrer : window.location.href) || "",
        impulsivity_score: interceptData.impulsivity_score ?? interceptData.importunity_score ?? 0,
        score_tier: interceptData.score_tier || "low",
        decision: decision,
        narrative: interceptData.narrative || "",
        challenge_difficulty: challengeDifficulty,
        challenge_passed: decision === "proceeded" ? 1 : 0,
      },
    });
  } catch (e) {
    // chrome.runtime unavailable in iframe context (Firefox, some MV3 edge cases).
    // Decision is still sent to parent — logging is best-effort.
    console.warn("[aib] Could not log event from overlay:", e.message);
  }
}

// ─── Handle buttons ───
function setupButtons() {
  document.getElementById("aib-proceed-btn").addEventListener("click", () => {
    sendDecision("proceeded");
  });

  document.getElementById("aib-wishlist-btn").addEventListener("click", () => {
    sendDecision("wishlisted");
  });
}

// ─── Init ───
function init() {
  parseInterceptData();

  const tier = interceptData.score_tier || "low";
  if (tier === "low") freezeDuration = 120;
  else freezeDuration = 300;

  startTimer();
  showNarrative();
  showScoreBar();
  loadChallenge();

  document
    .getElementById("aib-challenge-submit")
    .addEventListener("click", checkChallenge);

  document
    .getElementById("aib-challenge-input")
    .addEventListener("keydown", (e) => {
      if (e.key === "Enter") checkChallenge();
    });

  setupButtons();
}

document.addEventListener("DOMContentLoaded", init);
