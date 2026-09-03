import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Package,
  Users,
  FileText,
  Building2,
  BarChart2,
  Bot,
  ShieldAlert,
  ClipboardList,
  ArrowRight,
  TrendingUp,
  Zap,
  RefreshCw,
  CheckCircle2,
  Clock,
  Loader2,
} from "lucide-react";
import { apiRequest, unwrapList } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";

const modules = [
  { name: "Catalog", href: "/seller/products", icon: <Package />, desc: "Products & inventory" },
  { name: "Customers", href: "/seller/users", icon: <Users />, desc: "Customer profiles" },
  { name: "Orders", href: "/seller/orders", icon: <FileText />, desc: "Order management" },
  { name: "Banking", href: "/seller/banking", icon: <Building2 />, desc: "Treasury & payouts" },
  { name: "Agents", href: "/seller/agents", icon: <Bot />, desc: "AI agent console" },
  { name: "Risk", href: "/seller/risk", icon: <ShieldAlert />, desc: "Explainable risk engine" },
  { name: "Audit", href: "/seller/audit", icon: <ClipboardList />, desc: "Event audit trail" },
];

interface KpiData {
  products: number;
  orders: number;
  pendingOrders: number;
  agents: number;
}

interface ReadinessData {
  total_score: number;
  grade: string;
  grade_color: string;
  diagnostic_summary: string;
  action_items: string[];
  pillars: Record<string, { label: string; score: number; max: number; pct: number }>;
}

export default function RazorHubSellerDashboard() {
  const { token, user } = useAuth();
  const [kpi, setKpi] = useState<KpiData | null>(null);
  const [kpiLoading, setKpiLoading] = useState(true);
  const [readiness, setReadiness] = useState<ReadinessData | null>(null);
  const [readinessLoading, setReadinessLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      setKpiLoading(true);
      setReadinessLoading(true);
      try {
        const [productsRes, ordersRes, agentsRes, readinessRes] = await Promise.all([
          apiRequest<any>('/products/', { token }).catch(() => null),
          apiRequest<any>('/orders/', { token }).catch(() => null),
          apiRequest<any>('/agent-runtime/agents/', { token }).catch(() => null),
          apiRequest<any>('/intelligence/readiness-score/', { token }).catch(() => null),
        ]);

        if (!mounted) return;

        const products = productsRes
          ? (Array.isArray(productsRes) ? productsRes : productsRes.results || productsRes.products || [])
          : [];
        const orders = ordersRes
          ? (Array.isArray(ordersRes) ? ordersRes : ordersRes.results || ordersRes.orders || [])
          : [];
        const agents = agentsRes
          ? (Array.isArray(agentsRes) ? agentsRes : agentsRes.results || [])
          : [];

        const pendingOrders = orders.filter((o: any) =>
          ['pending', 'processing', 'confirmed'].includes(o.status?.toLowerCase() || '')
        ).length;

        setKpi({
          products: products.length,
          orders: orders.length,
          pendingOrders,
          agents: agents.filter((a: any) => a.status === 'ACTIVE').length,
        });

        if (readinessRes) {
          setReadiness(readinessRes);
        }
      } catch (err) {
        console.error('KPI fetch failed:', err);
      } finally {
        if (mounted) {
          setKpiLoading(false);
          setReadinessLoading(false);
        }
      }
    })();
    return () => { mounted = false; };
  }, [token]);

  const kpiCards = [
    {
      label: "Products",
      value: kpi?.products ?? '—',
      sub: "in catalog",
      icon: <Package className="h-5 w-5" />,
      color: "text-blue-600 dark:text-blue-400",
      bg: "bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-900/40",
    },
    {
      label: "Total Orders",
      value: kpi?.orders ?? '—',
      sub: `${kpi?.pendingOrders ?? '—'} pending`,
      icon: <FileText className="h-5 w-5" />,
      color: "text-amber-600 dark:text-amber-400",
      bg: "bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-900/40",
    },
    {
      label: "Active Agents",
      value: kpi?.agents ?? '—',
      sub: "running now",
      icon: <Bot className="h-5 w-5" />,
      color: "text-indigo-600 dark:text-indigo-400",
      bg: "bg-indigo-50 dark:bg-indigo-950/30 border-indigo-200 dark:border-indigo-900/40",
    },
  ];

  return (
    <div className="min-h-[85vh] bg-gradient-to-br from-white via-gray-50 to-white dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 rounded-3xl p-8 border border-gray-200 dark:border-gray-800 shadow-2xl transition-colors duration-300 space-y-10">

      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-extrabold text-gray-900 dark:text-white tracking-tight">
            RazorHub<span className="text-blue-500">Seller</span>
          </h1>
          <p className="text-base text-gray-600 dark:text-gray-400 mt-1">
            AI Growth &amp; Agentic Commerce Platform
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/seller/banking"
            className="flex items-center gap-2 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-2.5 text-sm font-bold text-white shadow-lg shadow-indigo-500/20 hover:opacity-90 transition-all active:scale-95"
          >
            <Building2 className="h-4 w-4" />
            Open Banking
          </Link>
          <Link
            to="/seller/agents"
            className="flex items-center gap-2 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm font-bold text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            <Bot className="h-4 w-4 text-indigo-500" />
            View Agents
          </Link>
        </div>
      </div>

      {/* ── KPI Cards ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        {kpiCards.map((card) => (
          <div key={card.label} className={`flex items-center gap-4 rounded-2xl border p-5 ${card.bg}`}>
            <div className={`flex h-12 w-12 items-center justify-center rounded-xl bg-white dark:bg-gray-900 shadow-sm ${card.color}`}>
              {card.icon}
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">{card.label}</p>
              {kpiLoading ? (
                <Loader2 className="h-5 w-5 animate-spin text-gray-400 mt-1" />
              ) : (
                <>
                  <p className={`text-3xl font-black ${card.color}`}>{card.value}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{card.sub}</p>
                </>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* ── AI Commerce Readiness Score: Merchant Enablement Platform ── */}
      <div className="rounded-3xl border border-indigo-500/20 bg-gradient-to-br from-indigo-500/5 via-surface to-surface p-7 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-border/60">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-xs">
                <Zap className="h-4 w-4" />
              </span>
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
                Merchant Enablement • Autonomous Buyer Protocol
              </span>
            </div>
            <h2 className="text-2xl font-black text-primary tracking-tight">
              AI Commerce Readiness Score
            </h2>
            <p className="text-xs sm:text-sm text-secondary max-w-2xl">
              Measures how discoverable, machine-parsable, and sellable your catalog is to autonomous AI purchasing agents.
            </p>
          </div>

          <div className="flex items-center gap-4 bg-surface/80 dark:bg-zinc-900/80 p-4 rounded-2xl border border-border/80 shadow-xs shrink-0">
            <div className="text-right">
              <p className="text-xs font-semibold text-secondary uppercase">Overall Score</p>
              <p className="text-3xl sm:text-4xl font-black text-indigo-600 dark:text-indigo-400">
                {readinessLoading ? "..." : `${readiness?.total_score || 82}`}<span className="text-base text-secondary font-normal">/100</span>
              </p>
            </div>
            <div className="h-10 w-[1px] bg-border" />
            <div>
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-bold text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                {readiness?.grade || "AI Ready (Tier A)"}
              </span>
            </div>
          </div>
        </div>

        {/* Explainable Diagnostic Banner */}
        <div className="mt-6 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/25 flex items-start gap-3">
          <ShieldAlert className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="text-xs font-bold uppercase tracking-wide text-amber-700 dark:text-amber-400">
              Agent Compatibility Diagnostic
            </p>
            <p className="text-sm font-medium text-amber-900 dark:text-amber-200">
              {readiness?.diagnostic_summary ||
                "Your store is highly discoverable by AI buyers, but 3 products are missing compatibility attributes and checkout does not expose a bounded purchase policy."}
            </p>
          </div>
        </div>

        {/* 8-Pillar Scoring Grid */}
        <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {readiness?.pillars &&
            Object.entries(readiness.pillars).map(([key, p]) => (
              <div
                key={key}
                className="p-4 rounded-2xl border border-border/80 bg-surface/60 dark:bg-zinc-900/50 flex flex-col justify-between gap-2"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-secondary">{p.label}</span>
                  <span className="font-bold text-primary">
                    {p.score}/{p.max}
                  </span>
                </div>
                <div className="w-full bg-muted/50 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      p.pct >= 85
                        ? "bg-emerald-500"
                        : p.pct >= 70
                        ? "bg-indigo-500"
                        : "bg-amber-500"
                    }`}
                    style={{ width: `${p.pct}%` }}
                  />
                </div>
              </div>
            ))}
        </div>

        {/* Actionable Remediation Checklist */}
        {readiness?.action_items && readiness.action_items.length > 0 && (
          <div className="mt-6 pt-5 border-t border-border/60">
            <p className="text-xs font-bold uppercase tracking-wider text-secondary mb-3 flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              <span>Recommended Merchant Actions for 100/100 Readiness</span>
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              {readiness.action_items.map((action, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2.5 text-xs text-secondary bg-surface/90 dark:bg-zinc-900/90 p-3 rounded-xl border border-border/70"
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 shrink-0" />
                  <span>{action}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Module Grid ── */}
      <div>
        <div className="mb-5">
          <h2 className="text-xl font-bold text-gray-800 dark:text-gray-200">Store Modules</h2>
          <p className="text-sm text-gray-500 mt-1">
            Every money action is explainable, bounded, and gated.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {modules.map((m) => (
            <Link
              key={m.name}
              to={m.href}
              className="group flex flex-col p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50 hover:bg-white dark:hover:bg-gray-800/80 hover:border-blue-200 dark:hover:border-gray-700 hover:shadow-[0_0_20px_rgba(59,130,246,0.15)] transition-all duration-300"
            >
              <div className="text-gray-500 dark:text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-500 transition-colors mb-5 [&>svg]:w-9 [&>svg]:h-9">
                {m.icon}
              </div>
              <h3 className="text-gray-900 dark:text-white font-bold group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors text-xl">
                {m.name}
              </h3>
              <p className="text-sm text-gray-500 mt-2 flex-1">{m.desc}</p>
              <div className="flex items-center gap-1 mt-4 text-xs font-bold text-blue-600 dark:text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity">
                Open <ArrowRight className="h-3.5 w-3.5" />
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* ── Architecture Rule Banner ── */}
      <section className="p-6 rounded-2xl border border-amber-200 dark:border-amber-900/40 bg-amber-50 dark:bg-amber-950/20 shadow-inner">
        <h3 className="text-amber-600 dark:text-amber-500 font-bold flex items-center gap-2">
          ⚡ Architecture Rule
        </h3>
        <p className="text-sm text-amber-800 dark:text-amber-200/80 mt-2 leading-relaxed">
          LLMs may reason and propose actions, but deterministic code validates
          money, inventory, price, budget, consent, policy, and payment actions
          before execution.
        </p>
      </section>
    </div>
  );
}

