import React, { useState, useEffect, useRef } from 'react';
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
  ChevronRight,
  FileCode,
  ShieldAlert,
  ShieldCheck,
  Play,
  Pause,
  RotateCcw,
  SkipForward,
  Cpu,
  Zap,
  Lock,
  Terminal,
  Activity,
  Copy,
  Check,
  Flame,
  Layers,
  Sparkles,
} from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';

interface TimelineEvent {
  time: string;
  timestamp: string;
  title: string;
  stage: string;
  status: 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR' | 'FAILED';
  meta?: any;
}

interface ExecutionRecord {
  executionId: string;
  execution_id?: string;
  agentId: string | number;
  agent_name?: string;
  userId?: string;
  timestamp: string;
  intent?: string;
  input?: any;
  context?: any;
  toolsSelected?: string[];
  toolInputs?: any[];
  policyChecks?: any[];
  riskChecks?: any;
  approvalRequest?: any;
  approvalResponse?: any;
  toolResults?: any[];
  finalAction?: string;
  status: string;
  error?: string;
  error_message?: string;
  duration?: number;
  duration_ms?: number;
  model?: string;
  model_name?: string;
  tokenUsage?: { prompt_tokens?: number; completion_tokens?: number; total_tokens?: number };
  timeline?: TimelineEvent[];
  initial_request?: string;
  started_at?: string;
  completed_at?: string;
}

export default function AgentExecutionsPage() {
  const { id } = useParams<{ id: string }>();
  const { token } = useAuth();

  const [agentName, setAgentName] = useState<string>('');
  const [executions, setExecutions] = useState<ExecutionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [onlyErrors, setOnlyErrors] = useState<boolean>(false);

  // Selected Execution Modal / Drawer
  const [selectedExec, setSelectedExec] = useState<ExecutionRecord | null>(null);
  const [activeTab, setActiveTab] = useState<'timeline' | 'tools' | 'policy' | 'errors' | 'raw'>('timeline');
  const [copiedJson, setCopiedJson] = useState(false);

  // Replay State
  const [replaying, setReplaying] = useState(false);
  const [replayComparison, setReplayComparison] = useState<any>(null);

  // Interactive Timeline Player State
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(-1);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const playbackTimerRef = useRef<any>(null);

  const fetchExecutions = async () => {
    setLoading(true);
    try {
      const endpoint = id
        ? `/agent-runtime/executions/?agent=${id}`
        : `/agent-runtime/executions/`;

      if (id) {
        const agentRes = await apiRequest<any>(`/agent-runtime/agents/${id}/`, { token }).catch(() => null);
        if (agentRes) setAgentName(agentRes.name);
      }

      const execRes = await apiRequest<any>(endpoint, { token });
      const list = Array.isArray(execRes) ? execRes : execRes.results || [];
      setExecutions(list);
    } catch (err) {
      console.error('Failed to load executions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExecutions();
  }, [id, token]);

  // Timeline player loop
  useEffect(() => {
    if (isPlaying && selectedExec && selectedExec.timeline && selectedExec.timeline.length > 0) {
      playbackTimerRef.current = setTimeout(() => {
        if (currentStepIndex < selectedExec.timeline!.length - 1) {
          setCurrentStepIndex((prev) => prev + 1);
        } else {
          setIsPlaying(false);
        }
      }, 1000 / playbackSpeed);
    }
    return () => {
      if (playbackTimerRef.current) clearTimeout(playbackTimerRef.current);
    };
  }, [isPlaying, currentStepIndex, playbackSpeed, selectedExec]);

  const openExecution = (exec: ExecutionRecord) => {
    setSelectedExec(exec);
    setActiveTab('timeline');
    setReplayComparison(null);
    setCurrentStepIndex((exec.timeline && exec.timeline.length > 0) ? exec.timeline.length - 1 : 0);
    setIsPlaying(false);
  };

  const startPlayback = () => {
    if (!selectedExec || !selectedExec.timeline) return;
    setCurrentStepIndex(0);
    setIsPlaying(true);
  };

  const handleReplay = async (execId: string) => {
    try {
      setReplaying(true);
      const res = await apiRequest<any>(`/agent-runtime/executions/${execId}/replay/`, {
        token,
        method: 'POST',
      });
      setReplayComparison(res);
      await fetchExecutions();
    } catch (e: any) {
      alert(`Replay failed: ${e.message}`);
    } finally {
      setReplaying(false);
    }
  };

  const copyRawJson = () => {
    if (!selectedExec) return;
    navigator.clipboard.writeText(JSON.stringify(selectedExec, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  // Filtered executions
  const filtered = executions.filter((e) => {
    if (statusFilter !== 'ALL' && e.status !== statusFilter) return false;
    if (onlyErrors && !(e.error || e.error_message || e.status === 'FAILED')) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const promptMatch = (e.initial_request || '').toLowerCase().includes(q);
      const idMatch = (e.executionId || e.execution_id || '').toLowerCase().includes(q);
      const intentMatch = (e.intent || '').toLowerCase().includes(q);
      if (!promptMatch && !idMatch && !intentMatch) return false;
    }
    return true;
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

  const getEventIcon = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
      case 'WARNING':
        return <AlertTriangle className="w-4 h-4 text-amber-500" />;
      case 'ERROR':
      case 'FAILED':
        return <XCircle className="w-4 h-4 text-rose-500" />;
      default:
        return <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" />;
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-16 px-4 sm:px-6">
      {/* Top Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Link
            to={id ? `/agents/${id}` : '/agents'}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-secondary hover:text-primary transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to {agentName || 'Agent Studio'}
          </Link>
          <span className="text-secondary text-xs">/</span>
          <span className="text-xs font-bold text-indigo-600">Observability & Audit Console</span>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-black text-primary tracking-tight flex items-center gap-3">
              <Activity className="w-7 h-7 text-indigo-600" />
              Agent Observability & Execution Audit
            </h1>
            <p className="text-xs sm:text-sm text-secondary mt-1">
              End-to-end 20-metric execution traces, deterministic timeline events, sandbox replays, and zero-trust secret masking.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-emerald-500/10 border border-emerald-500/25 text-emerald-600 dark:text-emerald-400">
              <Lock className="w-3.5 h-3.5" />
              Zero-Trust Redaction Active
            </span>
            <button
              onClick={fetchExecutions}
              disabled={loading}
              className="p-2.5 rounded-xl border border-border hover:bg-muted text-secondary hover:text-primary transition cursor-pointer"
              title="Refresh executions"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Stats Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-surface border border-border">
          <span className="text-xs font-bold text-secondary uppercase tracking-wider">Total Runs</span>
          <p className="text-2xl font-black text-primary mt-1">{executions.length}</p>
        </div>
        <div className="p-4 rounded-2xl bg-surface border border-border">
          <span className="text-xs font-bold text-secondary uppercase tracking-wider">Completed</span>
          <p className="text-2xl font-black text-emerald-600 mt-1">
            {executions.filter((e) => e.status === 'COMPLETED').length}
          </p>
        </div>
        <div className="p-4 rounded-2xl bg-surface border border-border">
          <span className="text-xs font-bold text-secondary uppercase tracking-wider">Firewall Interventions</span>
          <p className="text-2xl font-black text-amber-500 mt-1">
            {executions.filter((e) => e.status === 'WAITING_APPROVAL' || e.status === 'CANCELLED').length}
          </p>
        </div>
        <div className="p-4 rounded-2xl bg-surface border border-border">
          <span className="text-xs font-bold text-secondary uppercase tracking-wider">Avg Latency</span>
          <p className="text-2xl font-black text-indigo-600 mt-1">
            {executions.length > 0
              ? Math.round(
                  executions.reduce((acc, e) => acc + (e.duration || e.duration_ms || 0), 0) / executions.length
                )
              : 0}
            ms
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1">
          {['ALL', 'COMPLETED', 'WAITING_APPROVAL', 'CANCELLED', 'FAILED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer whitespace-nowrap ${
                statusFilter === st
                  ? 'bg-primary text-surface shadow-xs'
                  : 'bg-surface border border-border text-secondary hover:text-primary'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <label className="flex items-center gap-2 text-xs font-bold text-secondary cursor-pointer">
            <input
              type="checkbox"
              checked={onlyErrors}
              onChange={(e) => setOnlyErrors(e.target.checked)}
              className="accent-indigo-600 w-3.5 h-3.5"
            />
            <span>Errors Only</span>
          </label>

          <div className="relative flex-1 sm:w-64">
            <Search className="w-3.5 h-3.5 text-secondary absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search prompt, intent, ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl bg-surface border border-border text-primary"
            />
          </div>
        </div>
      </div>

      {/* Main Execution List */}
      {loading && executions.length === 0 ? (
        <div className="py-24 text-center space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin text-indigo-500 mx-auto" />
          <p className="text-sm text-secondary">Loading execution telemetry...</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="py-20 text-center rounded-3xl border border-dashed border-border p-8 space-y-3">
          <History className="w-8 h-8 text-gray-400 mx-auto" />
          <h3 className="text-base font-bold text-primary">No Execution Telemetry Found</h3>
          <p className="text-xs text-secondary">
            No agent executions matched your criteria. Test an execution in the Agent Playground or Command Bar.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((ex) => {
            const execId = ex.executionId || ex.execution_id;
            const durationVal = ex.duration || ex.duration_ms || 0;
            const tokenCount = ex.tokenUsage?.total_tokens;

            return (
              <div
                key={execId}
                onClick={() => openExecution(ex)}
                className="p-5 rounded-2xl border border-border/80 bg-surface hover:border-indigo-500/50 hover:shadow-md transition-all duration-150 cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4 group"
              >
                <div className="space-y-1.5 max-w-2xl">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400">
                      #{execId?.slice(0, 8)}
                    </span>
                    {getStatusBadge(ex.status)}
                    {ex.intent && (
                      <span className="px-2 py-0.5 rounded-md bg-muted text-[10px] font-mono font-bold text-secondary">
                        INTENT: {ex.intent}
                      </span>
                    )}
                    {ex.model && (
                      <span className="px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 text-[10px] font-bold">
                        {ex.model}
                      </span>
                    )}
                  </div>

                  <h3 className="text-sm font-bold text-primary group-hover:text-indigo-600 transition">
                    {ex.initial_request}
                  </h3>

                  <div className="flex flex-wrap items-center gap-4 text-[11px] text-secondary">
                    <span>Started: {new Date(ex.started_at || ex.timestamp).toLocaleString()}</span>
                    <span>Latency: {durationVal}ms</span>
                    {tokenCount && <span>Tokens: {tokenCount}</span>}
                    <span>Events: {ex.timeline?.length || 0}</span>
                  </div>
                </div>

                <div className="flex items-center gap-3 self-end md:self-center">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      openExecution(ex);
                    }}
                    className="px-3.5 py-1.5 rounded-xl bg-indigo-600/10 hover:bg-indigo-600 text-indigo-600 hover:text-white text-xs font-bold transition cursor-pointer flex items-center gap-1.5"
                  >
                    <span>Inspect</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Execution Detail Modal / Drawer */}
      {selectedExec && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="w-full max-w-4xl max-h-[90vh] bg-surface rounded-3xl border border-border shadow-2xl flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="p-6 border-b border-border bg-muted/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-indigo-600">
                    ID: {selectedExec.executionId || selectedExec.execution_id}
                  </span>
                  {getStatusBadge(selectedExec.status)}
                </div>
                <h2 className="text-base font-black text-primary">{selectedExec.initial_request}</h2>
                <div className="flex flex-wrap items-center gap-3 text-xs text-secondary">
                  <span>Model: {selectedExec.model || selectedExec.model_name || 'gemini-2.0-flash'}</span>
                  <span>•</span>
                  <span>Duration: {selectedExec.duration || selectedExec.duration_ms || 0}ms</span>
                  <span>•</span>
                  <span>Tokens: {selectedExec.tokenUsage?.total_tokens || 0}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 self-end sm:self-center">
                <button
                  type="button"
                  disabled={replaying}
                  onClick={() => handleReplay(selectedExec.executionId || selectedExec.execution_id!)}
                  className="px-3.5 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shadow"
                >
                  <RotateCcw className={`w-3.5 h-3.5 ${replaying ? 'animate-spin' : ''}`} />
                  <span>{replaying ? 'Replaying...' : 'Replay Execution'}</span>
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedExec(null)}
                  className="p-2 rounded-xl border border-border hover:bg-muted text-secondary hover:text-primary transition cursor-pointer"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Replay Banner if replayed */}
            {replayComparison && (
              <div className="p-4 bg-purple-500/10 border-b border-purple-500/30 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-600" />
                  <span className="font-bold text-purple-800 dark:text-purple-300">
                    Replay Finished: {replayComparison.matched ? 'Full Parity Matched' : 'Parity Discrepancy'}
                  </span>
                  <span className="text-secondary text-[11px]">
                    (Intent Match: {String(replayComparison.verifications?.intent_match)}, Tools Match: {String(replayComparison.verifications?.tools_match)})
                  </span>
                </div>
                <span className="font-mono text-purple-600 font-black">
                  New Exec ID: {replayComparison.replayed?.execution_id?.slice(0, 8)}...
                </span>
              </div>
            )}

            {/* Tabs */}
            <div className="flex items-center gap-2 px-6 pt-3 border-b border-border bg-surface text-xs font-bold">
              <button
                onClick={() => setActiveTab('timeline')}
                className={`pb-3 px-2 border-b-2 transition cursor-pointer ${
                  activeTab === 'timeline'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-secondary hover:text-primary'
                }`}
              >
                Timeline ({selectedExec.timeline?.length || 0})
              </button>
              <button
                onClick={() => setActiveTab('tools')}
                className={`pb-3 px-2 border-b-2 transition cursor-pointer ${
                  activeTab === 'tools'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-secondary hover:text-primary'
                }`}
              >
                Tool Calls ({selectedExec.toolsSelected?.length || 0})
              </button>
              <button
                onClick={() => setActiveTab('policy')}
                className={`pb-3 px-2 border-b-2 transition cursor-pointer ${
                  activeTab === 'policy'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-secondary hover:text-primary'
                }`}
              >
                Policy & Risk
              </button>
              <button
                onClick={() => setActiveTab('errors')}
                className={`pb-3 px-2 border-b-2 transition cursor-pointer ${
                  activeTab === 'errors'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-secondary hover:text-primary'
                }`}
              >
                Errors & Trace
              </button>
              <button
                onClick={() => setActiveTab('raw')}
                className={`pb-3 px-2 border-b-2 transition cursor-pointer ${
                  activeTab === 'raw'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-secondary hover:text-primary'
                }`}
              >
                Raw Telemetry
              </button>
            </div>

            {/* Tab Body */}
            <div className="p-6 overflow-y-auto flex-1 space-y-6">
              {/* TAB: TIMELINE */}
              {activeTab === 'timeline' && (
                <div className="space-y-6">
                  {/* Timeline Player Controls */}
                  <div className="p-3.5 rounded-2xl bg-muted/30 border border-border flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setIsPlaying(!isPlaying)}
                        className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold flex items-center gap-1.5 transition cursor-pointer"
                      >
                        {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                        <span>{isPlaying ? 'Pause' : 'Play Timeline'}</span>
                      </button>
                      <button
                        type="button"
                        onClick={startPlayback}
                        className="px-3 py-1.5 rounded-xl border border-border hover:bg-muted text-xs font-bold transition cursor-pointer flex items-center gap-1"
                      >
                        <RotateCcw className="w-3.5 h-3.5" /> Reset
                      </button>
                      <button
                        type="button"
                        disabled={!selectedExec.timeline || currentStepIndex >= selectedExec.timeline.length - 1}
                        onClick={() => setCurrentStepIndex((prev) => prev + 1)}
                        className="px-3 py-1.5 rounded-xl border border-border hover:bg-muted text-xs font-bold transition cursor-pointer flex items-center gap-1"
                      >
                        <SkipForward className="w-3.5 h-3.5" /> Step
                      </button>
                    </div>

                    <div className="flex items-center gap-3 text-xs">
                      <span className="text-secondary">Speed:</span>
                      {[1, 2, 5].map((sp) => (
                        <button
                          key={sp}
                          onClick={() => setPlaybackSpeed(sp)}
                          className={`px-2 py-0.5 rounded-lg text-xs font-bold transition cursor-pointer ${
                            playbackSpeed === sp ? 'bg-indigo-600 text-white' : 'bg-surface border border-border text-secondary'
                          }`}
                        >
                          {sp}x
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Chronological Timeline stream matching user format */}
                  <div className="space-y-3 font-mono">
                    {selectedExec.timeline && selectedExec.timeline.length > 0 ? (
                      selectedExec.timeline.map((evt, idx) => {
                        const isCurrent = idx === currentStepIndex;
                        const isPast = idx <= currentStepIndex;

                        return (
                          <div
                            key={idx}
                            className={`p-3 rounded-2xl border transition-all duration-200 flex items-start gap-4 ${
                              isCurrent
                                ? 'bg-indigo-500/10 border-indigo-500 ring-2 ring-indigo-500/30'
                                : isPast
                                ? 'bg-background border-border text-primary'
                                : 'bg-surface border-border/40 opacity-40'
                            }`}
                          >
                            <span className="text-xs font-black text-secondary shrink-0 select-none">
                              {evt.time || '00:00:00'}
                            </span>

                            <div className="shrink-0 mt-0.5">{getEventIcon(evt.status)}</div>

                            <div className="flex-1 space-y-1">
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-bold text-primary font-sans">{evt.title}</span>
                                <span className="text-[10px] uppercase font-bold text-secondary">{evt.stage}</span>
                              </div>
                              {evt.meta && Object.keys(evt.meta).length > 0 && (
                                <pre className="text-[10px] p-2 rounded-xl bg-surface border border-border/60 text-secondary overflow-x-auto">
                                  {JSON.stringify(evt.meta, null, 2)}
                                </pre>
                              )}
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="p-6 text-center text-xs text-secondary">No timeline events recorded.</div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB: TOOL CALLS */}
              {activeTab === 'tools' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-black uppercase tracking-wider text-secondary">
                      Tools Selected & Invoked ({selectedExec.toolsSelected?.length || 0})
                    </h3>
                  </div>

                  {selectedExec.toolsSelected && selectedExec.toolsSelected.length > 0 ? (
                    selectedExec.toolsSelected.map((tool, idx) => {
                      const inputPayload = selectedExec.toolInputs?.[idx] || {};
                      const outputPayload = selectedExec.toolResults?.[idx] || {};

                      return (
                        <div key={idx} className="p-4 rounded-2xl bg-background border border-border space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="font-mono font-bold text-xs text-indigo-600 dark:text-indigo-400">
                              {tool}
                            </span>
                            <span className="text-[11px] font-bold text-emerald-600 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                              Executed Successfully
                            </span>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
                            <div className="space-y-1">
                              <span className="text-[11px] font-sans font-bold text-secondary">
                                Inputs (Zero-Trust Scrubbed):
                              </span>
                              <pre className="p-2.5 rounded-xl bg-surface border border-border text-[11px] overflow-x-auto">
                                {JSON.stringify(inputPayload, null, 2)}
                              </pre>
                            </div>

                            <div className="space-y-1">
                              <span className="text-[11px] font-sans font-bold text-secondary">Results:</span>
                              <pre className="p-2.5 rounded-xl bg-surface border border-border text-[11px] overflow-x-auto">
                                {JSON.stringify(outputPayload, null, 2)}
                              </pre>
                            </div>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="p-8 text-center text-xs text-secondary rounded-2xl bg-background border border-border">
                      No tool calls executed for this task. Direct natural language response was generated.
                    </div>
                  )}
                </div>
              )}

              {/* TAB: POLICY & RISK */}
              {activeTab === 'policy' && (
                <div className="space-y-6">
                  {/* Risk Overview Card */}
                  <div className="p-5 rounded-2xl bg-background border border-border space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-black uppercase tracking-wider text-secondary">
                        Financial Risk Check Outcome
                      </h4>
                      <span className="font-mono font-black text-xs text-primary">
                        Score: {selectedExec.riskChecks?.risk_score ?? 0} / 100
                      </span>
                    </div>

                    <div className="flex items-center gap-3">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-black border ${
                          selectedExec.riskChecks?.risk_level === 'CRITICAL'
                            ? 'bg-rose-500/20 text-rose-600 border-rose-500/40 animate-pulse'
                            : selectedExec.riskChecks?.risk_level === 'HIGH'
                            ? 'bg-orange-500/20 text-orange-600 border-orange-500/40'
                            : 'bg-emerald-500/20 text-emerald-600 border-emerald-500/40'
                        }`}
                      >
                        {selectedExec.riskChecks?.risk_level || 'LOW'} RISK
                      </span>
                      {selectedExec.riskChecks?.critical_rule_triggered && (
                        <span className="text-xs font-bold text-rose-600">
                          Critical Rule Triggered: Execution Denied / Escalated
                        </span>
                      )}
                    </div>

                    {selectedExec.riskChecks?.reasons && selectedExec.riskChecks.reasons.length > 0 && (
                      <div className="space-y-1 pt-2 border-t border-border">
                        <span className="text-[11px] font-bold text-secondary">Triggered Reasons:</span>
                        <ul className="space-y-1">
                          {selectedExec.riskChecks.reasons.map((r: string, idx: number) => (
                            <li key={idx} className="text-xs font-medium text-primary flex items-center gap-2">
                              <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                              <span>{r}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {/* Policy Checks Stream */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-black uppercase tracking-wider text-secondary">
                      Governance Firewall Policy Decisions
                    </h4>
                    {selectedExec.policyChecks && selectedExec.policyChecks.length > 0 ? (
                      selectedExec.policyChecks.map((p, idx) => (
                        <div key={idx} className="p-3.5 rounded-2xl bg-background border border-border text-xs space-y-1.5">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-primary">
                              Decision: {p.governance_decision || (p.policy_engine_allowed ? 'ALLOW' : 'DENY')}
                            </span>
                            <span className="text-[11px] font-mono text-secondary">
                              Policy: {p.policy_triggered || 'STANDARD_FIREWALL'}
                            </span>
                          </div>
                          {p.reason && <p className="text-secondary text-[11px]">{p.reason}</p>}
                        </div>
                      ))
                    ) : (
                      <div className="p-4 rounded-xl bg-background border border-border text-xs text-secondary">
                        Standard zero-trust baseline policy evaluated and cleared.
                      </div>
                    )}
                  </div>

                  {/* Approval Information */}
                  {selectedExec.approvalRequest && Object.keys(selectedExec.approvalRequest).length > 0 && (
                    <div className="p-4 rounded-2xl bg-background border border-border space-y-2">
                      <h4 className="text-xs font-black uppercase tracking-wider text-secondary">Approval Protocol</h4>
                      <pre className="p-3 rounded-xl bg-surface border border-border text-xs font-mono overflow-x-auto">
                        {JSON.stringify(
                          { request: selectedExec.approvalRequest, response: selectedExec.approvalResponse },
                          null,
                          2
                        )}
                      </pre>
                    </div>
                  )}
                </div>
              )}

              {/* TAB: ERRORS */}
              {activeTab === 'errors' && (
                <div className="space-y-4">
                  {selectedExec.error || selectedExec.error_message || selectedExec.status === 'FAILED' ? (
                    <div className="p-5 rounded-2xl bg-rose-500/10 border border-rose-500/30 space-y-3">
                      <div className="flex items-center gap-2 text-rose-600 font-bold text-sm">
                        <AlertTriangle className="w-5 h-5" />
                        <span>Execution Failure Captured</span>
                      </div>
                      <p className="text-xs text-rose-700 dark:text-rose-300 font-mono whitespace-pre-wrap">
                        {selectedExec.error || selectedExec.error_message || 'Execution halted abnormally.'}
                      </p>
                    </div>
                  ) : (
                    <div className="p-8 text-center rounded-2xl bg-background border border-border space-y-2">
                      <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
                      <h4 className="text-sm font-bold text-primary">No Errors Encountered</h4>
                      <p className="text-xs text-secondary">
                        This execution finished smoothly with zero runtime exceptions or firewall policy denials.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* TAB: RAW JSON */}
              {activeTab === 'raw' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-secondary">
                      Full 20-Metric Schema (Secrets Redacted)
                    </span>
                    <button
                      type="button"
                      onClick={copyRawJson}
                      className="px-3 py-1.5 rounded-xl border border-border hover:bg-muted text-xs font-bold text-primary transition cursor-pointer flex items-center gap-1.5"
                    >
                      {copiedJson ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedJson ? 'Copied' : 'Copy JSON'}</span>
                    </button>
                  </div>
                  <pre className="p-4 rounded-2xl bg-background border border-border text-xs font-mono overflow-x-auto text-primary max-h-96">
                    {JSON.stringify(selectedExec, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
