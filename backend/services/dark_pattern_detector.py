"""Server-side dark pattern detection for page content.

When a user sends page text or HTML snippets during intercept,
this module analyzes them for known dark patterns and returns
warnings to display in the overlay.

The client-side dark_pattern_detector.js handles DOM-level scanning
and highlighting. This module provides additional server-side analysis
for page content the extension sends via the intercept request.
"""

import re

DARK_PATTERN_RULES = {
    "scarcity": {
        "patterns": [
            r"only\s+\d+\s+(left|remaining|available)",
            r"low\s+stock",
            r"selling\s+fast",
            r"running\s+out",
            r"last\s+\d+\s+(items?|units?)",
            r"almost\s+gone",
            r"few\s+left",
            r"limited\s+(edition|availability|stock|quantity)",
            r"while\s+supplies\s+last",
            r"\d+\s+sold\s+(in\s+the\s+last\s+\d+|today)",
            r"hurry",
            r"don't\s+miss\s+out",
            r"act\s+now",
        ],
        "label": "Fake Scarcity",
        "severity": "high",
    },
    "urgency": {
        "patterns": [
            r"\d{1,2}:\d{2}:\d{2}",
            r"ends?\s+in\s+\d+\s*(h|hr|hour|min|sec)",
            r"limited\s+time",
            r"flash\s+sale",
            r"today\s+only",
            r"last\s+chance",
            r"offer\s+ends\s+soon",
        ],
        "label": "False Urgency",
        "severity": "high",
    },
    "social_proof": {
        "patterns": [
            r"\d+\s*(people|persons|customers)\s+(are\s+)?(viewing|looking\s+at|bought)\s+this",
            r"\d+\s+others?\s+(in\s+)?(your\s+)?cart",
            r"trending\s+now",
            r"popular\s+(item|product|choice)",
            r"\d+\s+sold\s+(today|this\s+week)",
        ],
        "label": "Social Proof Manipulation",
        "severity": "medium",
    },
    "confirmshaming": {
        "patterns": [
            r"no\s+thanks,\s+i\s+(don'?t\s+)?(like|want|need)\s+(saving\s+)?money",
            r"i\s+prefer\s+(not\s+to\s+)?save\s+money",
            r"i\s+don'?t\s+want\s+(this\s+)?(deal|offer|discount)",
        ],
        "label": "Confirmshaming",
        "severity": "high",
    },
    "subscription_trap": {
        "patterns": [
            r"auto[\s-]?renew",
            r"recurring",
            r"every\s+\d+\s+(month|week|year)",
            r"subscribe\s+(and\s+)?save",
        ],
        "label": "Subscription Trap",
        "severity": "medium",
    },
}


def analyze_page_text(text: str) -> list[dict]:
    """Analyze page text for dark patterns.

    Returns list of detected patterns with type, label, severity, and matched text.
    """
    if not text:
        return []

    detected = []
    text_lower = text.lower()

    for pattern_type, config in DARK_PATTERN_RULES.items():
        for regex in config["patterns"]:
            matches = re.findall(regex, text_lower)
            if matches:
                detected.append(
                    {
                        "type": pattern_type,
                        "label": config["label"],
                        "severity": config["severity"],
                        "matched": matches[0] if isinstance(matches[0], str) else "",
                    }
                )
                break  # one match per pattern type

    return detected


def get_dark_pattern_warnings(page_text: str) -> list[str]:
    """Get human-readable warnings for display in the overlay."""
    patterns = analyze_page_text(page_text)
    warnings = []
    for p in patterns:
        icon = {
            "Fake Scarcity": "⚠️",
            "False Urgency": "⏰",
            "Social Proof Manipulation": "👥",
            "Confirmshaming": "😤",
            "Subscription Trap": "🔄",
        }.get(p["label"], "⚠️")
        warnings.append(f"{icon} {p['label']} detected")
    return warnings
