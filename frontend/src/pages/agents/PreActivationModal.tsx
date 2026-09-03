import React, { useState } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Lock,
  Wrench,
  Database,
  Activity,
  CheckCircle2,
  X,
  RefreshCw,
  Zap,
} from 'lucide-react';

interface PreActivationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  blueprint: any;
  loading?: boolean;
}

export default function PreActivationModal({
  isOpen,
  onClose,
  onConfirm,
  blueprint,
  loading = false,
}: PreActivationModalProps) {
  const [confirmed, setConfirmed] = useState(false);

  if (!isOpen || !blueprint) return null;

  const guardrails = blueprint.guardrails || {};
  const dataSources = blueprint.dataSources || [];
  const tools = blueprint.tools || [];
  const actions = blueprint.actions || [];
  const riskLevel = (blueprint.riskLevel || 'low').toUpperCase();
  const approvalMode = (blueprint.approvalMode || 'auto').toUpperCase();

  const getRiskBadge = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30">
            <ShieldAlert className="w-3.5 h-3.5" />
            CRITICAL RISK (Direct Disbursements)
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
            <AlertTriangle className="w-3.5 h-3.5" />
            HIGH RISK (Security Sentinel)
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30">
            <ShieldCheck className="w-3.5 h-3.5" />
            MEDIUM RISK (Refunds / Outflows)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
            <ShieldCheck className="w-3.5 h-3.5" />
            LOW RISK (Standard Read & Dunning)
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/75 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-white dark:bg-gray-900 rounded-3xl shadow-2xl border border-gray-200 dark:border-gray-800 overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="px-6 py-5 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between bg-gray-50/70 dark:bg-gray-950/60">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
              <Lock className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                Pre-Activation Security Verification
              </h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Verify agent scope, data access boundaries, and spending policies before going live.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body: All 6 Required Facets */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5 text-xs sm:text-sm">
          
          {/* Agent Header Summary */}
          <div className="p-4 rounded-2xl bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-200/60 dark:border-indigo-900/60 flex items-start justify-between gap-3">
            <div>
              <span className="text-[11px] font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider block">
                Target Agent
              </span>
              <h3 className="text-base font-extrabold text-gray-900 dark:text-gray-100">
                {blueprint.name}
              </h3>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                {blueprint.description}
              </p>
            </div>
            {getRiskBadge(riskLevel)}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            
            {/* 1. DATA ACCESS */}
            <div className="p-4 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-950/40 space-y-2">
              <div className="flex items-center gap-1.5 font-bold text-gray-900 dark:text-gray-100 text-xs uppercase tracking-wide">
                <Database className="w-4 h-4 text-cyan-500" />
                <span>1. Data Access Scope</span>
              </div>
              <p className="text-[11px] text-gray-500 dark:text-gray-400">
                Datasets this agent is authorized to query from platform databases:
              </p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {dataSources.map((ds: string) => (
                  <span
                    key={ds}
                    className="px-2.5 py-0.5 rounded-lg text-xs font-mono font-medium bg-cyan-500/15 text-cyan-700 dark:text-cyan-300 border border-cyan-500/30"
                  >
                    {ds}
                  </span>
                ))}
              </div>
            </div>

            {/* 2. TOOLS */}
            <div className="p-4 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-950/40 space-y-2">
              <div className="flex items-center gap-1.5 font-bold text-gray-900 dark:text-gray-100 text-xs uppercase tracking-wide">
                <Wrench className="w-4 h-4 text-indigo-500" />
                <span>2. Connected MCP Tools</span>
              </div>
              <p className="text-[11px] text-gray-500 dark:text-gray-400">
                Registered tools available to the LLM runtime:
              </p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {tools.map((tool: string) => (
                  <span
                    key={tool}
                    className="px-2.5 py-0.5 rounded-lg text-xs font-mono font-medium bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 border border-indigo-500/30"
                  >
                    {tool}
                  </span>
                ))}
              </div>
            </div>

            {/* 3. ACTIONS */}
            <div className="p-4 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-950/40 space-y-2">
              <div className="flex items-center gap-1.5 font-bold text-gray-900 dark:text-gray-100 text-xs uppercase tracking-wide">
                <Activity className="w-4 h-4 text-emerald-500" />
                <span>3. Authorized Actions</span>
              </div>
              <ul className="space-y-1 text-xs text-gray-700 dark:text-gray-300">
                {actions.map((act: string, idx: number) => (
                  <li key={idx} className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                    <span>{act}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* 4. APPROVALS */}
            <div className="p-4 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-950/40 space-y-2">
              <div className="flex items-center gap-1.5 font-bold text-gray-900 dark:text-gray-100 text-xs uppercase tracking-wide">
                <ShieldCheck className="w-4 h-4 text-amber-500" />
                <span>4. Approvals Policy</span>
              </div>
              <p className="text-xs text-gray-700 dark:text-gray-300">
                Approval Mode: <strong className="text-primary font-mono uppercase">{approvalMode}</strong>
              </p>
              <p className="text-[11px] text-gray-500 dark:text-gray-400">
                {approvalMode === 'AUTO'
                  ? 'Actions under threshold execute automatically; mutations above threshold halt for human review.'
                  : approvalMode === 'ALWAYS_CONFIRM'
                  ? 'Every single mutation requires explicit human sign-off with double confirmation.'
                  : 'Requires human review for financial mutations.'}
              </p>
            </div>

          </div>

          {/* 5. RISKS & 6. GUARDRAILS */}
          <div className="p-4 rounded-2xl border border-amber-300/50 dark:border-amber-900/50 bg-amber-50/40 dark:bg-amber-950/20 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs uppercase tracking-wide text-amber-800 dark:text-amber-300 flex items-center gap-1.5">
                <Lock className="w-4 h-4" />
                5. Risks & 6. Guardrail Ceilings
              </span>
              <span className="text-[11px] font-mono text-amber-700 dark:text-amber-400">
                Zero-Trust Firewall
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-2.5 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
                <span className="text-gray-500 dark:text-gray-400 text-[11px] block">Max Transaction</span>
                <span className="font-bold font-mono text-gray-900 dark:text-gray-100">
                  ₹{guardrails.maxTransactionAmount || 0}
                </span>
              </div>

              <div className="p-2.5 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
                <span className="text-gray-500 dark:text-gray-400 text-[11px] block">Daily Spend Limit</span>
                <span className="font-bold font-mono text-gray-900 dark:text-gray-100">
                  ₹{guardrails.dailySpendLimit || 0}
                </span>
              </div>

              <div className="p-2.5 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
                <span className="text-gray-500 dark:text-gray-400 text-[11px] block">Human Approval Above</span>
                <span className="font-bold font-mono text-gray-900 dark:text-gray-100">
                  ₹{guardrails.requireApprovalAbove || 0}
                </span>
              </div>
            </div>

            {guardrails.requireDoubleConfirmation && (
              <div className="text-[11px] text-rose-700 dark:text-rose-400 font-semibold flex items-center gap-1.5 pt-1">
                <ShieldAlert className="w-3.5 h-3.5" />
                Double confirmation enforced: Disbursements will mandate a secondary verification modal.
              </div>
            )}
          </div>

          {/* Mandatory Confirmation Checkbox */}
          <div className="pt-2 border-t border-gray-200 dark:border-gray-800">
            <label className="flex items-start gap-3 text-xs text-gray-900 dark:text-gray-100 font-medium cursor-pointer p-3 rounded-2xl bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-800">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
                className="mt-0.5 rounded text-indigo-600 focus:ring-indigo-500"
              />
              <span>
                I explicitly authorize this autonomous agent to operate with the defined Data Access, Connected Tools, and Transaction Guardrails.
              </span>
            </label>
          </div>

        </div>

        {/* Footer Buttons */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-800 bg-gray-50/70 dark:bg-gray-950/60 flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
          >
            Back to Blueprint
          </button>

          <button
            type="button"
            disabled={!confirmed || loading}
            onClick={onConfirm}
            className="px-6 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white shadow-lg shadow-indigo-600/20 disabled:opacity-50 transition flex items-center gap-2 cursor-pointer"
          >
            {loading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Zap className="w-4 h-4" />
            )}
            Confirm & Activate Agent
          </button>
        </div>

      </div>
    </div>
  );
}
