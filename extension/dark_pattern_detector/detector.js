/**
 * anti-impulse-buyer — Dark Pattern Detector
 *
 * Scans the page for known dark patterns and highlights them:
 * - Countdown timers (false urgency)
 * - Fake scarcity text ("Only 2 left!", "Low stock")
 * - Social proof manipulation ("247 people viewing this")
 * - Hidden subscription traps
 * - Confirmshaming ("No thanks, I hate saving money")
 *
 * Runs as part of the content script on supported e-commerce sites.
 */

const DARK_PATTERNS = {
  scarcity: {
    patterns: [
      /only\s+\d+\s+(left|remaining|available)/i,
      /low\s+stock/i,
      /selling\s+fast/i,
      /running\s+out/i,
      /last\s+\d+\s+(items?|units?)/i,
      /almost\s+gone/i,
      /few\s+left/i,
      /limited\s+(edition|availability|stock|quantity)/i,
      /while\s+supplies\s+last/i,
      /\d+\s+sold\s+(in\s+the\s+last\s+\d+|today)/i,
      /hurry/i,
      /don't\s+miss\s+out/i,
      /act\s+now/i,
      /offer\s+ends\s+soon/i,
    ],
    label: "Fake Scarcity",
    icon: "⚠️",
    color: "#f39c12",
  },
  urgency: {
    patterns: [
      /\d{1,2}:\d{2}:\d{2}/, // countdown timer HH:MM:SS
      /ends?\s+in\s+\d+\s*(h|hr|hour|min|sec)/i,
      /limited\s+time/i,
      /flash\s+sale/i,
      /today\s+only/i,
      /last\s+chance/i,
    ],
    label: "False Urgency",
    icon: "⏰",
    color: "#e74c3c",
  },
  socialProof: {
    patterns: [
      /\d+\s*(people|persons|customers)\s+(are\s+)?(viewing|looking\s+at|bought)\s+this/i,
      /\d+\s+others?\s+(in\s+)?(your\s+)?cart/i,
      /trending\s+now/i,
      /popular\s+(item|product|choice)/i,
      /\d+\s+sold\s+(today|this\s+week)/i,
      /best\s+sel(l|ing)/i,
      /top\s+rated/i,
    ],
    label: "Social Proof Manipulation",
    icon: "👥",
    color: "#9b59b6",
  },
  confirmshaming: {
    patterns: [
      /no\s+thanks,\s+i\s+(don'?t\s+)?(like|want|need)\s+(saving\s+)?money/i,
      /i\s+prefer\s+(not\s+to\s+)?save\s+money/i,
      /i\s+don'?t\s+want\s+(this\s+)?(deal|offer|discount)/i,
      /no,\s+(i\s+)?(don'?t\s+)?(want|need)\s+to\s+save/i,
    ],
    label: "Confirmshaming",
    icon: "😤",
    color: "#e67e22",
  },
  hiddenCosts: {
    patterns: [
      /free\s+(trial|shipping)(\s+\*)?/i,
      /\d+\s+days?\s+free/i,
      /small\s+(fee|charge|amount)\s+(will\s+be\s+)?added/i,
      /additional\s+fees?\s+(may\s+)?apply/i,
    ],
    label: "Hidden Costs",
    icon: "💰",
    color: "#1abc9c",
  },
  subscriptionTrap: {
    patterns: [
      /auto(-|\s)?renew/i,
      /recurring/i,
      /every\s+\d+\s+(month|week|year)/i,
      /subscribe\s+(and\s+)?save/i,
      /cancel\s+anytime/i,
    ],
    label: "Subscription Trap",
    icon: "🔄",
    color: "#3498db",
  },
};

let detectedPatterns = [];

function scanForDarkPatterns() {
  detectedPatterns = [];
  const walker = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_TEXT,
    null,
    false
  );

  const allTexts = [];
  let node;
  while ((node = walker.nextNode())) {
    const text = node.textContent.trim();
    if (text.length > 5 && text.length < 200) {
      allTexts.push({ text, node });
    }
  }

  for (const { text, node } of allTexts) {
    for (const [type, config] of Object.entries(DARK_PATTERNS)) {
      for (const pattern of config.patterns) {
        if (pattern.test(text)) {
          detectedPatterns.push({
            type,
            label: config.label,
            icon: config.icon,
            color: config.color,
            text: text.slice(0, 100),
            element: node.parentElement,
          });
          break;
        }
      }
    }
  }

  return detectedPatterns;
}

function highlightDarkPatterns() {
  const seen = new Set();
  for (const dp of detectedPatterns) {
    if (!dp.element || seen.has(dp.element)) continue;
    seen.add(dp.element);

    dp.element.style.outline = `3px solid ${dp.color}`;
    dp.element.style.outlineOffset = "2px";
    dp.element.style.position = "relative";

    const badge = document.createElement("div");
    badge.className = "aib-dark-pattern-badge";
    badge.textContent = `${dp.icon} ${dp.label}`;
    badge.style.cssText = `
      position: absolute;
      top: -12px;
      right: -4px;
      background: ${dp.color};
      color: white;
      font-size: 10px;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      z-index: 2147483646;
      pointer-events: none;
      white-space: nowrap;
      box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    `;

    // Don't add duplicates
    if (!dp.element.querySelector(".aib-dark-pattern-badge")) {
      dp.element.appendChild(badge);
    }
  }
}

function getDarkPatternSummary() {
  const summary = {};
  for (const dp of detectedPatterns) {
    summary[dp.type] = (summary[dp.type] || 0) + 1;
  }
  return {
    count: detectedPatterns.length,
    details: detectedPatterns.map((d) => ({
      type: d.type,
      label: d.label,
      text: d.text,
    })),
    summary,
  };
}

// ─── Public API ───
window.__aibDarkPatterns = {
  scan: scanForDarkPatterns,
  highlight: highlightDarkPatterns,
  getSummary: getDarkPatternSummary,
  detected: () => detectedPatterns,
};
