import React, { useState, useEffect } from 'react';
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Lock,
  Building2,
  DollarSign,
  AlertCircle,
  FileText,
  User,
  Check,
  X,
  Clock,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import { apiRequest } from '../lib/api';
import { useAuth } from '../context/AuthContext';

export interface AgentApprovalItem {
  approval_id: string;
  execution?: string | null;
  agent_id?: string | null;
  agent_name?: string;
  action?: string;
  requested_action: string;
  action_payload?: Record<string, any>;
  reason: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  amount?: string | number | null;
  merchant?: string;
  risk_score: number;
  policy_triggered?: string;
  requires_double_confirmation: boolean;
  is_double_confirmed: boolean;
  created_at: string;
}

interface HumanApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDecided?: (approvalId: string, decision: 'APPROVED' | 'REJECTED') => void;
  initialApprovalId?: string | null;
}

export default function HumanApprovalModal({
  isOpen,
  onClose,
  onDecided,
  initialApprovalId,
}: HumanApprovalModalProps) {
  const { token } = useAuth();
  const [approvals, setApprovals] = useState<AgentApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedApproval, setSelectedApproval] = useState<AgentApprovalItem | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Double confirmation state for high risk actions
  const [showDoubleConfirm, setShowDoubleConfirm] = useState(false);
  const [doubleConfirmChecked, setDoubleConfirmChecked] = useState(false);
  const [rejectNotes, setRejectNotes] = useState('');
  const [showRejectPrompt, setShowRejectPrompt] = useState(false);

  const fetchApprovals = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await apiRequest<any>('/agent-runtime/approvals/?status=PENDING', { token });
      const items: AgentApprovalItem[] = Array.isArray(data) ? data : data.results || [];
      setApprovals(items);
      if (items.length > 0) {
        if (initialApprovalId) {
          const found = items.find((a) => a.approval_id === initialApprovalId);
          setSelectedApproval(found || items[0]);
        } else if (!selectedApproval || !items.some(a => a.approval_id === selectedApproval.approval_id)) {
          setSelectedApproval(items[0]);
        }
      } else {
        setSelectedApproval(null);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load pending agent approvals.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchApprovals();
      setShowDoubleConfirm(false);
      setDoubleConfirmChecked(false);
      setShowRejectPrompt(false);
      setRejectNotes('');
    }
  }, [isOpen, initialApprovalId]);

  if (!isOpen) return null;

  const handleInitiateApprove = () => {
    if (!selectedApproval) return;
    // Check if this action mandates double confirmation
    const isHighRisk =
      selectedApproval.requires_double_confirmation ||
      (selectedApproval.risk_score !== undefined && selectedApproval.risk_score >= 0.75);

    if (isHighRisk) {
      setShowDoubleConfirm(true);
    } else {
      executeDecision('APPROVED');
    }
  };

  const executeDecision = async (decision: 'APPROVED' | 'REJECTED', doubleConfirmed = false) => {
    if (!selectedApproval) return;
    setActionLoading(true);
    setErrorMsg(null);
    try {
      await apiRequest(`/agent-runtime/approvals/${selectedApproval.approval_id}/decide/`, {
        token,
        method: 'POST',
        body: JSON.stringify({
          decision,
          double_confirmed: doubleConfirmed,
          notes: decision === 'REJECTED' ? rejectNotes : '',
        }),
      });

      setSuccessMsg(`Action successfully ${decision.toLowerCase()}.`);
      setTimeout(() => setSuccessMsg(null), 3000);

      if (onDecided) {
        onDecided(selectedApproval.approval_id, decision);
      }

      setShowDoubleConfirm(false);
      setDoubleConfirmChecked(false);
      setShowRejectPrompt(false);
      setRejectNotes('');

      // Refresh list
      await fetchApprovals();
    } catch (err: any) {
      setErrorMsg(err.message || `Failed to record decision for approval.`);
    } finally {
      setActionLoading(false);
    }
  };

  const formatCurrency = (val: string | number | null | undefined) => {
    if (val === null || val === undefined || val === '') return '—';
    const num = typeof val === 'string' ? parseFloat(val) : val;
    if (isNaN(num)) return '—';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(num);
  };

  const getRiskBadge = (score: number) => {
    if (score >= 0.8) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30">
          <ShieldAlert className="w-3.5 h-3.5 animate-pulse" />
          CRITICAL ({Math.round(score * 100)}%)
        </span>
      );
    }
    if (score >= 0.65) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
          <AlertTriangle className="w-3.5 h-3.5" />
          HIGH RISK ({Math.round(score * 100)}%)
        </span>
      );
    }
    if (score >= 0.4) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30">
          <Shield className="w-3.5 h-3.5" />
          MEDIUM ({Math.round(score * 100)}%)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
        <ShieldCheck className="w-3.5 h-3.5" />
        LOW RISK ({Math.round(score * 100)}%)
      </span>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/70 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-800 overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between bg-gradient-to-r from-gray-50 via-white to-gray-50 dark:from-gray-900 dark:via-gray-900/80 dark:to-gray-900">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-500/10 dark:bg-amber-400/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                  Transaction Governance Firewall
                </h2>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-100 dark:bg-amber-950/50 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
                  Human Approval Required
                </span>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Review and authorize autonomous AI agent financial mutations before execution.
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={fetchApprovals}
              disabled={loading}
              title="Refresh pending approvals"
              className="p-2 rounded-lg text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Feedback Messages */}
        {errorMsg && (
          <div className="mx-6 mt-4 p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-sm flex items-center gap-2.5">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
            <span>{errorMsg}</span>
          </div>
        )}
        {successMsg && (
          <div className="mx-6 mt-4 p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 text-emerald-700 dark:text-emerald-300 text-sm flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-500" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && approvals.length === 0 ? (
            <div className="py-16 text-center text-gray-500 dark:text-gray-400 space-y-3">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-amber-500" />
              <p className="text-sm">Querying pending governance approvals from runtime...</p>
            </div>
          ) : approvals.length === 0 ? (
            <div className="py-16 text-center space-y-4">
              <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 mx-auto flex items-center justify-center">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <div className="max-w-md mx-auto">
                <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                  No Pending Approvals
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  All agent executions are either within automatic approval thresholds or have already been authorized.
                </p>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              
              {/* Left Column: Approval List */}
              <div className="lg:col-span-5 space-y-3">
                <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-1">
                  Pending Actions ({approvals.length})
                </div>
                <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
                  {approvals.map((appr) => {
                    const isSelected = selectedApproval?.approval_id === appr.approval_id;
                    return (
                      <div
                        key={appr.approval_id}
                        onClick={() => {
                          setSelectedApproval(appr);
                          setShowDoubleConfirm(false);
                          setShowRejectPrompt(false);
                        }}
                        className={`p-4 rounded-xl border transition cursor-pointer text-left ${
                          isSelected
                            ? 'bg-amber-50/70 dark:bg-amber-950/20 border-amber-500/50 shadow-sm'
                            : 'bg-white dark:bg-gray-800/40 border-gray-200 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-700'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <span className="font-semibold text-sm text-gray-900 dark:text-gray-100 line-clamp-1">
                            {appr.action || appr.requested_action}
                          </span>
                          {getRiskBadge(appr.risk_score)}
                        </div>
                        
                        <div className="mt-2 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                          <span className="font-bold text-gray-900 dark:text-gray-200 text-sm">
                            {formatCurrency(appr.amount)}
                          </span>
                          <span>{appr.agent_name || 'Autonomous Agent'}</span>
                        </div>
                        
                        <p className="mt-1.5 text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                          {appr.reason}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Right Column: Active Approval Detail */}
              {selectedApproval && (
                <div className="lg:col-span-7 bg-gray-50/70 dark:bg-gray-950/40 border border-gray-200 dark:border-gray-800 rounded-xl p-5 flex flex-col justify-between">
                  
                  {/* Detailed Specification */}
                  <div className="space-y-4">
                    <div className="flex items-start justify-between gap-2 border-b border-gray-200 dark:border-gray-800 pb-3">
                      <div>
                        <span className="text-xs font-semibold text-amber-600 dark:text-amber-400 uppercase tracking-wide">
                          Action Payload
                        </span>
                        <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                          {selectedApproval.action || selectedApproval.requested_action}
                        </h3>
                      </div>
                      <div>
                        {getRiskBadge(selectedApproval.risk_score)}
                      </div>
                    </div>

                    {/* Metadata Grid */}
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div className="p-3 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
                        <span className="text-xs text-gray-500 dark:text-gray-400 block">Amount</span>
                        <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
                          {formatCurrency(selectedApproval.amount)}
                        </span>
                      </div>

                      <div className="p-3 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
                        <span className="text-xs text-gray-500 dark:text-gray-400 block">Merchant / Target</span>
                        <span className="font-semibold text-gray-900 dark:text-gray-100 truncate block">
                          {selectedApproval.merchant || 'Standard Partner'}
                        </span>
                      </div>

                      <div className="p-3 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
                        <span className="text-xs text-gray-500 dark:text-gray-400 block">Requesting Agent</span>
                        <span className="font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-1.5">
                          <User className="w-3.5 h-3.5 text-gray-400" />
                          {selectedApproval.agent_name || 'Shopping Agent'}
                        </span>
                      </div>

                      <div className="p-3 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
                        <span className="text-xs text-gray-500 dark:text-gray-400 block">Policy Triggered</span>
                        <span className="font-mono text-xs text-amber-600 dark:text-amber-400 truncate block">
                          {selectedApproval.policy_triggered || 'REQUIRE_APPROVAL_ABOVE'}
                        </span>
                      </div>
                    </div>

                    {/* Reason Box */}
                    <div className="p-3.5 rounded-lg bg-amber-50/60 dark:bg-amber-950/20 border border-amber-300/40 dark:border-amber-800/40 text-sm">
                      <span className="text-xs font-bold text-amber-800 dark:text-amber-300 block mb-1">
                        Reason for Human Approval:
                      </span>
                      <p className="text-xs sm:text-sm text-gray-800 dark:text-gray-200 leading-relaxed">
                        {selectedApproval.reason}
                      </p>
                    </div>

                    {/* Double Confirmation Interstitial for High-Risk Actions */}
                    {showDoubleConfirm ? (
                      <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/40 text-left space-y-3 animate-in fade-in zoom-in-95">
                        <div className="flex items-center gap-2 text-rose-600 dark:text-rose-400 font-bold text-sm">
                          <ShieldAlert className="w-4 h-4 animate-bounce" />
                          Double Confirmation Required (High-Risk Mutation)
                        </div>
                        <p className="text-xs text-gray-700 dark:text-gray-300">
                          This operation involves a high-risk financial mutation ({formatCurrency(selectedApproval.amount)}) that cannot be automated without secondary human verification.
                        </p>
                        
                        <label className="flex items-start gap-2.5 text-xs text-gray-900 dark:text-gray-100 font-medium cursor-pointer pt-1">
                          <input
                            type="checkbox"
                            checked={doubleConfirmChecked}
                            onChange={(e) => setDoubleConfirmChecked(e.target.checked)}
                            className="mt-0.5 rounded text-amber-600 focus:ring-amber-500 border-gray-300 dark:border-gray-700"
                          />
                          <span>
                            I explicitly verify this transaction details and authorize immediate execution.
                          </span>
                        </label>

                        <div className="flex items-center justify-end gap-2 pt-2 border-t border-rose-500/20">
                          <button
                            type="button"
                            onClick={() => setShowDoubleConfirm(false)}
                            className="px-3 py-1.5 text-xs font-semibold text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                          >
                            Cancel
                          </button>
                          <button
                            type="button"
                            disabled={!doubleConfirmChecked || actionLoading}
                            onClick={() => executeDecision('APPROVED', true)}
                            className="px-4 py-1.5 text-xs font-bold rounded-lg bg-rose-600 hover:bg-rose-700 text-white disabled:opacity-50 transition flex items-center gap-1.5"
                          >
                            {actionLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                            Confirm & Execute
                          </button>
                        </div>
                      </div>
                    ) : showRejectPrompt ? (
                      <div className="p-4 rounded-xl bg-gray-100 dark:bg-gray-800/80 border border-gray-300 dark:border-gray-700 text-left space-y-3">
                        <div className="text-xs font-bold text-gray-900 dark:text-gray-100">
                          Provide Rejection Justification
                        </div>
                        <textarea
                          value={rejectNotes}
                          onChange={(e) => setRejectNotes(e.target.value)}
                          placeholder="State reason for denying this transaction (e.g. Unverified vendor, amount exceeds project budget)..."
                          className="w-full text-xs p-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-1 focus:ring-amber-500"
                          rows={2}
                        />
                        <div className="flex items-center justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => setShowRejectPrompt(false)}
                            className="px-3 py-1.5 text-xs font-semibold text-gray-600 dark:text-gray-400 hover:text-gray-800"
                          >
                            Back
                          </button>
                          <button
                            type="button"
                            disabled={actionLoading}
                            onClick={() => executeDecision('REJECTED')}
                            className="px-4 py-1.5 text-xs font-bold rounded-lg bg-rose-600 hover:bg-rose-700 text-white disabled:opacity-50 transition flex items-center gap-1.5"
                          >
                            {actionLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                            Confirm Rejection
                          </button>
                        </div>
                      </div>
                    ) : null}
                  </div>

                  {/* Bottom Action Buttons */}
                  {!showDoubleConfirm && !showRejectPrompt && (
                    <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-800 flex items-center justify-between gap-3">
                      <button
                        type="button"
                        disabled={actionLoading}
                        onClick={() => setShowRejectPrompt(true)}
                        className="px-4 py-2.5 rounded-xl text-sm font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 border border-rose-200 dark:border-rose-900 transition flex items-center gap-2"
                      >
                        <XCircle className="w-4 h-4" />
                        Reject Action
                      </button>

                      <button
                        type="button"
                        disabled={actionLoading}
                        onClick={handleInitiateApprove}
                        className="px-6 py-2.5 rounded-xl text-sm font-bold bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg shadow-emerald-600/20 transition flex items-center gap-2"
                      >
                        {actionLoading ? (
                          <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                          <CheckCircle2 className="w-4 h-4" />
                        )}
                        Approve Action
                      </button>
                    </div>
                  )}

                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-950 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span className="flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5 text-gray-400" />
            Deterministic Zero-Trust Governance Firewall
          </span>
          <span>
            {approvals.length} pending authorization{approvals.length === 1 ? '' : 's'}
          </span>
        </div>

      </div>
    </div>
  );
}
