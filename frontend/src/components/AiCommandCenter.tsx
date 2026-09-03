import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  Send,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  Check,
  X,
  Bot,
  Database,
  Search,
  Zap,
  TrendingUp,
  FileText,
  Clock,
  DollarSign,
  ArrowRight,
  ExternalLink,
  ChevronRight,
  Layers,
  Info,
} from 'lucide-react';
import { apiRequest } from '../lib/api';
import { useAuth } from '../context/AuthContext';

interface CommandResponse {
  intent: 'QUERY' | 'ANALYZE' | 'ACTION' | 'CREATE_AGENT' | 'REPORT' | 'ESCALATE';
  confidence: number;
  understood: string;
  data_used: string[];
  plan: string;
  action_taken: string;
  result_data?: any;
  requires_approval: boolean;
  approval_card?: any;
}

export default function AiCommandCenter({ onActionExecuted }: { onActionExecuted?: () => void }) {
  const { token } = useAuth();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<CommandResponse | null>(null);
  const [approving, setApproving] = useState(false);
  const [approvalResult, setApprovalResult] = useState<any>(null);

  const samplePrompts = [
    "Show today's revenue.",
    "Why did revenue fall yesterday?",
    "Which invoices are overdue?",
    "Pay Rahul ₹18,500.",
    "Show payments above ₹50,000.",
    "Why are refunds increasing?",
    "Create an agent that reminds customers about overdue invoices.",
    "Give me tomorrow's cashflow forecast.",
  ];

  const handleExecute = async (promptText?: string) => {
    const q = (promptText || query).trim();
    if (!q || loading) return;

    if (promptText) {
      setQuery(promptText);
    }

    try {
      setLoading(true);
      setResponse(null);
      setApprovalResult(null);

      const res = await apiRequest<CommandResponse>('/agent-runtime/command-center/execute/', {
        token,
        method: 'POST',
        body: JSON.stringify({ query: q }),
      });

      setResponse(res);
    } catch (err: any) {
      alert(`Command Center Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveAction = async () => {
    if (!response?.approval_card) return;
    try {
      setApproving(true);
      const res = await apiRequest<any>('/agent-runtime/command-center/approve/', {
        token,
        method: 'POST',
        body: JSON.stringify({
          action_payload: {
            action_type: response.approval_card.type === 'REMINDER_DISPATCH_CARD'
              ? 'DISPATCH_RECEIVABLES_REMINDERS'
              : 'VENDOR_PAYOUT',
            invoice_id: response.approval_card.invoice_id,
          },
        }),
      });

      setApprovalResult(res);
      if (onActionExecuted) onActionExecuted();
    } catch (err: any) {
      alert(`Action execution failed: ${err.message}`);
    } finally {
      setApproving(false);
    }
  };

  const getIntentBadge = (intent: string) => {
    switch (intent) {
      case 'QUERY':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-black bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border border-cyan-500/30 flex items-center gap-1.5">
            <Search className="w-3.5 h-3.5" /> QUERY
          </span>
        );
      case 'ANALYZE':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-black bg-purple-500/15 text-purple-600 dark:text-purple-400 border border-purple-500/30 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5" /> ANALYZE
          </span>
        );
      case 'ACTION':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-black bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30 flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5" /> ACTION (GOVERNED)
          </span>
        );
      case 'CREATE_AGENT':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-black bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 border border-indigo-500/30 flex items-center gap-1.5">
            <Bot className="w-3.5 h-3.5" /> CREATE_AGENT
          </span>
        );
      case 'REPORT':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-black bg-teal-500/15 text-teal-600 dark:text-teal-400 border border-teal-500/30 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5" /> REPORT
          </span>
        );
      default:
        return (
          <span className="px-3 py-1 rounded-full text-xs font-black bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30 flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5" /> ESCALATE
          </span>
        );
    }
  };

  return (
    <div className="w-full space-y-4">
      {/* ── Persistent Natural-Language Command Bar ── */}
      <div className="relative rounded-3xl bg-surface border-2 border-indigo-500/30 shadow-lg p-2.5 sm:p-3 transition-all focus-within:border-indigo-500 focus-within:shadow-indigo-500/10">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleExecute();
          }}
          className="flex items-center gap-3"
        >
          <div className="pl-3 flex items-center justify-center shrink-0">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center shadow-md shadow-indigo-500/25">
              <Sparkles className="w-4 h-4 text-white animate-pulse" />
            </div>
          </div>

          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask anything or tell me what to do... (e.g. 'Show today\'s revenue', 'Pay Rahul ₹18,500')"
            className="flex-1 bg-transparent text-xs sm:text-sm text-primary placeholder:text-secondary/70 focus:outline-none font-medium"
          />

          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-5 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-md transition-all active:scale-95 cursor-pointer disabled:opacity-50 flex items-center gap-1.5 shrink-0"
          >
            {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline">Execute</span>
          </button>
        </form>

        {/* Quick Example Prompt Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pt-2.5 pb-1 px-2 text-[11px] scrollbar-none border-t border-border/50 mt-2">
          <span className="text-secondary font-bold shrink-0 mr-1 flex items-center gap-1">
            <Zap className="w-3 h-3 text-amber-500" /> Examples:
          </span>
          {samplePrompts.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleExecute(p)}
              className="px-2.5 py-1 rounded-xl bg-muted/60 hover:bg-muted border border-border/70 text-secondary hover:text-primary whitespace-nowrap transition cursor-pointer font-medium"
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* ── Structured 4-Step Transparency Result ── */}
      {response && (
        <div className="p-6 sm:p-7 rounded-3xl bg-surface border border-border/90 shadow-xl space-y-6 animate-in fade-in zoom-in-95 duration-200">
          {/* Header & Intent */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-2xl bg-indigo-500/10 text-indigo-600 flex items-center justify-center font-black">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-black text-primary">Autonomous Command Decision</h3>
                <p className="text-[11px] text-secondary">
                  Confidence: {(response.confidence * 100).toFixed(0)}% • Deterministic Governance Engine
                </p>
              </div>
            </div>
            <div>{getIntentBadge(response.intent)}</div>
          </div>

          {/* 4 Mandatory Pillars Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            {/* 1. What I understood */}
            <div className="p-4 rounded-2xl bg-background border border-border space-y-1.5">
              <span className="text-[10px] uppercase font-black tracking-wider text-indigo-500 block flex items-center gap-1">
                <Search className="w-3.5 h-3.5" /> 1. What I understood
              </span>
              <p className="text-primary font-medium leading-relaxed">{response.understood}</p>
            </div>

            {/* 2. What data I used */}
            <div className="p-4 rounded-2xl bg-background border border-border space-y-1.5">
              <span className="text-[10px] uppercase font-black tracking-wider text-purple-500 block flex items-center gap-1">
                <Database className="w-3.5 h-3.5" /> 2. What data I used
              </span>
              <div className="flex flex-wrap gap-1 pt-0.5">
                {response.data_used.map((d, i) => (
                  <span key={i} className="px-2 py-0.5 rounded-lg text-[10px] font-mono bg-muted text-secondary">
                    {d}
                  </span>
                ))}
              </div>
            </div>

            {/* 3. What I plan to do */}
            <div className="p-4 rounded-2xl bg-background border border-border space-y-1.5">
              <span className="text-[10px] uppercase font-black tracking-wider text-amber-500 block flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" /> 3. What I plan to do
              </span>
              <p className="text-secondary font-medium whitespace-pre-line leading-relaxed">{response.plan}</p>
            </div>

            {/* 4. What I actually did */}
            <div className="p-4 rounded-2xl bg-background border border-border space-y-1.5">
              <span className="text-[10px] uppercase font-black tracking-wider text-emerald-500 block flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> 4. What I actually did
              </span>
              <p className="text-primary font-semibold leading-relaxed">{response.action_taken}</p>
            </div>
          </div>

          {/* ── ACTION APPROVAL CARD (When Required) ── */}
          {response.requires_approval && response.approval_card && !approvalResult && (
            <div className="p-5 sm:p-6 rounded-3xl bg-amber-500/10 border-2 border-amber-500/40 text-xs space-y-4">
              <div className="flex items-center justify-between border-b border-amber-500/20 pb-3">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-amber-500" />
                  <span className="font-black text-amber-900 dark:text-amber-200 uppercase tracking-wider text-[11px]">
                    Zero-Trust Transaction Governance Approval
                  </span>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-600">
                  Human Sign-Off Required
                </span>
              </div>

              {response.approval_card.type === 'PAYOUT_APPROVAL_CARD' ? (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div>
                    <span className="text-secondary text-[10px] font-bold block uppercase">Beneficiary</span>
                    <span className="font-bold text-primary">{response.approval_card.recipient_name}</span>
                  </div>
                  <div>
                    <span className="text-secondary text-[10px] font-bold block uppercase">Invoice Number</span>
                    <span className="font-mono font-bold text-primary">{response.approval_card.invoice_number}</span>
                  </div>
                  <div>
                    <span className="text-secondary text-[10px] font-bold block uppercase">Disbursement Amount</span>
                    <span className="font-mono font-black text-base text-primary">
                      ₹{response.approval_card.amount?.toLocaleString('en-IN')}
                    </span>
                  </div>
                  <div>
                    <span className="text-secondary text-[10px] font-bold block uppercase">Risk Evaluation</span>
                    <span className="font-bold text-emerald-600">{response.approval_card.risk_level}</span>
                  </div>
                </div>
              ) : (
                <div className="text-secondary font-medium">
                  {response.approval_card.title || 'Approve batch notification to overdue customer accounts.'}
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-amber-500/20">
                <button
                  type="button"
                  onClick={() => setResponse(null)}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-secondary hover:bg-muted cursor-pointer"
                >
                  Cancel / Reject
                </button>
                <button
                  type="button"
                  disabled={approving}
                  onClick={handleApproveAction}
                  className="px-5 py-2.5 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-700 text-white shadow-md transition cursor-pointer flex items-center gap-2"
                >
                  {approving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                  <span>Approve & Execute Action</span>
                </button>
              </div>
            </div>
          )}

          {/* Action Approval Receipt */}
          {approvalResult && (
            <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-800 dark:text-emerald-200 text-xs flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>
                  <strong>Action Executed:</strong> Disbursed ₹{approvalResult.amount?.toLocaleString('en-IN')} to {approvalResult.recipient} (Ref: {approvalResult.utr_reference}).
                </span>
              </div>
              <span className="font-mono text-[10px] bg-emerald-500/20 px-2 py-0.5 rounded">DISBURSED</span>
            </div>
          )}

          {/* ── Contextual Data Payloads ── */}
          {response.intent === 'CREATE_AGENT' && response.result_data?.blueprint && (
            <div className="p-4 rounded-2xl bg-background border border-border text-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-primary">Generated Agent Blueprint</span>
                <Link
                  to="/agents/create"
                  className="text-indigo-600 hover:underline flex items-center gap-1 font-bold"
                >
                  <span>Open in Agent Studio</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </Link>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div>Name: <strong className="text-primary">{response.result_data.blueprint.name}</strong></div>
                <div>Trigger: <strong className="text-primary font-mono">Daily 09:00 IST</strong></div>
                <div className="col-span-2">
                  Tools: {response.result_data.blueprint.tools?.join(', ')}
                </div>
              </div>
            </div>
          )}

          {response.intent === 'REPORT' && response.result_data?.forecast_date && (
            <div className="p-4 rounded-2xl bg-background border border-border text-xs flex items-center justify-between">
              <div>
                <span className="text-secondary text-[11px] block">Projected Closing Cash ({response.result_data.forecast_date})</span>
                <span className="text-xl font-black font-mono text-primary">
                  ₹{response.result_data.projected_closing_balance?.toLocaleString('en-IN')}
                </span>
              </div>
              <div className="text-right">
                <span className="text-secondary text-[11px] block">Net Inflow Movement</span>
                <span className="text-sm font-bold font-mono text-emerald-600">
                  +₹{response.result_data.net_cashflow?.toLocaleString('en-IN')}
                </span>
              </div>
            </div>
          )}

          {response.intent === 'QUERY' && response.result_data?.invoices && (
            <div className="p-4 rounded-2xl bg-background border border-border text-xs space-y-2">
              <span className="font-bold text-primary">Overdue Debtor Accounts ({response.result_data.overdue_count}):</span>
              <div className="divide-y divide-border/60">
                {response.result_data.invoices.map((inv: any, i: number) => (
                  <div key={i} className="py-1.5 flex items-center justify-between text-[11px]">
                    <div>
                      <strong className="text-primary">{inv.customer}</strong> ({inv.invoice_number})
                    </div>
                    <div className="font-mono font-bold text-rose-500">
                      ₹{inv.amount.toLocaleString('en-IN')} ({inv.days_overdue}d overdue)
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  );
}
