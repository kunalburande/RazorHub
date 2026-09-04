import React, { useState, useEffect } from "react";
import {
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  X,
  Send,
  Calendar,
  ShieldCheck,
  Package,
  Layers,
  Check,
  TrendingUp,
  RefreshCw,
  Clock,
  XCircle,
  Store as StoreIcon,
  Inbox,
} from "lucide-react";
import Button from "../components/ui/Button";
import { apiRequest, unwrapList } from "../../lib/api";

interface EligibleProduct {
  name: string;
  slug: string;
  price: number;
  stock: number;
  margin_percent: number;
  inventory_healthy: boolean;
}

interface CadenceStage {
  day: number;
  stage: string;
  action?: string;
  event?: string;
  product?: string;
  channel?: string;
  type?: string;
  timing_rationale: string;
}

interface CampaignResult {
  campaign_id: number;
  merchant_prompt: string;
  segment: string;
  goal: string;
  eligible_products: EligibleProduct[];
  constraints: {
    max_discount_percent: number;
    min_inventory: number;
    complaint_cooldown_hours: number;
    max_recommendations_per_week: number;
    summary: string[];
  };
  cadence: CadenceStage[];
  summary_text?: string;
}

interface StoreRecoveryStats {
  active_recoveries: number;
  pending_retries: number;
  total_recovered: number;
  recovery_rate: number;
  store_name: string;
  store_id: number | null;
  total_records: number;
}

const PRESET_PROMPTS = [
  {
    label: "💻 Laptop Post-Purchase Cadence (Atom8)",
    prompt: "Increase revenue from customers who purchased laptops.",
    badge: "5-Stage Cadence",
  },
  {
    label: "🛒 Abandoned Cart Win-Back",
    prompt: "Win back abandoned carts with bounded 5% discount & 1-click UPI retry.",
    badge: "Cart Recovery",
  },
  {
    label: "💳 Payment Failure Smart Dunning",
    prompt: "Recover failed payments with multi-channel smart retry within capped 3 attempts.",
    badge: "Smart Dunning",
  },
];

export default function RecoveryDashboard() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [stats, setStats] = useState<StoreRecoveryStats | null>(null);
  const [storeName, setStoreName] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Campaign Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [prompt, setPrompt] = useState("Increase revenue from customers who purchased laptops.");
  const [compiling, setCompiling] = useState(false);
  const [launching, setLaunching] = useState(false);
  const [campaignResult, setCampaignResult] = useState<CampaignResult | null>(null);
  const [modalError, setModalError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Action loading for specific task IDs
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);

  async function fetchRecoveryData() {
    try {
      // 1. Fetch real-time store recovery statistics
      try {
        const statsRes = await apiRequest<StoreRecoveryStats>("/intelligence/recovery/stats/");
        if (statsRes) {
          setStats(statsRes);
          if (statsRes.store_name) {
            setStoreName(statsRes.store_name);
          }
        }
      } catch (e) {
        console.warn("Stats endpoint optional fetch:", e);
      }

      // 2. Fetch real recovery tasks strictly isolated to this seller/store
      const response = await apiRequest<any>("/intelligence/recovery/");
      const list = unwrapList<any>(response);
      setTasks(list);

      // If store_name was not provided in stats, extract from first task if available
      if (list.length > 0 && list[0]?.store_name && !storeName) {
        setStoreName(list[0].store_name);
      }
    } catch (err: any) {
      console.error("Error fetching recovery tasks from database:", err);
      setTasks([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    fetchRecoveryData();
  }, []);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Compile Campaign using Autonomous Campaign Orchestrator with seller store context
  const handleCompileCampaign = async (promptToUse?: string) => {
    const activePrompt = promptToUse || prompt;
    if (!activePrompt.trim()) return;

    setCompiling(true);
    setModalError(null);
    try {
      const res = await apiRequest<CampaignResult>("/intelligence/campaigns/orchestrate/", {
        method: "POST",
        body: JSON.stringify({ prompt: activePrompt }),
      });
      setCampaignResult(res);
    } catch (err: any) {
      console.error("Failed to compile campaign from database:", err);
      setModalError(err?.message || "Failed to compile campaign from store catalog. Please verify prompt and retry.");
    } finally {
      setCompiling(false);
    }
  };

  // Launch Campaign & Register Real Recovery Action in Database
  const handleLaunchCampaign = async () => {
    if (!campaignResult) return;
    setLaunching(true);
    setModalError(null);

    const isCartRecovery = prompt.toLowerCase().includes("cart");
    const isPaymentDunning = prompt.toLowerCase().includes("payment") || prompt.toLowerCase().includes("dunning");
    const domainPart = (storeName || "store").toLowerCase().replace(/[^a-z0-9]/g, "");

    const newTaskPayload = {
      task_id: `CMP-${Date.now().toString().slice(-6)}`,
      customer_email: isCartRecovery
        ? `cart-abandoner@${domainPart}.in`
        : isPaymentDunning
        ? `payment-retry@${domainPart}.in`
        : `${campaignResult.segment.toLowerCase().replace(/\s+/g, "-")}@${domainPart}.in`,
      cart_value: isCartRecovery ? "5499.00" : isPaymentDunning ? "2899.00" : "10468.00",
      status: "In_Progress",
      agent_action: isCartRecovery
        ? "CART_RECOVERY: 5% bounded discount + 1-click UPI retry link"
        : isPaymentDunning
        ? "PAYMENT_RETRY: Auto-retry via secondary UPI rails with WhatsApp fallback"
        : `POST_PURCHASE: Cadence Day 0-28 initiated (${campaignResult.segment})`,
    };

    try {
      await apiRequest<any>("/intelligence/recovery/", {
        method: "POST",
        body: JSON.stringify(newTaskPayload),
      });
      // Re-fetch canonical state from the database
      await fetchRecoveryData();
      setIsModalOpen(false);
      showToast(`Campaign launched! Active in your store's recovery ledger.`);
    } catch (err: any) {
      console.error("Failed to launch campaign to database:", err);
      setModalError(err?.message || "Could not launch campaign to database. Please check your seller permissions.");
    } finally {
      setLaunching(false);
    }
  };

  // Quick Action: Mark task as recovered
  const handleMarkRecovered = async (taskId: number) => {
    setActionLoadingId(taskId);
    try {
      await apiRequest(`/intelligence/recovery/${taskId}/`, {
        method: "PATCH",
        body: JSON.stringify({ status: "Recovered" }),
      });
      await fetchRecoveryData();
      showToast("Task marked as Recovered! Live store analytics updated.");
    } catch (err: any) {
      console.error("Failed to update recovery task status:", err);
      showToast("Could not update task status on server.");
    } finally {
      setActionLoadingId(null);
    }
  };

  // ── Database Analytics Calculations (Real-time from DB tasks or stats) ───
  const activeRecoveries =
    stats?.active_recoveries ??
    tasks.filter((t: any) =>
      ["in_progress", "pending", "active"].includes(String(t.status || "").toLowerCase())
    ).length;

  const pendingRetries =
    stats?.pending_retries ??
    tasks.filter((t: any) => {
      const act = String(t.agent_action || "").toLowerCase();
      const status = String(t.status || "").toLowerCase();
      return (
        status !== "recovered" &&
        status !== "completed" &&
        (act.includes("retry") || act.includes("upi") || act.includes("payment") || act.includes("dunn"))
      );
    }).length;

  const totalRecovered =
    stats?.total_recovered ??
    tasks
      .filter((t: any) => ["recovered", "completed", "success"].includes(String(t.status || "").toLowerCase()))
      .reduce((sum: number, t: any) => sum + (parseFloat(t.cart_value) || 0), 0);

  const recoveryRate =
    stats?.recovery_rate ??
    (tasks.length > 0
      ? Math.round(
          (tasks.filter((t: any) =>
            ["recovered", "completed", "success"].includes(String(t.status || "").toLowerCase())
          ).length /
            tasks.length) *
            100
        )
      : 0);

  // Status Presentation Helper
  const getStatusBadge = (statusRaw: string) => {
    const s = String(statusRaw || "").toLowerCase().trim();
    if (s === "recovered" || s === "completed" || s === "success") {
      return {
        label: "Recovered",
        badgeClass: "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-700",
        iconClass: "bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400",
        Icon: CheckCircle2,
      };
    }
    if (s === "in_progress" || s === "active") {
      return {
        label: "In Progress",
        badgeClass: "bg-blue-100 dark:bg-blue-950/60 text-blue-800 dark:text-blue-300 border-blue-300 dark:border-blue-700",
        iconClass: "bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400",
        Icon: RotateCcw,
      };
    }
    if (s === "lost" || s === "failed") {
      return {
        label: "Lost",
        badgeClass: "bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300 border-rose-300 dark:border-rose-700",
        iconClass: "bg-rose-100 dark:bg-rose-900/40 text-rose-600 dark:text-rose-400",
        Icon: XCircle,
      };
    }
    return {
      label: "Pending",
      badgeClass: "bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border-amber-300 dark:border-amber-700",
      iconClass: "bg-amber-100 dark:bg-amber-900/40 text-amber-600 dark:text-amber-400",
      Icon: Clock,
    };
  };

  return (
    <div className="min-h-[85vh] bg-white dark:bg-gray-950 rounded-3xl p-6 md:p-8 border border-gray-200 dark:border-gray-800 shadow-xl text-gray-900 dark:text-white transition-colors duration-200">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-6 right-6 z-50 flex items-center gap-3 bg-gray-900 text-white dark:bg-white dark:text-gray-900 px-5 py-3 rounded-2xl shadow-2xl border border-gray-700 dark:border-gray-200 animate-in fade-in slide-in-from-top-4 duration-200 font-medium">
          <Check className="w-5 h-5 text-emerald-400 dark:text-emerald-600" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header */}
      <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-extrabold tracking-tight text-gray-950 dark:text-white flex items-center gap-3">
              <div className="p-2.5 rounded-2xl bg-orange-100 dark:bg-orange-950/50 text-orange-600 dark:text-orange-400 border border-orange-200 dark:border-orange-800">
                <RotateCcw className="h-7 w-7" />
              </div>
              Revenue Recovery
            </h1>

            {storeName && (
              <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 border border-gray-300 dark:border-gray-700 flex items-center gap-1.5">
                <StoreIcon className="w-3.5 h-3.5 text-orange-500" />
                {storeName}
              </span>
            )}
          </div>
          <p className="text-gray-700 dark:text-gray-300 mt-2 text-sm max-w-2xl font-normal">
            Autonomous agentic cart abandonment recovery, smart dunning retries, and goal-driven post-purchase campaign orchestration scoped to your store's live orders.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              setRefreshing(true);
              fetchRecoveryData();
            }}
            disabled={refreshing}
            className="p-2.5 rounded-xl border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition-colors flex items-center gap-2 text-sm font-medium"
            title="Refresh database records"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin text-orange-500" : ""}`} />
            <span className="hidden sm:inline">Sync DB</span>
          </button>

          <Button
            onClick={() => {
              setIsModalOpen(true);
              if (!campaignResult) {
                handleCompileCampaign("Increase revenue from customers who purchased laptops.");
              }
            }}
            className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl px-5 py-2.5 font-bold shadow-md hover:shadow-lg flex items-center gap-2 text-sm transition-all"
          >
            <Sparkles className="w-4 h-4" />
            Start Campaign
          </Button>
        </div>
      </div>

      {/* Database-Driven Analytics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        {/* Card 1: Active Recoveries */}
        <div className="p-6 rounded-2xl border border-amber-300/80 dark:border-amber-900/60 bg-amber-50/90 dark:bg-amber-950/20 shadow-sm relative overflow-hidden">
          <div className="absolute -right-3 -bottom-3 text-amber-200/50 dark:text-amber-900/30">
            <AlertTriangle className="w-28 h-28" />
          </div>
          <div className="flex items-center justify-between relative z-10">
            <h3 className="text-sm font-bold text-amber-900 dark:text-amber-300 uppercase tracking-wider">Active Recoveries</h3>
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-200/70 text-amber-900 dark:bg-amber-900/60 dark:text-amber-200">
              Live DB
            </span>
          </div>
          <p className="text-3xl md:text-4xl font-black text-gray-950 dark:text-white mt-3 relative z-10">
            {activeRecoveries}
          </p>
          <p className="text-xs text-amber-800/90 dark:text-amber-400 mt-1 font-medium relative z-10">
            In progress or pending customer reach-out
          </p>
        </div>

        {/* Card 2: Pending Payment Retries */}
        <div className="p-6 rounded-2xl border border-blue-300/80 dark:border-blue-900/60 bg-blue-50/90 dark:bg-blue-950/20 shadow-sm relative overflow-hidden">
          <div className="absolute -right-3 -bottom-3 text-blue-200/50 dark:text-blue-900/30">
            <RotateCcw className="w-28 h-28" />
          </div>
          <div className="flex items-center justify-between relative z-10">
            <h3 className="text-sm font-bold text-blue-900 dark:text-blue-300 uppercase tracking-wider">Payment Retries</h3>
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-200/70 text-blue-900 dark:bg-blue-900/60 dark:text-blue-200">
              UPI Rails
            </span>
          </div>
          <p className="text-3xl md:text-4xl font-black text-gray-950 dark:text-white mt-3 relative z-10">
            {pendingRetries}
          </p>
          <p className="text-xs text-blue-800/90 dark:text-blue-400 mt-1 font-medium relative z-10">
            Automated 1-click UPI links dispatched
          </p>
        </div>

        {/* Card 3: Total Recovered */}
        <div className="p-6 rounded-2xl border border-emerald-300/80 dark:border-emerald-900/60 bg-emerald-50/90 dark:bg-emerald-950/20 shadow-sm relative overflow-hidden">
          <div className="absolute -right-3 -bottom-3 text-emerald-200/50 dark:text-emerald-900/30">
            <CheckCircle2 className="w-28 h-28" />
          </div>
          <div className="flex items-center justify-between relative z-10">
            <h3 className="text-sm font-bold text-emerald-900 dark:text-emerald-300 uppercase tracking-wider">Total Recovered</h3>
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-200/70 text-emerald-900 dark:bg-emerald-900/60 dark:text-emerald-200">
              Captured
            </span>
          </div>
          <p className="text-3xl md:text-4xl font-black text-gray-950 dark:text-white mt-3 relative z-10">
            ₹{totalRecovered.toLocaleString("en-IN")}
          </p>
          <p className="text-xs text-emerald-800/90 dark:text-emerald-400 mt-1 font-medium relative z-10">
            Calculated from verified recovered tasks
          </p>
        </div>

        {/* Card 4: Recovery Success Rate */}
        <div className="p-6 rounded-2xl border border-purple-300/80 dark:border-purple-900/60 bg-purple-50/90 dark:bg-purple-950/20 shadow-sm relative overflow-hidden">
          <div className="absolute -right-3 -bottom-3 text-purple-200/50 dark:text-purple-900/30">
            <TrendingUp className="w-28 h-28" />
          </div>
          <div className="flex items-center justify-between relative z-10">
            <h3 className="text-sm font-bold text-purple-900 dark:text-purple-300 uppercase tracking-wider">Success Rate</h3>
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-purple-200/70 text-purple-900 dark:bg-purple-900/60 dark:text-purple-200">
              Agentic
            </span>
          </div>
          <p className="text-3xl md:text-4xl font-black text-gray-950 dark:text-white mt-3 relative z-10">
            {recoveryRate}%
          </p>
          <p className="text-xs text-purple-800/90 dark:text-purple-400 mt-1 font-medium relative z-10">
            {tasks.length} store recovery interactions
          </p>
        </div>
      </div>

      {/* Recent Recovery Actions Table */}
      <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900/60 rounded-2xl overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800 bg-gray-50/80 dark:bg-gray-900/80 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-gray-950 dark:text-gray-100">
              Recent Recovery & Campaign Actions
            </h3>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
              Live orders and retry actions scoped strictly to {storeName || "your store"}
            </p>
          </div>
          <span className="text-xs font-bold text-gray-700 dark:text-gray-300 bg-gray-200 dark:bg-gray-800 px-3 py-1 rounded-full">
            {tasks.length} Records
          </span>
        </div>

        <div className="divide-y divide-gray-200 dark:divide-gray-800">
          {loading ? (
            <div className="p-12 text-center text-gray-600 dark:text-gray-400 font-medium">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto text-orange-500 mb-2" />
              Loading recovery tasks from database...
            </div>
          ) : tasks.length === 0 ? (
            <div className="p-12 text-center text-gray-600 dark:text-gray-400">
              <div className="w-12 h-12 rounded-2xl bg-gray-100 dark:bg-gray-800 text-gray-400 mx-auto flex items-center justify-center mb-3">
                <Inbox className="w-6 h-6" />
              </div>
              <p className="font-bold text-gray-900 dark:text-white text-base">
                No recovery tasks recorded for {storeName || "your store"} yet.
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 max-w-md mx-auto">
                When customers experience payment drop-offs, cart abandonments, or order retries on your products,
                autonomous recovery agents will track and execute resolution loops here in real time.
              </p>
              <button
                onClick={() => {
                  setIsModalOpen(true);
                  if (!campaignResult) {
                    handleCompileCampaign("Increase revenue from customers who purchased laptops.");
                  }
                }}
                className="mt-4 px-4 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white transition-colors"
              >
                Start Autonomous Campaign
              </button>
            </div>
          ) : (
            tasks.map((task) => {
              const { label, badgeClass, iconClass, Icon } = getStatusBadge(task.status);
              const isActionable = ["in_progress", "pending"].includes(String(task.status || "").toLowerCase());

              return (
                <div
                  key={task.id || task.task_id}
                  className="p-5 md:p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-gray-50/90 dark:hover:bg-gray-800/40 transition-colors"
                >
                  <div className="flex items-start sm:items-center gap-4">
                    <div className={`p-3 rounded-2xl shrink-0 ${iconClass}`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h4 className="font-bold text-gray-950 dark:text-gray-100 text-base">
                          {task.customer_email || "Customer"}
                        </h4>
                        <span className="text-xs font-mono text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded">
                          {task.task_id}
                        </span>
                        {task.store_name && (
                          <span className="text-[11px] font-semibold text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800/80 px-2 py-0.5 rounded">
                            {task.store_name}
                          </span>
                        )}
                      </div>
                      <div className="flex flex-wrap items-center gap-3 mt-1 text-sm">
                        <span className="font-bold text-gray-900 dark:text-gray-200">
                          Value: ₹{(parseFloat(task.cart_value) || 0).toLocaleString("en-IN")}
                        </span>
                        <span className="text-gray-400">•</span>
                        <span className="text-gray-600 dark:text-gray-400 text-xs sm:text-sm">
                          {task.agent_action || "Dunning sequence active"}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between md:justify-end gap-3 shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-gray-100 dark:border-gray-800">
                    <span className={`px-3 py-1 rounded-full text-xs font-extrabold border ${badgeClass}`}>
                      {label}
                    </span>

                    {isActionable && (
                      <button
                        onClick={() => handleMarkRecovered(task.id)}
                        disabled={actionLoadingId === task.id}
                        className="px-3 py-1.5 rounded-xl text-xs font-bold bg-emerald-50 hover:bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:hover:bg-emerald-900/60 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 transition-colors flex items-center gap-1.5"
                      >
                        {actionLoadingId === task.id ? (
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Check className="w-3.5 h-3.5" />
                        )}
                        Mark Recovered
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* ── AUTONOMOUS CAMPAIGN ORCHESTRATOR MODAL ───────────────────────── */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white dark:bg-gray-950 w-full max-w-4xl rounded-3xl border border-gray-200 dark:border-gray-800 shadow-2xl overflow-hidden max-h-[90vh] flex flex-col text-gray-900 dark:text-white animate-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="px-6 py-5 border-b border-gray-200 dark:border-gray-800 bg-gray-50/80 dark:bg-gray-900/80 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                  <Sparkles className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-xl font-black text-gray-950 dark:text-white">
                    Autonomous Campaign Orchestrator
                  </h2>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    Atom8 Goal-Driven Cadence & Dunning for {storeName || "Your Store"}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-2 rounded-xl text-gray-500 hover:text-gray-900 dark:hover:text-white hover:bg-gray-200 dark:hover:bg-gray-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Scrollable Body */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1 text-sm">
              {/* Intent Input & Preset Chips */}
              <div className="space-y-3">
                <label className="block text-sm font-bold text-gray-900 dark:text-gray-100">
                  Merchant Goal & Natural Language Intent
                </label>

                <div className="flex flex-wrap gap-2">
                  {PRESET_PROMPTS.map((item, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => {
                        setPrompt(item.prompt);
                        handleCompileCampaign(item.prompt);
                      }}
                      className={`text-xs font-semibold px-3 py-1.5 rounded-full border transition-all flex items-center gap-1.5 ${
                        prompt === item.prompt
                          ? "bg-emerald-600 text-white border-emerald-600 shadow-sm"
                          : "bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-700"
                      }`}
                    >
                      <span>{item.label}</span>
                      <span className="text-[10px] opacity-80 uppercase tracking-wider">({item.badge})</span>
                    </button>
                  ))}
                </div>

                <div className="flex gap-2">
                  <input
                    type="text"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="e.g. Increase revenue from customers who purchased laptops."
                    className="flex-1 px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-950 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        handleCompileCampaign();
                      }
                    }}
                  />
                  <button
                    onClick={() => handleCompileCampaign()}
                    disabled={compiling || !prompt.trim()}
                    className="px-5 py-3 rounded-xl font-bold bg-gray-900 hover:bg-gray-800 text-white dark:bg-white dark:text-gray-900 dark:hover:bg-gray-100 transition-colors flex items-center gap-2 shrink-0 disabled:opacity-50"
                  >
                    {compiling ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4 text-amber-400" />}
                    <span>{compiling ? "Compiling..." : "Orchestrate"}</span>
                  </button>
                </div>
              </div>

              {modalError && (
                <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800 text-xs font-semibold">
                  {modalError}
                </div>
              )}

              {/* Compiled Results Display */}
              {campaignResult && (
                <div className="space-y-6 animate-in fade-in duration-200">
                  {/* Summary Banner */}
                  <div className="p-5 rounded-2xl bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-950/30 dark:to-teal-950/20 border border-emerald-200 dark:border-emerald-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-extrabold uppercase tracking-wider text-emerald-800 dark:text-emerald-300">
                          Target Segment:
                        </span>
                        <span className="font-bold text-gray-950 dark:text-white bg-white dark:bg-gray-800 px-2.5 py-0.5 rounded-md shadow-xs border border-emerald-300 dark:border-emerald-700 text-xs">
                          {campaignResult.segment}
                        </span>
                      </div>
                      <p className="mt-2 text-base font-extrabold text-gray-950 dark:text-white">
                        Goal: <span className="text-emerald-700 dark:text-emerald-400">{campaignResult.goal}</span>
                      </p>
                    </div>
                    <div className="shrink-0 text-right">
                      <span className="text-xs font-mono text-gray-500 dark:text-gray-400">
                        Campaign #{campaignResult.campaign_id}
                      </span>
                      <div className="text-xs font-bold text-emerald-700 dark:text-emerald-400 mt-1 flex items-center gap-1 sm:justify-end">
                        <ShieldCheck className="w-4 h-4" /> Hard Policy Enforced
                      </div>
                    </div>
                  </div>

                  {/* Policy Constraints */}
                  <div>
                    <h4 className="font-bold text-gray-950 dark:text-white text-xs uppercase tracking-wider mb-2.5 flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-600" /> Hard Policy Guardrails
                    </h4>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                      {campaignResult.constraints?.summary?.map((c, i) => (
                        <div
                          key={i}
                          className="p-2.5 rounded-xl bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 text-center font-bold text-xs text-gray-800 dark:text-gray-200"
                        >
                          {c}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Discovered Eligible Products */}
                  <div>
                    <h4 className="font-bold text-gray-950 dark:text-white text-xs uppercase tracking-wider mb-2.5 flex items-center gap-2">
                      <Package className="w-4 h-4 text-blue-600" /> Discovered Eligible Products ({campaignResult.eligible_products?.length || 0})
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                      {campaignResult.eligible_products?.map((prod, idx) => (
                        <div
                          key={idx}
                          className="p-3.5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-xs flex flex-col justify-between"
                        >
                          <div>
                            <div className="flex items-center justify-between">
                              <h5 className="font-bold text-gray-900 dark:text-gray-100 text-sm">{prod.name}</h5>
                              {prod.inventory_healthy && (
                                <span className="text-[10px] font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-950 px-2 py-0.5 rounded-full">
                                  Stock: {prod.stock}
                                </span>
                              )}
                            </div>
                            <p className="text-base font-extrabold text-gray-950 dark:text-white mt-1">
                              ₹{prod.price.toLocaleString("en-IN")}
                            </p>
                          </div>
                          <div className="mt-3 pt-2 border-t border-gray-100 dark:border-gray-800 flex justify-between items-center text-xs">
                            <span className="text-gray-500 dark:text-gray-400">Margin:</span>
                            <span className="font-bold text-emerald-600 dark:text-emerald-400">
                              {prod.margin_percent}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Dynamic 5-Stage Cadence Timeline */}
                  <div>
                    <h4 className="font-bold text-gray-950 dark:text-white text-xs uppercase tracking-wider mb-2.5 flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-purple-600" /> 5-Stage Order-Triggered Dynamic Cadence
                    </h4>
                    <div className="space-y-2.5">
                      {campaignResult.cadence?.map((stage, idx) => (
                        <div
                          key={idx}
                          className="p-3.5 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/70 dark:bg-gray-900/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-gray-100/70 dark:hover:bg-gray-800/40 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <span className="px-2.5 py-1 rounded-lg text-xs font-black bg-gray-900 text-white dark:bg-white dark:text-gray-900 shrink-0">
                              {stage.stage}
                            </span>
                            <div>
                              <p className="font-bold text-gray-950 dark:text-gray-100 text-sm">
                                {stage.action || stage.event || "Lifecycle Step"}
                              </p>
                              <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                                {stage.timing_rationale}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-2 text-xs font-semibold text-gray-700 dark:text-gray-300 sm:text-right shrink-0">
                            {stage.channel && (
                              <span className="bg-gray-200 dark:bg-gray-800 px-2 py-0.5 rounded text-[11px]">
                                {stage.channel}
                              </span>
                            )}
                            {stage.type === "TRIGGER_EVENT" && (
                              <span className="bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 px-2 py-0.5 rounded text-[11px]">
                                Trigger Event
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-800 bg-gray-50/80 dark:bg-gray-900/80 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 rounded-xl text-sm font-bold text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-800 transition-colors"
              >
                Cancel
              </button>

              <button
                type="button"
                onClick={handleLaunchCampaign}
                disabled={launching || !campaignResult}
                className="px-6 py-2.5 rounded-xl font-extrabold text-sm bg-emerald-600 hover:bg-emerald-700 text-white shadow-md hover:shadow-lg transition-all flex items-center gap-2 disabled:opacity-50"
              >
                {launching ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" /> Launching...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" /> Launch & Activate Campaign
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
