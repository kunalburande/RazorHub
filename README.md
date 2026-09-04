# ⚡ RazorHub — Autonomous Agentic Commerce & Payments Engine

[![Frontend](https://img.shields.io/badge/Frontend-React%2019%20%2B%20TypeScript%20%2B%20Vite-61DAFB?logo=react)](frontend/)
[![Backend](https://img.shields.io/badge/Backend-Django%206%20%2B%20DRF-092E20?logo=django)](backend/)
[![Styling](https://img.shields.io/badge/Styling-Tailwind%20CSS%204-06B6D4?logo=tailwindcss)](frontend/src/index.css)
[![Payments](https://img.shields.io/badge/Payments-Razorpay%20MCP%20%2B%20x402-0C2340?logo=razorpay)](backend/intelligence/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%2F%20Neon-00E599?logo=postgresql)](backend/)

**RazorHub** is an agentic e-commerce platform that implements autonomous commerce patterns, agent-driven operations, and Razorpay's Agentic Payments architecture.

---

## 🌟 Key Architecture & Agentic Capabilities

### 1. Conversational In-App Checkout (Razorpay MCP Pattern)
- **Constraint-First Intent Resolution:** Transforms natural customer prompts (e.g. *"Find a mechanical keyboard under ₹4,000 with tactile switches"*) into verified product shortlists.
- **Model Context Protocol (MCP) Server Integration:** Built on the standardized Model Context Protocol (`mcp>=1.0.0`) client integration, connecting agents directly to live merchant tools without hand-rolled ad-hoc wrappers.
- **Non-Negotiable Cart Confirmation:** Strict adherence to Razorpay's liability model—the agent handles research, constraint filtering, and order staging, but requires an explicit, human-confirmed checkout modal before UPI or card payment capture.

### 2. "Why Not This?" Transparent Selection & Rejection Explainer
- Demystifies algorithmic decisions: customers can ask why a seemingly relevant item was omitted.
- Provides objective, multi-factor rejection reasons:
  - Budget boundaries exceeded
  - Marginal gain vs. price delta
  - Low seller contribution margin or high return risk
  - Stock scarcity or compatibility mismatches

### 3. Three-Way Reconciled Agent Catalog
Agents cross-reference product information across multiple surfaces. RazorHub guarantees exact parity across:
1. **Product UI:** Microdata and Schema.org `Product` + `Offer` JSON-LD markup.
2. **Catalog Feed:** `/api/catalog/agent-feed/` rendering 15+ canonical fields (GTIN/UPC/MPN, brand, condition, stock availability, standard taxonomy).
3. **Read-Only MCP API:** Tools querying live inventory with sub-minute synchronization to prevent stale cart errors.

### 4. Autonomous Operational Agents (Razorpay Agent Studio)
- **Dunning & Payment Recovery Agent:** Webhook listener on `payment.failed` that schedules intelligent multi-channel retry attempts (SMS, WhatsApp, Email, in-app push) with capped backoff schedules, logging every step to an immutable audit ledger.
- **Return / RTO-Risk Guardrail:** Pre-dispatch machine intelligence scoring Cash-on-Delivery (COD) orders based on pincode reliability, customer history, and product category risk. High-risk orders are flagged with explainable risk factors and automatically gated to prepaid checkout.
- **Cash-Flow & Payout Forecasting Agent:** Analyzes Razorpay settlement cycles (T+2), working capital velocity, return reserves, and supplier payables to project 7-day and 30-day liquidity.
- **Voice Commerce Assistant:** Speech-to-Text intent recognition and audio feedback for hands-free shopping and item additions.

### 5. x402 Micropayments Protocol & Agent Runtime
- **HTTP 402 Payment Required:** Autonomous agents accessing premium catalog endpoints, bulk feeds, or high-throughput settlement APIs authenticate via signed API keys and complete machine-to-machine micropayments before payload delivery.
- **Policy Engine & Decision Audit Trail:** Configurable merchant risk policies with full transparent logs visible in the Seller Portal (`/seller/policy` and `/agent-audit`).

---

## 🧱 Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS 4, React Router 7, Lucide Icons, Canvas Confetti, Sentry |
| **Backend** | Django 6, Django REST Framework, SQLite (Local) / PostgreSQL (Production via Neon), Gunicorn |
| **Agent / MCP** | Model Context Protocol (`mcp`), Anthropic / OpenAI / Google Gemini / OpenRouter / Groq LLM Gateway |
| **Payments** | Razorpay Python SDK, Razorpay Checkout JS, Webhook Verification, x402 Agentic Headers |
| **Cloud & Media** | Render (Backend API), Vercel (Frontend SPA), Cloudinary (Media assets) |

---

## 📁 Repository Structure

```text
RazorHub/
├── backend/
│   ├── core/               # Django project settings, ASGI/WSGI, routing
│   ├── intelligence/       # MCP tools, Dunning, RTO risk, Cashflow, Policy engine
│   ├── agent_api/          # Agent authentication, API keys, x402 micropayments
│   ├── agent_runtime/      # Autonomous execution engine & decision audit logs
│   ├── products/           # Catalog models, search, categories, inventory
│   ├── orders/             # Checkout, cart management, Razorpay payment capture
│   ├── sellers/            # Merchant stores, delivery zones, seller profiles
│   ├── users/              # User auth (JWT, OTP, Google OAuth), customer profiles
│   ├── crm/                # Merchant CRM analytics, customer retention
│   ├── wishlist/           # User wishlist synchronization
│   ├── requirements.txt    # Python dependencies (Django 6, DRF, mcp, razorpay)
│   └── .env.example        # Environment variable template
├── frontend/
│   ├── src/
│   │   ├── pages/          # Home, Products, ProductDetails, Cart, Checkout, AgentStudio, etc.
│   │   ├── seller/         # SellerPortal, PolicyEngine, RecoveryDashboard, RevenueIntelligence
│   │   ├── components/     # UI components, VoiceModal, RejectionExplainer, ProductCard
│   │   ├── context/        # AuthContext, CartContext, ThemeContext
│   │   ├── lib/            # api.ts, razorpayMcp.ts, agentAudit.ts, voiceAgent.ts, etc.
│   │   ├── App.tsx         # React Router routes with ProtectedRoute
│   │   └── main.tsx        # React entry point & Sentry initialization
│   ├── package.json        # Frontend dependencies
│   ├── vite.config.ts      # Vite configuration & dev server proxy
│   └── .env.example        # Frontend environment template
├── start.ps1               # Automated Windows PowerShell startup script
├── start.bat               # Automated Windows CMD launcher
├── start.sh                # Automated Linux/macOS bash launcher
├── vercel.json             # Vercel SPA routing rewrite configuration
└── render.yaml             # Render infrastructure-as-code specification
```

---

## 🚀 Quick Start & Local Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ (Node 20 recommended)
- Git

### One-Command Startup

#### Windows (PowerShell)
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\start.ps1
```

#### Windows (Command Prompt)
```cmd
start.bat
```

#### Linux / macOS
```bash
chmod +x start.sh
./start.sh
```

The script will automatically:
1. Verify Python and Node environments.
2. Initialize and activate Python virtual environment (`backend/venv`).
3. Install backend packages from `backend/requirements.txt`.
4. Apply database migrations (`python manage.py migrate`).
5. Install frontend dependencies (`npm install`).
6. Launch Django backend on port `8000` and Vite dev server on port `5173`.
7. Open the browser to `http://localhost:5173`.

---

## ⚙️ Environment Variables

### Backend (`backend/.env`)
Copy `backend/.env.example` to `backend/.env`:
```ini
DEBUG=True
SECRET_KEY=your-django-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Razorpay Credentials
RAZORPAY_KEY_ID=rzp_test_yourKeyId
RAZORPAY_KEY_SECRET=yourKeySecret
RAZORPAY_WEBHOOK_SECRET=yourWebhookSecret

# Multi-Provider AI Keys (at least one configured)
GEMINI_API_KEY=your-gemini-key
OPENROUTER_API_KEY=your-openrouter-key
GROQ_API_KEY=your-groq-key

# Media (Cloudinary for production)
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

### Frontend (`frontend/.env`)
Copy `frontend/.env.example` to `frontend/.env`:
```ini
VITE_API_URL=http://localhost:8000
VITE_RAZORPAY_KEY_ID=rzp_test_yourKeyId
```

---

## 🧪 Testing & Verification

### Backend Tests
Run the automated test suite covering intelligence tools, orders, payments, and auth:
```bash
cd backend
python manage.py test intelligence.tests orders users
```

### Frontend TypeScript Check
Verify zero TypeScript compiler warnings or errors:
```bash
cd frontend
npx tsc --noEmit
```

---

## 🛡️ License
Built for the next generation of autonomous commerce. Released under the MIT License.
