import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Shield,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  Clock,
  Lock,
  FileText,
  Filter,
  Eye,
} from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';

export default function AgentAuditPage() {
  const { id } = useParams<{ id: string }>();
  const { token } = useAuth();

  const [agentName, setAgentName] = useState<string>('');
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [selectedLog, setSelectedLog] = useState<any | null>(null);

  const fetchAuditLogs = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [agentRes, auditRes] = await Promise.all([
        apiRequest<any>(`/agent-runtime/agents/${id}/`, { token }).catch(() => null),
        apiRequest<any>(`/agent-runtime/audit-logs/?agent=${id}`, { token }),
      ]);

      if (agentRes) setAgentName(agentRes.name);
      setLogs(Array.isArray(auditRes) ? auditRes : auditRes.results || []);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, [id, token]);

  const filtered = logs.filter((l) => {
    if (severityFilter === 'ALL') return true;
    return l.severity === severityFilter;
  });

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30">
            <ShieldAlert className="w-3 h-3" />
            CRITICAL
          </span>
        );
      case 'ERROR':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30">
            ERROR
          </span>
        );
      case 'WARNING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
            <AlertTriangle className="w-3 h-3" />
            WARNING
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
            <ShieldCheck className="w-3 h-3" />
            INFO
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
              Forensic Audit Trail
            </h1>
            <p className="text-xs sm:text-sm text-secondary">
              Immutable security record of agent state changes, firewall verdicts, tool executions, and user decisions.
            </p>
          </div>

          <button
            onClick={fetchAuditLogs}
            disabled={loading}
            className="p-2.5 rounded-xl border border-border hover:bg-muted text-secondary hover:text-primary transition cursor-pointer"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Severity Filter Chips */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
        {['ALL', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'].map((sev) => (
          <button
            key={sev}
            onClick={() => setSeverityFilter(sev)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${
              severityFilter === sev
                ? 'bg-primary text-surface shadow-xs'
                : 'bg-surface border border-border text-secondary hover:text-primary'
            }`}
          >
            {sev}
          </button>
        ))}
      </div>

      {/* Audit Log Table */}
      {loading && logs.length === 0 ? (
        <div className="py-24 text-center space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin text-indigo-500 mx-auto" />
          <p className="text-sm text-secondary">Loading audit events...</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="py-20 text-center rounded-3xl border border-dashed border-border p-8 space-y-3">
          <Shield className="w-8 h-8 text-gray-400 mx-auto" />
          <h3 className="text-base font-bold text-primary">No Audit Logs Found</h3>
          <p className="text-xs text-secondary">No recorded audit events matching the selected filter.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((log) => (
            <div
              key={log.id}
              className="p-4 rounded-2xl border border-border/80 bg-surface shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs hover:border-indigo-500/40 transition"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-primary font-mono">{log.event_type}</span>
                  {getSeverityBadge(log.severity)}
                  <span className="text-[10px] px-2 py-0.5 rounded bg-muted text-secondary font-mono">
                    Actor: {log.actor_type || 'SYSTEM'}
                  </span>
                </div>
                <p className="text-secondary text-[11px]">
                  Logged at: <strong className="text-primary">{new Date(log.created_at).toLocaleString()}</strong>
                </p>
              </div>

              <div className="flex items-center gap-2 self-end sm:self-center">
                {log.details && Object.keys(log.details).length > 0 && (
                  <button
                    type="button"
                    onClick={() => setSelectedLog(selectedLog?.id === log.id ? null : log)}
                    className="px-3 py-1.5 rounded-lg border border-border bg-background hover:bg-muted text-xs font-semibold text-primary transition flex items-center gap-1"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    {selectedLog?.id === log.id ? 'Hide Details' : 'View Details'}
                  </button>
                )}
              </div>

              {/* Expandable JSON details */}
              {selectedLog?.id === log.id && (
                <div className="w-full mt-3 pt-3 border-t border-border">
                  <pre className="p-3 rounded-xl bg-gray-900 text-gray-200 font-mono text-[11px] overflow-x-auto max-h-48">
                    {JSON.stringify(log.details, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

    </div>
  );
}
