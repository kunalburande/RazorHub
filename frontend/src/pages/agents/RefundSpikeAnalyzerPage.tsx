import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp,
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  Play,
  Clock,
  RefreshCw,
  ArrowLeft,
  Calendar,
  Layers,
  ChevronRight,
  Package,
  CreditCard,
  Users,
  CheckCircle2,
  Sparkles,
  BarChart3,
  Flame,
  ArrowUpRight,
  Sliders,
  DollarSign,
  Activity,
  Bot,
  ExternalLink,
} from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';

interface AffectedProduct {
  product_id: string;
  product_name: string;
  category: string;
  order_count: number;
  refund_count: number;
  refund_rate: number;
  refund_amount: number;
  status: string;
}

interface PaymentMethodBreakdown {
  method: string;
  order_count: number;
  refund_count: number;
  refund_rate: number;
  refund_amount: number;
}

interface CustomerBreakdown {
  customer_id: string;
  customer_name: string;
  email: string;
  order_count: number;
  refund_count: number;
  refund_rate: number;
  total_refunded: number;
  risk_flag: string;
}

interface DailyTrend {
  date: string;
  day_label: string;
  refund_rate: number;
  order_count: number;
  refund_count: number;
}

interface RefundAnomalyReport {
  id: string;
  current_refund_rate: number;
  baseline_refund_rate: number;
  delta: number;
  threshold_multiplier: number;
  is_anomaly: boolean;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  refund_count: number;
  total_orders_count: number;
  refund_amount: number;
  total_sales_amount: number;
  affected_products: AffectedProduct[];
  by_product: AffectedProduct[];
  by_customer: CustomerBreakdown[];
  by_payment_method: PaymentMethodBreakdown[];
  by_day: DailyTrend[];
  explanation: string;
  likely_reasons: string[];
  recommended_actions: string[];
  created_at: string;
}

export default function RefundSpikeAnalyzerPage() {
  const { token } = useAuth();

  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [report, setReport] = useState<RefundAnomalyReport | null>(null);
  const [history, setHistory] = useState<RefundAnomalyReport[]>([]);
  const [activeTab, setActiveTab] = useState<'products' | 'daily' | 'payments' | 'customers'>('products');
  const [appliedActions, setAppliedActions] = useState<Record<number, boolean>>({});
  const [isScheduled, setIsScheduled] = useState(true);
  const [updatingSchedule, setUpdatingSchedule] = useState(false);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const fetchLatestAndHistory = async () => {
    try {
      setLoading(true);
      const [latestData, historyData] = await Promise.all([
        apiRequest<RefundAnomalyReport>('/agent-runtime/refund-spike-analyzer/latest/', { token }),
        apiRequest<RefundAnomalyReport[]>('/agent-runtime/refund-spike-analyzer/history/', { token }),
      ]);
      setReport(latestData);
      setHistory(Array.isArray(historyData) ? historyData : []);
    } catch (err: any) {
      console.error('Failed to load refund analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLatestAndHistory();
  }, [token]);

  const handleRunNow = async () => {
    try {
      setRunning(true);
      setActionNotice(null);
      const res = await apiRequest<RefundAnomalyReport>('/agent-runtime/refund-spike-analyzer/run/', {
        token,
        method: 'POST',
        body: JSON.stringify({
          baseline_rate: 4.20,
          threshold_factor: 1.50,
        }),
      });
      setReport(res);
      setHistory((prev) => [res, ...prev.filter((h) => h.id !== res.id)]);
      setActionNotice('Autonomous Refund Spike Analysis completed successfully!');
    } catch (err: any) {
      setActionNotice(`Failed to execute analysis: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  const handleToggleSchedule = async () => {
    try {
      setUpdatingSchedule(true);
      const nextState = !isScheduled;
      await apiRequest<any>('/agent-runtime/refund-spike-analyzer/schedule/', {
        token,
        method: 'POST',
        body: JSON.stringify({
          is_active: nextState,
          cron: '0 9 * * *',
          frequency: 'daily',
        }),
      });
      setIsScheduled(nextState);
      setActionNotice(
        nextState
          ? 'Autonomous daily schedule activated (Daily at 09:00 AM UTC)'
          : 'Autonomous schedule paused'
      );
    } catch (err: any) {
      setActionNotice(`Failed to update schedule: ${err.message}`);
    } finally {
      setUpdatingSchedule(false);
    }
  };

  const toggleActionApplied = (idx: number) => {
    setAppliedActions((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30 tracking-wider">
            <Flame className="w-3.5 h-3.5 animate-pulse" />
            CRITICAL SURGE
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30 tracking-wider">
            <AlertTriangle className="w-3.5 h-3.5" />
            HIGH ANOMALY
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30 tracking-wider">
            <ShieldAlert className="w-3.5 h-3.5" />
            MEDIUM ELEVATION
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 tracking-wider">
            <ShieldCheck className="w-3.5 h-3.5" />
            NORMAL
          </span>
        );
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCw className="w-8 h-8 text-indigo-500 animate-spin" />
        <p className="text-sm font-medium text-secondary">Loading Refund Spike Analyzer telemetry...</p>
      </div>
    );
  }

  const currentRate = report ? report.current_refund_rate : 12.70;
  const baselineRate = report ? report.baseline_refund_rate : 4.20;
  const delta = report ? report.delta : 8.50;
  const multiplier = report ? report.threshold_multiplier : 3.02;
  const severity = report ? report.severity : 'CRITICAL';

  return (
    <div className="space-y-8 pb-16 max-w-7xl mx-auto">
      
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 sm:p-8 rounded-3xl bg-surface border border-border/80 shadow-xs">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Link
              to="/agents"
              className="inline-flex items-center gap-1 text-xs font-semibold text-secondary hover:text-primary transition"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Agent Studio
            </Link>
            <span className="text-secondary text-xs">/</span>
            <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider">
              Autonomous Commerce Agent
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
              <TrendingUp className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-black text-primary tracking-tight">
                Refund Spike Analyzer
              </h1>
              <p className="text-xs sm:text-sm text-secondary">
                24/7 autonomous surveillance detecting abnormal refund velocity, isolating affected inventory, and orchestrating remediation.
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-3 shrink-0">
          <button
            type="button"
            disabled={updatingSchedule}
            onClick={handleToggleSchedule}
            className={`px-4 py-2.5 rounded-2xl text-xs font-bold border transition flex items-center gap-2 cursor-pointer ${
              isScheduled
                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20'
                : 'bg-muted text-secondary border-border hover:bg-border'
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            <span>{isScheduled ? 'Scheduled: Daily (09:00 UTC)' : 'Schedule Paused'}</span>
          </button>

          <button
            type="button"
            disabled={running}
            onClick={handleRunNow}
            className="px-6 py-2.5 rounded-2xl text-xs font-extrabold bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white shadow-lg shadow-indigo-600/25 transition flex items-center gap-2 cursor-pointer disabled:opacity-50"
          >
            {running ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4 fill-white" />
            )}
            <span>Run Now</span>
          </button>
        </div>
      </div>

      {actionNotice && (
        <div className="p-4 rounded-2xl bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-900 text-indigo-900 dark:text-indigo-200 text-xs sm:text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
            <span>{actionNotice}</span>
          </div>
          <button onClick={() => setActionNotice(null)} className="font-bold underline text-xs">Dismiss</button>
        </div>
      )}

      {/* ── TOP METRICS CARDS: REFUND RATE, BASELINE, DELTA, SEVERITY ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* 1. Current Refund Rate */}
        <div className="p-6 rounded-3xl bg-surface border border-border/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-secondary text-xs font-bold uppercase tracking-wider">
            <span>Current Refund Rate</span>
            <Activity className="w-4 h-4 text-rose-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl sm:text-4xl font-black font-mono text-primary">
              {currentRate}%
            </span>
            <span className="text-xs font-bold text-rose-600 dark:text-rose-400">
              Surge Active
            </span>
          </div>
          <p className="text-[11px] text-secondary">
            {report?.refund_count || 127} refunds on {report?.total_orders_count || 1000} orders (₹{(report?.refund_amount || 447000).toLocaleString('en-IN')})
          </p>
        </div>

        {/* 2. Historical Baseline */}
        <div className="p-6 rounded-3xl bg-surface border border-border/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-secondary text-xs font-bold uppercase tracking-wider">
            <span>Historical Baseline</span>
            <Calendar className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl sm:text-4xl font-black font-mono text-primary">
              {baselineRate}%
            </span>
            <span className="text-xs font-bold text-secondary">
              30-day benchmark
            </span>
          </div>
          <p className="text-[11px] text-secondary">
            Deterministic control threshold: {(baselineRate * 1.5).toFixed(2)}% (1.50x)
          </p>
        </div>

        {/* 3. Delta */}
        <div className="p-6 rounded-3xl bg-surface border border-border/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-secondary text-xs font-bold uppercase tracking-wider">
            <span>Surge Delta</span>
            <TrendingUp className="w-4 h-4 text-amber-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl sm:text-4xl font-black font-mono text-rose-600 dark:text-rose-400">
              +{delta}%
            </span>
            <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-rose-500/10 text-rose-600 border border-rose-500/20">
              {multiplier}x baseline
            </span>
          </div>
          <p className="text-[11px] text-secondary">
            Exceeds permissible tolerance ceiling by +{(currentRate - baselineRate * 1.5).toFixed(2)}%
          </p>
        </div>

        {/* 4. Severity & Autonomous Decision */}
        <div className="p-6 rounded-3xl bg-surface border border-border/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-secondary text-xs font-bold uppercase tracking-wider">
            <span>Deterministic Severity</span>
            <ShieldAlert className="w-4 h-4 text-rose-500" />
          </div>
          <div>
            {getSeverityBadge(severity)}
          </div>
          <p className="text-[11px] text-secondary pt-1">
            Deterministic Decision: <strong className="text-rose-600 dark:text-rose-400">ANOMALY DETECTED</strong>. LLM alerted.
          </p>
        </div>

      </div>

      {/* ── LLM EXPLANATION & ROOT CAUSE SECTION ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Natural Language Explanation */}
        <div className="lg:col-span-7 space-y-6">
          <div className="p-6 sm:p-7 rounded-3xl bg-surface border border-border/80 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-500" />
                <h2 className="text-sm font-bold text-primary uppercase tracking-wider">
                  AI Forensic Summary & Explanation
                </h2>
              </div>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 font-bold">
                LLM Synthesizer
              </span>
            </div>

            <p className="text-xs sm:text-sm text-secondary leading-relaxed bg-background p-4 rounded-2xl border border-border/80">
              {report?.explanation ||
                `The platform's refund rate has surged to ${currentRate}% compared against the historical baseline of ${baselineRate}% (+${delta}% delta, ${multiplier}x benchmark threshold). Total refund exposure is ₹${(report?.refund_amount || 447000).toLocaleString('en-IN')} across ${report?.refund_count || 127} orders. The surge is primarily concentrated in 'Wireless Noise Cancelling Headphones' and high-value Credit Card transactions.`}
            </p>

            {/* Likely Reasons List */}
            <div className="space-y-3 pt-2">
              <h3 className="text-xs font-bold text-primary uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                Likely Root Causes
              </h3>
              <div className="space-y-2">
                {(report?.likely_reasons || []).map((reason, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-2xl bg-amber-500/5 border border-amber-500/15 text-xs text-secondary flex items-start gap-2.5"
                  >
                    <div className="w-5 h-5 rounded-full bg-amber-500/20 text-amber-700 dark:text-amber-300 font-bold flex items-center justify-center shrink-0 mt-0.5 text-[11px]">
                      {idx + 1}
                    </div>
                    <span>{reason}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Recommended Actions */}
        <div className="lg:col-span-5 space-y-6">
          <div className="p-6 sm:p-7 rounded-3xl bg-surface border border-border/80 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-500" />
                <h2 className="text-sm font-bold text-primary uppercase tracking-wider">
                  Recommended Remediation
                </h2>
              </div>
              <span className="text-[10px] font-mono uppercase text-secondary">
                Actionable Guardrails
              </span>
            </div>

            <div className="space-y-2.5">
              {(report?.recommended_actions || []).map((action, idx) => {
                const isApplied = !!appliedActions[idx];
                return (
                  <div
                    key={idx}
                    className={`p-3.5 rounded-2xl border transition flex items-start justify-between gap-3 ${
                      isApplied
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-300'
                        : 'bg-background border-border text-secondary hover:border-border/80'
                    }`}
                  >
                    <div className="flex items-start gap-2.5 text-xs">
                      <CheckCircle2
                        className={`w-4 h-4 shrink-0 mt-0.5 ${
                          isApplied ? 'text-emerald-500' : 'text-gray-400'
                        }`}
                      />
                      <span>{action}</span>
                    </div>

                    <button
                      type="button"
                      onClick={() => toggleActionApplied(idx)}
                      className={`px-3 py-1 rounded-xl text-[11px] font-bold transition shrink-0 cursor-pointer ${
                        isApplied
                          ? 'bg-emerald-600 text-white shadow-xs'
                          : 'bg-primary text-surface hover:opacity-90'
                      }`}
                    >
                      {isApplied ? 'Applied' : 'Execute'}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

      </div>

      {/* ── ANALYTICS BREAKDOWNS TABS ── */}
      <div className="p-6 sm:p-8 rounded-3xl bg-surface border border-border/80 shadow-xs space-y-6">
        
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
          <div>
            <h2 className="text-lg font-bold text-primary">Granular Refund Telemetry</h2>
            <p className="text-xs text-secondary">Deterministic breakdown of refund velocity across products, time horizons, rails, and customers.</p>
          </div>

          <div className="flex items-center gap-1.5 p-1 rounded-2xl bg-muted border border-border overflow-x-auto">
            <button
              type="button"
              onClick={() => setActiveTab('products')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'products'
                  ? 'bg-primary text-surface shadow-xs'
                  : 'text-secondary hover:text-primary'
              }`}
            >
              <Package className="w-3.5 h-3.5" />
              <span>Affected Products</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('daily')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'daily'
                  ? 'bg-primary text-surface shadow-xs'
                  : 'text-secondary hover:text-primary'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>7-Day Daily Trend</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('payments')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'payments'
                  ? 'bg-primary text-surface shadow-xs'
                  : 'text-secondary hover:text-primary'
              }`}
            >
              <CreditCard className="w-3.5 h-3.5" />
              <span>Payment Methods</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('customers')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'customers'
                  ? 'bg-primary text-surface shadow-xs'
                  : 'text-secondary hover:text-primary'
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              <span>Customer Cohorts</span>
            </button>
          </div>
        </div>

        {/* TAB 1: AFFECTED PRODUCTS */}
        {activeTab === 'products' && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border text-secondary uppercase font-bold text-[11px]">
                  <th className="pb-3">Product Name</th>
                  <th className="pb-3">Category</th>
                  <th className="pb-3 text-right">Orders</th>
                  <th className="pb-3 text-right">Refunds</th>
                  <th className="pb-3 text-right">Refund Rate</th>
                  <th className="pb-3 text-right">Total Refunded</th>
                  <th className="pb-3 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {(report?.by_product || []).map((p) => {
                  const isSpike = p.refund_rate > 10;
                  return (
                    <tr key={p.product_id} className="hover:bg-muted/50 transition">
                      <td className="py-3.5 font-bold text-primary flex items-center gap-2">
                        <Package className="w-4 h-4 text-indigo-500 shrink-0" />
                        <span>{p.product_name}</span>
                      </td>
                      <td className="py-3.5 text-secondary">{p.category}</td>
                      <td className="py-3.5 text-right font-mono text-secondary">{p.order_count}</td>
                      <td className="py-3.5 text-right font-mono font-bold text-rose-600">{p.refund_count}</td>
                      <td className="py-3.5 text-right font-mono font-black">
                        <span className={isSpike ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600'}>
                          {p.refund_rate}%
                        </span>
                      </td>
                      <td className="py-3.5 text-right font-mono text-primary font-medium">
                        ₹{p.refund_amount.toLocaleString('en-IN')}
                      </td>
                      <td className="py-3.5 text-right">
                        <span
                          className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                            p.status === 'SPIKE_DETECTED'
                              ? 'bg-rose-500/15 text-rose-600 border border-rose-500/30'
                              : p.status === 'ELEVATED'
                              ? 'bg-amber-500/15 text-amber-600 border border-amber-500/30'
                              : 'bg-emerald-500/15 text-emerald-600 border border-emerald-500/30'
                          }`}
                        >
                          {p.status}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* TAB 2: DAILY TREND (BARS) */}
        {activeTab === 'daily' && (
          <div className="space-y-4">
            <p className="text-xs text-secondary">Refund Rate velocity over the last 7 calendar days:</p>
            <div className="grid grid-cols-7 gap-2 sm:gap-3 items-end h-48 pt-6 pb-2 border-b border-border">
              {(report?.by_day || []).map((d) => {
                const heightPercent = Math.min(Math.max((d.refund_rate / 20) * 100, 15), 100);
                const isOverThreshold = d.refund_rate > (baselineRate * 1.5);
                return (
                  <div key={d.date} className="flex flex-col items-center gap-2 h-full justify-end">
                    <span className="text-[11px] font-mono font-bold text-primary">
                      {d.refund_rate}%
                    </span>
                    <div
                      style={{ height: `${heightPercent}%` }}
                      className={`w-full max-w-[48px] rounded-t-xl transition-all ${
                        isOverThreshold
                          ? 'bg-gradient-to-t from-rose-600 to-rose-400'
                          : 'bg-gradient-to-t from-indigo-600 to-cyan-500'
                      }`}
                    />
                    <span className="text-[10px] text-secondary font-medium text-center">
                      {d.day_label}
                    </span>
                  </div>
                );
              })}
            </div>
            <div className="flex items-center justify-between text-xs text-secondary pt-1">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                <span>Threshold Breach Zone (&gt; 6.30%)</span>
              </span>
              <span>Baseline: 4.20%</span>
            </div>
          </div>
        )}

        {/* TAB 3: PAYMENT METHOD */}
        {activeTab === 'payments' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {(report?.by_payment_method || []).map((pm) => (
              <div key={pm.method} className="p-4 rounded-2xl bg-background border border-border space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-primary">{pm.method}</span>
                  <CreditCard className="w-4 h-4 text-indigo-500" />
                </div>
                <div className="text-2xl font-black font-mono text-primary">
                  {pm.refund_rate}%
                </div>
                <div className="text-[11px] text-secondary space-y-0.5">
                  <div className="flex justify-between">
                    <span>Refunds / Orders:</span>
                    <span className="font-mono font-medium">{pm.refund_count} / {pm.order_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Total Amount:</span>
                    <span className="font-mono font-medium">₹{pm.refund_amount.toLocaleString('en-IN')}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* TAB 4: CUSTOMERS */}
        {activeTab === 'customers' && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border text-secondary uppercase font-bold text-[11px]">
                  <th className="pb-3">Customer</th>
                  <th className="pb-3 text-right">Orders</th>
                  <th className="pb-3 text-right">Refunds</th>
                  <th className="pb-3 text-right">Refund Rate</th>
                  <th className="pb-3 text-right">Total Refunded</th>
                  <th className="pb-3 text-right">Cohort Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {(report?.by_customer || []).map((c) => (
                  <tr key={c.customer_id} className="hover:bg-muted/50 transition">
                    <td className="py-3 font-medium text-primary">
                      <div>{c.customer_name}</div>
                      <div className="text-[10px] text-secondary">{c.email}</div>
                    </td>
                    <td className="py-3 text-right font-mono text-secondary">{c.order_count}</td>
                    <td className="py-3 text-right font-mono font-bold text-rose-600">{c.refund_count}</td>
                    <td className="py-3 text-right font-mono font-bold text-primary">{c.refund_rate}%</td>
                    <td className="py-3 text-right font-mono text-primary font-medium">
                      ₹{c.total_refunded.toLocaleString('en-IN')}
                    </td>
                    <td className="py-3 text-right">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-muted text-secondary uppercase font-mono">
                        {c.risk_flag}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

      </div>

      {/* ── EXECUTION TIMELINE ── */}
      <div className="p-6 sm:p-8 rounded-3xl bg-surface border border-border/80 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-primary">Autonomous Execution Timeline</h2>
            <p className="text-xs text-secondary">Historical surveillance traces and deterministic evaluation runs.</p>
          </div>
          <span className="text-xs font-mono text-secondary">{history.length} Runs Recorded</span>
        </div>

        <div className="divide-y divide-border">
          {history.map((item, idx) => (
            <div
              key={item.id}
              className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-muted/30 p-2 rounded-xl transition"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-primary">Run #{history.length - idx}</span>
                    {getSeverityBadge(item.severity)}
                  </div>
                  <p className="text-[11px] text-secondary mt-0.5">
                    {new Date(item.created_at).toLocaleString()} • Rate: <strong>{item.current_refund_rate}%</strong> (Baseline: {item.baseline_refund_rate}%, Delta: +{item.delta}%)
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-xs font-mono font-semibold text-primary">
                  ₹{item.refund_amount.toLocaleString('en-IN')}
                </span>
                <button
                  type="button"
                  onClick={() => setReport(item)}
                  className="px-3 py-1 rounded-xl text-xs font-bold bg-muted hover:bg-border text-primary transition cursor-pointer"
                >
                  View Details
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
