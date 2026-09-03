import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Bot,
  Sparkles,
  Send,
  ArrowRight,
  ArrowLeft,
  Wrench,
  Lock,
  Database,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Plus,
  Trash2,
  Clock,
  Zap,
  Layers,
  HelpCircle,
  FileCode,
  ShieldCheck,
  Building2,
  DollarSign,
  AlertCircle,
  Cpu,
} from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';
import PreActivationModal from './PreActivationModal';

export interface AgentBlueprintState {
  name: string;
  description: string;
  goal: string;
  trigger: {
    type: string;
    frequency?: string;
    event?: string;
    threshold?: Record<string, any>;
    config?: Record<string, any>;
  };
  dataSources: string[];
  tools: string[];
  logic: string[];
  conditions: string[];
  actions: string[];
  notifications: string[];
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  approvalMode: 'auto' | 'review_required' | 'always_confirm' | 'blocked';
  guardrails: {
    maxTransactionAmount: number;
    dailySpendLimit: number;
    requireApprovalAbove: number;
    blockedCategories: string[];
    allowedMerchants: string[];
    requireDoubleConfirmation: boolean;
  };
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  source?: 'LLM' | 'DETERMINISTIC_FALLBACK';
  timestamp: string;
}

const DEFAULT_BLUEPRINT: AgentBlueprintState = {
  name: 'Refund Spike Analyzer',
  description: 'Autonomous monitoring agent that continually inspects refund velocity, detects unusual volume surges, and alerts operations teams.',
  goal: 'Detect anomalous refund rates against historical baselines and issue operational risk alerts.',
  trigger: {
    type: 'scheduled',
    frequency: 'daily',
    config: { cron: '0 9 * * *' },
  },
  dataSources: ['refunds', 'orders', 'payments'],
  tools: ['getRefunds', 'getOrder', 'createAlert', 'generateReport'],
  logic: [
    'calculate daily refund rate',
    'compare with 30-day baseline average',
    'identify statistical volume anomalies',
    'identify affected products and merchant batches',
  ],
  conditions: [
    'refund_rate > baseline * 1.5',
    'affected_sku_count >= 2',
  ],
  actions: [
    'create alert',
    'generate report',
    'notify operations team',
  ],
  notifications: [
    'email: finance-ops@razorhub.com',
    'slack: #payment-alerts',
  ],
  riskLevel: 'medium',
  approvalMode: 'auto',
  guardrails: {
    maxTransactionAmount: 25000.0,
    dailySpendLimit: 50000.0,
    requireApprovalAbove: 10000.0,
    blockedCategories: ['cash', 'unknown'],
    allowedMerchants: [],
    requireDoubleConfirmation: false,
  },
};

const PROMPT_SUGGESTIONS = [
  'Build me an agent that detects unusual refund spikes and alerts me.',
  'Build me an agent that recovers failed payments with dynamic payment links.',
  'Create an abandoned cart recovery agent with personalized follow-up offers.',
  'Build a cashflow forecasting agent for daily liquidity and runway analysis.',
  'Create a payout agent with double confirmation for vendor disbursements.',
];

export default function ConversationalAgentBuilder() {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'm-init',
      role: 'assistant',
      content:
        "Hello! I am your Autonomous Agent Architect. Tell me what kind of commerce agent you would like to construct (e.g. refund spike analyzer, failed payment dunning, cashflow forecaster), and I will generate a structured Agent Blueprint with zero-trust guardrails.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const [inputPrompt, setInputPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [blueprint, setBlueprint] = useState<AgentBlueprintState>(DEFAULT_BLUEPRINT);
  const [sourceEngine, setSourceEngine] = useState<'LLM' | 'DETERMINISTIC_FALLBACK'>('DETERMINISTIC_FALLBACK');
  
  // Available registered tools for dropdown / selection
  const [registeredTools, setRegisteredTools] = useState<string[]>([
    'getPayment', 'searchPayments', 'getOrder', 'searchOrders', 'createPaymentIntent',
    'createPaymentLink', 'getPaymentStatus', 'createRefund', 'getRefunds', 'getCustomer',
    'getInvoice', 'getOutstandingInvoices', 'createPayout', 'getPayout', 'getSettlement',
    'getCashflow', 'sendNotification', 'generateReport', 'createAlert'
  ]);

  // Pre-activation verification modal state
  const [showPreActivation, setShowPreActivation] = useState(false);
  const [activating, setActivating] = useState(false);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  // New tag inputs for editing
  const [newDataSource, setNewDataSource] = useState('');
  const [newLogic, setNewLogic] = useState('');
  const [newCondition, setNewCondition] = useState('');
  const [newAction, setNewAction] = useState('');
  const [newNotification, setNewNotification] = useState('');

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Fetch available registered tools
  useEffect(() => {
    async function loadTools() {
      try {
        const data = await apiRequest<any>('/agent-runtime/tools/', { token });
        const list = Array.isArray(data) ? data : data.results || [];
        if (list.length > 0) {
          setRegisteredTools(list.map((t: any) => t.name));
        }
      } catch (err) {
        console.error('Failed to load registered tools:', err);
      }
    }
    loadTools();
  }, [token]);

  const handleSendMessage = async (promptToSend?: string) => {
    const text = (promptToSend || inputPrompt).trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!promptToSend) setInputPrompt('');
    setLoading(true);

    try {
      const history = messages
        .filter((m) => m.id !== 'm-init')
        .map((m) => ({ role: m.role, content: m.content }));

      const res = await apiRequest<any>('/agent-runtime/blueprint/generate/', {
        token,
        method: 'POST',
        body: JSON.stringify({ message: text, history }),
      });

      if (res.blueprint) {
        setBlueprint(res.blueprint);
        setSourceEngine(res.source || 'LLM');
      }

      const aiMsg: ChatMessage = {
        id: `a-${Date.now()}`,
        role: 'assistant',
        content: res.ai_message || `I have updated the Agent Blueprint on the right.`,
        source: res.source,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `Error generating blueprint: ${err.message || 'Service temporarily offline'}. Switched to local deterministic template.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveDraft = async () => {
    setActivating(true);
    setActionNotice(null);
    try {
      const res = await apiRequest<any>('/agent-runtime/blueprint/activate/', {
        token,
        method: 'POST',
        body: JSON.stringify({
          blueprint,
          activate: false,
          confirmation: false,
        }),
      });

      navigate(`/agents/${res.id}`);
    } catch (err: any) {
      setActionNotice(`Failed to save draft: ${err.message}`);
      setActivating(false);
    }
  };

  const handleConfirmActivation = async () => {
    setActivating(true);
    try {
      const res = await apiRequest<any>('/agent-runtime/blueprint/activate/', {
        token,
        method: 'POST',
        body: JSON.stringify({
          blueprint,
          activate: true,
          confirmation: true,
        }),
      });

      setShowPreActivation(false);
      navigate(`/agents/${res.id}`);
    } catch (err: any) {
      setActionNotice(`Activation failed: ${err.message}`);
      setShowPreActivation(false);
      setActivating(false);
    }
  };

  // Helper mutators for blueprint editing
  const toggleTool = (toolName: string) => {
    setBlueprint((prev) => {
      const tools = prev.tools.includes(toolName)
        ? prev.tools.filter((t) => t !== toolName)
        : [...prev.tools, toolName];
      return { ...prev, tools };
    });
  };

  const addDataSource = () => {
    if (!newDataSource.trim()) return;
    const val = newDataSource.trim().toLowerCase();
    if (!blueprint.dataSources.includes(val)) {
      setBlueprint((prev) => ({ ...prev, dataSources: [...prev.dataSources, val] }));
    }
    setNewDataSource('');
  };

  const removeDataSource = (ds: string) => {
    setBlueprint((prev) => ({
      ...prev,
      dataSources: prev.dataSources.filter((s) => s !== ds),
    }));
  };

  const addLogicStep = () => {
    if (!newLogic.trim()) return;
    setBlueprint((prev) => ({ ...prev, logic: [...prev.logic, newLogic.trim()] }));
    setNewLogic('');
  };

  const removeLogicStep = (idx: number) => {
    setBlueprint((prev) => ({
      ...prev,
      logic: prev.logic.filter((_, i) => i !== idx),
    }));
  };

  const addCondition = () => {
    if (!newCondition.trim()) return;
    setBlueprint((prev) => ({ ...prev, conditions: [...prev.conditions, newCondition.trim()] }));
    setNewCondition('');
  };

  const removeCondition = (idx: number) => {
    setBlueprint((prev) => ({
      ...prev,
      conditions: prev.conditions.filter((_, i) => i !== idx),
    }));
  };

  const addActionItem = () => {
    if (!newAction.trim()) return;
    setBlueprint((prev) => ({ ...prev, actions: [...prev.actions, newAction.trim()] }));
    setNewAction('');
  };

  const removeActionItem = (idx: number) => {
    setBlueprint((prev) => ({
      ...prev,
      actions: prev.actions.filter((_, i) => i !== idx),
    }));
  };

  const addNotification = () => {
    if (!newNotification.trim()) return;
    setBlueprint((prev) => ({ ...prev, notifications: [...prev.notifications, newNotification.trim()] }));
    setNewNotification('');
  };

  const removeNotification = (idx: number) => {
    setBlueprint((prev) => ({
      ...prev,
      notifications: prev.notifications.filter((_, i) => i !== idx),
    }));
  };

  return (
    <div className="flex flex-col h-[calc(100vh-80px)] -mt-4 -mx-4 sm:-mx-6 lg:-mx-8 overflow-hidden bg-background">
      
      {/* Pre-Activation Modal */}
      <PreActivationModal
        isOpen={showPreActivation}
        onClose={() => setShowPreActivation(false)}
        onConfirm={handleConfirmActivation}
        blueprint={blueprint}
        loading={activating}
      />

      {/* Top Breadcrumb Bar */}
      <div className="h-12 border-b border-border bg-surface px-6 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <Link
            to="/agents"
            className="text-xs font-semibold text-secondary hover:text-primary transition flex items-center gap-1.5"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Agent Studio
          </Link>
          <span className="text-secondary text-xs">/</span>
          <span className="text-xs font-bold text-primary flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
            No-Code Conversational Builder
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] font-medium text-secondary">
            Engine Source:
          </span>
          <span
            className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${
              sourceEngine === 'LLM'
                ? 'bg-purple-500/15 text-purple-600 dark:text-purple-400 border border-purple-500/30'
                : 'bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border border-cyan-500/30'
            }`}
          >
            {sourceEngine === 'LLM' ? 'Gemini AI Engine' : 'Deterministic Sentinel'}
          </span>
        </div>
      </div>

      {actionNotice && (
        <div className="p-3 bg-rose-50 dark:bg-rose-950/30 border-b border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs flex items-center justify-between px-6">
          <span>{actionNotice}</span>
          <button onClick={() => setActionNotice(null)} className="font-bold underline">Dismiss</button>
        </div>
      )}

      {/* Main Dual-Panel Workspace */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden">
        
        {/* ── LEFT PANEL: CONVERSATION ── */}
        <div className="lg:col-span-5 flex flex-col border-r border-border bg-surface/50 h-full overflow-hidden">
          
          {/* Messages Stream */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-3 text-xs leading-relaxed ${
                  m.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {m.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-xl bg-indigo-600 text-white flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-2xl p-3.5 shadow-xs ${
                    m.role === 'user'
                      ? 'bg-primary text-surface rounded-tr-none'
                      : 'bg-surface border border-border text-primary rounded-tl-none space-y-1.5'
                  }`}
                >
                  <p>{m.content}</p>
                  <div className="flex items-center justify-between gap-2 pt-1 text-[10px] opacity-70">
                    <span>{m.timestamp}</span>
                    {m.source && (
                      <span className="font-mono uppercase">{m.source}</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-2 text-xs text-secondary pl-2 animate-pulse">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-indigo-500" />
                <span>Designing structured Agent Blueprint...</span>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Quick Prompt Suggestions */}
          <div className="p-3 border-t border-border bg-surface/80 space-y-1.5">
            <span className="text-[11px] font-bold text-secondary uppercase tracking-wider block px-1">
              Sample Inquiries:
            </span>
            <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
              {PROMPT_SUGGESTIONS.map((sug, idx) => (
                <button
                  key={idx}
                  type="button"
                  disabled={loading}
                  onClick={() => handleSendMessage(sug)}
                  className="px-3 py-1.5 rounded-xl border border-border bg-background hover:bg-muted text-[11px] font-medium text-secondary hover:text-primary whitespace-nowrap transition cursor-pointer text-left shrink-0"
                >
                  {sug.length > 40 ? `${sug.slice(0, 40)}...` : sug}
                </button>
              ))}
            </div>
          </div>

          {/* Chat Input */}
          <div className="p-4 border-t border-border bg-surface shrink-0">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="relative flex items-center"
            >
              <input
                type="text"
                value={inputPrompt}
                onChange={(e) => setInputPrompt(e.target.value)}
                placeholder="e.g. Build me an agent that detects unusual refund spikes and alerts me..."
                disabled={loading}
                className="w-full pl-4 pr-12 py-3 rounded-2xl border border-border bg-background text-primary text-xs focus:ring-2 focus:ring-indigo-500 outline-none transition"
              />
              <button
                type="submit"
                disabled={loading || !inputPrompt.trim()}
                className="absolute right-2 p-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white transition disabled:opacity-40 cursor-pointer"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>
          </div>

        </div>

        {/* ── RIGHT PANEL: AGENT BLUEPRINT ── */}
        <div className="lg:col-span-7 flex flex-col h-full overflow-hidden bg-background">
          
          <div className="px-6 py-3 border-b border-border bg-surface/80 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2">
              <FileCode className="w-4 h-4 text-indigo-500" />
              <h2 className="text-xs font-bold text-primary uppercase tracking-wider">
                Live Agent Blueprint
              </h2>
            </div>
            <span className="text-[11px] text-secondary">
              Interactive Editable Specification
            </span>
          </div>

          {/* Blueprint Scrollable Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            
            {/* Card 1: Identity & Goal */}
            <div className="p-5 rounded-3xl border border-border bg-surface shadow-xs space-y-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <label className="text-[11px] font-bold text-secondary uppercase block mb-1">Agent Name</label>
                  <input
                    type="text"
                    value={blueprint.name}
                    onChange={(e) => setBlueprint({ ...blueprint, name: e.target.value })}
                    className="w-full text-base font-bold text-primary bg-transparent border-b border-border hover:border-primary focus:border-indigo-500 outline-none pb-1"
                  />
                </div>
                <div className="flex items-center gap-1.5">
                  <select
                    value={blueprint.riskLevel}
                    onChange={(e) => setBlueprint({ ...blueprint, riskLevel: e.target.value as any })}
                    className="px-2.5 py-1 rounded-xl text-xs font-bold bg-muted text-primary border border-border outline-none uppercase"
                  >
                    <option value="low">LOW RISK</option>
                    <option value="medium">MEDIUM RISK</option>
                    <option value="high">HIGH RISK</option>
                    <option value="critical">CRITICAL RISK</option>
                  </select>

                  <select
                    value={blueprint.approvalMode}
                    onChange={(e) => setBlueprint({ ...blueprint, approvalMode: e.target.value as any })}
                    className="px-2.5 py-1 rounded-xl text-xs font-bold bg-muted text-primary border border-border outline-none uppercase"
                  >
                    <option value="auto">AUTO</option>
                    <option value="review_required">REVIEW REQUIRED</option>
                    <option value="always_confirm">ALWAYS CONFIRM</option>
                    <option value="blocked">BLOCKED</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-[11px] font-bold text-secondary uppercase block mb-1">Description</label>
                <textarea
                  value={blueprint.description}
                  onChange={(e) => setBlueprint({ ...blueprint, description: e.target.value })}
                  rows={2}
                  className="w-full text-xs text-secondary bg-background p-2.5 rounded-xl border border-border outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-secondary uppercase block mb-1">Goal Statement</label>
                <input
                  type="text"
                  value={blueprint.goal}
                  onChange={(e) => setBlueprint({ ...blueprint, goal: e.target.value })}
                  className="w-full text-xs text-primary bg-background px-3 py-2 rounded-xl border border-border outline-none"
                />
              </div>
            </div>

            {/* Card 2: Trigger & Data Sources */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              
              {/* Trigger */}
              <div className="p-4 rounded-2xl border border-border bg-surface shadow-xs space-y-3">
                <div className="flex items-center gap-1.5 font-bold text-xs text-primary uppercase">
                  <Clock className="w-3.5 h-3.5 text-indigo-500" />
                  <span>Execution Trigger</span>
                </div>
                <div className="space-y-2 text-xs">
                  <div>
                    <span className="text-[11px] text-secondary block mb-1">Type</span>
                    <select
                      value={blueprint.trigger?.type || 'scheduled'}
                      onChange={(e) =>
                        setBlueprint({
                          ...blueprint,
                          trigger: { ...blueprint.trigger, type: e.target.value },
                        })
                      }
                      className="w-full px-3 py-1.5 rounded-lg border border-border bg-background text-primary outline-none"
                    >
                      <option value="scheduled">Scheduled (Cron)</option>
                      <option value="event">Event (Webhook)</option>
                      <option value="threshold">Threshold Alert</option>
                      <option value="user_request">User Request (On Demand)</option>
                    </select>
                  </div>
                  <div>
                    <span className="text-[11px] text-secondary block mb-1">Frequency / Event</span>
                    <input
                      type="text"
                      value={blueprint.trigger?.frequency || blueprint.trigger?.event || 'daily'}
                      onChange={(e) =>
                        setBlueprint({
                          ...blueprint,
                          trigger: { ...blueprint.trigger, frequency: e.target.value },
                        })
                      }
                      className="w-full px-3 py-1.5 rounded-lg border border-border bg-background text-primary outline-none"
                    />
                  </div>
                </div>
              </div>

              {/* Data Sources */}
              <div className="p-4 rounded-2xl border border-border bg-surface shadow-xs space-y-3">
                <div className="flex items-center gap-1.5 font-bold text-xs text-primary uppercase">
                  <Database className="w-3.5 h-3.5 text-cyan-500" />
                  <span>Data Sources ({blueprint.dataSources.length})</span>
                </div>
                <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                  {blueprint.dataSources.map((ds) => (
                    <span
                      key={ds}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-mono bg-cyan-500/10 text-cyan-700 dark:text-cyan-300 border border-cyan-500/20"
                    >
                      {ds}
                      <button
                        type="button"
                        onClick={() => removeDataSource(ds)}
                        className="hover:text-rose-500"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex items-center gap-1 pt-1">
                  <input
                    type="text"
                    value={newDataSource}
                    onChange={(e) => setNewDataSource(e.target.value)}
                    placeholder="Add source (e.g. payments)..."
                    className="flex-1 px-2.5 py-1 rounded-lg border border-border bg-background text-xs outline-none"
                  />
                  <button
                    type="button"
                    onClick={addDataSource}
                    className="p-1 rounded-lg bg-muted hover:bg-border text-primary text-xs"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

            </div>

            {/* Card 3: Connected MCP Tools */}
            <div className="p-5 rounded-3xl border border-border bg-surface shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 font-bold text-xs text-primary uppercase">
                  <Wrench className="w-3.5 h-3.5 text-indigo-500" />
                  <span>Connected MCP Tools ({blueprint.tools.length})</span>
                </div>
                <span className="text-[11px] text-secondary">Toggle tools to connect or disconnect</span>
              </div>

              <div className="flex flex-wrap gap-1.5 pt-1">
                {registeredTools.map((toolName) => {
                  const isAttached = blueprint.tools.includes(toolName);
                  return (
                    <button
                      key={toolName}
                      type="button"
                      onClick={() => toggleTool(toolName)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-mono transition cursor-pointer flex items-center gap-1.5 ${
                        isAttached
                          ? 'bg-indigo-600 text-white font-bold shadow-xs'
                          : 'bg-muted text-secondary hover:text-primary border border-border'
                      }`}
                    >
                      {isAttached && <CheckCircle2 className="w-3 h-3 text-white" />}
                      {toolName}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Card 4: Operational Logic & Rules */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              
              {/* Logic sequence */}
              <div className="p-4 rounded-2xl border border-border bg-surface shadow-xs space-y-3">
                <span className="font-bold text-xs text-primary uppercase block">
                  Operational Logic
                </span>
                <ul className="space-y-1.5 text-xs text-secondary max-h-36 overflow-y-auto">
                  {blueprint.logic.map((step, idx) => (
                    <li key={idx} className="flex items-center justify-between gap-2 p-1.5 rounded-lg bg-background border border-border">
                      <span className="truncate">{idx + 1}. {step}</span>
                      <button onClick={() => removeLogicStep(idx)} className="hover:text-rose-500">×</button>
                    </li>
                  ))}
                </ul>
                <div className="flex items-center gap-1 pt-1">
                  <input
                    type="text"
                    value={newLogic}
                    onChange={(e) => setNewLogic(e.target.value)}
                    placeholder="Add step..."
                    className="flex-1 px-2.5 py-1 rounded-lg border border-border bg-background text-xs outline-none"
                  />
                  <button onClick={addLogicStep} className="p-1 rounded-lg bg-muted hover:bg-border text-primary text-xs">
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Conditions / Thresholds */}
              <div className="p-4 rounded-2xl border border-border bg-surface shadow-xs space-y-3">
                <span className="font-bold text-xs text-primary uppercase block">
                  Rules & Threshold Conditions
                </span>
                <ul className="space-y-1.5 text-xs text-secondary max-h-36 overflow-y-auto">
                  {blueprint.conditions.map((cond, idx) => (
                    <li key={idx} className="flex items-center justify-between gap-2 p-1.5 rounded-lg bg-background border border-border font-mono text-[11px]">
                      <span className="truncate">{cond}</span>
                      <button onClick={() => removeCondition(idx)} className="hover:text-rose-500">×</button>
                    </li>
                  ))}
                </ul>
                <div className="flex items-center gap-1 pt-1">
                  <input
                    type="text"
                    value={newCondition}
                    onChange={(e) => setNewCondition(e.target.value)}
                    placeholder="Add rule condition..."
                    className="flex-1 px-2.5 py-1 rounded-lg border border-border bg-background text-xs outline-none"
                  />
                  <button onClick={addCondition} className="p-1 rounded-lg bg-muted hover:bg-border text-primary text-xs">
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

            </div>

            {/* Card 5: Actions & Notifications */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              
              {/* Actions */}
              <div className="p-4 rounded-2xl border border-border bg-surface shadow-xs space-y-3">
                <span className="font-bold text-xs text-primary uppercase block">
                  Authorized Actions
                </span>
                <ul className="space-y-1.5 text-xs text-secondary">
                  {blueprint.actions.map((act, idx) => (
                    <li key={idx} className="flex items-center justify-between gap-2 p-1.5 rounded-lg bg-background border border-border">
                      <span className="truncate">{act}</span>
                      <button onClick={() => removeActionItem(idx)} className="hover:text-rose-500">×</button>
                    </li>
                  ))}
                </ul>
                <div className="flex items-center gap-1 pt-1">
                  <input
                    type="text"
                    value={newAction}
                    onChange={(e) => setNewAction(e.target.value)}
                    placeholder="Add action..."
                    className="flex-1 px-2.5 py-1 rounded-lg border border-border bg-background text-xs outline-none"
                  />
                  <button onClick={addActionItem} className="p-1 rounded-lg bg-muted text-primary text-xs">
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Notifications */}
              <div className="p-4 rounded-2xl border border-border bg-surface shadow-xs space-y-3">
                <span className="font-bold text-xs text-primary uppercase block">
                  Notification Destinations
                </span>
                <ul className="space-y-1.5 text-xs text-secondary">
                  {blueprint.notifications.map((notif, idx) => (
                    <li key={idx} className="flex items-center justify-between gap-2 p-1.5 rounded-lg bg-background border border-border text-[11px] font-mono">
                      <span className="truncate">{notif}</span>
                      <button onClick={() => removeNotification(idx)} className="hover:text-rose-500">×</button>
                    </li>
                  ))}
                </ul>
                <div className="flex items-center gap-1 pt-1">
                  <input
                    type="text"
                    value={newNotification}
                    onChange={(e) => setNewNotification(e.target.value)}
                    placeholder="Add email or webhook..."
                    className="flex-1 px-2.5 py-1 rounded-lg border border-border bg-background text-xs outline-none"
                  />
                  <button onClick={addNotification} className="p-1 rounded-lg bg-muted text-primary text-xs">
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

            </div>

            {/* Card 6: Spending Limits & Guardrails */}
            <div className="p-5 rounded-3xl border border-amber-300/50 dark:border-amber-900/50 bg-amber-50/20 dark:bg-amber-950/10 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Lock className="w-4 h-4 text-amber-500" />
                  <span className="font-bold text-xs uppercase tracking-wider text-amber-800 dark:text-amber-300">
                    Deterministic Firewall Guardrails
                  </span>
                </div>
                <span className="text-[11px] text-amber-700 dark:text-amber-400 font-mono">
                  Enforced at Runtime
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="text-[11px] text-gray-500 dark:text-gray-400 block mb-1">Max Transaction (₹)</label>
                  <input
                    type="number"
                    value={blueprint.guardrails?.maxTransactionAmount || 5000}
                    onChange={(e) =>
                      setBlueprint({
                        ...blueprint,
                        guardrails: {
                          ...blueprint.guardrails,
                          maxTransactionAmount: parseFloat(e.target.value) || 0,
                        },
                      })
                    }
                    className="w-full px-3 py-1.5 rounded-xl border border-border bg-surface text-primary font-mono text-xs outline-none"
                  />
                </div>

                <div>
                  <label className="text-[11px] text-gray-500 dark:text-gray-400 block mb-1">Daily Spend Limit (₹)</label>
                  <input
                    type="number"
                    value={blueprint.guardrails?.dailySpendLimit || 10000}
                    onChange={(e) =>
                      setBlueprint({
                        ...blueprint,
                        guardrails: {
                          ...blueprint.guardrails,
                          dailySpendLimit: parseFloat(e.target.value) || 0,
                        },
                      })
                    }
                    className="w-full px-3 py-1.5 rounded-xl border border-border bg-surface text-primary font-mono text-xs outline-none"
                  />
                </div>

                <div>
                  <label className="text-[11px] text-gray-500 dark:text-gray-400 block mb-1">Approval Above (₹)</label>
                  <input
                    type="number"
                    value={blueprint.guardrails?.requireApprovalAbove || 2000}
                    onChange={(e) =>
                      setBlueprint({
                        ...blueprint,
                        guardrails: {
                          ...blueprint.guardrails,
                          requireApprovalAbove: parseFloat(e.target.value) || 0,
                        },
                      })
                    }
                    className="w-full px-3 py-1.5 rounded-xl border border-border bg-surface text-primary font-mono text-xs outline-none"
                  />
                </div>
              </div>
            </div>

          </div>

        </div>

      </div>

      {/* ── BOTTOM ACTION BAR: CREATE DRAFT / ACTIVATE ── */}
      <div className="h-16 border-t border-border bg-surface px-6 flex items-center justify-between shrink-0 shadow-lg">
        <div className="flex items-center gap-3 text-xs text-secondary">
          <span className="flex items-center gap-1.5 font-bold text-primary">
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            Blueprint Structured & Validated
          </span>
          <span>•</span>
          <span>{blueprint.tools.length} Tools Connected</span>
          <span>•</span>
          <span className="font-mono">₹{blueprint.guardrails.maxTransactionAmount} Max Cap</span>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            disabled={activating}
            onClick={handleSaveDraft}
            className="px-5 py-2 rounded-xl border border-border hover:bg-muted text-xs font-bold text-secondary hover:text-primary transition cursor-pointer"
          >
            Create Draft
          </button>

          <button
            type="button"
            disabled={activating}
            onClick={() => setShowPreActivation(true)}
            className="px-6 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white shadow-md shadow-indigo-600/25 transition flex items-center gap-2 cursor-pointer"
          >
            {activating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
            <span>Activate Agent</span>
          </button>
        </div>
      </div>

    </div>
  );
}
