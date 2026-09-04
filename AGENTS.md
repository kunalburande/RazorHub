# RazorHub — Autonomous Agentic Commerce & Payments Engine

## Stack
- **Backend:** Django 6 + Django REST Framework, SQLite (local) / PostgreSQL (Neon), Cloudinary (media), Gunicorn, Razorpay SDK, MCP (`mcp>=1.0.0`)
- **Frontend:** React 19 + TypeScript, Vite, Tailwind CSS 4, React Router 7, Canvas Confetti, Lucide Icons
- **Deployment:** Backend on Render, Frontend on Vercel
- **Error Tracking:** Sentry (sentry-sdk on backend, @sentry/react on frontend)

## Backend Structure (`backend/`)
- `core/` — Django project root: `settings.py`, `urls.py`, `wsgi.py`, `asgi.py`
- `intelligence/` — Autonomous agent engines:
  - Razorpay MCP (Model Context Protocol) client and tools
  - Dunning / Payment Recovery agent (webhook-driven retry scheduling, multi-channel dunning, ledger logging)
  - RTO Risk guardrail (pre-dispatch COD scoring, return-to-origin mitigation)
  - Cash-Flow and payout forecasting (working capital velocity, T+2 settlement modeling)
  - 3-Way Reconciled agent catalog feed (`/api/catalog/agent-feed/`)
  - Decision audit trail and policy engine evaluation
- `agent_api/` — Agent machine-to-machine authentication, API key lifecycle, and x402 Micropayments protocol
- `agent_runtime/` — Autonomous execution engine, policy checks, and execution logs
- `users/` — Customer authentication (Google OAuth, JWT, email OTP) and profiles
- `products/` — Product catalog, categories, search, pricing, and Schema.org JSON-LD structured data
- `orders/` — Order lifecycle, smart store cart grouping, Razorpay checkout, webhook handling
- `sellers/` — Merchant store management, delivery zones, seller profiles
- `crm/` — CRM module, customer retention insights, admin analytics
- `wishlist/` — Customer wishlist synchronization
- `templates/` — Email notification templates (welcome, promo, password reset, OTP)

## Frontend Structure (`frontend/src/`)
- `App.tsx` — Application root and route tree (including `/agents`, `/agent-audit`, `/catalog-agent`, `/wishlist`, `/seller/*`)
- `pages/` — Core customer and agent pages:
  - `AgentStudio.tsx` — Conversational checkout assistant built on Razorpay MCP patterns
  - `AgentAuditPage.tsx` — Transparent decision audit logs and agent actions
  - `CatalogAgentFeedPage.tsx` — Machine-readable 15-attribute catalog inspection
  - `AiShopping.tsx`, `Home.tsx`, `Products.tsx`, `ProductDetails.tsx`, `Cart.tsx`, `Checkout.tsx`
  - `DashboardHome.tsx` — Customer dashboard with integrated Wishlist and Order History
  - `AdminDashboard.tsx`, `AdminUsersPage.tsx`, `CRMPage.tsx`, `OrdersPage.tsx`, `StoreDetails.tsx`
- `seller/` — Merchant Intelligence Suite:
  - `SellerPortal.tsx` — Unified merchant navigation and shell
  - `pages/PolicyEngine.tsx` — Risk limits and autonomous agent guardrails
  - `pages/RecoveryDashboard.tsx` — Dunning agent recovery metrics and ledger
  - `pages/RevenueIntelligence.tsx` — Cashflow and settlement forecast charts
  - `pages/AgentsConsole.tsx` — Active agent management and health
- `components/` — Reusable UI modules:
  - `voice/VoiceShoppingModal.tsx`, `VoiceMicButton.tsx` — Voice commerce assistant
  - `cart/WhyNotThisModal.tsx`, `RejectionExplainerModal.tsx` — Transparent exclusion explainer
  - `agent/AgentKeyModal.tsx` — x402 machine credentials manager
  - `Navbar.tsx`, `Footer.tsx`, `ProductCard.tsx`, `CartContext.tsx`, `ThemeToggle.tsx`
- `context/` — `AuthContext`, `CartContext`, `ThemeContext`
- `lib/` — Core utilities:
  - `razorpayMcp.ts`, `agentAudit.ts`, `voiceAgent.ts`, `policyEngine.ts`, `dunningAgent.ts`, `rtoRisk.ts`, `cashflowForecast.ts`
  - `api.ts`, `products.ts`, `checkout.ts`, `orders.ts`, `googleAuth.ts`, `recentlyViewed.ts`
- `hooks/` — Custom React hooks
- `i18n/` — Internationalization (`localeStore.ts`, `LocaleContext.tsx`)
- `layouts/` — `RootLayout`, `DashboardLayout`

## Key Conventions
- Django backend uses function-based views decorated with `@api_view` and `@permission_classes`
- Frontend uses functional React components with hooks
- API base path: `/api/`
- Frontend API calls go through `lib/api.ts` (configured Axios instance with auth interceptors)
- Authentication: JWT tokens stored in localStorage, Google OAuth supported
- Non-Negotiable Human Cart Confirmation: Agents stage products and resolve constraints, but payment capture strictly requires user checkout confirmation modal (Razorpay liability pattern)
- Reconciled Catalog: Product page JSON-LD, agent feed, and MCP tools must agree on price and stock
- Media files: Cloudinary for production, local `/media/` for development
- Single-page application rewrites enabled in `vercel.json` (`/(.*) -> /index.html`)

## Common Commands
- Run backend tests: `cd backend && python manage.py test intelligence.tests orders users`
- Frontend typecheck: `cd frontend && npx tsc --noEmit`
- Full stack local launch: `.\start.ps1` (Windows) or `./start.sh` (macOS/Linux)
