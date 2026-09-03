import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Bot,
  Sparkles,
  ArrowLeft,
  Play,
  Pause,
  Sliders,
  History,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  Wrench,
  Zap,
  Lock,
  Clock,
  CheckCircle2,
  XCircle,
  FileText,
  Activity,
  Send,
  AlertCircle,
  Layers,
  ChevronRight,
  UserCheck,
  Building2,
} from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';

export default function AgentDetails() {
  const { id } = useParams<{ id: string }>();
  const { token } = useAuth();

  const [agent, setAgent] = useState<any | null>(null);
  const [executions, setExecutions] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    'overview' | 'capabilities' | 'tools' | 'triggers' | 'guardrails' | 'executions' | 'performance' | 'activity'
  >('overview');

  // Interactive Playground State
  const [promptText, setPromptText] = useState('');
  const [runningPrompt, setRunningPrompt] = useState(false);
  const [executionResult, setExecutionResult] = useState<any | null>(null);
  const [promptError, setPromptError] = useState<string | null>(null);

  // Status toggle
  const [togglingStatus, setTogglingStatus] = useState(false);

  const fetchAgentData = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [agentRes, execRes, auditRes] = await Promise.all([
        apiRequest<any>(`/agent-runtime/agents/${id}/`, { token }),
        apiRequest<any>(`/agent-runtime/executions/?agent=${id}`, { token }).catch(() => []),
        apiRequest<any>(`/agent-runtime/audit-logs/?agent=${id}`, { token }).catch(() => []),
      ]);

      setAgent(agentRes);
      setExecutions(Array.isArray(execRes) ? execRes : execRes.results || []);
      setAuditLogs(Array.isArray(auditRes) ? auditRes : auditRes.results || []);
    } catch (err) {
      console.error('Failed to load agent details:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgentData();
  }, [id, token]);

  const handleToggleStatus = async () => {
    if (!agent) return;
    setTogglingStatus(true);
    const targetAction = agent.status === 'ACTIVE' ? 'pause' : 'activate';
    try {
      await apiRequest(`/agent-runtime/agents/${agent.id}/${targetAction}/`, {
        token,
        method: 'POST',
      });
      await fetchAgentData();
    } catch (err) {
      console.error('Failed to toggle status:', err);
    } finally {
      setTogglingStatus(false);
    }
  };

  const handleRunPrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!promptText.trim() || !agent) return;

    setRunningPrompt(true);
    setPromptError(null);
    setExecutionResult(null);

    try {
      const res = await apiRequest<any>(`/agent-runtime/agents/${agent.id}/execute/`, {
        token,
        method: 'POST',
        body: JSON.stringify({ request: promptText.trim() }),
      });
      setExecutionResult(res);
      // Refresh execution history
      const updatedExecs = await apiRequest<any>(`/agent-runtime/executions/?agent=${id}`, { token }).catch(() => []);
      setExecutions(Array.isArray(updatedExecs) ? updatedExecs : updatedExecs.results || []);
    } catch (err: any) {
      setPromptError(err.message || 'Execution failed.');
    } finally {
      setRunningPrompt(false);
    }
  };

  if (loading && !agent) {
    return (
      <div className="py-24 text-center space-y-3">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-500 mx-auto" />
        <p className="text-sm text-secondary">Loading Agent Command Center...</p>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="py-20 text-center space-y-4">
        <h2 className="text-lg font-bold text-primary">Agent Not Found</h2>
        <Link to="/agents" className="text-xs text-indigo-600 underline font-semibold">
          ← Return to Agent Studio
        </Link>
      </div>
    );
  }

  const capabilities = agent.metadata?.capabilities || [
    'Autonomous transaction analysis',
    'MCP tool routing and parameter validation',
    'Deterministic governance policy compliance',
  ];

  const govPolicy = agent.governance_policy || {};
  const completedExecutions = executions.filter((e) => e.status === 'COMPLETED').length;
  const successRate = executions.length > 0 ? Math.round((completedExecutions / executions.length) * 100) : 100;

  return (
    <div className="space-y-8 pb-16">
      
      {/* Top Header Card */}
      <div className="p-6 sm:p-8 rounded-3xl border border-border/80 bg-surface shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="p-3.5 rounded-2xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 shrink-0">
              <Bot className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl font-black text-primary tracking-tight">{agent.name}</h1>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 border border-indigo-500/30">
                  {agent.metadata?.category || 'COMMERCE'}
                </span>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${
                    agent.status === 'ACTIVE'
                      ? 'bg-emerald-500/15 text-emerald-600 border-emerald-500/30'
                      : 'bg-amber-500/15 text-amber-600 border-amber-500/30'
                  }`}
                >
                  {agent.status}
                </span>
              </div>
              <p className="text-xs sm:text-sm text-secondary max-w-2xl">{agent.description}</p>
            </div>
          </div>

          {/* Quick Action Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              disabled={togglingStatus}
              onClick={handleToggleStatus}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer ${
                agent.status === 'ACTIVE'
                  ? 'border border-amber-500/40 text-amber-600 hover:bg-amber-500/10'
                  : 'bg-emerald-600 text-white hover:bg-emerald-700'
              }`}
            >
              {togglingStatus ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : agent.status === 'ACTIVE' ? (
                <>
                  <Pause className="w-3.5 h-3.5" />
                  <span>Pause Agent</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5" />
                  <span>Activate Agent</span>
                </>
              )}
            </button>

            <Link
              to={`/agents/${agent.id}/configuration`}
              className="px-4 py-2 rounded-xl border border-border text-xs font-bold text-secondary hover:text-primary hover:bg-muted transition flex items-center gap-1.5"
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>Configure</span>
            </Link>

            <Link
              to={`/agents/${agent.id}/executions`}
              className="px-4 py-2 rounded-xl border border-border text-xs font-bold text-secondary hover:text-primary hover:bg-muted transition flex items-center gap-1.5"
            >
              <History className="w-3.5 h-3.5" />
              <span>Traces ({executions.length})</span>
            </Link>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="pt-4 border-t border-border flex items-center gap-1 overflow-x-auto scrollbar-none">
          {[
            { id: 'overview', label: 'Overview & Playground' },
            { id: 'capabilities', label: 'Capabilities' },
            { id: 'tools', label: `Tools (${agent.tools?.length || 0})` },
            { id: 'triggers', label: `Triggers (${agent.triggers?.length || 0})` },
            { id: 'guardrails', label: 'Guardrails & Policy' },
            { id: 'executions', label: `Executions (${executions.length})` },
            { id: 'performance', label: 'Performance' },
            { id: 'activity', label: `Activity Log (${auditLogs.length})` },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                activeTab === tab.id
                  ? 'bg-primary text-surface shadow-xs'
                  : 'text-secondary hover:text-primary hover:bg-muted'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* TAB CONTENT */}

      {/* 1. OVERVIEW & PLAYGROUND */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* KPI Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl border border-border bg-surface shadow-xs space-y-1">
              <span className="text-xs text-secondary font-medium">Total Executions</span>
              <p className="text-2xl font-black text-primary">{executions.length}</p>
            </div>
            <div className="p-5 rounded-2xl border border-border bg-surface shadow-xs space-y-1">
              <span className="text-xs text-secondary font-medium">Success Rate</span>
              <p className="text-2xl font-black text-emerald-500">{successRate}%</p>
            </div>
            <div className="p-5 rounded-2xl border border-border bg-surface shadow-xs space-y-1">
              <span className="text-xs text-secondary font-medium">Approval Mode</span>
              <p className="text-base font-bold text-primary mt-1">{agent.approval_mode}</p>
            </div>
            <div className="p-5 rounded-2xl border border-border bg-surface shadow-xs space-y-1">
              <span className="text-xs text-secondary font-medium">Risk Level</span>
              <p className="text-base font-bold text-indigo-600 dark:text-indigo-400 mt-1">{agent.risk_level}</p>
            </div>
          </div>

          {/* Interactive Playground */}
          <div className="p-6 rounded-3xl border border-border bg-surface shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-primary flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-500" />
                  Interactive Prompt Playground
                </h3>
                <p className="text-xs text-secondary">
                  Execute test runs directly against this agent. The runtime orchestrates intent parsing, context gathering, and MCP tools with zero-trust governance.
                </p>
              </div>
            </div>

            <form onSubmit={handleRunPrompt} className="space-y-3">
              <div className="relative">
                <input
                  type="text"
                  value={promptText}
                  onChange={(e) => setPromptText(e.target.value)}
                  placeholder="e.g. Check overdue invoices and prepare a payment link for customer..."
                  className="w-full pl-4 pr-28 py-3 rounded-2xl border border-border bg-background text-primary text-xs sm:text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                />
                <button
                  type="submit"
                  disabled={runningPrompt || !promptText.trim()}
                  className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
                >
                  {runningPrompt ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Send className="w-3.5 h-3.5" />
                  )}
                  Run
                </button>
              </div>
            </form>

            {promptError && (
              <div className="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
                <span>{promptError}</span>
              </div>
            )}

            {executionResult && (
              <div className="mt-4 p-5 rounded-2xl bg-gray-50 dark:bg-gray-900/80 border border-border space-y-3 animate-in fade-in">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    Execution {executionResult.status} ({executionResult.execution_id?.slice(0, 8)})
                  </span>
                  <span className="text-[11px] font-mono text-secondary">
                    {executionResult.steps?.length || 0} Steps Executed
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-surface border border-border text-xs text-primary leading-relaxed">
                  {executionResult.output_response || 'Execution completed.'}
                </div>

                {executionResult.execution_trace && executionResult.execution_trace.length > 0 && (
                  <div className="space-y-1.5 pt-2">
                    <span className="text-[11px] font-bold text-secondary uppercase tracking-wider block">
                      Execution Trace Timeline
                    </span>
                    <div className="space-y-1 max-h-40 overflow-y-auto font-mono text-[11px] bg-black/40 text-gray-300 p-2.5 rounded-xl">
                      {executionResult.execution_trace.map((item: any, idx: number) => (
                        <div key={idx} className="flex items-start gap-2">
                          <span className="text-cyan-400">[{item.timestamp?.slice(11, 19) || 'TRACE'}]</span>
                          <span className="font-semibold text-white">{item.stage || item.event}:</span>
                          <span>{item.message}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 2. CAPABILITIES */}
      {activeTab === 'capabilities' && (
        <div className="p-6 rounded-3xl border border-border bg-surface shadow-xs space-y-4">
          <h3 className="text-base font-bold text-primary">Autonomous Capabilities</h3>
          <p className="text-xs text-secondary">
            Authorized tasks this agent is certified to execute within RazorHub.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            {capabilities.map((cap: string, idx: number) => (
              <div
                key={idx}
                className="p-4 rounded-2xl border border-border bg-background flex items-start gap-3"
              >
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                <span className="text-xs text-primary font-medium">{cap}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. TOOLS */}
      {activeTab === 'tools' && (
        <div className="p-6 rounded-3xl border border-border bg-surface shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-primary">Connected MCP Tools</h3>
              <p className="text-xs text-secondary">
                Tools available to this agent via the Model Context Protocol registry.
              </p>
            </div>
            <Link
              to={`/agents/${agent.id}/configuration`}
              className="text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              Edit Tools →
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            {agent.tools && agent.tools.length > 0 ? (
              agent.tools.map((tool: any) => (
                <div
                  key={tool.id}
                  className="p-4 rounded-2xl border border-border bg-background space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs font-mono text-primary">{tool.name}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-muted text-secondary uppercase">
                      {tool.category}
                    </span>
                  </div>
                  <p className="text-[11px] text-secondary leading-relaxed">{tool.description}</p>
                </div>
              ))
            ) : (
              <div className="text-xs text-secondary col-span-2 py-8 text-center">
                No tools attached yet. Connect tools in Configuration.
              </div>
            )}
          </div>
        </div>
      )}

      {/* 4. TRIGGERS */}
      {activeTab === 'triggers' && (
        <div className="p-6 rounded-3xl border border-border bg-surface shadow-xs space-y-4">
          <h3 className="text-base font-bold text-primary">Configured Triggers</h3>
          <p className="text-xs text-secondary">
            Events and schedules that awaken this agent.
          </p>
          <div className="space-y-2 pt-2">
            {agent.triggers && agent.triggers.length > 0 ? (
              agent.triggers.map((trig: any) => (
                <div
                  key={trig.id}
                  className="p-4 rounded-2xl border border-border bg-background flex items-center justify-between"
                >
                  <div>
                    <span className="font-bold text-xs text-primary">{trig.name}</span>
                    <span className="text-[11px] text-secondary block">{trig.trigger_type}</span>
                  </div>
                  <span className="px-2 py-1 rounded-lg text-xs font-mono bg-muted text-secondary">
                    {JSON.stringify(trig.config || {})}
                  </span>
                </div>
              ))
            ) : (
              <div className="p-4 rounded-2xl border border-border bg-background flex items-center justify-between">
                <div>
                  <span className="font-bold text-xs text-primary">Interactive Request Trigger</span>
                  <span className="text-[11px] text-secondary block">USER_REQUEST</span>
                </div>
                <span className="px-2 py-1 rounded-lg text-xs font-mono bg-muted text-secondary">
                  Manual Invocation
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 5. GUARDRAILS & POLICY */}
      {activeTab === 'guardrails' && (
        <div className="p-6 rounded-3xl border border-border bg-surface shadow-xs space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-primary flex items-center gap-2">
                <Lock className="w-4 h-4 text-indigo-500" />
                Deterministic Governance Firewall
              </h3>
              <p className="text-xs text-secondary">
                Spending limits and security constraints enforced on every transaction attempt.
              </p>
            </div>
            <Link
              to={`/agents/${agent.id}/configuration`}
              className="text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              Edit Policies →
            </Link>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl bg-background border border-border space-y-1">
              <span className="text-[11px] text-secondary block">Max Single Transaction</span>
              <span className="text-base font-bold font-mono text-primary">
                ₹{govPolicy.max_transaction_amount || '5,000.00'}
              </span>
            </div>
            <div className="p-4 rounded-2xl bg-background border border-border space-y-1">
              <span className="text-[11px] text-secondary block">Daily Spend Velocity</span>
              <span className="text-base font-bold font-mono text-primary">
                ₹{govPolicy.daily_spend_limit || '10,000.00'}
              </span>
            </div>
            <div className="p-4 rounded-2xl bg-background border border-border space-y-1">
              <span className="text-[11px] text-secondary block">Approval Above</span>
              <span className="text-base font-bold font-mono text-primary">
                ₹{govPolicy.require_approval_above || '2,000.00'}
              </span>
            </div>
            <div className="p-4 rounded-2xl bg-background border border-border space-y-1">
              <span className="text-[11px] text-secondary block">Double Confirmation</span>
              <span className="text-xs font-bold text-primary mt-1 block">
                {govPolicy.require_double_confirmation ? 'Enforced' : 'Disabled'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 6. EXECUTIONS */}
      {activeTab === 'executions' && (
        <div className="p-6 rounded-3xl border border-border bg-surface shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-primary">Recent Executions</h3>
            <Link
              to={`/agents/${agent.id}/executions`}
              className="text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              View Full Execution Log →
            </Link>
          </div>

          <div className="space-y-2">
            {executions.slice(0, 5).map((ex) => (
              <div
                key={ex.execution_id}
                className="p-3.5 rounded-xl border border-border bg-background flex items-center justify-between text-xs"
              >
                <div>
                  <span className="font-bold text-primary">{ex.initial_request || 'Triggered Action'}</span>
                  <span className="text-[11px] text-secondary block">
                    {new Date(ex.started_at).toLocaleString()}
                  </span>
                </div>
                <span
                  className={`px-2.5 py-1 rounded-full text-xs font-bold border ${
                    ex.status === 'COMPLETED'
                      ? 'bg-emerald-500/15 text-emerald-600 border-emerald-500/30'
                      : 'bg-amber-500/15 text-amber-600 border-amber-500/30'
                  }`}
                >
                  {ex.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 7. PERFORMANCE */}
      {activeTab === 'performance' && (
        <div className="p-6 rounded-3xl border border-border bg-surface shadow-xs space-y-4">
          <h3 className="text-base font-bold text-primary">Performance & Reliability</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div className="p-4 rounded-2xl bg-background border border-border space-y-1">
              <span className="text-xs text-secondary">Success Rate</span>
              <p className="text-xl font-black text-emerald-500">{successRate}%</p>
            </div>
            <div className="p-4 rounded-2xl bg-background border border-border space-y-1">
              <span className="text-xs text-secondary">Total Managed Actions</span>
              <p className="text-xl font-black text-primary">{executions.length}</p>
            </div>
            <div className="p-4 rounded-2xl bg-background border border-border space-y-1">
              <span className="text-xs text-secondary">System Health</span>
              <p className="text-xl font-black text-cyan-500">100% Operational</p>
            </div>
          </div>
        </div>
      )}

      {/* 8. ACTIVITY LOG */}
      {activeTab === 'activity' && (
        <div className="p-6 rounded-3xl border border-border bg-surface shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-primary">Activity & Audit Trail</h3>
            <Link
              to={`/agents/${agent.id}/audit`}
              className="text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              View Full Forensic Trail →
            </Link>
          </div>

          <div className="space-y-2">
            {auditLogs.slice(0, 6).map((log) => (
              <div
                key={log.id}
                className="p-3 rounded-xl border border-border bg-background text-xs flex items-center justify-between"
              >
                <div>
                  <span className="font-bold text-primary">{log.event_type}</span>
                  <span className="text-[11px] text-secondary block font-mono">
                    {new Date(log.created_at).toLocaleString()}
                  </span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-muted text-secondary">
                  {log.severity}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
