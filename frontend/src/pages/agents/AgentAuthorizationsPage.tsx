import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Play,
  Pause,
  XCircle,
  Edit3,
  Plus,
  RefreshCw,
  Clock,
  Calendar,
  Lock,
  Bot,
  Zap,
  CheckCircle2,
  Sliders,
  DollarSign,
  ArrowRight,
  TrendingUp,
  Tag,
  Store,
  Layers,
  Info,
} from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';

interface PaymentAuthorization {
  id: string;
  agent: string;
  agent_name: string;
  user_email: string;
  max_transaction_amount: number;
  daily_limit: number;
  monthly_limit: number;
  used_today: number;
  used_this_month: number;
  remaining_today: number;
  remaining_month: number;
  allowed_categories: string[];
  blocked_categories: string[];
  allowed_merchants: string[];
  blocked_merchants: string[];
  approval_threshold: number;
  status: 'ACTIVE' | 'PAUSED' | 'REVOKED' | 'EXPIRED';
  expires_at: string | null;
  created_at: string;
  updated_at: string;
}

interface AgentOption {
  id: string;
  name: string;
  category: string;
  description: string;
}

export default function AgentAuthorizationsPage() {
  const { token, user } = useAuth();

  const [authorizations, setAuthorizations] = useState<PaymentAuthorization[]>([]);
  const [agents, setAgents] = useState<AgentOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Modal / Form state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingAuth, setEditingAuth] = useState<PaymentAuthorization | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState('');
  const [maxTxAmount, setMaxTxAmount] = useState(5000);
  const [dailyLimit, setDailyLimit] = useState(10000);
  const [monthlyLimit, setMonthlyLimit] = useState(50000);
  const [approvalThreshold, setApprovalThreshold] = useState(2000);
  const [allowedCategories, setAllowedCategories] = useState('electronics, accessories, apparel, home');
  const [blockedCategories, setBlockedCategories] = useState('cash, crypto, gambling');
  const [allowedMerchants, setAllowedMerchants] = useState('RazorHub Direct, SonicAudio Official Store, boAt Lifestyle Flagship, JBL Direct Hub');
  const [blockedMerchants, setBlockedMerchants] = useState('');
  const [expiryDays, setExpiryDays] = useState(30);

  // Simulation runner state
  const [simAuthId, setSimAuthId] = useState<string>('');
  const [simAmount, setSimAmount] = useState<number>(1500);
  const [simMerchant, setSimMerchant] = useState('RazorHub Direct');
  const [simCategory, setSimCategory] = useState('electronics');
  const [simRunning, setSimRunning] = useState(false);
  const [simResult, setSimResult] = useState<any>(null);

  const [notice, setNotice] = useState<string | null>(null);

  const fetchAuthorizationsAndAgents = async () => {
    try {
      setLoading(true);
      const [authsData, agentsData] = await Promise.all([
        apiRequest<any>('/agent-runtime/authorizations/', { token }),
        apiRequest<any>('/agent-runtime/agents/', { token }),
      ]);
      const authList = Array.isArray(authsData) ? authsData : authsData.results || [];
      const agentList = Array.isArray(agentsData) ? agentsData : agentsData.results || [];
      setAuthorizations(authList);
      setAgents(agentList);
      if (authList.length > 0 && !simAuthId) {
        setSimAuthId(authList[0].id);
      }
      if (agentList.length > 0 && !selectedAgentId) {
        setSelectedAgentId(agentList[0].id);
      }
    } catch (err: any) {
      console.error('Failed to load authorizations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuthorizationsAndAgents();
  }, [token]);

  const handleCreateAuthorization = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setActionLoading('create');
      const expiryDate = new Date();
      expiryDate.setDate(expiryDate.getDate() + Number(expiryDays));

      const payload = {
        agent: selectedAgentId,
        max_transaction_amount: maxTxAmount,
        daily_limit: dailyLimit,
        monthly_limit: monthlyLimit,
        approval_threshold: approvalThreshold,
        allowed_categories: allowedCategories.split(',').map((c) => c.trim()).filter(Boolean),
        blocked_categories: blockedCategories.split(',').map((c) => c.trim()).filter(Boolean),
        allowed_merchants: allowedMerchants.split(',').map((m) => m.trim()).filter(Boolean),
        blocked_merchants: blockedMerchants.split(',').map((m) => m.trim()).filter(Boolean),
        expires_at: expiryDate.toISOString(),
      };

      await apiRequest('/agent-runtime/authorizations/', {
        token,
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setShowCreateModal(false);
      setNotice('Agent payment authorization created successfully!');
      fetchAuthorizationsAndAgents();
    } catch (err: any) {
      alert(`Failed to create authorization: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handlePause = async (id: string) => {
    try {
      setActionLoading(id);
      await apiRequest(`/agent-runtime/authorizations/${id}/pause/`, { token, method: 'POST' });
      setNotice('Authorization paused.');
      fetchAuthorizationsAndAgents();
    } catch (err: any) {
      alert(`Failed to pause: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleResume = async (id: string) => {
    try {
      setActionLoading(id);
      await apiRequest(`/agent-runtime/authorizations/${id}/resume/`, { token, method: 'POST' });
      setNotice('Authorization resumed and is now ACTIVE.');
      fetchAuthorizationsAndAgents();
    } catch (err: any) {
      alert(`Failed to resume: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRevoke = async (id: string) => {
    if (!window.confirm('Are you sure you want to revoke this agent authorization? This action cannot be undone.')) {
      return;
    }
    try {
      setActionLoading(id);
      await apiRequest(`/agent-runtime/authorizations/${id}/revoke/`, { token, method: 'POST' });
      setNotice('Authorization revoked.');
      fetchAuthorizationsAndAgents();
    } catch (err: any) {
      alert(`Failed to revoke: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleSaveLimits = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingAuth) return;
    try {
      setActionLoading('edit-limits');
      const payload = {
        max_transaction_amount: editingAuth.max_transaction_amount,
        daily_limit: editingAuth.daily_limit,
        monthly_limit: editingAuth.monthly_limit,
        approval_threshold: editingAuth.approval_threshold,
        allowed_categories: editingAuth.allowed_categories,
        blocked_categories: editingAuth.blocked_categories,
        allowed_merchants: editingAuth.allowed_merchants,
        blocked_merchants: editingAuth.blocked_merchants,
      };

      await apiRequest(`/agent-runtime/authorizations/${editingAuth.id}/limits/`, {
        token,
        method: 'PATCH',
        body: JSON.stringify(payload),
      });

      setEditingAuth(null);
      setNotice('Authorization limits updated.');
      fetchAuthorizationsAndAgents();
    } catch (err: any) {
      alert(`Failed to save limits: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRunSimulation = async (isConfirm = false) => {
    if (!simAuthId) return;
    try {
      setSimRunning(true);
      setSimResult(null);
      const res = await apiRequest(`/agent-runtime/authorizations/${simAuthId}/test_verify/`, {
        token,
        method: 'POST',
        body: JSON.stringify({
          amount: simAmount,
          merchant: simMerchant,
          category: simCategory,
          is_confirmation: isConfirm,
        }),
      });
      setSimResult(res);
      fetchAuthorizationsAndAgents();
    } catch (err: any) {
      setSimResult({ decision: 'BLOCKED', reason: err.message });
    } finally {
      setSimRunning(false);
    }
  };

  const getStatusBadge = (st: string) => {
    switch (st) {
      case 'ACTIVE':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            ACTIVE
          </span>
        );
      case 'PAUSED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
            <Pause className="w-3.5 h-3.5" />
            PAUSED
          </span>
        );
      case 'REVOKED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30">
            <XCircle className="w-3.5 h-3.5" />
            REVOKED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-gray-500/15 text-gray-500 border border-gray-500/30">
            <Clock className="w-3.5 h-3.5" />
            EXPIRED
          </span>
        );
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 sm:py-8 space-y-6">
      
      {/* ── SANDBOX DISCLAIMER NOTICE ── */}
      <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-800 dark:text-amber-200 text-xs flex items-start gap-3 shadow-xs">
        <Info className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <strong className="font-bold">SANDBOX / DEMONSTRATION SIMULATOR</strong>
          <p className="leading-relaxed text-[11px] opacity-90">
            This module is a simulated agent payment authorization system inspired by consent-based pre-authorized payment concepts (such as UPI Reserve Pay).
            It demonstrates atomic concurrency locking, real-time balance consumption, and human-in-the-loop threshold gating without executing real bank transactions.
          </p>
        </div>
      </div>

      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-3xl bg-surface border border-border/80 shadow-xs">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <Link to="/agents" className="text-xs font-semibold text-secondary hover:text-primary transition">
              Agent Studio
            </Link>
            <span className="text-secondary text-xs">/</span>
            <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider">
              Payment Authorizations
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-primary tracking-tight">
            Agent Payment Authorizations
          </h1>
          <p className="text-xs sm:text-sm text-secondary">
            Manage pre-authorized payment consent mandates, spending limits, and real-time reservation firewalls for your autonomous agents.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setShowCreateModal(true)}
            className="px-5 py-2.5 rounded-2xl text-xs font-extrabold bg-gradient-to-r from-indigo-600 to-purple-600 hover:opacity-95 text-white shadow-lg shadow-indigo-600/25 transition flex items-center gap-2 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Allow New Agent</span>
          </button>
        </div>
      </div>

      {notice && (
        <div className="p-4 rounded-2xl bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-900 text-indigo-900 dark:text-indigo-200 text-xs sm:text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
            <span>{notice}</span>
          </div>
          <button onClick={() => setNotice(null)} className="font-bold underline text-xs">Dismiss</button>
        </div>
      )}

      {/* ── AUTHORIZATIONS LIST ── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-primary flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-indigo-500" />
            <span>Active Agent Mandates ({authorizations.length})</span>
          </h2>
          <button
            onClick={fetchAuthorizationsAndAgents}
            className="text-xs font-bold text-secondary hover:text-primary flex items-center gap-1"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        {authorizations.length === 0 ? (
          <div className="p-12 text-center rounded-3xl border border-dashed border-border bg-surface/50 space-y-3">
            <Bot className="w-8 h-8 text-secondary mx-auto opacity-50" />
            <p className="text-sm font-semibold text-primary">No Payment Authorizations Configured</p>
            <p className="text-xs text-secondary max-w-md mx-auto">
              Grant spending consent to autonomous commerce agents so they can execute pre-approved purchases under your exact financial guardrails.
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold cursor-pointer"
            >
              Create Authorization
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {authorizations.map((auth) => {
              const isActionRunning = actionLoading === auth.id;
              const dailyPct = Math.min((auth.used_today / auth.daily_limit) * 100, 100);
              const monthlyPct = Math.min((auth.used_this_month / auth.monthly_limit) * 100, 100);

              return (
                <div
                  key={auth.id}
                  className="p-6 rounded-3xl bg-surface border border-border/80 shadow-xs hover:border-indigo-500/40 transition space-y-5 flex flex-col justify-between"
                >
                  <div className="space-y-4">
                    {/* Header with status */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 flex items-center justify-center font-black shrink-0">
                          <Bot className="w-5 h-5" />
                        </div>
                        <div>
                          <h3 className="text-sm font-black text-primary">{auth.agent_name}</h3>
                          <p className="text-[11px] text-secondary font-mono">ID: {auth.id.slice(0, 8)}...</p>
                        </div>
                      </div>
                      <div>{getStatusBadge(auth.status)}</div>
                    </div>

                    {/* Spend Meters */}
                    <div className="space-y-3 pt-1">
                      
                      {/* Daily Limit Bar */}
                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between text-[11px]">
                          <span className="text-secondary font-semibold">Daily Spend Limit:</span>
                          <span className="font-mono font-bold text-primary">
                            ₹{auth.used_today.toLocaleString('en-IN')} / ₹{auth.daily_limit.toLocaleString('en-IN')} ({dailyPct.toFixed(0)}%)
                          </span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                          <div
                            style={{ width: `${dailyPct}%` }}
                            className={`h-full rounded-full transition-all ${
                              dailyPct > 80 ? 'bg-rose-500' : 'bg-indigo-600'
                            }`}
                          />
                        </div>
                        <p className="text-[10px] text-secondary">
                          Remaining Today: <strong className="text-primary font-mono">₹{auth.remaining_today.toLocaleString('en-IN')}</strong>
                        </p>
                      </div>

                      {/* Monthly Limit Bar */}
                      <div className="space-y-1 text-xs pt-1">
                        <div className="flex justify-between text-[11px]">
                          <span className="text-secondary font-semibold">Monthly Spend Limit:</span>
                          <span className="font-mono font-bold text-primary">
                            ₹{auth.used_this_month.toLocaleString('en-IN')} / ₹{auth.monthly_limit.toLocaleString('en-IN')} ({monthlyPct.toFixed(0)}%)
                          </span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                          <div
                            style={{ width: `${monthlyPct}%` }}
                            className="h-full bg-purple-600 rounded-full transition-all"
                          />
                        </div>
                      </div>

                    </div>

                    {/* Rule Grid */}
                    <div className="grid grid-cols-2 gap-3 pt-2 text-xs bg-background p-3.5 rounded-2xl border border-border/80">
                      <div>
                        <span className="text-secondary text-[10px] uppercase font-bold block">Max Per Tx</span>
                        <span className="font-mono font-black text-primary">₹{auth.max_transaction_amount.toLocaleString('en-IN')}</span>
                      </div>
                      <div>
                        <span className="text-secondary text-[10px] uppercase font-bold block">Auto-Approve Below</span>
                        <span className="font-mono font-bold text-emerald-600">&lt; ₹{auth.approval_threshold.toLocaleString('en-IN')}</span>
                      </div>
                      <div className="col-span-2 pt-1 border-t border-border/50 flex flex-wrap gap-1">
                        <span className="text-secondary text-[10px] font-bold">Categories:</span>
                        {auth.allowed_categories.map((c, i) => (
                          <span key={i} className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-muted text-primary">
                            {c}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Actions Bar */}
                  <div className="pt-4 border-t border-border flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      {auth.status === 'ACTIVE' ? (
                        <button
                          type="button"
                          disabled={isActionRunning}
                          onClick={() => handlePause(auth.id)}
                          className="px-3 py-1.5 rounded-xl text-xs font-bold border border-amber-500/30 text-amber-600 hover:bg-amber-500/10 transition cursor-pointer flex items-center gap-1.5"
                        >
                          <Pause className="w-3.5 h-3.5" />
                          <span>Pause</span>
                        </button>
                      ) : auth.status === 'PAUSED' ? (
                        <button
                          type="button"
                          disabled={isActionRunning}
                          onClick={() => handleResume(auth.id)}
                          className="px-3 py-1.5 rounded-xl text-xs font-bold border border-emerald-500/30 text-emerald-600 hover:bg-emerald-500/10 transition cursor-pointer flex items-center gap-1.5"
                        >
                          <Play className="w-3.5 h-3.5" />
                          <span>Resume</span>
                        </button>
                      ) : null}

                      <button
                        type="button"
                        onClick={() => setEditingAuth(auth)}
                        className="px-3 py-1.5 rounded-xl text-xs font-bold border border-border text-secondary hover:text-primary hover:bg-muted transition cursor-pointer flex items-center gap-1.5"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                        <span>Edit Limits</span>
                      </button>
                    </div>

                    {auth.status !== 'REVOKED' && (
                      <button
                        type="button"
                        disabled={isActionRunning}
                        onClick={() => handleRevoke(auth.id)}
                        className="px-3 py-1.5 rounded-xl text-xs font-bold text-rose-600 hover:bg-rose-500/10 transition cursor-pointer"
                      >
                        Revoke
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── INTERACTIVE SANDBOX TRANSACTION SIMULATOR ── */}
      <div className="p-6 sm:p-8 rounded-3xl bg-surface border border-border/80 shadow-xs space-y-5">
        <div className="flex items-center justify-between border-b border-border pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-indigo-500" />
              <h2 className="text-lg font-bold text-primary">Live Sandbox Verification & Concurrency Tester</h2>
            </div>
            <p className="text-xs text-secondary">
              Fire test transactions to inspect atomic row-locking, idempotency deduplication, and real-time spend depletion.
            </p>
          </div>
          <span className="text-xs font-mono text-secondary">Simulation Engine Active</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs">
          <div>
            <label className="block text-secondary font-bold mb-1">Target Mandate</label>
            <select
              value={simAuthId}
              onChange={(e) => setSimAuthId(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary font-medium"
            >
              {authorizations.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.agent_name} (₹{a.used_today}/{a.daily_limit})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-secondary font-bold mb-1">Transaction Amount (₹)</label>
            <input
              type="number"
              value={simAmount}
              onChange={(e) => setSimAmount(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary font-mono"
            />
          </div>

          <div>
            <label className="block text-secondary font-bold mb-1">Merchant</label>
            <input
              type="text"
              value={simMerchant}
              onChange={(e) => setSimMerchant(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary"
            />
          </div>

          <div>
            <label className="block text-secondary font-bold mb-1">Category</label>
            <input
              type="text"
              value={simCategory}
              onChange={(e) => setSimCategory(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary"
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 pt-2">
          <button
            type="button"
            disabled={simRunning || !simAuthId}
            onClick={() => handleRunSimulation(false)}
            className="px-5 py-2.5 rounded-2xl text-xs font-black bg-indigo-600 hover:bg-indigo-700 text-white shadow-md transition cursor-pointer flex items-center gap-2"
          >
            {simRunning ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-white" />}
            <span>Test Verify & Consume</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setSimAmount(1500);
              setSimMerchant('RazorHub Direct');
              setSimCategory('electronics');
            }}
            className="px-3 py-1.5 rounded-xl text-xs font-bold bg-muted hover:bg-border text-secondary"
          >
            Preset: ₹1,500 (Auto-Approve)
          </button>

          <button
            type="button"
            onClick={() => {
              setSimAmount(3500);
              setSimMerchant('RazorHub Direct');
              setSimCategory('electronics');
            }}
            className="px-3 py-1.5 rounded-xl text-xs font-bold bg-muted hover:bg-border text-secondary"
          >
            Preset: ₹3,500 (Confirmation Gate)
          </button>

          <button
            type="button"
            onClick={() => {
              setSimAmount(7500);
              setSimMerchant('RazorHub Direct');
              setSimCategory('electronics');
            }}
            className="px-3 py-1.5 rounded-xl text-xs font-bold bg-muted hover:bg-border text-secondary"
          >
            Preset: ₹7,500 (Limit Block)
          </button>
        </div>

        {/* Simulation Output Card */}
        {simResult && (
          <div className="p-4 rounded-2xl bg-background border border-border space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-bold text-primary uppercase tracking-wider text-[11px]">Sandbox Verification Output</span>
              <span
                className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                  simResult.decision === 'AUTO_APPROVED'
                    ? 'bg-emerald-500/15 text-emerald-600'
                    : simResult.decision === 'REQUIRES_CONFIRMATION'
                    ? 'bg-amber-500/15 text-amber-600'
                    : 'bg-rose-500/15 text-rose-600'
                }`}
              >
                {simResult.decision}
              </span>
            </div>

            <p className="text-secondary">{simResult.reason || 'Criteria verified successfully.'}</p>

            {simResult.decision === 'REQUIRES_CONFIRMATION' && (
              <div className="pt-2 flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => handleRunSimulation(true)}
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-emerald-600 text-white hover:bg-emerald-700 cursor-pointer"
                >
                  Confirm & Consume
                </button>
              </div>
            )}

            {simResult.idempotency_key && (
              <div className="text-[10px] font-mono text-secondary pt-1 border-t border-border/50 flex justify-between">
                <span>Idempotency Key: {simResult.idempotency_key}</span>
                <span>Remaining Today: ₹{simResult.remaining_today?.toLocaleString()}</span>
              </div>
            )}
          </div>
        )}

      </div>

      {/* ── CREATE AUTHORIZATION MODAL ("Allow this agent to make payments?") ── */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-3xl max-w-lg w-full p-6 sm:p-7 space-y-5 shadow-2xl animate-in fade-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto">
            
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-indigo-500" />
                <h3 className="text-sm font-black text-primary">Allow this agent to make payments?</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="text-secondary hover:text-primary text-xs font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateAuthorization} className="space-y-4 text-xs">
              
              <div>
                <label className="block text-secondary font-bold mb-1">Select Autonomous Agent</label>
                <select
                  value={selectedAgentId}
                  onChange={(e) => setSelectedAgentId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary font-medium"
                >
                  {agents.map((ag) => (
                    <option key={ag.id} value={ag.id}>
                      {ag.name} ({ag.category})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-secondary font-bold mb-1">Max Transaction (₹)</label>
                  <input
                    type="number"
                    value={maxTxAmount}
                    onChange={(e) => setMaxTxAmount(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary font-mono"
                  />
                  <p className="text-[10px] text-secondary mt-0.5">Ceiling per payment</p>
                </div>

                <div>
                  <label className="block text-secondary font-bold mb-1">Auto-Approve Threshold (₹)</label>
                  <input
                    type="number"
                    value={approvalThreshold}
                    onChange={(e) => setApprovalThreshold(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary font-mono"
                  />
                  <p className="text-[10px] text-secondary mt-0.5">Below this = auto pay</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-secondary font-bold mb-1">Daily Limit (₹)</label>
                  <input
                    type="number"
                    value={dailyLimit}
                    onChange={(e) => setDailyLimit(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary font-mono"
                  />
                </div>

                <div>
                  <label className="block text-secondary font-bold mb-1">Monthly Limit (₹)</label>
                  <input
                    type="number"
                    value={monthlyLimit}
                    onChange={(e) => setMonthlyLimit(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-secondary font-bold mb-1">Allowed Categories (comma separated)</label>
                <input
                  type="text"
                  value={allowedCategories}
                  onChange={(e) => setAllowedCategories(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary"
                />
              </div>

              <div>
                <label className="block text-secondary font-bold mb-1">Blocked Categories (comma separated)</label>
                <input
                  type="text"
                  value={blockedCategories}
                  onChange={(e) => setBlockedCategories(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary"
                />
              </div>

              <div>
                <label className="block text-secondary font-bold mb-1">Allowed Merchants (comma separated)</label>
                <input
                  type="text"
                  value={allowedMerchants}
                  onChange={(e) => setAllowedMerchants(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary"
                />
              </div>

              <div>
                <label className="block text-secondary font-bold mb-1">Expiry Duration</label>
                <select
                  value={expiryDays}
                  onChange={(e) => setExpiryDays(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary"
                >
                  <option value={7}>7 Days</option>
                  <option value={30}>30 Days</option>
                  <option value={90}>90 Days</option>
                  <option value={365}>1 Year</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-secondary hover:bg-muted"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading === 'create'}
                  className="px-5 py-2 rounded-xl text-xs font-extrabold bg-indigo-600 hover:bg-indigo-700 text-white shadow-md cursor-pointer flex items-center gap-1.5"
                >
                  {actionLoading === 'create' && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  <span>Create Authorization</span>
                </button>
              </div>

            </form>

          </div>
        </div>
      )}

      {/* ── EDIT LIMITS MODAL ── */}
      {editingAuth && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-sm font-bold text-primary">Edit Authorization Limits</h3>
              <button onClick={() => setEditingAuth(null)} className="text-secondary text-xs">✕</button>
            </div>

            <form onSubmit={handleSaveLimits} className="space-y-3 text-xs">
              <div>
                <label className="block text-secondary font-bold mb-1">Max Transaction Amount (₹)</label>
                <input
                  type="number"
                  value={editingAuth.max_transaction_amount}
                  onChange={(e) => setEditingAuth({ ...editingAuth, max_transaction_amount: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary font-mono"
                />
              </div>

              <div>
                <label className="block text-secondary font-bold mb-1">Daily Limit (₹)</label>
                <input
                  type="number"
                  value={editingAuth.daily_limit}
                  onChange={(e) => setEditingAuth({ ...editingAuth, daily_limit: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary font-mono"
                />
              </div>

              <div>
                <label className="block text-secondary font-bold mb-1">Monthly Limit (₹)</label>
                <input
                  type="number"
                  value={editingAuth.monthly_limit}
                  onChange={(e) => setEditingAuth({ ...editingAuth, monthly_limit: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary font-mono"
                />
              </div>

              <div>
                <label className="block text-secondary font-bold mb-1">Auto-Approve Threshold (₹)</label>
                <input
                  type="number"
                  value={editingAuth.approval_threshold}
                  onChange={(e) => setEditingAuth({ ...editingAuth, approval_threshold: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary font-mono"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={() => setEditingAuth(null)}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 text-white"
                >
                  Save Limits
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
