import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  Save,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Play,
  FileCode,
  Sliders,
  Lock,
  Zap,
} from "lucide-react";
import Button from "../components/ui/Button";
import { apiRequest } from "../../lib/api";

const DEFAULT_POLICY_YAML = `merchant_policy:
  max_discount: 10%
  max_autonomous_order_value: 5000
  max_items_per_order: 5
  min_margin_percent: 18%
  preferred_categories:
    - accessories
    - bundles
  forbidden_categories:
    - restricted_products
  auto_approval:
    under: 1500
  human_approval:
    from: 1500
    to: 5000
  human_required:
    above: 5000`;

export default function PolicyEngine() {
  const [policyYaml, setPolicyYaml] = useState(DEFAULT_POLICY_YAML);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [simulating, setSimulating] = useState(false);

  // Simulation test state
  const [simProposal, setSimProposal] = useState({
    items: "Phone, Case",
    total_price: 32698,
    discount_pct: 5,
    margin_pct: 25,
    category: "mobiles",
  });

  const [simResult, setSimResult] = useState<any>({
    allowed: false,
    decision: "BLOCKED → human confirmation required",
    status: "BLOCKED",
    rule_violated: "max_autonomous_order_value",
    limit_value: 5000,
    proposed_value: 32698,
    explanation:
      "Policy limit: max autonomous order = ₹5,000. Proposed offer total of ₹32,698 exceeds limit. Decision: BLOCKED → human confirmation required.",
  });

  const fetchPolicy = async () => {
    try {
      setLoading(true);
      const res = await apiRequest<any>("/intelligence/policy/");
      if (res && res.policy_yaml) {
        setPolicyYaml(res.policy_yaml);
      }
    } catch (err) {
      console.error("Error fetching policy:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicy();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiRequest("/intelligence/policy/", {
        method: "PUT",
        body: JSON.stringify({ policy_yaml: policyYaml }),
      });
      alert("Merchant Policy Language DSL successfully saved and applied!");
    } catch (err) {
      console.error("Error saving policy:", err);
      alert("Failed to save policy.");
    } finally {
      setSaving(false);
    }
  };

  const runSimulation = async () => {
    setSimulating(true);
    try {
      const itemsArray = simProposal.items
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      const res = await apiRequest<any>("/intelligence/policy/simulate/", {
        method: "POST",
        body: JSON.stringify({
          proposal: {
            items: itemsArray,
            total_price: Number(simProposal.total_price),
            discount_pct: Number(simProposal.discount_pct),
            margin_pct: Number(simProposal.margin_pct),
            categories: [simProposal.category],
          },
          policy_yaml: policyYaml,
        }),
      });
      setSimResult(res);
    } catch (err) {
      console.error("Simulation error:", err);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="min-h-[85vh] bg-gradient-to-br from-white via-gray-50 to-white dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 rounded-3xl p-8 border border-gray-200 dark:border-gray-800 shadow-2xl text-gray-900 dark:text-white transition-colors duration-300 space-y-8">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-gray-200 dark:border-gray-800">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-xs">
              <ShieldAlert className="h-4 w-4" />
            </span>
            <span className="text-xs font-extrabold uppercase tracking-widest text-indigo-600 dark:text-indigo-400">
              Centerpiece Guardrails • Explainable • Bounded • Gated
            </span>
          </div>
          <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
            Merchant Policy Language (DSL)
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1 text-sm max-w-2xl">
            LLMs can propose and draft offers, but deterministic policy code strictly validates money, discount ceilings, and approval thresholds. The LLM cannot override these boundaries.
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <Button
            onClick={fetchPolicy}
            className="bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-800 dark:text-white rounded-xl px-4 py-2.5 text-xs font-bold shadow-sm border border-gray-300 dark:border-gray-700"
          >
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" /> Reset
          </Button>
          <Button
            onClick={handleSave}
            disabled={saving}
            className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl px-5 py-2.5 text-xs font-bold shadow-md shadow-indigo-500/25"
          >
            <Save className="h-3.5 w-3.5 mr-1.5" /> {saving ? "Saving..." : "Save Policy"}
          </Button>
        </div>
      </div>

      {/* ── Main Dual-Column: Policy DSL vs Live Verification Sandbox ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column: Declarative Policy Editor */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <FileCode className="h-4 w-4 text-indigo-500" />
              Declarative Policy Specification (YAML)
            </h3>
            <span className="text-xs font-mono text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded">
              schema: merchant_policy/v1
            </span>
          </div>

          <div className="relative rounded-2xl border border-gray-300 dark:border-gray-700 overflow-hidden shadow-inner bg-zinc-950">
            <textarea
              value={policyYaml}
              onChange={(e) => setPolicyYaml(e.target.value)}
              rows={18}
              spellCheck={false}
              className="w-full bg-transparent p-5 font-mono text-xs sm:text-sm text-emerald-400 focus:outline-none resize-none leading-relaxed"
            />
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
            <Lock className="h-3.5 w-3.5 text-amber-500 shrink-0" />
            Deterministic verification: Changes here immediately constrain all agent execution paths.
          </p>
        </div>

        {/* Right Column: Live Policy Verification Sandbox */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <Zap className="h-4 w-4 text-amber-500" />
              Live Deterministic Guardrail Sandbox
            </h3>
            <span className="text-xs font-bold text-amber-600 dark:text-amber-400 bg-amber-500/10 px-2.5 py-0.5 rounded-full border border-amber-500/20">
              Zero-Bypass Simulator
            </span>
          </div>

          <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/60 shadow-sm space-y-4">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Simulate an agent proposing an offer and test whether the deterministic engine allows, gates, or blocks execution:
            </p>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] font-bold text-gray-500 uppercase">Proposed Offer Items</label>
                <input
                  type="text"
                  value={simProposal.items}
                  onChange={(e) => setSimProposal({ ...simProposal, items: e.target.value })}
                  className="w-full mt-1 bg-white dark:bg-gray-950 border border-gray-300 dark:border-gray-700 rounded-xl px-3 py-2 text-xs font-semibold text-gray-900 dark:text-white"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-gray-500 uppercase">Proposed Order Total (₹)</label>
                <input
                  type="number"
                  value={simProposal.total_price}
                  onChange={(e) => setSimProposal({ ...simProposal, total_price: Number(e.target.value) })}
                  className="w-full mt-1 bg-white dark:bg-gray-950 border border-gray-300 dark:border-gray-700 rounded-xl px-3 py-2 text-xs font-bold text-gray-900 dark:text-white"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-gray-500 uppercase">Discount (%)</label>
                <input
                  type="number"
                  value={simProposal.discount_pct}
                  onChange={(e) => setSimProposal({ ...simProposal, discount_pct: Number(e.target.value) })}
                  className="w-full mt-1 bg-white dark:bg-gray-950 border border-gray-300 dark:border-gray-700 rounded-xl px-3 py-2 text-xs font-semibold text-gray-900 dark:text-white"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-gray-500 uppercase">Margin (%)</label>
                <input
                  type="number"
                  value={simProposal.margin_pct}
                  onChange={(e) => setSimProposal({ ...simProposal, margin_pct: Number(e.target.value) })}
                  className="w-full mt-1 bg-white dark:bg-gray-950 border border-gray-300 dark:border-gray-700 rounded-xl px-3 py-2 text-xs font-semibold text-gray-900 dark:text-white"
                />
              </div>
            </div>

            <Button
              onClick={runSimulation}
              disabled={simulating}
              className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:opacity-90 text-white rounded-xl py-3 font-bold text-xs shadow-md shadow-indigo-500/20 flex items-center justify-center gap-2 cursor-pointer"
            >
              <Play className="h-3.5 w-3.5" />
              {simulating ? "Evaluating Policy..." : "Test Deterministic Guardrails"}
            </Button>

            {/* ── Deterministic Output Card ── */}
            {simResult && (
              <div
                className={`p-4 rounded-2xl border transition-all ${
                  simResult.status === "APPROVED"
                    ? "bg-emerald-500/10 border-emerald-500/30"
                    : simResult.status === "GATED"
                    ? "bg-amber-500/10 border-amber-500/30"
                    : "bg-rose-500/10 border-rose-500/30"
                }`}
              >
                <div className="flex items-center justify-between gap-2 pb-2 border-b border-border/50">
                  <div className="flex items-center gap-2">
                    {simResult.status === "APPROVED" ? (
                      <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                    ) : simResult.status === "GATED" ? (
                      <AlertTriangle className="h-5 w-5 text-amber-500" />
                    ) : (
                      <XCircle className="h-5 w-5 text-rose-500" />
                    )}
                    <span
                      className={`text-xs font-black uppercase tracking-wider ${
                        simResult.status === "APPROVED"
                          ? "text-emerald-600 dark:text-emerald-400"
                          : simResult.status === "GATED"
                          ? "text-amber-600 dark:text-amber-400"
                          : "text-rose-600 dark:text-rose-400"
                      }`}
                    >
                      Decision: {simResult.decision}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-black/10 dark:bg-white/10">
                    {simResult.allowed ? "AUTONOMOUS ALLOWED" : "EXECUTION INTERCEPTED"}
                  </span>
                </div>

                <p className="mt-3 text-xs leading-relaxed font-medium text-gray-800 dark:text-gray-200">
                  {simResult.explanation}
                </p>

                {simResult.rule_violated && (
                  <div className="mt-3 pt-2 border-t border-border/40 flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400 font-mono">
                    <span>Rule: {simResult.rule_violated}</span>
                    <span>
                      Limit: ₹{Number(simResult.limit_value || 0).toLocaleString()} • Proposed: ₹{Number(simResult.proposed_value || 0).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Explainable, Bounded & Gated Architecture Callout ── */}
      <div className="p-6 rounded-3xl border border-indigo-500/20 bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-transparent flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-1">
          <h3 className="text-base font-black text-gray-900 dark:text-white flex items-center gap-2">
            <Lock className="h-4 w-4 text-indigo-500" />
            Core Invariant: Explainable + Bounded + Gated
          </h3>
          <p className="text-xs text-gray-600 dark:text-gray-400 max-w-3xl leading-relaxed">
            No autonomous agent or language model can bypass the merchant policy layer. Every high-value transaction above ₹5,000 is automatically intercepted, providing complete financial sovereignty to merchants while retaining the speed of autonomous commerce for low-risk transactions.
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="inline-flex items-center gap-1 rounded-xl bg-indigo-500/15 px-3 py-1.5 text-xs font-bold text-indigo-600 dark:text-indigo-400 border border-indigo-500/30">
            ✓ Deterministic Policy Active
          </span>
        </div>
      </div>
    </div>
  );
}
