import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Bot,
  Save,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Lock,
  Wrench,
  Sliders,
  Check,
} from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';

export default function AgentConfigurationPage() {
  const { id } = useParams<{ id: string }>();
  const { token } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Agent Fields
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [approvalMode, setApprovalMode] = useState('AUTO');
  const [riskLevel, setRiskLevel] = useState('LOW');
  const [selectedToolIds, setSelectedToolIds] = useState<string[]>([]);

  // Policy Fields
  const [policyId, setPolicyId] = useState<string | null>(null);
  const [maxTransactionAmount, setMaxTransactionAmount] = useState('5000.00');
  const [dailySpendLimit, setDailySpendLimit] = useState('10000.00');
  const [weeklySpendLimit, setWeeklySpendLimit] = useState('40000.00');
  const [monthlySpendLimit, setMonthlySpendLimit] = useState('150000.00');
  const [requireApprovalAbove, setRequireApprovalAbove] = useState('2000.00');
  const [blockedCategories, setBlockedCategories] = useState('cash, unknown');
  const [allowedMerchants, setAllowedMerchants] = useState('');
  const [requireHumanApproval, setRequireHumanApproval] = useState(false);
  const [requireDoubleConfirmation, setRequireDoubleConfirmation] = useState(false);

  // Available Tools
  const [availableTools, setAvailableTools] = useState<any[]>([]);

  useEffect(() => {
    async function loadData() {
      if (!id) return;
      setLoading(true);
      try {
        const [agentData, toolsData] = await Promise.all([
          apiRequest<any>(`/agent-runtime/agents/${id}/`, { token }),
          apiRequest<any>('/agent-runtime/tools/', { token }),
        ]);

        setName(agentData.name || '');
        setDescription(agentData.description || '');
        setSystemPrompt(agentData.system_prompt || '');
        setApprovalMode(agentData.approval_mode || 'AUTO');
        setRiskLevel(agentData.risk_level || 'LOW');
        setSelectedToolIds(agentData.tools?.map((t: any) => t.id) || []);

        const gov = agentData.governance_policy;
        if (gov) {
          setPolicyId(gov.id);
          setMaxTransactionAmount(String(gov.max_transaction_amount || '5000.00'));
          setDailySpendLimit(String(gov.daily_spend_limit || '10000.00'));
          setWeeklySpendLimit(String(gov.weekly_spend_limit || '40000.00'));
          setMonthlySpendLimit(String(gov.monthly_spend_limit || '150000.00'));
          setRequireApprovalAbove(String(gov.require_approval_above || '2000.00'));
          setBlockedCategories(Array.isArray(gov.blocked_categories) ? gov.blocked_categories.join(', ') : '');
          setAllowedMerchants(Array.isArray(gov.allowed_merchants) ? gov.allowed_merchants.join(', ') : '');
          setRequireHumanApproval(Boolean(gov.require_human_approval));
          setRequireDoubleConfirmation(Boolean(gov.require_double_confirmation));
        }

        const toolsList = Array.isArray(toolsData) ? toolsData : toolsData.results || [];
        setAvailableTools(toolsList);
      } catch (err: any) {
        setErrorMsg(err.message || 'Failed to load agent configuration.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id, token]);

  const toggleTool = (toolId: string) => {
    setSelectedToolIds((prev) =>
      prev.includes(toolId) ? prev.filter((t) => t !== toolId) : [...prev, toolId]
    );
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setSaving(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      // 1. Update Agent
      await apiRequest(`/agent-runtime/agents/${id}/`, {
        token,
        method: 'PATCH',
        body: JSON.stringify({
          name: name.trim(),
          description: description.trim(),
          system_prompt: systemPrompt.trim(),
          approval_mode: approvalMode,
          risk_level: riskLevel,
          tool_ids: selectedToolIds,
        }),
      });

      // 2. Update Governance Policy
      const policyPayload = {
        agent: id,
        name: `${name.trim()} Policy`,
        max_transaction_amount: parseFloat(maxTransactionAmount) || 5000,
        daily_spend_limit: parseFloat(dailySpendLimit) || 10000,
        weekly_spend_limit: parseFloat(weeklySpendLimit) || 40000,
        monthly_spend_limit: parseFloat(monthlySpendLimit) || 150000,
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
      };

      if (policyId) {
        await apiRequest(`/agent-runtime/governance-policies/${policyId}/`, {
          token,
          method: 'PATCH',
          body: JSON.stringify(policyPayload),
        });
      } else {
        const createdPolicy = await apiRequest<any>('/agent-runtime/governance-policies/', {
          token,
          method: 'POST',
          body: JSON.stringify(policyPayload),
        });
        setPolicyId(createdPolicy.id);
      }

      setSuccessMsg('Agent configuration and governance guardrails updated successfully!');
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to save configuration.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="py-24 text-center space-y-3">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-500 mx-auto" />
        <p className="text-sm text-secondary">Loading agent configuration...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      
      {/* Top Header */}
      <div>
        <Link
          to={`/agents/${id}`}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-secondary hover:text-primary transition mb-1"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Command Center
        </Link>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl sm:text-3xl font-black text-primary tracking-tight">
            Agent Configuration & Guardrails
          </h1>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="px-5 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-md transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            {saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            Save Changes
          </button>
        </div>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 text-xs sm:text-sm flex items-center gap-3">
          <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs sm:text-sm flex items-center gap-3">
          <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Form Container */}
      <form onSubmit={handleSave} className="space-y-8">
        
        {/* Section 1: Core Parameters */}
        <div className="p-6 sm:p-8 rounded-3xl border border-border/80 bg-surface shadow-xs space-y-5">
          <div className="border-b border-border pb-3">
            <h2 className="text-base font-bold text-primary">Core Identity & Prompt</h2>
            <p className="text-xs text-secondary">Tune prompt logic and operational modes.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-primary uppercase mb-1.5">Agent Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-primary text-sm outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-primary uppercase mb-1.5">Description</label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-primary text-sm outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-primary uppercase mb-1.5">System Prompt</label>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              rows={4}
              className="w-full p-3.5 rounded-xl border border-border bg-background text-primary font-mono text-xs sm:text-sm outline-none"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-primary uppercase mb-1.5">Approval Mode</label>
              <select
                value={approvalMode}
                onChange={(e) => setApprovalMode(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-background text-primary text-xs sm:text-sm outline-none"
              >
                <option value="AUTO">AUTO (Automatic under limits)</option>
                <option value="REVIEW_REQUIRED">REVIEW_REQUIRED (Manual sign-off)</option>
                <option value="ALWAYS_CONFIRM">ALWAYS_CONFIRM (Every action requires confirm)</option>
                <option value="BLOCKED">BLOCKED (Disabled)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-primary uppercase mb-1.5">Risk Rating</label>
              <select
                value={riskLevel}
                onChange={(e) => setRiskLevel(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-background text-primary text-xs sm:text-sm outline-none"
              >
                <option value="LOW">LOW</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="HIGH">HIGH</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </div>
          </div>
        </div>

        {/* Section 2: MCP Tools */}
        <div className="p-6 sm:p-8 rounded-3xl border border-border/80 bg-surface shadow-xs space-y-5">
          <div className="border-b border-border pb-3">
            <h2 className="text-base font-bold text-primary">Connected MCP Tools</h2>
            <p className="text-xs text-secondary">
              Toggle which Model Context Protocol tools are accessible to this agent.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-80 overflow-y-auto pr-1">
            {availableTools.map((tool) => {
              const isChecked = selectedToolIds.includes(tool.id);
              return (
                <div
                  key={tool.id}
                  onClick={() => toggleTool(tool.id)}
                  className={`p-3.5 rounded-2xl border transition cursor-pointer flex items-start justify-between gap-2 ${
                    isChecked
                      ? 'bg-indigo-50/70 dark:bg-indigo-950/30 border-indigo-500/50'
                      : 'bg-background hover:bg-muted/40 border-border'
                  }`}
                >
                  <div className="space-y-1">
                    <span className="font-bold text-xs font-mono text-primary">{tool.name}</span>
                    <p className="text-[11px] text-secondary line-clamp-1">{tool.description}</p>
                  </div>
                  <div
                    className={`w-5 h-5 rounded-lg border flex items-center justify-center shrink-0 mt-0.5 ${
                      isChecked ? 'bg-indigo-600 border-indigo-600 text-white' : 'border-border bg-surface'
                    }`}
                  >
                    {isChecked && <Check className="w-3.5 h-3.5" />}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Section 3: Spending Policies & Guardrails */}
        <div className="p-6 sm:p-8 rounded-3xl border border-border/80 bg-surface shadow-xs space-y-5">
          <div className="border-b border-border pb-3 flex items-center gap-2">
            <Lock className="w-4 h-4 text-indigo-500" />
            <div>
              <h2 className="text-base font-bold text-primary">Transaction Governance & Spending Policies</h2>
              <p className="text-xs text-secondary">Strict ceilings enforced by the deterministic firewall.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-bold text-primary uppercase mb-1.5">
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
              <label className="block text-xs font-bold text-primary uppercase mb-1.5">
                Daily Spend Limit (₹)
              </label>
              <input
                type="number"
                value={dailySpendLimit}
                onChange={(e) => setDailySpendLimit(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-background text-primary text-sm font-mono outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-primary uppercase mb-1.5">
                Approval Required Above (₹)
              </label>
              <input
                type="number"
                value={requireApprovalAbove}
                onChange={(e) => setRequireApprovalAbove(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-background text-primary text-sm font-mono outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-primary uppercase mb-1.5">
                Blocked Categories
              </label>
              <input
                type="text"
                value={blockedCategories}
                onChange={(e) => setBlockedCategories(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-background text-primary text-sm outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-primary uppercase mb-1.5">
                Allowed Merchants
              </label>
              <input
                type="text"
                value={allowedMerchants}
                onChange={(e) => setAllowedMerchants(e.target.value)}
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
              <span>Require human approval for all mutations regardless of amount</span>
            </label>

            <label className="flex items-center gap-2.5 text-xs text-primary font-medium cursor-pointer">
              <input
                type="checkbox"
                checked={requireDoubleConfirmation}
                onChange={(e) => setRequireDoubleConfirmation(e.target.checked)}
                className="rounded text-indigo-600"
              />
              <span>Enforce double confirmation on high-risk disbursements</span>
            </label>
          </div>
        </div>

        {/* Submit */}
        <div className="flex justify-end gap-3">
          <Link
            to={`/agents/${id}`}
            className="px-5 py-2.5 rounded-xl border border-border text-xs font-bold text-secondary hover:text-primary transition"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            {saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            Save Configuration
          </button>
        </div>

      </form>

    </div>
  );
}
