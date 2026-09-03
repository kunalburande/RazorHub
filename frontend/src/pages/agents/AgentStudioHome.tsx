import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Bot,
  Sparkles,
  Play,
  Pause,
  Plus,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  RefreshCw,
  Sliders,
  History,
  FileCode,
  Activity,
  Zap,
  CheckCircle2,
  Lock,
  Layers,
  ShoppingBag,
  CreditCard,
  Building2,
  TrendingUp,
} from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';

interface AgentListItem {
  id: string;
  name: string;
  description: string;
  status: 'DRAFT' | 'ACTIVE' | 'PAUSED' | 'DISABLED' | 'FAILED';
  approval_mode: string;
  risk_level: string;
  system_prompt?: string;
  tools?: Array<{ id: string; name: string }>;
  created_at: string;
  updated_at: string;
  metadata?: {
    category?: string;
    template_id?: string;
    automation_level?: string;
    capabilities?: string[];
  };
}

export default function AgentStudioHome() {
  const { token } = useAuth();
  const [agents, setAgents] = useState<AgentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'ALL' | 'ACTIVE' | 'PAUSED' | 'DRAFT'>('ALL');
  const [togglingId, setTogglingId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const fetchAgents = async () => {
    setLoading(true);
    try {
      const data = await apiRequest<any>('/agent-runtime/agents/', { token });
      const list = Array.isArray(data) ? data : data.results || [];
      setAgents(list);
    } catch (err: any) {
      console.error('Failed to fetch agents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, [token]);

  const handleToggleStatus = async (agent: AgentListItem) => {
    setTogglingId(agent.id);
    setFeedback(null);
    const targetAction = agent.status === 'ACTIVE' ? 'pause' : 'activate';
    try {
      await apiRequest(`/agent-runtime/agents/${agent.id}/${targetAction}/`, {
        token,
        method: 'POST',
      });
      setFeedback(`Agent '${agent.name}' is now ${targetAction === 'activate' ? 'ACTIVE' : 'PAUSED'}.`);
      setTimeout(() => setFeedback(null), 3000);
      await fetchAgents();
    } catch (err: any) {
      setFeedback(err.message || `Failed to update status`);
    } finally {
      setTogglingId(null);
    }
  };

  const filteredAgents = agents.filter((a) => {
    if (filter === 'ALL') return true;
    return a.status === filter;
  });

  const activeCount = agents.filter((a) => a.status === 'ACTIVE').length;
  const totalTools = agents.reduce((acc, a) => acc + (a.tools?.length || 0), 0);

  const getRiskBadge = (level: string) => {
    const l = level.toUpperCase();
    if (l === 'CRITICAL') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30">
          <ShieldAlert className="w-3 h-3" />
          CRITICAL
        </span>
      );
    }
    if (l === 'HIGH') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
          <AlertTriangle className="w-3 h-3" />
          HIGH
        </span>
      );
    }
    if (l === 'MEDIUM') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30">
          <ShieldCheck className="w-3 h-3" />
          MEDIUM
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
        <ShieldCheck className="w-3 h-3" />
        LOW
      </span>
    );
  };

  const getStatusPill = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            ACTIVE
          </span>
        );
      case 'PAUSED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
            <Pause className="w-3 h-3" />
            PAUSED
          </span>
        );
      case 'DRAFT':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-500/15 text-gray-600 dark:text-gray-400 border border-gray-500/30">
            DRAFT
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/15 text-rose-600 border border-rose-500/30">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-8 pb-16">
      
      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-gray-900 via-indigo-950 to-slate-900 text-white p-6 sm:p-10 shadow-2xl border border-indigo-500/20">
        <div className="absolute -right-16 -top-16 w-80 h-80 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute right-32 bottom-0 w-64 h-64 bg-cyan-500/15 rounded-full blur-2xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-indigo-500/20 border border-indigo-400/30 text-indigo-300">
              <Sparkles className="w-3.5 h-3.5" />
              Razorpay Agent Studio Architecture
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
              Autonomous Agent Studio
            </h1>
            <p className="text-sm sm:text-base text-gray-300 leading-relaxed">
              Deploy, govern, and monitor autonomous commerce agents, payment recovery pipelines, and risk sentinels. Powered by deterministic zero-trust transaction firewalls.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Link
              to="/agents/marketplace"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl text-sm font-bold bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white shadow-lg shadow-cyan-500/25 transition-all transform active:scale-95"
            >
              <ShoppingBag className="w-4 h-4" />
              Agent Marketplace
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              to="/agents/create"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl text-sm font-bold bg-white/10 hover:bg-white/15 border border-white/20 text-white backdrop-blur-md transition-all active:scale-95"
            >
              <Plus className="w-4 h-4" />
              Custom Agent Builder
            </Link>

            <Link
              to="/agents/authorizations"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl text-sm font-bold bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 text-emerald-300 backdrop-blur-md transition-all active:scale-95"
            >
              <ShieldCheck className="w-4 h-4" />
              Payment Authorizations
            </Link>
          </div>
        </div>


        {/* Live Metrics Ribbon */}
        <div className="mt-8 pt-6 border-t border-white/10 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="space-y-1">
            <span className="text-xs text-gray-400 font-medium">Configured Agents</span>
            <p className="text-2xl font-black text-white">{agents.length}</p>
          </div>
          <div className="space-y-1">
            <span className="text-xs text-gray-400 font-medium">Active Autonomous Agents</span>
            <p className="text-2xl font-black text-emerald-400">{activeCount}</p>
          </div>
          <div className="space-y-1">
            <span className="text-xs text-gray-400 font-medium">MCP Connected Tools</span>
            <p className="text-2xl font-black text-cyan-300">{totalTools}</p>
          </div>
          <div className="space-y-1">
            <span className="text-xs text-gray-400 font-medium">Governance Policy</span>
            <p className="text-2xl font-black text-indigo-300 flex items-center gap-1.5">
              <Lock className="w-4 h-4 text-emerald-400" />
              Zero-Trust
            </p>
          </div>
        </div>
      </div>

      {/* Feedback Alert */}
      {feedback && (
        <div className="p-4 rounded-2xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 text-indigo-800 dark:text-indigo-200 text-sm flex items-center justify-between animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-indigo-600" />
            <span>{feedback}</span>
          </div>
          <button onClick={() => setFeedback(null)} className="text-xs font-bold hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Controls & Filter Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-1 p-1 bg-gray-100 dark:bg-gray-800/80 rounded-2xl border border-gray-200 dark:border-gray-700 w-fit">
          {(['ALL', 'ACTIVE', 'PAUSED', 'DRAFT'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer ${
                filter === tab
                  ? 'bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 shadow-sm'
                  : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              {tab === 'ALL' ? `All Agents (${agents.length})` : tab}
            </button>
          ))}
        </div>

        <button
          onClick={fetchAgents}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-surface border border-border text-secondary hover:text-primary transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Registry
        </button>
      </div>

      {/* Agent Cards Grid */}
      {loading && agents.length === 0 ? (
        <div className="py-24 text-center space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin text-indigo-500 mx-auto" />
          <p className="text-sm text-secondary">Loading agent studio configurations...</p>
        </div>
      ) : filteredAgents.length === 0 ? (
        <div className="py-16 text-center rounded-3xl border border-dashed border-gray-300 dark:border-gray-800 p-8 space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 mx-auto flex items-center justify-center">
            <Bot className="w-7 h-7" />
          </div>
          <div className="max-w-md mx-auto space-y-1">
            <h3 className="text-base font-bold text-primary">No Agents in View</h3>
            <p className="text-xs text-secondary">
              {filter === 'ALL'
                ? 'Get started by deploying prebuilt commerce agents from the marketplace or assembling a custom agent.'
                : `There are currently no agents with status '${filter}'.`}
            </p>
          </div>
          <div className="flex items-center justify-center gap-3 pt-2">
            <Link
              to="/agents/marketplace"
              className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow transition"
            >
              Browse Marketplace
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAgents.map((agent) => {
            const isToggling = togglingId === agent.id;
            return (
              <div
                key={agent.id}
                className="group relative rounded-3xl border border-border/80 bg-surface hover:border-indigo-500/50 hover:shadow-xl transition-all duration-300 flex flex-col justify-between p-6"
              >
                <div>
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="p-3 rounded-2xl bg-gradient-to-br from-indigo-500/10 to-cyan-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 group-hover:scale-105 transition-transform">
                      <Bot className="w-6 h-6" />
                    </div>
                    <div className="flex items-center gap-2">
                      {getRiskBadge(agent.risk_level)}
                      {getStatusPill(agent.status)}
                    </div>
                  </div>

                  {/* Title & Description */}
                  <h3 className="text-lg font-bold text-primary group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                    {agent.name}
                  </h3>
                  <p className="mt-1.5 text-xs text-secondary line-clamp-2 leading-relaxed">
                    {agent.description}
                  </p>

                  {/* Badges / Specs */}
                  <div className="mt-4 pt-4 border-t border-border/60 grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-secondary text-[11px] block">Approval Mode</span>
                      <span className="font-semibold text-primary">{agent.approval_mode}</span>
                    </div>
                    <div>
                      <span className="text-secondary text-[11px] block">Connected Tools</span>
                      <span className="font-semibold text-primary">
                        {agent.tools?.length || 0} Tools
                      </span>
                    </div>
                  </div>

                  {/* Capabilities Preview */}
                  {agent.metadata?.capabilities && agent.metadata.capabilities.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {agent.metadata.capabilities.slice(0, 2).map((cap, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-muted text-secondary"
                        >
                          {cap}
                        </span>
                      ))}
                      {agent.metadata.capabilities.length > 2 && (
                        <span className="px-1.5 py-0.5 rounded-md text-[10px] text-secondary">
                          +{agent.metadata.capabilities.length - 2} more
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Footer Controls */}
                <div className="mt-6 pt-4 border-t border-border flex items-center justify-between gap-2">
                  <button
                    type="button"
                    disabled={isToggling}
                    onClick={() => handleToggleStatus(agent)}
                    title={agent.status === 'ACTIVE' ? 'Pause Agent' : 'Activate Agent'}
                    className={`p-2 rounded-xl border text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
                      agent.status === 'ACTIVE'
                        ? 'border-amber-500/30 text-amber-600 hover:bg-amber-500/10'
                        : 'border-emerald-500/30 text-emerald-600 hover:bg-emerald-500/10'
                    }`}
                  >
                    {isToggling ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : agent.status === 'ACTIVE' ? (
                      <>
                        <Pause className="w-3.5 h-3.5" />
                        <span>Pause</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-3.5 h-3.5" />
                        <span>Activate</span>
                      </>
                    )}
                  </button>

                  <div className="flex items-center gap-1.5">
                    {agent.name.toLowerCase().includes('refund') && (
                      <Link
                        to="/agents/refund-spike-analyzer"
                        title="Live Refund Spike Surveillance Dashboard"
                        className="px-2.5 py-2 rounded-xl text-xs font-bold border border-rose-500/30 bg-rose-500/10 text-rose-600 dark:text-rose-400 hover:bg-rose-500/20 transition flex items-center gap-1.5"
                      >
                        <TrendingUp className="w-3.5 h-3.5" />
                        <span className="hidden sm:inline">Surveillance</span>
                      </Link>
                    )}

                    <Link
                      to={`/agents/${agent.id}/configuration`}
                      title="Configuration & Guardrails"
                      className="p-2 rounded-xl text-secondary hover:text-primary hover:bg-muted transition"
                    >
                      <Sliders className="w-4 h-4" />
                    </Link>


                    <Link
                      to={`/agents/${agent.id}/executions`}
                      title="Execution Traces"
                      className="p-2 rounded-xl text-secondary hover:text-primary hover:bg-muted transition"
                    >
                      <History className="w-4 h-4" />
                    </Link>

                    <Link
                      to={`/agents/${agent.id}`}
                      className="px-3.5 py-2 rounded-xl text-xs font-bold bg-primary text-surface hover:opacity-90 transition flex items-center gap-1.5"
                    >
                      <span>Command Center</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>

              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}
