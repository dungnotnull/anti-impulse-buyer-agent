# PROJECT-detail.md — anti-impulse-buyer
## Source of Truth — Technical Specification

---

## Executive Summary
**anti-impulse-buyer** is a browser extension and local AI agent that acts as a financial guardian at the precise moment of purchase. When a user clicks "Checkout" or "Buy Now" on any e-commerce platform, the agent intercepts the action, freezes the transaction for 5 minutes, delivers a cold financial analysis personalized to the user's spending history, and requires completion of a logic challenge before allowing the purchase to proceed. The system combines browser-level DOM interception, a local SQLite spending ledger, ML-based product classification, and an LLM-generated financial narrative to break the psychological manipulation loop engineered by modern e-commerce dark patterns.

---

## Problem Statement

### The Scale of Impulse Buying
- **Globally, 40–80% of all purchases** are unplanned or impulse-driven (Journal of Consumer Psychology, 2023)
- **$5,400 per year** is the average amount US consumers waste on impulse purchases (Slickdeals survey, 2022)
- **E-commerce amplifies impulse buying** by 3× compared to physical stores due to frictionless one-click purchasing (MIT Sloan, 2021)
- **Dark patterns are deliberate:** countdown timers, fake scarcity ("only 2 left!"), social proof manipulation ("247 people viewing this") are documented UX dark patterns that exploit System 1 thinking
- **Late-night purchases (10 PM–2 AM)** show 34% higher return rates and 28% lower post-purchase satisfaction (Nielsen, 2023), confirming impaired rational judgment

### The Intervention Gap
Current solutions — budgeting apps, card spending limits — operate after the damage is done. No tool currently intervenes at the exact moment of purchase with personalized, contextual financial friction. This is the gap anti-impulse-buyer fills.

---

## Target Users & Use Cases

| User Type | Pain Point | Use Case |
|-----------|-----------|---------|
| Young professionals (22–35) | BNPL debt, overspending on fashion/tech | Want guardrails without losing spending freedom |
| Students | Limited budget, heavy social media influence | Need hard stops on non-essential spending |
| Budget-conscious families | Impulse grocery/household items, Amazon binges | Track household spending vs. essential items list |
| Recovering shopaholics | Emotional spending triggers | Enforce cooling-off periods, track progress |
| Financial wellness coaches | Client accountability | Recommend as accountability tool |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    BROWSER LAYER                            │
│  ┌─────────────────┐    ┌──────────────────────────────┐   │
│  │  Content Script  │    │      Popup Dashboard         │   │
│  │  (DOM Monitor)   │    │   (React + Recharts)         │   │
│  │  Intercept Buy   │    │   Spending Analytics UI      │   │
│  │  button clicks   │    └──────────────────────────────┘   │
│  └────────┬────────┘                                        │
│           │ checkout event                                   │
│  ┌────────▼────────────────────────────────────────────┐    │
│  │              Service Worker (Background)             │    │
│  │  - Route interception via webRequest API             │    │
│  │  - Freeze UI overlay (5-min countdown)               │    │
│  │  - Dispatch to local backend                         │    │
│  └────────┬────────────────────────────────────────────┘    │
└───────────┼─────────────────────────────────────────────────┘
            │ HTTP (localhost:7432)
┌───────────▼─────────────────────────────────────────────────┐
│                  LOCAL PYTHON BACKEND                        │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  Impulsivity   │  │  Product     │  │  Financial      │  │
│  │  Score Engine  │  │  Classifier  │  │  Narrative Gen  │  │
│  │  (Rules +SLM)  │  │  (BART-MNLI) │  │  (LLM Router)   │  │
│  └───────┬────────┘  └──────┬───────┘  └────────┬────────┘  │
│          └─────────────────┼──────────────────── ┘           │
│                    ┌───────▼───────┐                         │
│                    │   SQLite DB   │                         │
│                    │ (AES-256 enc) │                         │
│                    │ spending_log  │                         │
│                    │ essentials    │                         │
│                    │ user_profile  │                         │
│                    └───────┬───────┘                         │
└────────────────────────────┼────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                     AI / ML LAYER                            │
│  ┌─────────────────┐  ┌───────────────┐  ┌───────────────┐  │
│  │  Ollama Local   │  │  Claude API   │  │  OpenAI API   │  │
│  │  (Phi-3-mini)   │  │  (Narrative)  │  │  (Fallback)   │  │
│  │  Primary SLM    │  │  Primary LLM  │  │  Secondary    │  │
│  └─────────────────┘  └───────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology | Source |
|-----------|-----------|--------|
| Browser Extension | Chrome/Firefox WebExtension (Manifest V3) | Native |
| Content Scripts | Vanilla JavaScript (ES2022) | Native |
| Extension Popup | React 18 + Vite + Recharts | npm |
| Local Backend | Python 3.12 + FastAPI | pip |
| SQLite ORM | SQLAlchemy 2.0 + sqlcipher3 (AES-256) | pip |
| Product Classifier | facebook/bart-large-mnli via HuggingFace Transformers | pip |
| Sentence Similarity | sentence-transformers/all-MiniLM-L6-v2 | pip |
| Sentiment Analysis | cardiffnlp/twitter-roberta-base-sentiment-latest | pip |
| Local SLM | Phi-3-mini via Ollama | Ollama |
| LLM Router | Custom pluggable backend (Claude → GPT-4 → Ollama) | Custom |
| Claude API | anthropic Python SDK 0.30+ | pip |
| OpenAI API | openai Python SDK 1.40+ | pip |
| Task Queue | Celery + Redis (for async SLM inference) | pip |
| Testing | pytest + playwright (browser automation tests) | pip |
| Packaging | PyInstaller (local backend) + web-ext (extension) | pip/npm |

---

## ML/DL Models

### Core Models

| Model | HuggingFace ID | Purpose | Fine-tune Needed |
|-------|---------------|---------|-----------------|
| BART-Large-MNLI | `facebook/bart-large-mnli` | Zero-shot product category classification (essential vs. impulse vs. ambiguous) | No |
| all-MiniLM-L6-v2 | `sentence-transformers/all-MiniLM-L6-v2` | Semantic similarity: match product name to user's essential items list | No |
| Twitter RoBERTa Sentiment | `cardiffnlp/twitter-roberta-base-sentiment-latest` | Detect emotional state signal from recent browsing text for impulsivity context | No |
| Phi-3-mini-4k-instruct | `microsoft/phi-3-mini-4k-instruct` | Local SLM for spending pattern reasoning, generating budget impact statements | No (prompt engineering) |

### Impulsivity Score Formula
```
ImpulsivityScore = (
  0.25 * time_of_day_factor +        # 0.0 (daytime) to 1.0 (midnight)
  0.20 * essential_similarity_inv +  # 1 - cosine_similarity(product, essentials_list)
  0.20 * recent_purchase_frequency + # purchases last 48h / baseline
  0.20 * price_to_income_ratio +     # item_price / (monthly_avg_spend / 30)
  0.15 * category_impulse_weight     # per-category base weight (fashion=0.9, groceries=0.2)
) * sentiment_multiplier             # 1.0-1.3 based on detected emotional state
```

Score thresholds:
- `0.0–0.4`: Low — purchase proceeds after 2-minute educational nudge
- `0.4–0.7`: Medium — 5-minute freeze + financial analysis + easy logic challenge
- `0.7–1.0`: High — 5-minute freeze + harsh financial analysis + hard logic challenge + 24h "wish list" suggestion

### Fine-tuning Plan
BART-MNLI performs well zero-shot for product classification. If accuracy on niche categories drops below 85%, fine-tune on a custom dataset of product titles labeled as essential/impulse/ambiguous (target: 10,000 labeled examples scraped from Amazon categories + manual annotation).

---

## External LLM API Integration

### LLM Router Design (Pluggable Backend)
```python
class LLMRouter:
    backends = ["claude", "openai", "ollama"]  # priority order
    
    def generate_narrative(self, context: SpendingContext) -> str:
        for backend in self.backends:
            try:
                return self._call(backend, context)
            except (APIError, RateLimitError):
                continue
        raise AllBackendsFailedError()
```

### Narrative Prompt Template
```
System: You are a brutally honest financial advisor. Generate a 2-3 sentence 
cold financial analysis of this purchase. Be specific, data-driven, and empathetic 
but firm. Do NOT moralize.

User: The user is about to buy: {product_name} for ${price}.
Their monthly average spending is ${monthly_avg}. 
They already own {similar_items_count} similar items unused.
This item costs {days_of_salary:.1f} days of their estimated income.
Their impulsivity score is {score:.2f}/1.0 (high = more impulsive).
Generate the financial reality check message.
```

| Provider | Model | Use Case | Config Key |
|----------|-------|---------|-----------|
| Anthropic Claude | claude-sonnet-4-6 | Primary narrative generation | `CLAUDE_API_KEY` |
| OpenAI | gpt-4o-mini | Fallback narrative generation | `OPENAI_API_KEY` |
| Ollama | phi3:mini | Privacy-first local inference | `OLLAMA_BASE_URL` |

---

## Feature Specification

### MVP Features (Phase 1)
- [ ] Checkout button interception on top 20 e-commerce sites (Amazon, eBay, Shopee, Lazada, Temu, Shein, Zalando, etc.)
- [ ] 5-minute mandatory freeze with countdown overlay UI
- [ ] Essential items list management (user-curated whitelist)
- [ ] Basic impulsivity score (price + time-of-day + category)
- [ ] Financial narrative generation (local Ollama only in MVP)
- [ ] Logic challenge gate (3 simple math/logic puzzles)
- [ ] Local SQLite purchase history logging
- [ ] Browser popup: spending summary for last 30 days

### Advanced Features (Phase 2–4)
- [ ] Full ML impulsivity score (all 5 factors + sentiment multiplier)
- [ ] BART-MNLI product category auto-classification
- [ ] Semantic matching to essential items list (MiniLM)
- [ ] Claude API / GPT-4 narrative generation (with opt-in)
- [ ] "Wish list quarantine": deferred purchases reviewed weekly
- [ ] Monthly spending trend charts (Recharts dashboard)
- [ ] "Money saved" tracker: cumulative savings from blocked impulse buys
- [ ] Dark pattern detector: flag countdown timers, fake scarcity messages on page
- [ ] Accountability buddy: share weekly spending report via email
- [ ] Gamification: streaks, badges for resisting impulse purchases
- [ ] Multi-device sync via end-to-end encrypted cloud backup (optional)
- [ ] Import bank statement CSV to bootstrap spending history

---

## Full E2E Data Flow

1. User navigates to an e-commerce product page; content script detects site via URL pattern matching
2. Content script scans DOM for checkout/buy-now buttons; attaches click event interceptors
3. User clicks "Buy Now" → content script extracts product name, price, category from page DOM
4. Content script sends event to Service Worker with `{product_name, price, category, url, timestamp}`
5. Service Worker sends POST to local Python backend at `localhost:7432/api/intercept`
6. Backend: BART-MNLI classifies product category (essential vs. impulse vs. ambiguous)
7. Backend: MiniLM computes cosine similarity between product and user's essential items list
8. Backend: SQLite queries user's 90-day spending history for baseline metrics
9. Backend: Computes composite Impulsivity Score using formula above
10. Backend: Routes to LLM (Ollama → Claude → GPT-4) for financial narrative generation
11. Backend returns `{score, category, narrative, challenge_difficulty, similar_owned_count}` to Service Worker
12. Service Worker injects freeze overlay into page: countdown timer + financial analysis + logic challenge
13. If user completes challenge → purchase proceeds; event logged as "proceeded"
14. If user closes overlay / timer expires → purchase blocked; event logged as "blocked"
15. If user clicks "Add to Wish List" → item added to deferred queue; reviewed in weekly digest
16. All events written to SQLite `purchase_events` table for dashboard analytics

---

## Privacy & Security

| Concern | Mitigation |
|---------|-----------|
| Spending history sensitivity | AES-256 encryption on SQLite via sqlcipher3 |
| Product data to external LLM | Opt-in only; user must explicitly enable Claude/GPT-4; local Ollama is default |
| Browser permissions | Minimal: `activeTab`, `webRequest`, `storage`; no broad host permissions |
| Local backend exposure | Listens on localhost only; CORS restricted to extension origin |
| Data retention | User controls retention window (30/90/365 days); one-click data purge |
| No account required | Extension works fully offline and account-free |

---

## Key Python/JS Dependencies

```
# Python (requirements.txt)
fastapi==0.115.0
uvicorn==0.30.0
sqlalchemy==2.0.35
sqlcipher3==0.5.3
transformers==4.44.0
sentence-transformers==3.1.0
anthropic==0.40.0
openai==1.51.0
ollama==0.3.3
celery==5.4.0
redis==5.1.1
torch==2.4.1
pytest==8.3.3
playwright==1.47.0

# JavaScript/Node (package.json)
react: ^18.3.0
vite: ^5.4.0
recharts: ^2.13.0
web-ext: ^8.3.0
@types/chrome: ^0.0.270
```

---

## Improvement Suggestions (Beyond Original Idea)

1. **Dark Pattern Detector Mode**: Before interception, visually highlight manipulative UI elements on the page (countdown timer = red border, "Only 1 left" = yellow warning) to make the manipulation visible
2. **Recurring Purchase Intelligence**: Learn which items the user buys monthly/quarterly and auto-whitelist them to reduce false-positive friction
3. **Price History Integration**: Pull price history from CamelCamelCamel or Keepa API to show "this item was 30% cheaper last month" — adds objective financial context beyond personal spending
4. **Salary-Linked Calibration**: Let user input monthly net income; all financial analyses become calibrated ("this costs 4.2 hours of your work time")
5. **Emotional Trigger Mapping**: Track which emotional states (bored, stressed, lonely — inferred from time patterns) correlate with high-impulse purchases; generate personalized alerts
6. **Gift vs. Self-Purchase Distinction**: Let user tag a purchase as a gift; gifts follow a different (more lenient) impulsivity scoring path
7. **Group Accountability**: Optional anonymous leaderboard within a friend group showing total impulse purchases resisted this month
8. **Return Rate Feedback Loop**: Let user mark items as "returned/unused"; feed this back into the category impulse weight calibration
9. **Subscription Spending Radar**: Detect recurring charges that were originally impulse subscriptions and surface them in the weekly digest for cancellation review
10. **Browser History Mood Proxy**: Analyze browsing session duration, tab count, and site diversity as a proxy for focus vs. distracted state to refine time-of-day factor
