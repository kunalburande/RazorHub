import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  History,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  RefreshCw,
  Search,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  FileCode,
  ShieldAlert,
} from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';

export default function AgentExecutionsPage() {
  const { id } = useParams<{ id: string }>();
  const { token } = useAuth();

  const [agentName, setAgentName] = useState<string>('');
  const [executions, setExecutions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [expandedExecId, setExpandedExecId] = useState<string | null>(null);

  const fetchExecutions = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [agentRes, execRes] = await Promise.all([
        apiRequest<any>(`/agent-runtime/agents/${id}/`, { token }).catch(() => null),
        apiRequest<any>(`/agent-runtime/executions/?agent=${id}`, { token }),
      ]);

      if (agentRes) setAgentName(agentRes.name);
      setExecutions(Array.isArray(execRes) ? execRes : execRes.results || []);
    } catch (err) {
      console.error('Failed to load executions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExecutions();
  }, [id, token]);

  const filtered = executions.filter((e) => {
    if (statusFilter === 'ALL') return true;
    return e.status === statusFilter;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3 h-3" />
            COMPLETED
          </span>
        );
      case 'WAITING_APPROVAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
            <Clock className="w-3 h-3 animate-pulse" />
            WAITING APPROVAL
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-500/15 text-gray-600 dark:text-gray-400 border border-gray-500/30">
            CANCELLED
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30">
            <XCircle className="w-3 h-3" />
            FAILED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/15 text-blue-600 border border-blue-500/30">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-16">
      
      {/* Top Header */}
      <div>
        <Link
          to={`/agents/${id}`}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-secondary hover:text-primary transition mb-1"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to {agentName || 'Agent'} Command Center
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl sm:text-3xl font-black text-primary tracking-tight">
              Execution History & Traces
            </h1>
            <p className="text-xs sm:text-sm text-secondary">
              Chronological log of natural language prompts, planning phases, tool invocations, and firewall checkpoints.
            </p>
          </div>

          <button
            onClick={fetchExecutions}
            disabled={loading}
            className="p-2.5 rounded-xl border border-border hover:bg-muted text-secondary hover:text-primary transition cursor-pointer"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
        {['ALL', 'COMPLETED', 'WAITING_APPROVAL', 'CANCELLED', 'FAILED'].map((st) => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${
              statusFilter === st
                ? 'bg-primary text-surface shadow-xs'
                : 'bg-surface border border-border text-secondary hover:text-primary'
            }`}
          >
            {st}
          </button>
        ))}
      </div>

      {/* Execution List */}
      {loading && executions.length === 0 ? (
        <div className="py-24 text-center space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin text-indigo-500 mx-auto" />
          <p className="text-sm text-secondary">Loading execution traces...</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="py-20 text-center rounded-3xl border border-dashed border-border p-8 space-y-3">
          <History className="w-8 h-8 text-gray-400 mx-auto" />
          <h3 className="text-base font-bold text-primary">No Executions Found</h3>
          <p className="text-xs text-secondary">
            {statusFilter === 'ALL'
              ? 'This agent has not executed any tasks yet. Test it in the Command Center playground.'
              : `No executions found matching filter '${statusFilter}'.`}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((ex) => {
            const isExpanded = expandedExecId === ex.execution_id;
            return (
              <div
                key={ex.execution_id}
                className="rounded-3xl border border-border/80 bg-surface shadow-xs overflow-hidden transition-all duration-200"
              >
                {/* Row Summary */}
                <div
                  onClick={() => setExpandedExecId(isExpanded ? null : ex.execution_id)}
                  className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer hover:bg-muted/30 transition"
                >
                  <div className="space-y-1 max-w-xl">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-secondary">
                        ID: {ex.execution_id?.slice(0, 8)}...
                      </span>
                      {getStatusBadge(ex.status)}
                    </div>
                    <h3 className="text-sm font-bold text-primary">{ex.initial_request}</h3>
                    <div className="flex items-center gap-3 text-[11px] text-secondary">
                      <span>Started: {new Date(ex.started_at).toLocaleString()}</span>
                      {ex.completed_at && (
                        <span>
                          Completed: {new Date(ex.completed_at).toLocaleTimeString()}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-3 self-end sm:self-center">
                    <span className="text-xs font-mono text-secondary">
                      {ex.steps?.length || 0} Steps
                    </span>
                    <button
                      type="button"
                      className="p-1 rounded-lg text-secondary hover:text-primary transition"
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Expanded Trace Inspector */}
                {isExpanded && (
                  <div className="p-6 border-t border-border bg-gray-50/70 dark:bg-gray-900/60 space-y-5 animate-in fade-in">
                    
                    {/* Final Output */}
                    <div className="space-y-1.5">
                      <span className="text-xs font-bold text-primary uppercase tracking-wider block">
                        Final Output Response
                      </span>
                      <div className="p-4 rounded-2xl bg-surface border border-border text-xs sm:text-sm text-primary leading-relaxed">
                        {ex.output_response || 'No final response output recorded.'}
                      </div>
                    </div>

                    {/* Steps Detail */}
                    {ex.steps && ex.steps.length > 0 && (
                      <div className="space-y-2">
                        <span className="text-xs font-bold text-primary uppercase tracking-wider block">
                          Execution Steps ({ex.steps.length})
                        </span>
                        <div className="space-y-2">
                          {ex.steps.map((st: any, idx: number) => (
                            <div
                              key={st.id || idx}
                              className="p-3.5 rounded-xl border border-border bg-surface text-xs space-y-2"
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-bold text-primary">
                                  Step {st.step_number}: {st.step_type}
                                </span>
                                <span className="font-mono text-[10px] text-secondary">
                                  {st.duration_ms ? `${st.duration_ms}ms` : ''}
                                </span>
                              </div>
                              {st.input_payload && Object.keys(st.input_payload).length > 0 && (
                                <pre className="p-2 rounded bg-muted/60 text-[11px] font-mono overflow-x-auto">
                                  {JSON.stringify(st.input_payload, null, 2)}
                                </pre>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Trace Timeline */}
                    {ex.execution_trace && ex.execution_trace.length > 0 && (
                      <div className="space-y-1.5">
                        <span className="text-xs font-bold text-primary uppercase tracking-wider block">
                          Raw Trace Log
                        </span>
                        <div className="p-3 rounded-2xl bg-black/50 text-gray-300 font-mono text-[11px] max-h-60 overflow-y-auto space-y-1">
                          {ex.execution_trace.map((item: any, idx: number) => (
                            <div key={idx} className="flex items-start gap-2">
                              <span className="text-cyan-400">
                                [{item.timestamp?.slice(11, 19) || 'TRACE'}]
                              </span>
                              <span className="font-bold text-white">{item.stage || item.event}:</span>
                              <span>{item.message}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}
