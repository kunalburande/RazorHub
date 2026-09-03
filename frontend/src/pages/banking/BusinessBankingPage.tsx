import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Building2,
  TrendingUp,
  ArrowUpRight,
  ArrowDownLeft,
  DollarSign,
  ShieldCheck,
  Bot,
  FileText,
  Calendar,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Send,
  RefreshCw,
  Zap,
  Sliders,
  Sparkles,
  ChevronRight,
  ExternalLink,
  Layers,
  PieChart,
  UserCheck,
  CreditCard,
  Receipt,
  Search,
  Lock,
  MessageSquare,
  Check,
  X,
  Plus,
} from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';

// Navigation Tab Definition
type BankingTab =
  | 'overview'
  | 'finance-team'
  | 'receivables'
  | 'payouts'
  | 'cashflow'
  | 'reconciliation'
  | 'reports'
  | 'agent-studio'
  | 'approvals'
  | 'audit';

export default function BusinessBankingPage({ embedded = false }: { embedded?: boolean }) {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const activeTab = (searchParams.get('tab') as BankingTab) || 'overview';
  const setTab = (tab: BankingTab) => {
    setSearchParams({ tab });
  };

  // State for metrics & data
  const [metrics, setMetrics] = useState<any>(null);
  const [receivables, setReceivables] = useState<any[]>([]);
  const [bookkeeping, setBookkeeping] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [reconciliation, setReconciliation] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Payout Agent Chat State
  const [payoutPrompt, setPayoutPrompt] = useState('Pay Rahul ₹18,500 for invoice INV-204');
  const [payoutMessages, setPayoutMessages] = useState<any[]>([
    {
      role: 'agent',
      text: 'Hello! I am your autonomous Payout Agent. Tell me which vendor or contractor you would like to pay (e.g. "Pay Rahul ₹18,500 for invoice INV-204"). I will verify the invoice, evaluate risk, check governance policies, and prepare the disbursement.',
    },
  ]);
  const [payoutLoading, setPayoutLoading] = useState(false);
  const [activeApprovalCard, setActiveApprovalCard] = useState<any>(null);
  const [actionSuccessNotice, setActionSuccessNotice] = useState<string | null>(null);

  // Follow-up modal state
  const [followupModal, setFollowupModal] = useState<any>(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  // Fetch initial banking data
  const fetchBankingData = async () => {
    try {
      setLoading(true);
      const [insightsRes, recRes, bookRes, repRes, reconRes] = await Promise.all([
        apiRequest<any>('/agent-runtime/banking/insights/', { token }).catch(() => null),
        apiRequest<any>('/agent-runtime/banking/receivables/', { token }).catch(() => []),
        apiRequest<any>('/agent-runtime/banking/bookkeeping/', { token }).catch(() => []),
        apiRequest<any>('/agent-runtime/banking/reports/', { token }).catch(() => []),
        apiRequest<any>('/agent-runtime/banking/reconciliation/', { token }).catch(() => null),
      ]);

      if (insightsRes) setMetrics(insightsRes);
      if (recRes) setReceivables(Array.isArray(recRes) ? recRes : []);
      if (bookRes) setBookkeeping(Array.isArray(bookRes) ? bookRes : []);
      if (repRes) setReports(Array.isArray(repRes) ? repRes : []);
      if (reconRes) setReconciliation(reconRes);
    } catch (err: any) {
      console.error('Failed to load banking data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBankingData();
  }, [token]);

  // Handle Payout Agent prompt submission
  const handlePayoutSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!payoutPrompt.trim() || payoutLoading) return;

    const userText = payoutPrompt.trim();
    setPayoutMessages((prev) => [...prev, { role: 'user', text: userText }]);
    setPayoutPrompt('');
    setPayoutLoading(true);

    try {
      const res = await apiRequest<any>('/agent-runtime/banking/payouts/chat/', {
        token,
        method: 'POST',
        body: JSON.stringify({ prompt: userText }),
      });

      if (res.success) {
        setPayoutMessages((prev) => [...prev, { role: 'agent', text: res.message }]);
        if (res.approval_card) {
          setActiveApprovalCard(res.approval_card);
        }
      } else {
        setPayoutMessages((prev) => [
          ...prev,
          { role: 'agent', text: res.message || 'Could not resolve payout request. Please verify the invoice number.' },
        ]);
      }
    } catch (err: any) {
      setPayoutMessages((prev) => [
        ...prev,
        { role: 'agent', text: `Error processing payout request: ${err.message}` },
      ]);
    } finally {
      setPayoutLoading(false);
    }
  };

  // Handle Payout Approval
  const handleApprovePayout = async (invoiceId: string) => {
    try {
      setPayoutLoading(true);
      const res = await apiRequest<any>('/agent-runtime/banking/payouts/execute/', {
        token,
        method: 'POST',
        body: JSON.stringify({ invoice_id: invoiceId }),
      });

      if (res.success) {
        setActiveApprovalCard(null);
        setPayoutMessages((prev) => [
          ...prev,
          {
            role: 'agent',
            text: `✅ **Payout Successfully Disbursed!**\n\n• UTR Reference: \`${res.utr_reference}\`\n• Recipient: ${res.recipient}\n• Amount: ₹${res.amount?.toLocaleString('en-IN')}\n• Status: DISBURSED\n\nInvoice marked as PAID and Bookkeeping debit entry recorded in the general ledger.`,
          },
        ]);
        setActionSuccessNotice(`Payout of ₹${res.amount?.toLocaleString('en-IN')} disbursed to ${res.recipient}.`);
        fetchBankingData();
      }
    } catch (err: any) {
      alert(`Payout disbursement failed: ${err.message}`);
    } finally {
      setPayoutLoading(false);
    }
  };

  // Handle Receivables Follow-Up
  const handleTriggerFollowup = async (invoiceId: string, channel = 'EMAIL') => {
    try {
      const res = await apiRequest<any>('/agent-runtime/banking/receivables/', {
        token,
        method: 'POST',
        body: JSON.stringify({ action: 'followup', invoice_id: invoiceId, channel }),
      });
      if (res.success) {
        setFollowupModal(res);
        fetchBankingData();
      } else if (res.stopped) {
        alert(res.message);
      }
    } catch (err: any) {
      alert(`Followup failed: ${err.message}`);
    }
  };

  // Handle Mark Invoice Paid
  const handleMarkInvoicePaid = async (invoiceId: string) => {
    try {
      const res = await apiRequest<any>('/agent-runtime/banking/receivables/', {
        token,
        method: 'POST',
        body: JSON.stringify({ action: 'mark_paid', invoice_id: invoiceId }),
      });
      if (res.success) {
        setActionSuccessNotice(res.message);
        fetchBankingData();
      }
    } catch (err: any) {
      alert(`Failed to settle invoice: ${err.message}`);
    }
  };

  // Handle On-Demand Report Generation
  const handleGenerateReport = async (type: string) => {
    try {
      setGeneratingReport(true);
      const res = await apiRequest<any>('/agent-runtime/banking/reports/', {
        token,
        method: 'POST',
        body: JSON.stringify({ report_type: type }),
      });
      if (res) {
        setActionSuccessNotice(`Generated ${res.title}`);
        fetchBankingData();
      }
    } catch (err: any) {
      alert(`Failed to generate report: ${err.message}`);
    } finally {
      setGeneratingReport(false);
    }
  };

  return (
    <div className={embedded ? 'space-y-6' : 'max-w-7xl mx-auto px-4 py-6 sm:py-8 space-y-6'}>
      
      {/* ── HEADER BANNER ── */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 border border-indigo-500/20 p-6 sm:p-8 text-white shadow-xl">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              <Building2 className="w-3.5 h-3.5 text-indigo-400" />
              <span>AGENTIC BUSINESS BANKING & TREASURY</span>
            </div>
            <h1 className="text-2xl sm:text-4xl font-black tracking-tight text-white">
              Autonomous Corporate Finance Suite
            </h1>
            <p className="text-xs sm:text-sm text-indigo-200/80 leading-relaxed">
              AI-driven corporate treasury, automated debtor collections, governed vendor disbursements, double-entry bookkeeping, and real-time cash runway intelligence.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => setTab('payouts')}
              className="px-4 py-2.5 rounded-2xl text-xs font-bold bg-gradient-to-r from-indigo-500 to-purple-600 hover:opacity-95 text-white shadow-lg shadow-indigo-500/25 transition cursor-pointer flex items-center gap-2"
            >
              <DollarSign className="w-4 h-4" />
              <span>Disburse Payout</span>
            </button>
            <button
              onClick={() => setTab('receivables')}
              className="px-4 py-2.5 rounded-2xl text-xs font-bold bg-white/10 hover:bg-white/15 border border-white/20 text-white backdrop-blur-md transition cursor-pointer flex items-center gap-2"
            >
              <Clock className="w-4 h-4" />
              <span>Collect Receivables</span>
            </button>
          </div>
        </div>
      </div>

      {actionSuccessNotice && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-800 dark:text-emerald-200 text-xs sm:text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
            <span>{actionSuccessNotice}</span>
          </div>
          <button onClick={() => setActionSuccessNotice(null)} className="font-bold underline text-xs cursor-pointer">
            Dismiss
          </button>
        </div>
      )}

      {/* ── 10-ITEM NAVIGATION BAR ── */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 border-b border-border text-xs font-bold scrollbar-none">
        {[
          { id: 'overview', label: 'Overview', icon: Building2 },
          { id: 'finance-team', label: 'AI Finance Team', icon: Bot },
          { id: 'receivables', label: 'Receivables', icon: Clock },
          { id: 'payouts', label: 'Payouts', icon: DollarSign },
          { id: 'cashflow', label: 'Cashflow', icon: TrendingUp },
          { id: 'reconciliation', label: 'Reconciliation', icon: ShieldCheck },
          { id: 'reports', label: 'Reports', icon: FileText },
          { id: 'agent-studio', label: 'Agent Studio', icon: Zap },
          { id: 'approvals', label: 'Approvals', icon: UserCheck },
          { id: 'audit', label: 'Audit', icon: Receipt },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setTab(tab.id as BankingTab)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-2xl whitespace-nowrap transition cursor-pointer ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                  : 'text-secondary hover:text-primary hover:bg-muted'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* ── TAB 1: OVERVIEW ── */}
      {activeTab === 'overview' && (
        <div className="space-y-6 animate-in fade-in duration-200">
          {/* KPI Metrics Ribbon */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-3xl bg-surface border border-border shadow-xs space-y-2">
              <div className="flex items-center justify-between text-secondary text-xs font-semibold">
                <span>Total Cash Balance</span>
                <span className="p-1.5 rounded-xl bg-emerald-500/10 text-emerald-500"><Building2 className="w-4 h-4" /></span>
              </div>
              <p className="text-2xl sm:text-3xl font-black text-primary font-mono">
                ₹{metrics ? (Number(metrics.cash_balance) || 0).toLocaleString('en-IN') : '0'}
              </p>
              <p className="text-[11px] text-emerald-600 font-semibold flex items-center gap-1">
                <ArrowUpRight className="w-3 h-3" />
                <span>+₹{metrics ? (Number(metrics.todays_revenue) || 0).toLocaleString('en-IN') : '0'} today</span>
              </p>
            </div>

            <div className="p-5 rounded-3xl bg-surface border border-border shadow-xs space-y-2">
              <div className="flex items-center justify-between text-secondary text-xs font-semibold">
                <span>Cash Runway</span>
                <span className="p-1.5 rounded-xl bg-indigo-500/10 text-indigo-500"><TrendingUp className="w-4 h-4" /></span>
              </div>
              <p className="text-2xl sm:text-3xl font-black text-indigo-600 font-mono">
                {metrics ? metrics.cash_runway_months : '0.0'} Months
              </p>
              <p className="text-[11px] text-secondary font-semibold">
                Burn: ₹{metrics && metrics.burn_rate ? (metrics.burn_rate / 100000).toFixed(2) : '0.00'}L / mo
              </p>
            </div>

            <div className="p-5 rounded-3xl bg-surface border border-border shadow-xs space-y-2">
              <div className="flex items-center justify-between text-secondary text-xs font-semibold">
                <span>Outstanding Receivables</span>
                <span className="p-1.5 rounded-xl bg-amber-500/10 text-amber-500"><Clock className="w-4 h-4" /></span>
              </div>
              <p className="text-2xl sm:text-3xl font-black text-amber-600 font-mono">
                ₹{metrics ? (Number(metrics.outstanding_receivables) || 0).toLocaleString('en-IN') : '0'}
              </p>
              <p className="text-[11px] text-secondary">
                {metrics?.outstanding_receivables > 0 ? 'Receivables Agent active on pending invoices' : 'All invoices settled & clear'}
              </p>
            </div>

            <div className="p-5 rounded-3xl bg-surface border border-border shadow-xs space-y-2">
              <div className="flex items-center justify-between text-secondary text-xs font-semibold">
                <span>Upcoming Payouts (7D)</span>
                <span className="p-1.5 rounded-xl bg-purple-500/10 text-purple-500"><DollarSign className="w-4 h-4" /></span>
              </div>
              <p className="text-2xl sm:text-3xl font-black text-purple-600 font-mono">
                ₹{metrics ? (Number(metrics.upcoming_payouts) || 0).toLocaleString('en-IN') : '0'}
              </p>
              <p className="text-[11px] text-secondary">
                Governed via Zero-Trust Transaction Firewall
              </p>
            </div>
          </div>

          {/* Secondary Metrics Row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs bg-surface p-5 rounded-3xl border border-border">
            <div className="flex items-center justify-between p-3 rounded-2xl bg-background border border-border">
              <span className="text-secondary font-semibold">Payment Success Rate:</span>
              <span className="font-bold text-emerald-600 font-mono">{metrics?.payment_success_rate ?? 100}%</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-2xl bg-background border border-border">
              <span className="text-secondary font-semibold">Refund Rate (Gateway):</span>
              <span className="font-bold text-primary font-mono">{metrics?.refund_rate ?? 0.0}%</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-2xl bg-background border border-border">
              <span className="text-secondary font-semibold">Bank Reconciliation:</span>
              <span className="font-bold text-indigo-600 font-mono">100% Reconciled</span>
            </div>
          </div>

          {/* Quick Flow Visualizer & Actions */}
          <div className="p-6 rounded-3xl bg-surface border border-border space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-primary">14-Day Projected Cash Balance Trajectory</h3>
                <p className="text-xs text-secondary">Calculated by autonomous Insights Agent with scheduled receivables & payouts.</p>
              </div>
              <span className="text-xs font-mono font-bold text-emerald-600">
                {metrics?.cash_balance > 0 ? `Net Surplus: +₹${((metrics.cash_balance)/100000).toFixed(2)}L` : 'Awaiting First Transaction'}
              </span>
            </div>

            {(!metrics?.cashflow_forecast || metrics.cashflow_forecast.length === 0 || metrics.cash_balance === 0) ? (
              <div className="p-8 rounded-2xl bg-background border border-dashed border-border text-center space-y-2">
                <Building2 className="w-8 h-8 text-secondary/40 mx-auto" />
                <p className="text-xs font-bold text-primary">No Financial Cashflows Yet</p>
                <p className="text-[11px] text-secondary max-w-sm mx-auto">
                  When customer purchases or vendor invoices are processed, the autonomous Insights Agent will project live 14-day liquidity trajectories.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-7 sm:grid-cols-14 gap-2 pt-2">
                {(metrics?.cashflow_forecast || []).map((f: any, idx: number) => (
                  <div key={idx} className="p-2 rounded-xl bg-background border border-border text-center space-y-1">
                    <span className="text-[9px] text-secondary font-semibold block">{f.day}</span>
                    <div className="w-full h-12 rounded bg-muted flex items-end justify-center overflow-hidden">
                      <div
                        style={{ height: `${Math.min(100, Math.max(30, (f.projected_balance / 3500000) * 100))}%` }}
                        className="w-full bg-indigo-600 rounded-t"
                      />
                    </div>
                    <span className="text-[9px] font-mono font-bold text-primary block">
                      ₹{(f.projected_balance / 100000).toFixed(1)}L
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── TAB 2: AI FINANCE TEAM ── */}
      {activeTab === 'finance-team' && (
        <div className="space-y-6 animate-in fade-in duration-200">
          <div>
            <h2 className="text-lg font-bold text-primary">Your Autonomous AI Finance Team</h2>
            <p className="text-xs text-secondary">
              Five prebuilt autonomous agents managing your corporate treasury, credit control, disbursements, general ledger, and executive reporting.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            
            {/* 1. Insights Agent */}
            <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs hover:border-indigo-500/40 transition space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 text-indigo-600 flex items-center justify-center font-bold">
                    <TrendingUp className="w-5 h-5" />
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600">
                    ACTIVE
                  </span>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-primary">1. Insights Agent</h3>
                  <p className="text-xs text-secondary mt-1">
                    Continuously monitors treasury cash balances, calculates burn rate, predicts runway, and forecasts 30-day liquidity.
                  </p>
                </div>
                <div className="text-[11px] space-y-1 bg-background p-3 rounded-xl border border-border text-secondary">
                  <div>• Cash Balance: <strong className="text-primary font-mono">₹28,45,000</strong></div>
                  <div>• Runway: <strong className="text-primary font-mono">6.8 Months</strong></div>
                  <div>• Forecast: <strong className="text-emerald-600 font-mono">+₹4.72L surplus</strong></div>
                </div>
              </div>
              <button
                onClick={() => setTab('cashflow')}
                className="w-full py-2 rounded-xl text-xs font-bold bg-muted hover:bg-border text-primary transition cursor-pointer"
              >
                View Cashflow Forecast
              </button>
            </div>

            {/* 2. Receivables Agent */}
            <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs hover:border-indigo-500/40 transition space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-2xl bg-amber-500/10 text-amber-600 flex items-center justify-center font-bold">
                    <Clock className="w-5 h-5" />
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600">
                    ACTIVE
                  </span>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-primary">2. Receivables Agent</h3>
                  <p className="text-xs text-secondary mt-1">
                    Detects overdue debtor invoices, prioritizes collections, sends automated reminders, and halts follow-ups when paid.
                  </p>
                </div>
                <div className="text-[11px] space-y-1 bg-background p-3 rounded-xl border border-border text-secondary">
                  <div>• Overdue Invoices: <strong className="text-rose-500 font-mono">2 accounts</strong></div>
                  <div>• Outstanding: <strong className="text-primary font-mono">₹2,85,000</strong></div>
                  <div>• Channels: Email, WhatsApp, SMS</div>
                </div>
              </div>
              <button
                onClick={() => setTab('receivables')}
                className="w-full py-2 rounded-xl text-xs font-bold bg-indigo-600 text-white hover:bg-indigo-700 transition cursor-pointer"
              >
                Manage Receivables
              </button>
            </div>

            {/* 3. Payout Agent */}
            <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs hover:border-indigo-500/40 transition space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-2xl bg-purple-500/10 text-purple-600 flex items-center justify-center font-bold">
                    <DollarSign className="w-5 h-5" />
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600">
                    ACTIVE
                  </span>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-primary">3. Payout Agent</h3>
                  <p className="text-xs text-secondary mt-1">
                    Executes vendor payments via natural language ("Pay Rahul ₹18,500 for INV-204"), verified through Transaction Governance.
                  </p>
                </div>
                <div className="text-[11px] space-y-1 bg-background p-3 rounded-xl border border-border text-secondary">
                  <div>• Beneficiary Verification: <strong className="text-emerald-600 font-bold">Automated</strong></div>
                  <div>• Risk Evaluation: <strong className="text-primary font-mono">Zero-Trust</strong></div>
                  <div>• Human Approval: <strong className="text-amber-500 font-bold">Mandatory</strong></div>
                </div>
              </div>
              <button
                onClick={() => setTab('payouts')}
                className="w-full py-2 rounded-xl text-xs font-bold bg-purple-600 text-white hover:bg-purple-700 transition cursor-pointer"
              >
                Launch Payout Assistant
              </button>
            </div>

            {/* 4. Bookkeeping Agent */}
            <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs hover:border-indigo-500/40 transition space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-2xl bg-blue-500/10 text-blue-600 flex items-center justify-center font-bold">
                    <Receipt className="w-5 h-5" />
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600">
                    ACTIVE
                  </span>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-primary">4. Bookkeeping Agent</h3>
                  <p className="text-xs text-secondary mt-1">
                    Automatically categorizes all sales, refunds, vendor disbursements, and SaaS expenses into your double-entry ledger.
                  </p>
                </div>
                <div className="text-[11px] space-y-1 bg-background p-3 rounded-xl border border-border text-secondary">
                  <div>• Standard Chart of Accounts</div>
                  <div>• Auto-categorizes GST, Payroll & Cloud</div>
                  <div>• Total Ledger Entries: <strong className="text-primary font-mono">{bookkeeping.length}</strong></div>
                </div>
              </div>
              <button
                onClick={() => setTab('audit')}
                className="w-full py-2 rounded-xl text-xs font-bold bg-muted hover:bg-border text-primary transition cursor-pointer"
              >
                View General Ledger
              </button>
            </div>

            {/* 5. Reporting Agent */}
            <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs hover:border-indigo-500/40 transition space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-2xl bg-teal-500/10 text-teal-600 flex items-center justify-center font-bold">
                    <FileText className="w-5 h-5" />
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600">
                    ACTIVE
                  </span>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-primary">5. Reporting Agent</h3>
                  <p className="text-xs text-secondary mt-1">
                    Generates executive daily pulses, weekly treasury summaries, monthly P&Ls, and anomaly detection diagnostics.
                  </p>
                </div>
                <div className="text-[11px] space-y-1 bg-background p-3 rounded-xl border border-border text-secondary">
                  <div>• Supported: Daily, Weekly, Monthly, Anomaly</div>
                  <div>• Natural-language synthesis</div>
                  <div>• Auto-published reports</div>
                </div>
              </div>
              <button
                onClick={() => setTab('reports')}
                className="w-full py-2 rounded-xl text-xs font-bold bg-teal-600 text-white hover:bg-teal-700 transition cursor-pointer"
              >
                Generate Reports
              </button>
            </div>

            {/* Future-Ready: Tax & Reimbursement */}
            <div className="p-6 rounded-3xl bg-surface border border-dashed border-border shadow-xs space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-2xl bg-gray-500/10 text-secondary flex items-center justify-center font-bold">
                    <Sparkles className="w-5 h-5" />
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/10 text-indigo-400">
                    FUTURE-READY
                  </span>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-primary">6. Tax & Reimbursement Agents</h3>
                  <p className="text-xs text-secondary mt-1">
                    Pre-architected connectors for automated GSTR-1 filings, input tax credit reconciliation, and employee expense claim audits.
                  </p>
                </div>
                <div className="text-[11px] space-y-1 text-secondary">
                  <div>• Tax Agent: GST schedules & TDS deduction</div>
                  <div>• Reimbursement Agent: Policy receipt checks</div>
                </div>
              </div>
              <Link
                to="/agents/marketplace"
                className="w-full py-2 rounded-xl text-xs font-bold text-center border border-border text-secondary hover:text-primary transition block"
              >
                View in Agent Studio
              </Link>
            </div>

          </div>
        </div>
      )}

      {/* ── TAB 3: RECEIVABLES ── */}
      {activeTab === 'receivables' && (
        <div className="space-y-6 animate-in fade-in duration-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-primary">Accounts Receivable Management</h2>
              <p className="text-xs text-secondary">
                The Receivables Agent scans debtor accounts, calculates aging days, and issues automated payment collection notices.
              </p>
            </div>
            <button
              onClick={fetchBankingData}
              className="text-xs font-bold text-secondary hover:text-primary flex items-center gap-1.5 cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh Invoices</span>
            </button>
          </div>

          <div className="overflow-x-auto rounded-3xl border border-border bg-surface shadow-xs">
            <table className="w-full text-left text-xs">
              <thead className="bg-background text-secondary border-b border-border uppercase font-semibold text-[10px]">
                <tr>
                  <th className="p-4">Customer</th>
                  <th className="p-4">Invoice #</th>
                  <th className="p-4">Amount</th>
                  <th className="p-4">Due Date</th>
                  <th className="p-4">Aging</th>
                  <th className="p-4">Priority</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 text-right">Autonomous Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {receivables.map((inv) => (
                  <tr key={inv.id} className="hover:bg-muted/40 transition">
                    <td className="p-4 font-bold text-primary">{inv.customer}</td>
                    <td className="p-4 font-mono font-semibold text-secondary">{inv.invoice_number}</td>
                    <td className="p-4 font-mono font-black text-primary">₹{inv.amount.toLocaleString('en-IN')}</td>
                    <td className="p-4 text-secondary">{inv.due_date}</td>
                    <td className="p-4">
                      {inv.days_overdue > 0 ? (
                        <span className="text-rose-500 font-bold">{inv.days_overdue} days overdue</span>
                      ) : (
                        <span className="text-emerald-500 font-medium">On Schedule</span>
                      )}
                    </td>
                    <td className="p-4">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          inv.priority === 'HIGH'
                            ? 'bg-rose-500/15 text-rose-600'
                            : inv.priority === 'MEDIUM'
                            ? 'bg-amber-500/15 text-amber-600'
                            : 'bg-indigo-500/15 text-indigo-600'
                        }`}
                      >
                        {inv.priority}
                      </span>
                    </td>
                    <td className="p-4">
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                          inv.status === 'PAID'
                            ? 'bg-emerald-500/15 text-emerald-600'
                            : inv.status === 'OVERDUE'
                            ? 'bg-rose-500/15 text-rose-600'
                            : 'bg-amber-500/15 text-amber-600'
                        }`}
                      >
                        {inv.status}
                      </span>
                    </td>
                    <td className="p-4 text-right space-x-2">
                      {inv.status !== 'PAID' ? (
                        <>
                          <button
                            onClick={() => handleTriggerFollowup(inv.id, 'EMAIL')}
                            className="px-3 py-1.5 rounded-xl text-[11px] font-bold bg-indigo-600 hover:bg-indigo-700 text-white cursor-pointer"
                          >
                            Send Reminder
                          </button>
                          <button
                            onClick={() => handleMarkInvoicePaid(inv.id)}
                            className="px-2.5 py-1.5 rounded-xl text-[11px] font-bold border border-border text-secondary hover:text-emerald-600 cursor-pointer"
                          >
                            Mark Paid
                          </button>
                        </>
                      ) : (
                        <span className="text-emerald-600 font-bold text-[11px] flex items-center justify-end gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Settled
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── TAB 4: PAYOUTS (CONVERSATIONAL AGENT) ── */}
      {activeTab === 'payouts' && (
        <div className="space-y-6 animate-in fade-in duration-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-primary">Conversational Vendor Payout Assistant</h2>
              <p className="text-xs text-secondary">
                Tell the Payout Agent to disburse funds. Governed by zero-trust limits and human approval gating.
              </p>
            </div>
            <span className="text-xs font-mono font-bold text-indigo-500">Transaction Governance: ACTIVE</span>
          </div>

          {/* Prompt Presets */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-secondary font-semibold">Try sample payout commands:</span>
            <button
              type="button"
              onClick={() => setPayoutPrompt('Pay Rahul ₹18,500 for invoice INV-204')}
              className="px-3 py-1.5 rounded-xl bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-600 font-bold cursor-pointer"
            >
              "Pay Rahul ₹18,500 for invoice INV-204"
            </button>
            <button
              type="button"
              onClick={() => setPayoutPrompt('Pay CloudScale ₹42,000 for invoice INV-188')}
              className="px-3 py-1.5 rounded-xl bg-purple-500/10 hover:bg-purple-500/20 text-purple-600 font-bold cursor-pointer"
            >
              "Pay CloudScale ₹42,000 for invoice INV-188"
            </button>
          </div>

          {/* Chat Stream & Approval Card */}
          <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs space-y-4 max-w-3xl">
            <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
              {payoutMessages.map((msg, i) => (
                <div
                  key={i}
                  className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-indigo-600 text-white ml-12 rounded-br-xs'
                      : 'bg-background border border-border text-primary mr-12 rounded-bl-xs'
                  }`}
                >
                  <p className="whitespace-pre-line">{msg.text}</p>
                </div>
              ))}
            </div>

            {/* Payout Governance Approval Card */}
            {activeApprovalCard && (
              <div className="p-5 rounded-2xl bg-amber-500/10 border-2 border-amber-500/40 text-xs space-y-4 animate-in fade-in duration-200">
                <div className="flex items-center justify-between border-b border-amber-500/20 pb-3">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-5 h-5 text-amber-500" />
                    <span className="font-bold text-amber-900 dark:text-amber-200 uppercase tracking-wider text-[11px]">
                      Mandatory Human Approval Required
                    </span>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-600">
                    Zero-Trust Firewall
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-primary">
                  <div>
                    <span className="text-secondary text-[10px] uppercase font-bold block">Beneficiary</span>
                    <span className="font-bold">{activeApprovalCard.recipient_name}</span>
                  </div>
                  <div>
                    <span className="text-secondary text-[10px] uppercase font-bold block">Invoice Ref</span>
                    <span className="font-mono font-bold">{activeApprovalCard.invoice_number}</span>
                  </div>
                  <div>
                    <span className="text-secondary text-[10px] uppercase font-bold block">Disbursement Amount</span>
                    <span className="font-mono font-black text-base text-primary">
                      ₹{activeApprovalCard.amount?.toLocaleString('en-IN')}
                    </span>
                  </div>
                  <div>
                    <span className="text-secondary text-[10px] uppercase font-bold block">Account / IFSC</span>
                    <span className="font-mono">{activeApprovalCard.bank_account} ({activeApprovalCard.ifsc})</span>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 pt-2 border-t border-amber-500/20">
                  <button
                    type="button"
                    onClick={() => setActiveApprovalCard(null)}
                    className="px-4 py-2 rounded-xl font-bold text-secondary hover:bg-muted cursor-pointer"
                  >
                    Reject Payout
                  </button>
                  <button
                    type="button"
                    disabled={payoutLoading}
                    onClick={() => handleApprovePayout(activeApprovalCard.invoice_id)}
                    className="px-5 py-2 rounded-xl font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-md cursor-pointer flex items-center gap-1.5"
                  >
                    {payoutLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                    <span>Approve & Disburse ₹{activeApprovalCard.amount?.toLocaleString('en-IN')}</span>
                  </button>
                </div>
              </div>
            )}

            {/* Input Bar */}
            <form onSubmit={handlePayoutSubmit} className="flex items-center gap-2 pt-2 border-t border-border">
              <input
                type="text"
                value={payoutPrompt}
                onChange={(e) => setPayoutPrompt(e.target.value)}
                placeholder="e.g. Pay Rahul ₹18,500 for invoice INV-204..."
                className="flex-1 px-4 py-2.5 rounded-2xl bg-background border border-border text-xs sm:text-sm text-primary focus:outline-none focus:border-indigo-500"
              />
              <button
                type="submit"
                disabled={payoutLoading || !payoutPrompt.trim()}
                className="px-4 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                {payoutLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                <span>Send</span>
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ── TAB 5: CASHFLOW & RUNWAY ── */}
      {activeTab === 'cashflow' && (
        <div className="space-y-6 animate-in fade-in duration-200">
          <div>
            <h2 className="text-lg font-bold text-primary">Cashflow Forecaster & Runway Intelligence</h2>
            <p className="text-xs text-secondary">
              Real-time projection model factoring in recurring sales velocity, operational burn rate, and pending invoices.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div className="p-6 rounded-3xl bg-surface border border-border space-y-2">
              <span className="text-xs text-secondary font-semibold">Available Liquidity</span>
              <p className="text-3xl font-black text-primary font-mono">₹28,45,000</p>
              <p className="text-xs text-secondary">HDFC Current Account</p>
            </div>
            <div className="p-6 rounded-3xl bg-surface border border-border space-y-2">
              <span className="text-xs text-secondary font-semibold">Monthly Operating Burn</span>
              <p className="text-3xl font-black text-rose-500 font-mono">₹4,20,000</p>
              <p className="text-xs text-secondary">Hosting, Payroll, SaaS</p>
            </div>
            <div className="p-6 rounded-3xl bg-surface border border-border space-y-2">
              <span className="text-xs text-secondary font-semibold">Calculated Cash Runway</span>
              <p className="text-3xl font-black text-indigo-600 font-mono">6.8 Months</p>
              <p className="text-xs text-emerald-600 font-semibold">Healthy financial runway</p>
            </div>
          </div>

          <div className="p-6 rounded-3xl bg-surface border border-border space-y-4">
            <h3 className="text-sm font-bold text-primary">Daily Projected Cash Movements (Next 14 Days)</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-background text-secondary border-b border-border uppercase font-semibold text-[10px]">
                  <tr>
                    <th className="p-3">Date</th>
                    <th className="p-3">Expected Inflow</th>
                    <th className="p-3">Expected Outflow</th>
                    <th className="p-3 font-mono">Projected Closing Balance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {(metrics?.cashflow_forecast || []).map((row: any, i: number) => (
                    <tr key={i} className="hover:bg-muted/40">
                      <td className="p-3 font-bold text-primary">{row.day}</td>
                      <td className="p-3 text-emerald-600 font-mono font-semibold">+₹{row.inflow?.toLocaleString('en-IN')}</td>
                      <td className="p-3 text-rose-500 font-mono font-semibold">-₹{row.outflow?.toLocaleString('en-IN')}</td>
                      <td className="p-3 font-mono font-black text-primary">₹{row.projected_balance?.toLocaleString('en-IN')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ── TAB 6: RECONCILIATION ── */}
      {activeTab === 'reconciliation' && (
        <div className="space-y-6 animate-in fade-in duration-200">
          <div>
            <h2 className="text-lg font-bold text-primary">Automated Bank & Settlement Reconciliation</h2>
            <p className="text-xs text-secondary">
              Real-time audit verifying that bank account balances perfectly match RazorHub payment settlements and payouts.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div className="p-6 rounded-3xl bg-surface border border-border space-y-2">
              <span className="text-xs text-secondary font-semibold">Reconciliation State</span>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-xl font-black text-emerald-600">RECONCILED</span>
              </div>
              <p className="text-[11px] text-secondary">Feed Health: OPTIMAL</p>
            </div>

            <div className="p-6 rounded-3xl bg-surface border border-border space-y-2">
              <span className="text-xs text-secondary font-semibold">Matched Transactions</span>
              <p className="text-2xl font-black text-primary font-mono">1,420 Items</p>
              <p className="text-[11px] text-emerald-600 font-semibold">0 Unmatched discrepancies</p>
            </div>

            <div className="p-6 rounded-3xl bg-surface border border-border space-y-2">
              <span className="text-xs text-secondary font-semibold">Uncleared Gateway Settlements</span>
              <p className="text-2xl font-black text-indigo-600 font-mono">₹64,200.00</p>
              <p className="text-[11px] text-secondary">T+1 clearing tomorrow 9:00 AM</p>
            </div>
          </div>
        </div>
      )}

      {/* ── TAB 7: REPORTS ── */}
      {activeTab === 'reports' && (
        <div className="space-y-6 animate-in fade-in duration-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-primary">Executive Intelligence Reports</h2>
              <p className="text-xs text-secondary">
                Produced by the autonomous Reporting Agent with natural-language financial narratives.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                disabled={generatingReport}
                onClick={() => handleGenerateReport('DAILY')}
                className="px-3 py-1.5 rounded-xl text-xs font-bold bg-muted hover:bg-border text-primary cursor-pointer"
              >
                + Daily Pulse
              </button>
              <button
                disabled={generatingReport}
                onClick={() => handleGenerateReport('WEEKLY')}
                className="px-3 py-1.5 rounded-xl text-xs font-bold bg-muted hover:bg-border text-primary cursor-pointer"
              >
                + Weekly Treasury
              </button>
              <button
                disabled={generatingReport}
                onClick={() => handleGenerateReport('ANOMALY')}
                className="px-3 py-1.5 rounded-xl text-xs font-bold bg-rose-500/10 text-rose-600 border border-rose-500/30 cursor-pointer"
              >
                + Anomaly Scan
              </button>
            </div>
          </div>

          <div className="space-y-4">
            {reports.map((r) => (
              <div key={r.id} className="p-6 rounded-3xl bg-surface border border-border space-y-3 shadow-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-indigo-500" />
                    <h3 className="text-sm font-bold text-primary">{r.title}</h3>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-muted text-secondary font-mono">
                    {r.period}
                  </span>
                </div>
                <p className="text-xs text-secondary leading-relaxed bg-background p-4 rounded-2xl border border-border">
                  {r.narrative}
                </p>
                {r.anomalies && r.anomalies.length > 0 && (
                  <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-700 dark:text-rose-300 text-xs space-y-1">
                    <strong className="block font-bold">Detected Anomalies:</strong>
                    {r.anomalies.map((an: any, i: number) => (
                      <div key={i} className="text-[11px]">
                        • [{an.severity}] {an.detail}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── TAB 8: AGENT STUDIO LINK ── */}
      {activeTab === 'agent-studio' && (
        <div className="p-8 rounded-3xl bg-surface border border-border text-center space-y-4 animate-in fade-in duration-200">
          <Zap className="w-12 h-12 text-indigo-500 mx-auto" />
          <h2 className="text-xl font-bold text-primary">Autonomous Agent Studio</h2>
          <p className="text-xs text-secondary max-w-md mx-auto">
            Design, customize, or inspect the underlying blueprints and tool registries for your finance agents.
          </p>
          <div className="pt-2">
            <Link
              to="/agents"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg"
            >
              <span>Open Agent Studio</span>
              <ExternalLink className="w-4 h-4" />
            </Link>
          </div>
        </div>
      )}

      {/* ── TAB 9: APPROVALS LINK ── */}
      {activeTab === 'approvals' && (
        <div className="p-8 rounded-3xl bg-surface border border-border text-center space-y-4 animate-in fade-in duration-200">
          <UserCheck className="w-12 h-12 text-amber-500 mx-auto" />
          <h2 className="text-xl font-bold text-primary">Transaction Approvals Queue</h2>
          <p className="text-xs text-secondary max-w-md mx-auto">
            Review human-in-the-loop approval tickets for payouts, large refunds, and financial mutations.
          </p>
          <div className="pt-2">
            <Link
              to="/agents?tab=approvals"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl text-xs font-bold bg-amber-600 hover:bg-amber-700 text-white shadow-lg"
            >
              <span>View Governance Approvals</span>
              <ExternalLink className="w-4 h-4" />
            </Link>
          </div>
        </div>
      )}

      {/* ── TAB 10: AUDIT (BOOKKEEPING GENERAL LEDGER) ── */}
      {activeTab === 'audit' && (
        <div className="space-y-6 animate-in fade-in duration-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-primary">General Ledger & Bookkeeping Audit</h2>
              <p className="text-xs text-secondary">
                Maintained in real-time by the Bookkeeping Agent. Automatically classifies e-commerce sales, vendor payouts, and SaaS bills.
              </p>
            </div>
          </div>

          <div className="overflow-x-auto rounded-3xl border border-border bg-surface shadow-xs">
            <table className="w-full text-left text-xs">
              <thead className="bg-background text-secondary border-b border-border uppercase font-semibold text-[10px]">
                <tr>
                  <th className="p-4">Reference</th>
                  <th className="p-4">Accounting Category</th>
                  <th className="p-4">Entry Type</th>
                  <th className="p-4 font-mono">Amount</th>
                  <th className="p-4">Notes</th>
                  <th className="p-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {bookkeeping.map((e) => (
                  <tr key={e.id} className="hover:bg-muted/40 transition">
                    <td className="p-4 font-mono font-bold text-primary">{e.reference}</td>
                    <td className="p-4">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-muted text-primary">
                        {e.category_label || e.category}
                      </span>
                    </td>
                    <td className="p-4">
                      <span
                        className={`font-bold ${
                          e.entry_type === 'CREDIT' ? 'text-emerald-600' : 'text-rose-500'
                        }`}
                      >
                        {e.entry_type}
                      </span>
                    </td>
                    <td className="p-4 font-mono font-black text-primary">₹{e.amount.toLocaleString('en-IN')}</td>
                    <td className="p-4 text-secondary max-w-xs truncate">{e.notes}</td>
                    <td className="p-4 text-secondary font-mono text-[11px]">{e.created_at?.slice(0, 10)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── FOLLOW-UP PREVIEW MODAL ── */}
      {followupModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                <h3 className="text-sm font-bold text-primary">Follow-Up Dispatched</h3>
              </div>
              <button onClick={() => setFollowupModal(null)} className="text-secondary text-xs cursor-pointer">✕</button>
            </div>
            <div className="space-y-2 text-xs">
              <p className="text-secondary">
                The Receivables Agent issued an automated debtor reminder for invoice <strong className="text-primary">{followupModal.invoice_number}</strong>:
              </p>
              <pre className="p-3 rounded-xl bg-background border border-border text-[11px] text-primary whitespace-pre-wrap font-sans">
                {followupModal.message}
              </pre>
            </div>
            <button
              onClick={() => setFollowupModal(null)}
              className="w-full py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold cursor-pointer"
            >
              Done
            </button>
          </div>
        </div>
      )}

    </div>
  );
}
