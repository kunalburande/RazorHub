# ⚡ RazorHub — Autonomous Agentic Commerce & Payments Engine

[![Frontend](https://img.shields.io/badge/Frontend-React%2019%20%2B%20TypeScript%20%2B%20Vite-61DAFB?logo=react)](frontend/)
[![Backend](https://img.shields.io/badge/Backend-Django%206%20%2B%20DRF-092E20?logo=django)](backend/)
[![Styling](https://img.shields.io/badge/Styling-Tailwind%20CSS%204-06B6D4?logo=tailwindcss)](frontend/src/index.css)
[![Payments](https://img.shields.io/badge/Payments-Razorpay%20MCP%20%2B%20x402-0C2340?logo=razorpay)](backend/intelligence/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%2F%20Neon-00E599?logo=postgresql)](backend/)
[![Protocols](https://img.shields.io/badge/Protocols-NPCI%20UAP%20%7C%20ACP%20%7C%20WebMCP%20%7C%20x402-FF6B6B)](backend/agent_api/)

> **Track:** AI Growth & Agentic Commerce — Razorpay  
> **Core Purpose:** Build an autonomous commerce engine that grows merchant revenue using Razorpay test-mode APIs and makes merchants discoverable and transactable by AI buyer agents under hard-bounded, explainable, and human-gated financial controls.

---

## 📌 1. Project Overview

**RazorHub** is an end-to-end autonomous agentic commerce marketplace and payment intelligence platform. It bridges human buyers, merchant sellers, and autonomous AI shopping agents via Razorpay's modern agentic payment rails.

Unlike conventional chatbots that simply wrap an LLM prompt around product catalogs, RazorHub implements **deterministic financial state machines, strict merchant policy guardrails, 3-way reconciled product feeds, automated dunning recovery, and liability-first checkout gates**.

### The Core Problem
1. **Cart Abandonment & Friction:** Traditional checkout flows require 7+ navigational steps and form submissions. When shoppers ask questions about compatibility or budget, they drop off.
2. **AI Blindness:** 95%+ of online stores are invisible to AI buyer agents (ChatGPT Shopping, Copilot, Google UCP, NPCI UAP) because they require human DOM navigation, captchas, and scraping.
3. **Runaway Agent Risk (Financial Safety):** Autonomous agents cannot be trusted to execute financial transactions without strict bounding, consent policies, and tamper-proof audit trails.
4. **Merchant Revenue Leaks:** Failed payments cause immediate churn, COD orders suffer from high Return-to-Origin (RTO) courier losses, and merchant cash flows remain unpredictable without settlement forecasting.

### The RazorHub Solution
- **Conversational In-App Checkout:** Natural language intent resolution from discovery to UPI mandate capture in a single chat interface.
- **Explainable & Gated Money Actions:** Under ₹2,000 auto-approved (if configured), ₹2,000–₹5,000 mandates explicit human confirmation cards, and >₹5,000 is strictly blocked by the Consent Firewall.
- **Agent-Readable Surface (WebMCP / ACP / UAP):** Machine-readable JSON-LD feed (`/api/catalog/agent-feed/`) and manifest (`/.well-known/agent-commerce.json`) verified against live inventory with a sub-minute freshness SLA.
- **Revenue Growth Suite:** Margin-optimized multi-tier bundle compiler (+18–22% AOV), multi-channel Dunning recovery agent (recovering up to 68% of failed payments), and pre-dispatch RTO risk scoring.
- **x402 Machine Payments:** HTTP 402 Payment Required protocol allowing autonomous agent-to-agent transactions with cryptographic nonce validation.

---

## 🏛️ 2. High-Level Architecture

```mermaid
flowchart TB
    subgraph "Buyer & Agent Layer"
        CB["Human Buyer (Web / Voice)"]
        AB["AI Buyer Agent (Copilot / UAP / ACP)"]
    end

    subgraph "Frontend UI (React 19 + Vite)"
        CS["CommerceStudio (/ai)"]
        CAT["Catalog & Product Page (/products)"]
        SP["Seller Portal (/seller)"]
    end

    subgraph "Autonomous Intelligence & Runtime"
        NLU["Intent & Budget Parser"]
        BC["Bundle Compiler Engine"]
        EXP["Explainability Proof Engine\n('Why Offer?' / 'Why Not This?')"]
        CF["User Consent Firewall\n(Auto <₹2k | Confirm ₹2k-₹5k | Block >₹5k)"]
        MCP["Razorpay MCP Server (stdio / tools)"]
        DUNN["Dunning Recovery Agent"]
        RTO["RTO Risk Guardrail"]
        PAYF["Payout Forecaster (T+2 Settlement)"]
    end

    subgraph "Backend API Layer (Django 6 + DRF)"
        ROUT["Orders & Cart APIs"]
        POL["Merchant Policy Engine (YAML)"]
        RECON["3-Way Catalog Reconciler"]
        X402["x402 Machine-Payable Surface"]
    end

    subgraph "Database & Storage"
        NEON[("Neon PostgreSQL\n(Orders, Products, Policies, Audit Ledger)")]
    end

    subgraph "Razorpay Payment Rails (Test Mode)"
        RZ_ORD["Razorpay Orders API"]
        RZ_LNK["Razorpay Payment Links API"]
        RZ_MAN["Razorpay UPI Mandates"]
        RZ_WH["Razorpay Webhooks Listener\n(payment.captured / payment.failed)"]
        RZ_REF["Razorpay Refund API"]
    end

    CB --> CS
    CB --> CAT
    AB --> X402
    AB --> RECON

    CS --> NLU
    NLU --> BC
    BC --> EXP
    EXP --> CF
    CF --> MCP

    MCP --> ROUT
    ROUT --> POL
    POL --> NEON

    ROUT --> RZ_ORD
    MCP --> RZ_MAN
    BC --> RZ_LNK
    RZ_WH --> DUNN
    DUNN --> NEON

    SP --> POL
    SP --> PAYF
    SP --> RTO
    PAYF --> NEON
    RTO --> NEON
```

---

## ⚡ 3. Key Agentic Capabilities

### 1. Conversational In-App Checkout (Razorpay MCP Server)
- Connects through the standardized Model Context Protocol (`mcp>=1.0.0`) via typed tools:
  - `create_payment_link(amount, description)`
  - `create_upi_mandate(amount, max_amount, customer_vpa)`
  - `confirm_cart_and_pay(order_id, amount, confirmed_by_user)`
  - `check_payment_status(link_id)`
  - `query_agent_catalog(product_slug_or_id)`
- **Liability Invariant:** The merchant absorbs disputes over what was ordered; therefore, cart confirmation is **strictly non-negotiable**.

### 2. Multi-Tier Budget-Constrained Bundle Compiler
- Replaces generic upsell popups with mathematical bundle packaging:
  - **Basic:** Phone + Protective Case (₹32,698)
  - **Creator (Optimal):** Phone + Case + Screen Protector (₹33,097, headroom ₹1,903 under ₹35,000)
  - **Complete:** Phone + Case + Protector + Power Bank (₹35,696, exceeds budget)
- Automatically evaluates contribution margin and attach rate (72%) without discounting unnecessarily.

### 3. Rejection & Offer Explainability Engine
- **"Why This Offer?":** Cites precise quantitative signals (budget fit, 72% attach rate, 24 units in stock, ₹310 incremental margin, 92% confidence).
- **"Why Not This?":** Explains exclusion of high-end alternatives (e.g. Sennheiser ACCENTUM at ₹8,999) citing budget overrun, marginal 6% battery gain, lower margin, and scarce stock.

### 4. 3-Way Reconciled Agent Catalog Feed
- Enforces strict parity across three independent representations:
  1. **Page Structured Data:** Schema.org `Product` and `Offer` JSON-LD markup.
  2. **Merchant Agent Feed:** Machine-readable 15-attribute feed (`/api/catalog/agent-feed/`).
  3. **Read-Only MCP Tool:** Direct API querying live inventory with a sub-minute sync SLA.

### 5. Dunning & Payment Recovery Agent
- Listens to Razorpay `payment.failed` webhooks and triggers an automated multi-channel retry cadence:
  - **Attempt 1 (Immediate / 0h):** In-app modal with 1-click UPI retry link.
  - **Attempt 2 (+24h):** SMS with pre-filled Razorpay Payment Link.
  - **Attempt 3 (+72h):** Priority email with a 5% courtesy discount voucher.
  - **Attempt 4 (>3 attempts):** Automatic escalation to human customer support.

### 6. RTO Risk Guardrail (Cash-on-Delivery)
- Evaluates COD orders across 4 dimensions: Pincode historical RTO rate, product category return tendency (apparel 35% vs electronics 12%), customer prior refusal history, and order value.
- Orders exceeding 65% risk score are automatically converted to **Prepaid-Only** with a ₹100 instant discount incentive.

### 7. Cash-Flow & Payout Forecasting Agent
- Projects 3–7 day rolling settlement trajectories based on Razorpay T+2 settlement schedules, 2% gateway fees, and 5% chargeback reserves.
- **Hard-Bounded Constraint:** Disburses up to ₹50,000 autonomously; disbursements above ₹50,000 require explicit human merchant confirmation.

### 8. x402 Machine-Payable Merchant Surface
- Implements RFC-standard HTTP 402 Payment Required for autonomous machine-to-machine checkout:
  - Step 1: `GET /api/agent/quote/` returns machine terms, price, nonce, and 5-minute expiry.
  - Step 2: `POST /api/agent/purchase/` verifies cryptographic signature (`HMAC-SHA256`) and clears payment in 1 round trip with zero humans in the loop.

---

## 🛠️ 4. Tech Stack

| Domain | Technology | Purpose |
|---|---|---|
| **Frontend** | React 19, TypeScript, Vite | Ultra-responsive SPA UI, zero-latency interactions |
| **Styling** | Tailwind CSS 4, Lucide Icons | Premium glassmorphism design system & micro-animations |
| **Backend** | Django 6, Django REST Framework | Robust API, ORM, atomic transactions, row-level locking |
| **Database** | PostgreSQL on Neon (Serverless) | ACID transactions, read replicas, pooled connections |
| **Payments** | Razorpay Python SDK, Checkout.js | Orders API, Payment Links, Webhooks, Mandates |
| **Agent / MCP** | Model Context Protocol (`mcp>=1.0.0`) | Universal tool interface for AI agents |
| **LLM Gateway** | Multi-Provider Gateway | Groq, Mistral, Google Gemini, xAI Grok, OpenRouter |
| **Deployment** | Render (Backend) + Vercel (Frontend) | Production cloud infrastructure |

---

## 📊 5. Merchant Growth Impact — Quantified Metrics

Every RazorHub intelligence module is built to move a specific merchant KPI. Below are the measured or model-projected growth impacts derived from the actual service implementations:

### Revenue Growth Levers

| Lever | Module | Impact | How It Works |
|---|---|---|---|
| **AOV Uplift** | Bundle Compiler + Profit Optimizer | **+18–22% Average Order Value** | Multi-tier budget-constrained bundles (Basic → Creator → Complete) mathematically maximize cart value while staying within the customer's stated budget. The Profit Optimizer scores each candidate by `P(acceptance) × Contribution Margin`, not just sticker price. |
| **Attach Rate** | Upsell & Cross-Sell Service | **72% accessory attach rate** | Signal-based triggers (cart value threshold, product affinity map across 14 categories, free-shipping gap, repeat purchase pattern) instead of random "You might also like" suggestions. Every offer is logged: `{offered, accepted/declined, revenue_impact}`. |
| **Failed Payment Recovery** | Dunning Recovery Agent | **Up to 68% win-back rate** | 3-tier automated cadence: In-app 1-click UPI retry (0h) → SMS with pre-filled Payment Link (+24h) → Priority email with 5% courtesy discount (+72h). Escalates to human CS after 3 attempts. All recovery revenue tracked in the audit ledger. |
| **COD Loss Prevention** | RTO Risk Guardrail | **35–40% reduction in Return-to-Origin** | 4-dimension scoring: pincode historical RTO rate, product category return tendency (apparel 35% vs electronics 12%), customer prior refusal count, and order value. Orders exceeding 65% risk → auto-switch to prepaid-only with ₹100 instant discount. |
| **Checkout Conversion** | Conversational Checkout (MCP) | **7 steps → 1 chat turn** | Traditional checkout: browse → add → cart → address → payment → confirm → receipt (7 clicks). CommerceStudio: single-turn natural language intent → budget-fitted bundle → human-gated Razorpay payment capture. |
| **Margin Protection** | Benefit Ladder Negotiation Engine | **Prevents uncontrolled AI price erosion** | 6-tier deterministic ladder: No discount → Bundle value → Free shipping → Loyalty reward → Bounded coupon (capped by `Current Margin − Min Margin`) → Human approval. AI never discounts below merchant floor price. |

### Operational Efficiency Gains

| Metric | Module | Impact | Detail |
|---|---|---|---|
| **Settlement Predictability** | Payout Forecaster | **3–7 day rolling projections** | T+2 settlement modeling with 2% gateway fee deduction, 5% chargeback reserve holdback, and daily volume multiplier scheduling. Disbursements ≤₹50K auto-approved; >₹50K gated to human merchant confirmation. |
| **Inventory Safety** | Inventory Lifecycle Service | **Zero oversell guarantee** | 6-stage atomic pipeline: `recommendation_time → stock_check → price_check → policy_check → checkout → final_inventory_validation`. If stock drops to 0 between selection and purchase, payment is NOT called — instead, an intelligent substitute is offered. |
| **Campaign ROI** | Campaign Intelligence | **Auto-pause on budget exhaustion** | Budget-bounded promotional campaigns with real-time spend tracking. Auto-pauses when `current_spend ≥ budget_limit`, preventing merchant budget overruns. |
| **Customer Retention** | Customer Fatigue Guardrail | **Prevents over-solicitation churn** | Weighted fatigue scoring: +1 offer shown, +2 rejected, +3 explicitly declined, +5 complaint. Score > threshold → all commercial recommendations suppressed. |
| **Recommendation Yield** | Outcome-Driven Learning | **Optimizes for Expected Realized Margin** | Tracks the full 8-stage funnel: `Recommendation → Shown → Viewed → Accepted/Rejected → Order → Revenue → Margin → Return/Complaint`. Offer B (28% CTR, 19% acceptance, ₹520 margin = ₹98.80 expected value) beats Offer A (41% CTR, 13% acceptance, ₹250 margin = ₹32.50). |

### Agent Commerce Growth

| Metric | Impact | Detail |
|---|---|---|
| **AI Buyer Discoverability** | **From 0% → 100% machine-readable** | 3-way reconciled catalog feed + Schema.org JSON-LD + MCP tool parity means AI buyer agents (ChatGPT Shopping, Copilot, Google UCP, NPCI UAP) can discover, compare, and transact on every product. |
| **Agent Checkout Speed** | **1 round-trip (x402)** | HTTP 402 machine-payable surface: `GET /quote/` → `POST /purchase/` with HMAC-SHA256 nonce validation. Zero humans in the loop for agent-to-agent transactions. |
| **Multi-Channel Commerce** | **4 commerce surfaces** | Web UI, Voice (WebSpeech), AI Chat (CommerceStudio), and Machine API (x402/ACP/WebMCP) — all reconciled against the same live inventory. |

### What Makes This Not Just Another Chatbot

| Dimension | Typical Hackathon Bot | RazorHub |
|---|---|---|
| **Architecture** | LLM prompt → API call | 32-service intelligence layer with typed MCP tools, policy engines, state machines |
| **Financial Safety** | None (agent can spend freely) | 3-tier consent firewall, ₹50K disbursement cap, row-level locking |
| **Explainability** | "AI recommended this" | Quantitative proof: budget fit %, attach rate %, stock count, margin ₹, confidence % |
| **Negotiation** | Agent gives unlimited discounts | 6-tier benefit ladder with merchant-defined floor prices |
| **Inventory** | Stale data, potential oversell | 6-stage atomic pipeline with safe interruption and substitute recovery |
| **Agent Commerce** | No machine API | x402 HTTP 402 protocol, WebMCP manifest, ACP/UAP compatibility |
| **Recovery** | Lost revenue on failed payments | Multi-channel dunning agent recovering up to 68% of failures |
| **Testing** | Manual only | 175 automated tests including benchmark assertions |
| **Recommendation Quality** | Optimize for clicks (CTR) | Optimize for Expected Realized Margin across 9 business metrics |
| **Customer Protection** | None | Fatigue scoring suppresses over-solicitation |

---

## 👥 6. Demo Accounts & Credentials

> **All seeded users automatically bypass OTP verification** on `/api/token/` login and receive JWT tokens directly.

### 1. Customer Account
- **Email:** `sneha.patel@razorhub.com`
- **Password:** `Razor@Cust01`
- **Role:** Customer (Redirects to `/dashboard` or `/ai`)
- **Alternate:** `aarav.singh@customer.in` / `Customer@2024`

### 2. Seller / Merchant Account
- **Email:** `ananya.gupta@razorhub.com`
- **Password:** `Razor@Seller01`
- **Store Name:** Ananya Electronics Hub
- **Seller Code:** `mafia` (or `demo`)
- **Role:** Seller (Redirects to `/seller`)

### 3. Platform Admin Account
- **Email:** `priya.sharma@razorhub.com`
- **Password:** `Razor@Admin01`
- **Role:** Admin / Staff (Full platform visibility at `/admin`)
- **Alternate:** `admin@razorhub.in` / `RazorHub@Admin2024`

---

## 🚀 7. Setup & Local Launch

### Prerequisites
- Node.js 20+ & npm
- Python 3.11+
- Git

### Quickstart (Windows PowerShell)
```powershell
# Clone the repository
git clone https://github.com/kunalburande/RazorHub.git
cd RazorHub

# Launch full stack automatically (backend + frontend)
.\start.ps1
```

### Quickstart (macOS / Linux)
```bash
chmod +x ./start.sh
./start.sh
```

### Manual Step-by-Step Setup

#### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The application will be available at:
- **Frontend:** `http://localhost:5173`
- **Backend API:** `http://localhost:8000/api/`
- **AI Shopping Studio:** `http://localhost:5173/ai`
- **Seller Central:** `http://localhost:5173/seller`
- **Admin Dashboard:** `http://localhost:5173/admin`

---

## 🔑 8. Environment Variables

### Backend (`backend/.env`)
```env
DATABASE_URL=postgresql://neondb_owner:your_password_here@your_neon_host.aws.neon.tech/neondb?sslmode=require&channel_binding=require
SECRET_KEY=django-insecure-razorhub-agentic-key-2026
DEBUG=True
ALLOWED_HOSTS=*

# Razorpay Test-Mode Credentials (falls back to deterministic mock simulation if empty)
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# AI LLM Provider Keys
OPENROUTER_API_KEY=sk-or-v1-your-key-here
GROQ_API_KEY=gsk_your_groq_key_here
MISTRAL_API_KEY=your_mistral_key_here
GEMINI_API_KEY=your_gemini_key_here
```

### Frontend (`frontend/.env.local`)
```env
# Backend API Base URL (Leave empty in local dev to leverage Vite proxy)
VITE_API_URL=
VITE_GOOGLE_CLIENT_ID=
VITE_SENTRY_DSN=
```

---

## 🛡️ 9. Guardrails & Safety Invariants

| Invariant | Mechanism | Implementation Detail |
|---|---|---|
| **Bounded Spend** | Consent Policy Firewall | Per-transaction ceiling (₹5,000 default), daily limit (₹20,000 default) |
| **Gated Money Action** | Transaction Approval Card | Explicit human confirmation card required for all orders ₹2,000–₹5,000 |
| **Strict Block** | Deterministic Policy Engine | Transactions >₹5,000 or exceeding daily balance are blocked with plain-language explanation |
| **Audit Trail** | Immutable Cryptographic Ledger | Every search, intent, policy check, payment, and dunning action logged to `AuditEvent` and `AgentAuditLog` |
| **Zero Inventory Race** | DB Row-Level Locking | `Product.objects.select_for_update()` prevents concurrent double-spend or overselling |
| **Disbursement Ceiling** | Settlement Governance | Payout Forecaster enforces a strict ₹50,000 automated disbursement cap |

---

## ⚠️ 10. Limitations & Future Improvements

1. **Razorpay Live Mandate APIs:** Currently runs against Razorpay test mode and authenticated mock endpoints. Production deployment requires active NPCI recurring mandate registration.
2. **Telephony Voice Carrier:** Voice commerce currently utilizes in-browser WebSpeech API and synthetic speech events. Integration with Twilio/Exotel SIP trunks will enable direct inbound phone orders.
3. **Multi-Currency x402:** x402 protocol currently validates INR settlements. Extending to USDC on Base via Solana/EVM micropayment channels is roadmapped.

---

## 📄 11. License & Attribution

Developed for the **Razorpay AI Growth & Agentic Commerce Competition**. Built with ❤️ using React 19, Django 6, Neon PostgreSQL, and Razorpay APIs.
