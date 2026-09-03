import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Bot,
  Zap,
  Activity,
  ExternalLink,
  ArrowRight,
  Play,
  Pause,
  Settings,
  Eye,
  Plus,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Clock,
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
  created_at: string;
  updated_at: string;
  metadata?: {
    category?: string;
    capabilities?: string[];
  };
}

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  ACTIVE: {
    label: 'Active',
    color: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30',
    icon: <CheckCircle2 className="w-3.5 h-3.5" />,
  },
  PAUSED: {
    label: 'Paused',
    color: 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30',
    icon: <Pause className="w-3.5 h-3.5" />,
  },
  DRAFT: {
    label: 'Draft',
    color: 'bg-gray-200 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-700',
    icon: <Clock className="w-3.5 h-3.5" />,
  },
  DISABLED: {
    label: 'Disabled',
    color: 'bg-gray-200 dark:bg-gray-800 text-gray-500 dark:text-gray-500 border-gray-300 dark:border-gray-700',
    icon: <Pause className="w-3.5 h-3.5" />,
  },
  FAILED: {
    label: 'Failed',
    color: 'bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30',
    icon: <AlertTriangle className="w-3.5 h-3.5" />,
  },
};

const RISK_COLOR: Record<string, string> = {
  LOW: 'text-emerald-600 dark:text-emerald-400',
  MEDIUM: 'text-amber-500 dark:text-amber-400',
  HIGH: 'text-orange-500 dark:text-orange-400',
  CRITICAL: 'text-rose-600 dark:text-rose-400',
};

export default function AgentsBridge() {
  const { token } = useAuth();
  const [agents, setAgents] = useState<AgentListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const data = await apiRequest<any>('/agent-runtime/agents/', { token });
        const list = Array.isArray(data) ? data : data.results || [];
        setAgents(list);
      } catch (err) {
        console.error('Failed to fetch agents:', err);
      } finally {
        setLoading(false);
      }
    })();
  }, [token]);

  const activeCount = agents.filter((a) => a.status === 'ACTIVE').length;
  const pausedCount = agents.filter((a) => a.status === 'PAUSED').length;
  const draftCount = agents.filter((a) => a.status === 'DRAFT').length;

  return (
    <div className="min-h-[85vh] bg-gradient-to-br from-white via-gray-50 to-white dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 rounded-3xl p-6 sm:p-8 border border-gray-200 dark:border-gray-800 shadow-2xl space-y-8 transition-colors duration-300">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-6">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/10 px-3 py-1 text-xs font-bold text-indigo-600 dark:text-indigo-400">
            <Bot className="h-3.5 w-3.5" />
            <span>AI Agent Fleet</span>
          </div>
          <h1 className="text-3xl font-black tracking-tight text-gray-900 dark:text-white">
            Your Agents
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 max-w-xl">
            Autonomous agents running on your behalf. Monitor and manage them here, or open the full Agent Studio for advanced controls.
          </p>
        </div>

        <Link
          to="/agents"
          className="flex-shrink-0 flex items-center gap-2 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:opacity-90 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-500/20 transition-all active:scale-95"
        >
          <Zap className="h-4 w-4" />
          Open Agent Studio
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>

      {/* Summary KPIs */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Active', value: activeCount, color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
          { label: 'Paused', value: pausedCount, color: 'text-amber-500', bg: 'bg-amber-500/10 border-amber-500/20' },
          { label: 'Draft', value: draftCount, color: 'text-gray-500 dark:text-gray-400', bg: 'bg-gray-100 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700' },
        ].map((stat) => (
          <div key={stat.label} className={`rounded-2xl border p-4 ${stat.bg}`}>
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400">{stat.label}</p>
            <p className={`text-3xl font-black mt-1 ${stat.color}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Agent Cards */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-100 dark:bg-gray-900 h-48" />
          ))}
        </div>
      ) : agents.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 p-12 text-center">
          <Bot className="h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-base font-bold text-gray-900 dark:text-white">No agents yet</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 max-w-sm">
            Create your first autonomous agent in the Agent Studio to automate payments, collections, and more.
          </p>
          <Link
            to="/agents/create"
            className="mt-6 flex items-center gap-2 rounded-2xl bg-indigo-600 hover:bg-indigo-700 px-5 py-2.5 text-sm font-bold text-white transition-all active:scale-95"
          >
            <Plus className="h-4 w-4" />
            Create First Agent
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {agents.map((agent) => {
            const sc = STATUS_CONFIG[agent.status] ?? STATUS_CONFIG.DRAFT;
            const riskColor = RISK_COLOR[agent.risk_level] ?? 'text-gray-500';
            return (
              <div
                key={agent.id}
                className="group flex flex-col rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/60 hover:bg-white dark:hover:bg-gray-800/80 hover:border-indigo-200 dark:hover:border-gray-700 hover:shadow-[0_0_24px_rgba(99,102,241,0.12)] p-6 transition-all duration-300"
              >
                {/* Agent header row */}
                <div className="flex items-start justify-between gap-3 mb-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/10 border border-indigo-500/20">
                      <Bot className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-gray-900 dark:text-white leading-tight line-clamp-1 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                        {agent.name}
                      </h3>
                      <span className={`text-[10px] font-bold uppercase tracking-wider ${riskColor}`}>
                        {agent.risk_level} RISK
                      </span>
                    </div>
                  </div>
                  <span className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-bold border ${sc.color}`}>
                    {sc.icon}
                    {sc.label}
                  </span>
                </div>

                {/* Description */}
                <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed line-clamp-2 flex-1 mb-5">
                  {agent.description || 'No description provided.'}
                </p>

                {/* Metadata */}
                <div className="flex items-center justify-between text-[10px] text-gray-400 dark:text-gray-500 mb-4">
                  <div className="flex items-center gap-1">
                    <ShieldCheck className="h-3 w-3" />
                    <span>{agent.approval_mode?.replace('_', ' ')}</span>
                  </div>
                  {agent.metadata?.category && (
                    <span className="px-2 py-0.5 rounded-md bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide">
                      {agent.metadata.category}
                    </span>
                  )}
                </div>

                {/* Action row */}
                <div className="flex gap-2 pt-3 border-t border-gray-200 dark:border-gray-800">
                  <Link
                    to={`/agents/${agent.id}/executions`}
                    className="flex-1 flex items-center justify-center gap-1.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-xs font-bold text-gray-700 dark:text-gray-300 py-2 transition-colors"
                  >
                    <Activity className="h-3.5 w-3.5" />
                    Executions
                  </Link>
                  <Link
                    to={`/agents/${agent.id}/configuration`}
                    className="flex-1 flex items-center justify-center gap-1.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-xs font-bold text-gray-700 dark:text-gray-300 py-2 transition-colors"
                  >
                    <Settings className="h-3.5 w-3.5" />
                    Configure
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Quick Links */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
        {[
          { label: 'Build a New Agent', desc: 'Visual + conversational builder', href: '/agents/create', icon: Plus, cls: 'border-indigo-200 dark:border-indigo-900/40 bg-indigo-50 dark:bg-indigo-950/20 text-indigo-700 dark:text-indigo-400 hover:border-indigo-300' },
          { label: 'All Executions', desc: 'Timeline, replay, observability', href: '/agents/executions', icon: Eye, cls: 'border-purple-200 dark:border-purple-900/40 bg-purple-50 dark:bg-purple-950/20 text-purple-700 dark:text-purple-400 hover:border-purple-300' },
          { label: 'Agent Marketplace', desc: 'Pre-built agent templates', href: '/agents/marketplace', icon: Zap, cls: 'border-sky-200 dark:border-sky-900/40 bg-sky-50 dark:bg-sky-950/20 text-sky-700 dark:text-sky-400 hover:border-sky-300' },
        ].map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              to={item.href}
              className={`flex items-center gap-4 rounded-2xl border p-4 transition-all hover:shadow-sm ${item.cls}`}
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/60 dark:bg-gray-900/60 shadow-xs">
                <Icon className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-bold">{item.label}</p>
                <p className="text-xs opacity-70 truncate">{item.desc}</p>
              </div>
              <ExternalLink className="h-4 w-4 ml-auto shrink-0 opacity-50" />
            </Link>
          );
        })}
      </div>
    </div>
  );
}
