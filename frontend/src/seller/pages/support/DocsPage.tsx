import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpen,
  Compass,
  FileText,
  Search,
  Bot,
  Building2,
  Shield,
  ShieldAlert,
  Cpu,
  Database,
  Code2,
  Zap,
  CheckCircle2,
  Lock,
  Layers,
  Sparkles,
  ArrowRight,
  ExternalLink,
  ChevronRight,
  Terminal,
} from 'lucide-react';

interface DocSection {
  id: string;
  title: string;
  badge: string;
  icon: any;
  summary: string;
  topics: {
    title: string;
    description: string;
    codeSnippet?: string;
  }[];
}

const DOC_SECTIONS: DocSection[] = [
  {
    id: 'architecture',
    title: 'Platform Architecture & Tech Stack',
    badge: 'Core Engine',
    icon: Layers,
    summary:
      'RazorHub combines a high-concurrency Django 6 REST backend with a modern React 19 frontend, deployed on Render and Vercel with NeonDB serverless PostgreSQL.',
    topics: [
      {
        title: 'Backend Framework & Database',
        description:
          'Django 6.0 + Django REST Framework. Uses function-based views decorated with @api_view and strict permission classes. Production data is stored in NeonDB PostgreSQL (ap-southeast-1) with SQLite fallback for offline development.',
        codeSnippet: `// Backend Stack Summary
• Framework: Django 6.0 + Django REST Framework
• Database: NeonDB Serverless PostgreSQL (ap-southeast-1)
• Media Storage: Cloudinary CDN & local /media/
• Production Server: Gunicorn with Gevent workers
• Observability: Sentry SDK with Zero-Trust Scrubber`,
      },
      {
        title: 'Frontend Architecture',
        description:
          'React 19 + TypeScript + Vite + Tailwind CSS 4. Client routing is orchestrated by React Router 7 with role-based Route Guards protecting Customer, Seller, and Admin environments.',
      },
      {
        title: 'Autonomous Error Healing Pipeline',
        description:
          'Integrated with Sentry webhook listeners and GitHub Actions workflows (.github/workflows/opencode-autofix.yml) for automated issue classification and code repair.',
      },
    ],
  },
  {
    id: 'agentic-banking',
    title: 'Agentic Business Banking Suite',
    badge: 'Treasury Module',
    icon: Building2,
    summary:
      'An autonomous corporate finance team providing continuous balance monitoring, debtor collection, governed disbursements, and automated double-entry bookkeeping.',
    topics: [
      {
        title: 'Insights Agent (Real-Time Treasury Intelligence)',
        description:
          'Calculates cash balance, today\'s/weekly/monthly revenue, outstanding receivables, upcoming vendor disbursements, burn rate, cash runway, and forecast curves.',
      },
      {
        title: 'Receivables Agent (Autonomous Invoicing & Collections)',
        description:
          'Continuously scans active invoices, identifies overdue debtor balances, prioritizes recovery via communication consent rules, and terminates follow-ups automatically upon payment.',
      },
      {
        title: 'Payout Agent (Governed Vendor Disbursements)',
        description:
          'Processes natural-language payout instructions (e.g., "Pay Rahul ₹18,500 for invoice INV-204"). Verifies vendor records, evaluates transaction risk, checks spending limits, and halts for human administrator authorization.',
      },
      {
        title: 'Double-Entry Bookkeeping Agent',
        description:
          'Automatically records ledger journal entries for all money inflows and outflows, generating compliant P&L, balance sheets, and tax provisions.',
      },
    ],
  },
  {
    id: 'risk-engine',
    title: 'Explainable Financial Risk Engine',
    badge: 'Security Firewall',
    icon: ShieldAlert,
    summary:
      'A deterministic 11-factor risk scoring engine that evaluates transaction risk in under 15ms. Critical deterministic rules cannot be bypassed or overridden by LLMs.',
    topics: [
      {
        title: '11 Risk Dimensions',
        description:
          'Evaluates transaction amount vs customer average, customer age, merchant history, chargeback record, refund frequency, 10-minute velocity, category anomaly, new device fingerprint, VPN proxy detection, impossible travel velocity, and failed payment attempts.',
        codeSnippet: `// Example Risk Output Schema
{
  "riskScore": 82,
  "riskLevel": "HIGH",
  "critical_rule_triggered": false,
  "reasons": [
    "amount 4.2x customer average",
    "7 failed attempts in 10 minutes",
    "new device fingerprint detected",
    "unusual crypto/high-risk category"
  ]
}`,
      },
      {
        title: 'Governance Thresholds & Enforcement',
        description:
          'Transactions with risk scores ≥85 are marked CRITICAL and blocked automatically. Scores between 60–84 require dual-factor human administrator authorization.',
      },
    ],
  },
  {
    id: 'command-center',
    title: 'AI Command Center & Intent Engine',
    badge: 'Natural Language UI',
    icon: Sparkles,
    summary:
      'Natural-language command bar enabling operators to query metrics, trigger actions, or deploy agents without manual menu navigation.',
    topics: [
      {
        title: 'Deterministic Intent Classification',
        description:
          'Categorizes user prompts into 6 deterministic buckets: QUERY, ANALYZE, ACTION, CREATE_AGENT, REPORT, or ESCALATE. Commands requiring money movement generate interactive approval cards.',
      },
      {
        title: '4-Step Transparency Guarantee',
        description:
          'Every executed command returns structured accountability data: 1) What I understood, 2) What data I used, 3) What I plan to do, and 4) What I actually did.',
      },
    ],
  },
  {
    id: 'connectors',
    title: 'Connector Architecture & Observability',
    badge: 'Integrations',
    icon: Code2,
    summary:
      'Extensible connector system supporting mock, Razorpay test mode, and third-party accounting/communication systems with 20-field audit telemetry.',
    topics: [
      {
        title: 'Supported Connector Types',
        description:
          'PaymentGateway, Commerce, Banking, Accounting, Communication (Email, WhatsApp, SMS, In-app, Telegram), and Analytics. Connectors expose explicit capabilities: READ, WRITE, SEND, CREATE, UPDATE, DELETE.',
      },
      {
        title: 'Zero-Trust Observability & Scrubber',
        description:
          'Every agent execution captures a 20-field telemetry record with timeline playback. The SecretScrubber redacts API keys, passwords, and bearer tokens before persistence.',
      },
    ],
  },
];

export default function DocsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeSectionId, setActiveSectionId] = useState<string>('architecture');

  const filteredSections = useMemo(() => {
    if (!searchQuery.trim()) return DOC_SECTIONS;
    const q = searchQuery.toLowerCase();
    return DOC_SECTIONS.filter(
      (sec) =>
        sec.title.toLowerCase().includes(q) ||
        sec.summary.toLowerCase().includes(q) ||
        sec.topics.some(
          (t) =>
            t.title.toLowerCase().includes(q) ||
            t.description.toLowerCase().includes(q)
        )
    );
  }, [searchQuery]);

  const activeSection =
    filteredSections.find((s) => s.id === activeSectionId) ||
    filteredSections[0] ||
    DOC_SECTIONS[0];

  return (
    <div className="min-h-screen bg-background text-primary pb-20 font-sans transition-colors">
      
      {/* ── Documentation Header ── */}
      <div className="border-b border-border bg-gradient-to-b from-surface via-surface to-background/50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-5xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 mb-2">
                <BookOpen className="w-3.5 h-3.5" />
                <span>Developer &amp; Operator Documentation</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-primary">
                RazorHub Technical Documentation
              </h1>
              <p className="text-sm text-secondary mt-1 max-w-2xl">
                Comprehensive blueprints, architecture guides, Agentic Banking workflows, Explainable Risk Engine specs, and API connectors.
              </p>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <Link
                to="/api-reference"
                className="px-4 py-2.5 rounded-2xl border border-border bg-surface text-xs font-bold text-primary hover:bg-muted transition flex items-center gap-1.5"
              >
                <FileText className="h-4 w-4 text-accent" />
                <span>API Reference</span>
              </Link>
              <Link
                to="/banking"
                className="px-4 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-xs font-bold text-white shadow-md shadow-indigo-500/25 transition flex items-center gap-1.5"
              >
                <Building2 className="h-4 w-4" />
                <span>Launch Banking</span>
              </Link>
            </div>
          </div>

          {/* Search Bar */}
          <div className="relative pt-2">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-secondary" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search documentation (e.g. Risk Engine, Payout Agent, Django, SecretScrubber, Connectors)..."
              className="w-full h-12 rounded-2xl border border-border bg-surface pl-11 pr-4 text-sm text-primary placeholder:text-secondary/70 shadow-sm focus:border-accent focus:outline-none transition-all"
            />
          </div>
        </div>
      </div>

      {/* ── Main Layout: Sidebar Nav + Content ── */}
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 pt-10">
        <div className="grid grid-cols-1 lg:grid-cols-[280px_minmax(0,1fr)] gap-8 items-start">
          
          {/* Left Navigation Sidebar */}
          <aside className="rounded-3xl border border-border bg-surface p-4 shadow-xs space-y-2 lg:sticky lg:top-24">
            <h3 className="px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-secondary">
              Core Modules
            </h3>
            <div className="space-y-1">
              {filteredSections.map((sec) => {
                const Icon = sec.icon;
                const isActive = activeSection.id === sec.id;
                return (
                  <button
                    key={sec.id}
                    type="button"
                    onClick={() => setActiveSectionId(sec.id)}
                    className={`w-full flex items-center justify-between p-3 rounded-2xl text-left text-xs font-bold transition-all cursor-pointer ${
                      isActive
                        ? 'bg-accent text-white shadow-md shadow-accent/20'
                        : 'text-secondary hover:text-primary hover:bg-muted/60'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <Icon className={`h-4 w-4 shrink-0 ${isActive ? 'text-white' : 'text-secondary'}`} />
                      <span className="truncate">{sec.title}</span>
                    </div>
                    <ChevronRight className={`h-3.5 w-3.5 shrink-0 opacity-60 ${isActive ? 'text-white' : ''}`} />
                  </button>
                );
              })}
            </div>

            <div className="pt-4 border-t border-border mt-4 space-y-2">
              <span className="block px-3 text-[11px] font-bold uppercase tracking-wider text-secondary">
                Quick Shortcuts
              </span>
              <Link
                to="/agents"
                className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold text-secondary hover:text-primary hover:bg-muted"
              >
                <Bot className="h-3.5 w-3.5 text-indigo-500" />
                <span>Agent Studio Suite</span>
              </Link>
              <Link
                to="/risk-engine"
                className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold text-secondary hover:text-primary hover:bg-muted"
              >
                <ShieldAlert className="h-3.5 w-3.5 text-orange-500" />
                <span>Risk Engine Simulator</span>
              </Link>
              <Link
                to="/help-center"
                className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold text-secondary hover:text-primary hover:bg-muted"
              >
                <BookOpen className="h-3.5 w-3.5 text-accent" />
                <span>24/7 Help Center</span>
              </Link>
            </div>
          </aside>

          {/* Right Content Panel */}
          <main className="space-y-8 min-w-0">
            {activeSection && (
              <div className="space-y-8 animate-in fade-in duration-200">
                {/* Section Hero Banner */}
                <div className="rounded-3xl border border-border bg-surface p-6 sm:p-8 shadow-xs space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-md text-[10px] font-extrabold uppercase tracking-wide bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
                      {activeSection.badge}
                    </span>
                  </div>
                  <h2 className="text-2xl sm:text-3xl font-black text-primary tracking-tight">
                    {activeSection.title}
                  </h2>
                  <p className="text-xs sm:text-sm text-secondary leading-relaxed max-w-3xl">
                    {activeSection.summary}
                  </p>
                </div>

                {/* Topics Grid */}
                <div className="space-y-6">
                  {activeSection.topics.map((topic, idx) => (
                    <div
                      key={idx}
                      className="rounded-3xl border border-border bg-surface p-6 sm:p-7 shadow-xs space-y-4"
                    >
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                        <h3 className="text-base font-black text-primary">
                          {topic.title}
                        </h3>
                      </div>

                      <p className="text-xs sm:text-sm text-secondary leading-relaxed">
                        {topic.description}
                      </p>

                      {topic.codeSnippet && (
                        <div className="rounded-2xl border border-border/80 bg-zinc-950 p-4 font-mono text-xs text-emerald-400 overflow-x-auto shadow-inner">
                          <pre className="whitespace-pre">{topic.codeSnippet}</pre>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Section Footer Callout */}
                <div className="rounded-2xl border border-border bg-muted/20 p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-accent/10 text-accent">
                      <Terminal className="h-4 w-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-primary">Want to inspect code implementations?</h4>
                      <p className="text-[11px] text-secondary">Review tests and open-source models in backend/agent_runtime/ and frontend/src/lib/.</p>
                    </div>
                  </div>
                  <Link
                    to="/help-center"
                    className="text-xs font-bold text-accent hover:underline flex items-center gap-1 shrink-0"
                  >
                    Contact Engineers →
                  </Link>
                </div>
              </div>
            )}
          </main>

        </div>
      </div>
    </div>
  );
}

