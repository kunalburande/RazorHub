import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  Sliders,
  CheckCircle2,
  Sparkles,
  Zap,
  Activity,
  ChevronRight,
  TrendingUp,
  Cpu,
  Lock,
  Globe,
  Smartphone,
  CreditCard,
  UserCheck,
  History,
  AlertOctagon,
} from 'lucide-react';
import { apiRequest } from '../lib/api';
import { useAuth } from '../context/AuthContext';

interface RuleBreakdownItem {
  rule_id: string;
  rule_name: string;
  points: number;
  reason: string;
  is_critical: boolean;
  details: any;
}

interface RiskEvaluationResponse {
  riskScore: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  reasons: string[];
  critical_rule_triggered: boolean;
  rule_breakdown: RuleBreakdownItem[];
  explanation: string;
  record_id?: string;
}

interface RiskHistoryRecord {
  id: string;
  transaction_amount: string | number;
  risk_score: number;
  risk_level: string;
  reasons: string[];
  critical_rule_triggered: boolean;
  explanation: string;
  created_at: string;
}

export default function RiskEnginePage({ embedded = false }: { embedded?: boolean }) {
  const { token } = useAuth();

  // Inputs state
  const [amount, setAmount] = useState<number>(21000);
  const [customerAvg, setCustomerAvg] = useState<number>(5000);
  const [failedAttempts, setFailedAttempts] = useState<number>(7);
  const [customerAgeDays, setCustomerAgeDays] = useState<number>(180);
  const [category, setCategory] = useState<string>('crypto');
  const [isNewDevice, setIsNewDevice] = useState<boolean>(true);
  const [isVpnProxy, setIsVpnProxy] = useState<boolean>(false);
  const [isNewMerchant, setIsNewMerchant] = useState<boolean>(true);
  const [isImpossibleTravel, setIsImpossibleTravel] = useState<boolean>(false);
  const [countryMismatch, setCountryMismatch] = useState<boolean>(false);
  const [txns10m, setTxns10m] = useState<number>(1);
  const [chargebackCount, setChargebackCount] = useState<number>(0);

  // Evaluation & LLM state
  const [includeLlm, setIncludeLlm] = useState<boolean>(false);
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [evaluation, setEvaluation] = useState<RiskEvaluationResponse | null>(null);
  const [history, setHistory] = useState<RiskHistoryRecord[]>([]);

  useEffect(() => {
    // Initial evaluation with prompt default
    handleEvaluate();
    loadHistory();
  }, [token]);

  const loadHistory = async () => {
    try {
      const data = await apiRequest<RiskHistoryRecord[]>('/agent-runtime/risk/history/', { token });
      setHistory(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error('Failed to load risk history', e);
    }
  };

  const handleEvaluate = async (customInputs?: any, withLlm?: boolean) => {
    try {
      setEvaluating(true);
      const inputsPayload = customInputs || {
        transaction_amount: amount,
        customer_avg_amount: customerAvg,
        customer_age_days: customerAgeDays,
        failed_attempts: failedAttempts,
        category: category,
        device: {
          is_new_device: isNewDevice,
          is_vpn_proxy: isVpnProxy,
        },
        merchant_history: {
          is_new: isNewMerchant,
        },
        location: {
          is_impossible_travel: isImpossibleTravel,
          distance_km: isImpossibleTravel ? 4800 : 0,
          current_country: countryMismatch ? 'RU' : 'IN',
          home_country: 'IN',
        },
        velocity: {
          txns_last_10m: txns10m,
        },
        chargeback_history: {
          chargeback_count: chargebackCount,
        },
      };

      const res = await apiRequest<RiskEvaluationResponse>('/agent-runtime/risk/evaluate/', {
        token,
        method: 'POST',
        body: JSON.stringify({
          inputs: inputsPayload,
          include_llm_explanation: withLlm !== undefined ? withLlm : includeLlm,
          save_record: true,
        }),
      });

      setEvaluation(res);
      await loadHistory();
    } catch (e: any) {
      alert(`Risk evaluation failed: ${e.message}`);
    } finally {
      setEvaluating(false);
    }
  };

  const applyPreset = (preset: string) => {
    if (preset === 'prompt_example') {
      setAmount(21000);
      setCustomerAvg(5000);
      setFailedAttempts(7);
      setIsNewDevice(true);
      setIsVpnProxy(false);
      setIsNewMerchant(true);
      setCategory('crypto');
      setIsImpossibleTravel(false);
      setCountryMismatch(false);
      setTxns10m(1);
      setChargebackCount(0);
      setCustomerAgeDays(180);
      handleEvaluate({
        transaction_amount: 21000,
        customer_avg_amount: 5000,
        failed_attempts: 7,
        device: { is_new_device: true },
        merchant_history: { is_new: true },
        category: 'crypto',
      });
    } else if (preset === 'impossible_travel') {
      setAmount(4500);
      setCustomerAvg(4000);
      setFailedAttempts(0);
      setIsNewDevice(true);
      setIsImpossibleTravel(true);
      setCountryMismatch(true);
      setCategory('services');
      handleEvaluate({
        transaction_amount: 4500,
        customer_avg_amount: 4000,
        location: { is_impossible_travel: true, distance_km: 5200, current_country: 'RU', home_country: 'IN' },
        device: { is_new_device: true },
        category: 'services',
      });
    } else if (preset === 'clean_low_risk') {
      setAmount(1250);
      setCustomerAvg(1500);
      setFailedAttempts(0);
      setIsNewDevice(false);
      setIsVpnProxy(false);
      setIsNewMerchant(false);
      setCategory('groceries');
      setIsImpossibleTravel(false);
      setCountryMismatch(false);
      setTxns10m(0);
      setChargebackCount(0);
      setCustomerAgeDays(365);
      handleEvaluate({
        transaction_amount: 1250,
        customer_avg_amount: 1500,
        failed_attempts: 0,
        customer_age_days: 365,
        device: { is_new_device: false },
        merchant_history: { is_new: false },
        category: 'groceries',
        location: { is_impossible_travel: false, current_country: 'IN', home_country: 'IN' },
      });
    } else if (preset === 'brute_force') {
      setAmount(3000);
      setCustomerAvg(2500);
      setFailedAttempts(12);
      setIsNewDevice(true);
      setIsVpnProxy(true);
      setTxns10m(8);
      handleEvaluate({
        transaction_amount: 3000,
        customer_avg_amount: 2500,
        failed_attempts: 12,
        velocity: { txns_last_10m: 8 },
        device: { is_new_device: true, is_vpn_proxy: true },
      });
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'text-rose-600 dark:text-rose-400';
    if (score >= 60) return 'text-amber-500 dark:text-amber-400';
    if (score >= 30) return 'text-yellow-500 dark:text-yellow-400';
    return 'text-emerald-600 dark:text-emerald-400';
  };

  const getBadgeStyle = (level: string) => {
    if (level === 'CRITICAL') return 'bg-rose-500/20 text-rose-600 dark:text-rose-300 border-rose-500/40 animate-pulse';
    if (level === 'HIGH') return 'bg-orange-500/20 text-orange-600 dark:text-orange-300 border-orange-500/40';
    if (level === 'MEDIUM') return 'bg-amber-500/20 text-amber-600 dark:text-amber-300 border-amber-500/40';
    return 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-300 border-emerald-500/40';
  };

  return (
    <div className={embedded ? 'space-y-8' : 'max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8'}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link to="/dashboard" className="text-xs font-bold text-secondary hover:text-primary transition">
              Dashboard
            </Link>
            <span className="text-secondary text-xs">/</span>
            <span className="text-xs font-bold text-indigo-600">Explainable Risk Engine</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-primary flex items-center gap-3">
            <Shield className="w-8 h-8 text-indigo-600" />
            Explainable Financial Risk Engine
          </h1>
          <p className="text-xs sm:text-sm text-secondary mt-1 max-w-3xl">
            Deterministic multi-factor risk scoring across 11 financial and behavioral dimensions. Zero LLM overrides for critical rules.
          </p>
        </div>

        {/* Preset quick buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => applyPreset('prompt_example')}
            className="px-3 py-1.5 rounded-xl bg-orange-500/15 hover:bg-orange-500/25 border border-orange-500/30 text-orange-700 dark:text-orange-300 text-xs font-bold transition cursor-pointer"
          >
            Prompt Example (82 HIGH)
          </button>
          <button
            type="button"
            onClick={() => applyPreset('impossible_travel')}
            className="px-3 py-1.5 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-rose-700 dark:text-rose-300 text-xs font-bold transition cursor-pointer"
          >
            Impossible Travel (CRITICAL)
          </button>
          <button
            type="button"
            onClick={() => applyPreset('clean_low_risk')}
            className="px-3 py-1.5 rounded-xl bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 text-emerald-700 dark:text-emerald-300 text-xs font-bold transition cursor-pointer"
          >
            Clean Everyday (LOW)
          </button>
          <button
            type="button"
            onClick={() => applyPreset('brute_force')}
            className="px-3 py-1.5 rounded-xl bg-purple-500/15 hover:bg-purple-500/25 border border-purple-500/30 text-purple-700 dark:text-purple-300 text-xs font-bold transition cursor-pointer"
          >
            Brute-Force (CRITICAL)
          </button>
        </div>
      </div>

      {/* Main Grid: Left Score & Reasons (5 cols), Right Parameters (7 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: Score Display, Reasons & Explanation */}
        <div className="lg:col-span-5 space-y-6">
          {/* Main Risk Card */}
          <div className="p-6 rounded-3xl bg-surface border border-border shadow-md space-y-6">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-secondary uppercase tracking-wider">Evaluation Result</span>
              {evaluation && (
                <span className={`px-3 py-1 rounded-full text-xs font-black border ${getBadgeStyle(evaluation.riskLevel)}`}>
                  {evaluation.riskLevel} RISK
                </span>
              )}
            </div>

            {/* Big Radial/Meter Score */}
            <div className="flex items-center justify-center py-4">
              <div className="relative flex flex-col items-center justify-center w-48 h-48 rounded-full border-8 border-muted bg-background shadow-inner">
                <span className={`text-6xl font-black tracking-tight ${getScoreColor(evaluation?.riskScore || 0)}`}>
                  {evaluation?.riskScore ?? '--'}
                </span>
                <span className="text-[11px] font-bold text-secondary uppercase tracking-widest mt-1">Score / 100</span>
                {evaluation?.critical_rule_triggered && (
                  <span className="absolute -bottom-3 px-3 py-0.5 rounded-full bg-rose-600 text-white text-[10px] font-black uppercase tracking-wider shadow">
                    CRITICAL OVERRIDE
                  </span>
                )}
              </div>
            </div>

            {/* Critical Intervention Banner */}
            {evaluation?.critical_rule_triggered && (
              <div className="p-4 rounded-2xl bg-rose-500/15 border border-rose-500/40 flex items-start gap-3">
                <AlertOctagon className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <h4 className="text-xs font-black text-rose-700 dark:text-rose-300 uppercase tracking-wider">
                    Critical Security Intervention
                  </h4>
                  <p className="text-[11px] text-rose-600/90 dark:text-rose-400 leading-relaxed">
                    A non-negotiable deterministic security rule was triggered. System automatically halts execution regardless of agent prompt.
                  </p>
                </div>
              </div>
            )}

            {/* Reasons List */}
            <div className="space-y-3 border-t border-border pt-4">
              <h3 className="text-xs font-black text-primary uppercase tracking-wider flex items-center justify-between">
                <span>Triggered Reasons ({evaluation?.reasons.length || 0})</span>
                <span className="text-[10px] font-mono text-secondary">Rules First</span>
              </h3>

              {evaluation && evaluation.reasons.length > 0 ? (
                <ul className="space-y-2">
                  {evaluation.reasons.map((reason, idx) => (
                    <li
                      key={idx}
                      className="p-2.5 rounded-xl bg-background border border-border flex items-center gap-2.5 text-xs font-bold text-primary"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-rose-500 shrink-0" />
                      <span>{reason}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="p-3 rounded-xl bg-background border border-border text-center text-xs text-secondary">
                  No risk triggers detected. Transaction profile is clean.
                </div>
              )}
            </div>

            {/* Explainability Card */}
            <div className="space-y-2 border-t border-border pt-4">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-black text-secondary uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-600" /> Explainable Narrative
                </h4>
                <button
                  type="button"
                  disabled={evaluating}
                  onClick={() => handleEvaluate(undefined, true)}
                  className="text-[10px] font-bold text-indigo-600 hover:text-indigo-700 cursor-pointer flex items-center gap-1"
                >
                  <RefreshCw className={`w-3 h-3 ${evaluating ? 'animate-spin' : ''}`} /> Refresh with AI
                </button>
              </div>

              <div className="p-3 rounded-2xl bg-background border border-border text-xs text-primary font-medium leading-relaxed whitespace-pre-line">
                {evaluation?.explanation || 'Awaiting evaluation...'}
              </div>
            </div>
          </div>

          {/* Rule Breakdown Drawer */}
          {evaluation && evaluation.rule_breakdown.length > 0 && (
            <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs space-y-3">
              <h3 className="text-xs font-black text-primary uppercase tracking-wider">
                Detailed Rule Breakdown ({evaluation.rule_breakdown.length})
              </h3>
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {evaluation.rule_breakdown.map((item, idx) => (
                  <div key={idx} className="p-2.5 rounded-xl bg-background border border-border text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-primary text-[11px]">{item.rule_name}</span>
                      <span className="font-mono font-black text-[11px] text-rose-500">+{item.points} pts</span>
                    </div>
                    <p className="text-[11px] text-secondary">{item.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: Interactive 11-Dimensional Parameter Sandbox */}
        <div className="lg:col-span-7 space-y-6">
          <div className="p-6 rounded-3xl bg-surface border border-border shadow-md space-y-5">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div>
                <h2 className="text-sm font-black text-primary uppercase tracking-wider flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-indigo-600" /> 11-Dimensional Risk Parameters
                </h2>
                <p className="text-[11px] text-secondary">Tune attributes to inspect real-time deterministic scoring.</p>
              </div>
              <button
                type="button"
                disabled={evaluating}
                onClick={() => handleEvaluate()}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-md transition cursor-pointer flex items-center gap-2"
              >
                {evaluating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Activity className="w-3.5 h-3.5" />}
                <span>Evaluate Risk</span>
              </button>
            </div>

            {/* Inputs Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              {/* 1. Transaction Amount */}
              <div className="p-3 rounded-2xl bg-background border border-border space-y-1.5">
                <label className="block font-bold text-secondary">1. Transaction Amount (₹)</label>
                <input
                  type="number"
                  value={amount}
                  onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-1.5 rounded-xl bg-surface border border-border text-primary font-mono font-bold"
                />
              </div>

              {/* 2. Customer Average Amount */}
              <div className="p-3 rounded-2xl bg-background border border-border space-y-1.5">
                <label className="block font-bold text-secondary">Customer Baseline Avg (₹)</label>
                <input
                  type="number"
                  value={customerAvg}
                  onChange={(e) => setCustomerAvg(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-1.5 rounded-xl bg-surface border border-border text-primary font-mono font-bold"
                />
                <span className="text-[10px] text-secondary">
                  Multiplier: {(amount / (customerAvg || 1)).toFixed(1)}x
                </span>
              </div>

              {/* 3. Failed Attempts in 10m */}
              <div className="p-3 rounded-2xl bg-background border border-border space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="font-bold text-secondary">2. Failed Attempts (10m)</label>
                  <span className="font-mono font-black text-rose-500">{failedAttempts}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="15"
                  value={failedAttempts}
                  onChange={(e) => setFailedAttempts(parseInt(e.target.value))}
                  className="w-full accent-indigo-600 cursor-pointer"
                />
              </div>

              {/* 4. Customer Account Age */}
              <div className="p-3 rounded-2xl bg-background border border-border space-y-1.5">
                <label className="block font-bold text-secondary">3. Customer Account Age (Days)</label>
                <input
                  type="number"
                  value={customerAgeDays}
                  onChange={(e) => setCustomerAgeDays(parseInt(e.target.value) || 0)}
                  className="w-full px-3 py-1.5 rounded-xl bg-surface border border-border text-primary font-mono font-bold"
                />
              </div>

              {/* 5. Category */}
              <div className="p-3 rounded-2xl bg-background border border-border space-y-1.5">
                <label className="block font-bold text-secondary">4. Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-xl bg-surface border border-border text-primary font-bold"
                >
                  <option value="crypto">crypto (Unusual / High Risk)</option>
                  <option value="gambling">gambling (High Risk)</option>
                  <option value="cash">cash / withdrawal (High Risk)</option>
                  <option value="gift_cards">gift_cards</option>
                  <option value="electronics">electronics</option>
                  <option value="groceries">groceries (Low Risk)</option>
                  <option value="services">services</option>
                </select>
              </div>

              {/* 6. Velocity Txns in 10m */}
              <div className="p-3 rounded-2xl bg-background border border-border space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="font-bold text-secondary">5. Velocity (Txns in 10m)</label>
                  <span className="font-mono font-black text-primary">{txns10m}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="20"
                  value={txns10m}
                  onChange={(e) => setTxns10m(parseInt(e.target.value))}
                  className="w-full accent-indigo-600 cursor-pointer"
                />
              </div>

              {/* 7. Prior Chargebacks */}
              <div className="p-3 rounded-2xl bg-background border border-border space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="font-bold text-secondary">6. Prior Chargebacks</label>
                  <span className="font-mono font-black text-rose-500">{chargebackCount}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="10"
                  value={chargebackCount}
                  onChange={(e) => setChargebackCount(parseInt(e.target.value))}
                  className="w-full accent-indigo-600 cursor-pointer"
                />
              </div>

              {/* Checkboxes Group */}
              <div className="p-3 rounded-2xl bg-background border border-border space-y-2.5">
                <label className="block font-bold text-secondary">7. Contextual Toggles</label>
                <div className="space-y-1.5">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isNewDevice}
                      onChange={(e) => setIsNewDevice(e.target.checked)}
                      className="w-3.5 h-3.5 accent-indigo-600"
                    />
                    <span className="text-[11px] font-medium text-primary">New Device</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isVpnProxy}
                      onChange={(e) => setIsVpnProxy(e.target.checked)}
                      className="w-3.5 h-3.5 accent-indigo-600"
                    />
                    <span className="text-[11px] font-medium text-primary">VPN / Tor Proxy</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isNewMerchant}
                      onChange={(e) => setIsNewMerchant(e.target.checked)}
                      className="w-3.5 h-3.5 accent-indigo-600"
                    />
                    <span className="text-[11px] font-medium text-primary">New Merchant</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isImpossibleTravel}
                      onChange={(e) => setIsImpossibleTravel(e.target.checked)}
                      className="w-3.5 h-3.5 accent-rose-600"
                    />
                    <span className="text-[11px] font-bold text-rose-600">Impossible Travel (CRITICAL)</span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* Audit History Log */}
          <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs space-y-3">
            <h3 className="text-sm font-black text-primary uppercase tracking-wider flex items-center gap-2">
              <History className="w-4 h-4 text-indigo-600" /> Recent Risk Evaluations ({history.length})
            </h3>

            <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
              {history.length === 0 ? (
                <div className="p-4 rounded-xl bg-background border border-border text-center text-xs text-secondary">
                  No risk evaluation records found.
                </div>
              ) : (
                history.map((rec) => (
                  <div key={rec.id} className="p-3 rounded-2xl bg-background border border-border text-xs space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-primary">
                        ₹{parseFloat(String(rec.transaction_amount || 0)).toLocaleString()}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-black">{rec.risk_score}/100</span>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-black border ${getBadgeStyle(rec.risk_level)}`}>
                          {rec.risk_level}
                        </span>
                      </div>
                    </div>
                    {rec.reasons && rec.reasons.length > 0 && (
                      <div className="text-[11px] text-secondary flex flex-wrap gap-1">
                        {rec.reasons.map((r, i) => (
                          <span key={i} className="px-1.5 py-0.5 rounded bg-muted text-[10px]">
                            {r}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
