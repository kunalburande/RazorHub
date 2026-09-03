import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Bot,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  Sliders,
  Wrench,
  Clock,
  Lock,
  RefreshCw,
  Plus,
  Trash2,
  Info,
  Check,
  Zap,
} from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';
import ConversationalAgentBuilder from './ConversationalAgentBuilder';


interface ToolItem {
  id: string;
  name: string;
  description: string;
  category: string;
  risk_level: string;
  requires_approval: boolean;
}

export default function AgentBuilder() {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [builderMode, setBuilderMode] = useState<'conversational' | 'stepper'>('conversational');
  const [step, setStep] = useState<1 | 2 | 3 | 4 | 5>(1);
  const [availableTools, setAvailableTools] = useState<ToolItem[]>([]);

  const [loadingTools, setLoadingTools] = useState(true);
  const [deploying, setDeploying] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Form State
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [systemPrompt, setSystemPrompt] = useState(
    'You are a specialized autonomous commerce agent. Analyze incoming data, verify constraints against governance guardrails, and invoke tools deterministically.'
  );
  const [approvalMode, setApprovalMode] = useState<'AUTO' | 'REVIEW_REQUIRED' | 'ALWAYS_CONFIRM' | 'BLOCKED'>('AUTO');
  const [riskLevel, setRiskLevel] = useState<'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'>('LOW');

  // Tools Selection
  const [selectedToolIds, setSelectedToolIds] = useState<string[]>([]);
  const [toolSearch, setToolSearch] = useState('');
  const [selectedToolCategory, setSelectedToolCategory] = useState('ALL');

  // Trigger State
  const [triggerType, setTriggerType] = useState<'USER_REQUEST' | 'SCHEDULE' | 'EVENT' | 'THRESHOLD'>('USER_REQUEST');
  const [triggerName, setTriggerName] = useState('Default Interactive Trigger');
  const [triggerConfig, setTriggerConfig] = useState('{}');

  // Governance Policy State
  const [maxTransactionAmount, setMaxTransactionAmount] = useState('5000.00');
  const [dailySpendLimit, setDailySpendLimit] = useState('15000.00');
  const [requireApprovalAbove, setRequireApprovalAbove] = useState('2000.00');
  const [blockedCategories, setBlockedCategories] = useState('cash, unknown');
  const [allowedMerchants, setAllowedMerchants] = useState('');
  const [requireHumanApproval, setRequireHumanApproval] = useState(false);
  const [requireDoubleConfirmation, setRequireDoubleConfirmation] = useState(false);

  // Fetch available registered tools
  useEffect(() => {
    async function loadTools() {
      setLoadingTools(true);
      try {
        const data = await apiRequest<any>('/agent-runtime/tools/', { token });
        const list = Array.isArray(data) ? data : data.results || [];
        setAvailableTools(list);
      } catch (err) {
        console.error('Failed to load registered tools:', err);
      } finally {
        setLoadingTools(false);
      }
    }
    loadTools();
  }, [token]);

  const toggleTool = (toolId: string) => {
    setSelectedToolIds((prev) =>
      prev.includes(toolId) ? prev.filter((id) => id !== toolId) : [...prev, toolId]
    );
  };

  const handleDeploy = async () => {
    if (!name.trim()) {
      setErrorMsg('Agent name is required.');
      setStep(1);
      return;
    }

    setDeploying(true);
    setErrorMsg(null);

    try {
      const payload = {
        name: name.trim(),
        description: description.trim(),
        system_prompt: systemPrompt.trim(),
        approval_mode: approvalMode,
        risk_level: riskLevel,
        status: 'ACTIVE',
        tool_ids: selectedToolIds,
        metadata: {
          custom_built: true,
          trigger_type: triggerType,
          trigger_name: triggerName,
        },
        governance_policy: {
          name: `${name.trim()} Guardrail Policy`,
          max_transaction_amount: parseFloat(maxTransactionAmount) || 5000,
          daily_spend_limit: parseFloat(dailySpendLimit) || 10000,
          require_approval_above: parseFloat(requireApprovalAbove) || 2000,
          blocked_categories: blockedCategories
            .split(',')
            .map((c) => c.trim())
            .filter(Boolean),
          allowed_merchants: allowedMerchants
            .split(',')
            .map((m) => m.trim())
            .filter(Boolean),
          require_human_approval: requireHumanApproval,
          require_double_confirmation: requireDoubleConfirmation,
        },
      };

      const newAgent = await apiRequest<any>('/agent-runtime/agents/', {
        token,
        method: 'POST',
        body: JSON.stringify(payload),
      });

      navigate(`/agents/${newAgent.id}`);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to deploy custom agent.');
      setDeploying(false);
    }
  };

  const toolCategories = ['ALL', ...Array.from(new Set(availableTools.map((t) => t.category.toUpperCase())))];

  const filteredTools = availableTools.filter((t) => {
    const matchesCat = selectedToolCategory === 'ALL' || t.category.toUpperCase() === selectedToolCategory;
    const matchesSearch =
      t.name.toLowerCase().includes(toolSearch.toLowerCase()) ||
      t.description.toLowerCase().includes(toolSearch.toLowerCase());
    return matchesCat && matchesSearch;
  });

  if (builderMode === 'conversational') {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-end px-2">
          <button
            type="button"
            onClick={() => setBuilderMode('stepper')}
            className="text-xs font-semibold text-secondary hover:text-primary flex items-center gap-1.5 transition cursor-pointer p-1 rounded-lg hover:bg-muted"
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Switch to Manual Stepper Form</span>
          </button>
        </div>
        <ConversationalAgentBuilder />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      
      {/* Top Breadcrumb & Title */}
      <div className="flex items-center justify-between">
        <div>
          <Link
            to="/agents"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-secondary hover:text-primary transition mb-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Agent Studio
          </Link>
          <h1 className="text-2xl sm:text-3xl font-black text-primary tracking-tight">
            Custom Agent Builder
          </h1>
          <p className="text-xs sm:text-sm text-secondary">
            Assemble an autonomous commerce agent with custom system prompts, MCP tool connections, and strict financial firewalls.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setBuilderMode('conversational')}
            className="px-3 py-1.5 rounded-xl border border-indigo-500/30 bg-indigo-50 dark:bg-indigo-950/40 text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/40 transition flex items-center gap-1.5 cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            Switch to AI Conversational Builder
          </button>
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-muted border border-border text-xs font-bold text-primary">
            Step {step} of 5
          </div>
        </div>
      </div>


      {/* Progress Stepper */}
      <div className="grid grid-cols-5 gap-2">
        {[
          { num: 1, label: 'Identity' },
          { num: 2, label: 'Tools' },
          { num: 3, label: 'Triggers' },
          { num: 4, label: 'Guardrails' },
          { num: 5, label: 'Deploy' },
        ].map((s) => (
          <button
            key={s.num}
            onClick={() => setStep(s.num as any)}
            className={`p-2.5 rounded-2xl text-xs font-bold text-center border transition ${
              step === s.num
                ? 'bg-primary text-surface border-primary shadow-sm'
                : step > s.num
                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30'
                : 'bg-surface text-secondary border-border hover:border-gray-400'
            }`}
          >
            <span className="block sm:inline mr-1">{s.num}.</span>
            {s.label}
          </button>
        ))}
      </div>

      {/* Error Banner */}
      {errorMsg && (
        <div className="p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs sm:text-sm flex items-center gap-3">
          <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Step Content Container */}
      <div className="p-6 sm:p-8 rounded-3xl border border-border/80 bg-surface shadow-xs space-y-6">
        
        {/* STEP 1: IDENTITY */}
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-bold text-primary">Agent Identity & Purpose</h2>
              <p className="text-xs text-secondary">Define the agent's core mission, risk profile, and initial system prompt.</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-primary uppercase tracking-wider mb-1.5">
                  Agent Name *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Supplier Reconciliation Bot"
                  className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-primary text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-primary uppercase tracking-wider mb-1.5">
                  Description
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Briefly state what this agent accomplishes autonomously..."
                  className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-primary text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-primary uppercase tracking-wider mb-1.5">
                  System Prompt *
                </label>
                <textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  rows={4}
                  className="w-full p-3.5 rounded-xl border border-border bg-background text-primary text-xs sm:text-sm font-mono focus:ring-2 focus:ring-indigo-500 outline-none"
                />
                <div className="mt-1 flex items-center justify-between text-[11px] text-secondary">
                  <span>Instruct the LLM on deterministic tool invocation and boundaries.</span>
                  <button
                    type="button"
                    onClick={() =>
                      setSystemPrompt(
                        'You are an autonomous treasury agent for RazorHub. Verify invoice references, calculate net balances, and prepare reconciliation reports. Adhere strictly to spending ceilings.'
                      )
                    }
                    className="text-indigo-600 dark:text-indigo-400 font-semibold hover:underline"
                  >
                    Load Preset Prompt
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div>
                  <label className="block text-xs font-bold text-primary uppercase tracking-wider mb-1.5">
                    Approval Mode
                  </label>
                  <select
                    value={approvalMode}
                    onChange={(e) => setApprovalMode(e.target.value as any)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-background text-primary text-xs sm:text-sm outline-none"
                  >
                    <option value="AUTO">AUTO (Automatic under thresholds)</option>
                    <option value="REVIEW_REQUIRED">REVIEW_REQUIRED (Human signs off mutations)</option>
                    <option value="ALWAYS_CONFIRM">ALWAYS_CONFIRM (Every action requires sign-off)</option>
                    <option value="BLOCKED">BLOCKED (ReadOnly only)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-primary uppercase tracking-wider mb-1.5">
                    Risk Classification
                  </label>
                  <select
                    value={riskLevel}
                    onChange={(e) => setRiskLevel(e.target.value as any)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-background text-primary text-xs sm:text-sm outline-none"
                  >
                    <option value="LOW">LOW (Read & Low Value)</option>
                    <option value="MEDIUM">MEDIUM (Moderate Inflows/Refunds)</option>
                    <option value="HIGH">HIGH (Escalations & Alerts)</option>
                    <option value="CRITICAL">CRITICAL (Direct Disbursements)</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* STEP 2: CONNECTED TOOLS */}
        {step === 2 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-bold text-primary">Connect MCP Tools</h2>
              <p className="text-xs text-secondary">
                Select tools the agent is authorized to invoke. All financial mutation tools undergo firewall validation.
              </p>
            </div>

            {/* Filter Chips */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <input
                type="text"
                value={toolSearch}
                onChange={(e) => setToolSearch(e.target.value)}
                placeholder="Search tools by name or purpose..."
                className="px-3.5 py-2 rounded-xl border border-border bg-background text-primary text-xs outline-none max-w-xs"
              />

              <div className="flex items-center gap-1 overflow-x-auto pb-1 scrollbar-none">
                {toolCategories.map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setSelectedToolCategory(cat)}
                    className={`px-3 py-1 rounded-lg text-xs font-semibold whitespace-nowrap transition ${
                      selectedToolCategory === cat
                        ? 'bg-primary text-surface'
                        : 'bg-muted text-secondary hover:text-primary'
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            {/* Tools Grid */}
            {loadingTools ? (
              <div className="py-12 text-center text-secondary text-xs">Loading registered tools...</div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[420px] overflow-y-auto pr-1">
                {filteredTools.map((tool) => {
                  const isSelected = selectedToolIds.includes(tool.id);
                  return (
                    <div
                      key={tool.id}
                      onClick={() => toggleTool(tool.id)}
                      className={`p-3.5 rounded-2xl border transition cursor-pointer flex items-start justify-between gap-2 ${
                        isSelected
                          ? 'bg-indigo-50/70 dark:bg-indigo-950/30 border-indigo-500/50 shadow-xs'
                          : 'bg-background hover:bg-muted/40 border-border'
                      }`}
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs text-primary font-mono">{tool.name}</span>
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-muted text-secondary uppercase">
                            {tool.category}
                          </span>
                        </div>
                        <p className="text-[11px] text-secondary line-clamp-2 leading-relaxed">
                          {tool.description}
                        </p>
                      </div>

                      <div
                        className={`w-5 h-5 rounded-lg border flex items-center justify-center shrink-0 mt-0.5 ${
                          isSelected
                            ? 'bg-indigo-600 border-indigo-600 text-white'
                            : 'border-border bg-surface'
                        }`}
                      >
                        {isSelected && <Check className="w-3.5 h-3.5" />}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="text-xs text-secondary font-medium pt-2 border-t border-border flex items-center justify-between">
              <span>Selected Tools: <strong>{selectedToolIds.length}</strong></span>
              {selectedToolIds.length > 0 && (
                <button
                  type="button"
                  onClick={() => setSelectedToolIds([])}
                  className="text-rose-500 hover:underline text-xs"
                >
                  Clear Selection
                </button>
              )}
            </div>
          </div>
        )}

        {/* STEP 3: TRIGGERS */}
        {step === 3 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-bold text-primary">Execution Triggers</h2>
              <p className="text-xs text-secondary">
                Configure how this agent wakes up and takes action.
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { type: 'USER_REQUEST', label: 'User Request', desc: 'Interactive prompts & playground' },
                { type: 'SCHEDULE', label: 'Schedule (Cron)', desc: 'Recurring background execution' },
                { type: 'EVENT', label: 'Webhook Event', desc: 'Reacts to platform commerce events' },
                { type: 'THRESHOLD', label: 'Threshold Alert', desc: 'Triggers when metrics spike' },
              ].map((t) => (
                <div
                  key={t.type}
                  onClick={() => setTriggerType(t.type as any)}
                  className={`p-3.5 rounded-2xl border text-left cursor-pointer transition ${
                    triggerType === t.type
                      ? 'bg-indigo-50/70 dark:bg-indigo-950/30 border-indigo-500 text-primary shadow-xs'
                      : 'bg-background border-border text-secondary hover:border-gray-400'
                  }`}
                >
                  <span className="font-bold text-xs block text-primary">{t.label}</span>
                  <span className="text-[11px] text-secondary mt-1 block leading-tight">{t.desc}</span>
                </div>
              ))}
            </div>

            <div className="space-y-4 pt-2">
              <div>
                <label className="block text-xs font-bold text-primary uppercase tracking-wider mb-1.5">
                  Trigger Name
                </label>
                <input
                  type="text"
                  value={triggerName}
                  onChange={(e) => setTriggerName(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-primary text-sm outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-primary uppercase tracking-wider mb-1.5">
                  Configuration JSON
                </label>
                <textarea
                  value={triggerConfig}
                  onChange={(e) => setTriggerConfig(e.target.value)}
                  rows={3}
                  className="w-full p-3 rounded-xl border border-border bg-background text-primary font-mono text-xs outline-none"
                />
              </div>
            </div>
          </div>
        )}

        {/* STEP 4: GUARDRAILS */}
        {step === 4 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-bold text-primary">Transaction Governance & Firewall Policy</h2>
              <p className="text-xs text-secondary">
                Deterministic rules enforced by the transaction firewall. The agent cannot bypass these limits.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-primary uppercase tracking-wider mb-1.5">
                  Max Single Transaction (₹)
                </label>
                <input
                  type="number"
                  value={maxTransactionAmount}
                  onChange={(e) => setMaxTransactionAmount(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-background text-primary text-sm font-mono outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-primary uppercase tracking-wider mb-1.5">
                  Daily Spend Velocity Limit (₹)
                </label>
                <input
                  type="number"
                  value={dailySpendLimit}
                  onChange={(e) => setDailySpendLimit(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-background text-primary text-sm font-mono outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-primary uppercase tracking-wider mb-1.5">
                  Human Sign-Off Above (₹)
                </label>
                <input
                  type="number"
                  value={requireApprovalAbove}
                  onChange={(e) => setRequireApprovalAbove(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-background text-primary text-sm font-mono outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-xs font-bold text-primary uppercase tracking-wider mb-1.5">
                  Blocked Categories
                </label>
                <input
                  type="text"
                  value={blockedCategories}
                  onChange={(e) => setBlockedCategories(e.target.value)}
                  placeholder="e.g. cash, electronics, unknown"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-background text-primary text-sm outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-primary uppercase tracking-wider mb-1.5">
                  Allowed Merchants (Optional)
                </label>
                <input
                  type="text"
                  value={allowedMerchants}
                  onChange={(e) => setAllowedMerchants(e.target.value)}
                  placeholder="e.g. approved_distributor, razorpay"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-background text-primary text-sm outline-none"
                />
              </div>
            </div>

            <div className="space-y-3 pt-2">
              <label className="flex items-center gap-2.5 text-xs text-primary font-medium cursor-pointer">
                <input
                  type="checkbox"
                  checked={requireHumanApproval}
                  onChange={(e) => setRequireHumanApproval(e.target.checked)}
                  className="rounded text-indigo-600"
                />
                <span>Mandate Human Approval for all financial mutations regardless of amount</span>
              </label>

              <label className="flex items-center gap-2.5 text-xs text-primary font-medium cursor-pointer">
                <input
                  type="checkbox"
                  checked={requireDoubleConfirmation}
                  onChange={(e) => setRequireDoubleConfirmation(e.target.checked)}
                  className="rounded text-indigo-600"
                />
                <span>Require Double Confirmation for high-risk executions</span>
              </label>
            </div>
          </div>
        )}

        {/* STEP 5: REVIEW & DEPLOY */}
        {step === 5 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-bold text-primary">Review & Deploy Agent</h2>
              <p className="text-xs text-secondary">
                Verify agent specifications before deploying to the autonomous runtime.
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-gray-50 dark:bg-gray-900/60 border border-border space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-base font-bold text-primary">{name || 'Unnamed Agent'}</h3>
                  <p className="text-xs text-secondary">{description || 'No description provided.'}</p>
                </div>
                <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 border border-indigo-500/30">
                  {approvalMode} • {riskLevel} RISK
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs pt-3 border-t border-border">
                <div>
                  <span className="text-secondary block text-[11px]">Connected Tools</span>
                  <span className="font-bold text-primary">{selectedToolIds.length} Tools</span>
                </div>
                <div>
                  <span className="text-secondary block text-[11px]">Trigger Type</span>
                  <span className="font-bold text-primary">{triggerType}</span>
                </div>
                <div>
                  <span className="text-secondary block text-[11px]">Max Transaction</span>
                  <span className="font-bold text-primary font-mono">₹{maxTransactionAmount}</span>
                </div>
                <div>
                  <span className="text-secondary block text-[11px]">Daily Limit</span>
                  <span className="font-bold text-primary font-mono">₹{dailySpendLimit}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Stepper Navigation Buttons */}
        <div className="pt-6 border-t border-border flex items-center justify-between">
          {step > 1 ? (
            <button
              type="button"
              onClick={() => setStep((step - 1) as any)}
              className="px-4 py-2.5 rounded-xl border border-border text-xs font-bold text-secondary hover:text-primary transition flex items-center gap-1.5"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Previous
            </button>
          ) : (
            <div />
          )}

          {step < 5 ? (
            <button
              type="button"
              onClick={() => setStep((step + 1) as any)}
              className="px-5 py-2.5 rounded-xl bg-primary text-surface text-xs font-bold hover:opacity-90 transition flex items-center gap-1.5"
            >
              Next
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <button
              type="button"
              disabled={deploying}
              onClick={handleDeploy}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/20 transition flex items-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {deploying ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Deploying to Studio...</span>
                </>
              ) : (
                <>
                  <Zap className="w-3.5 h-3.5" />
                  <span>Deploy Agent</span>
                </>
              )}
            </button>
          )}
        </div>

      </div>

    </div>
  );
}
