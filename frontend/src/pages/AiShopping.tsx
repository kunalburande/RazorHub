import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Bot,
  Send,
  CreditCard,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Package,
  Layers,
  ArrowRight,
  RefreshCw,
  Sliders,
  DollarSign,
  TrendingUp,
  ShoppingBag,
  Clock,
  ExternalLink,
  ChevronRight,
  Scale,
  Zap,
} from 'lucide-react';
import { apiRequest } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';

interface ProductItem {
  id: string;
  name: string;
  brand: string;
  category: string;
  price: number;
  original_price: number;
  rating: number;
  reviews_count: number;
  battery_life: string;
  features: string[];
  merchant: string;
  in_stock: boolean;
  image_url: string;
}

interface ApprovalCardData {
  card_type: string;
  intent_id: string;
  title: string;
  merchant: string;
  product: string;
  amount: number;
  currency: string;
  payment_method: string;
  reason: string;
  risk: string;
  policy: string;
  status: string;
}

interface PaymentSuccessData {
  success: boolean;
  order_id: number;
  amount: number;
  payment_reference: string;
  status: string;
  delivery_eta: string;
  receipt_url: string;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  intent?: string;
  products?: ProductItem[];
  cart?: any;
  approval_card?: ApprovalCardData;
  payment_success?: PaymentSuccessData;
  suggested_followups?: string[];
  timestamp: string;
}

interface ConsentPolicy {
  per_transaction_limit: number;
  approval_threshold: number;
  daily_limit: number;
  monthly_limit: number;
  allowed_categories: string[];
  daily_spent: number;
  monthly_spent: number;
}

export default function AiShopping() {
  const { user, token } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [approving, setApproving] = useState(false);
  const [policy, setPolicy] = useState<ConsentPolicy>({
    per_transaction_limit: 5000,
    approval_threshold: 2000,
    daily_limit: 10000,
    monthly_limit: 50000,
    allowed_categories: ['electronics', 'accessories', 'apparel', 'home'],
    daily_spent: 0,
    monthly_spent: 0,
  });
  const [showPolicyDrawer, setShowPolicyDrawer] = useState(false);
  const [updatingPolicy, setUpdatingPolicy] = useState(false);
  const [policyNotice, setPolicyNotice] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Fetch initial consent policy & seed initial welcome message
  useEffect(() => {
    const initData = async () => {
      if (token) {
        try {
          const res = await apiRequest<ConsentPolicy>('/agent-runtime/commerce/consent/', { token });
          setPolicy(res);
        } catch (err) {
          console.warn('Could not fetch consent policy, using default:', err);
        }
      }

      setMessages([
        {
          id: 'welcome',
          sender: 'agent',
          text: "Hello! I'm your **Agentic Commerce & Payment Assistant**.\n\nI can search our live catalog, run spec comparisons, prepare your cart, and execute simulated payments under your **Consent Authorization Policy**.\n\nTry asking: *\"I need wireless headphones under ₹5,000\"*",
          suggested_followups: [
            'I need wireless headphones under ₹5,000',
            'Compare Sony WH-CH520 vs JBL Tune 510BT',
            'Show my consent limits',
          ],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    };
    initData();
  }, [token]);

  const handleSendMessage = async (textToSend?: string) => {
    const msg = textToSend || inputMessage;
    if (!msg.trim()) return;

    const userMsgObj: ChatMessage = {
      id: `u-${Date.now()}`,
      sender: 'user',
      text: msg,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsgObj]);
    setInputMessage('');
    setLoading(true);

    try {
      const res = await apiRequest<any>('/agent-runtime/commerce/chat/', {
        token,
        method: 'POST',
        body: JSON.stringify({
          message: msg,
          history: messages.slice(-4).map((m) => ({ role: m.sender, content: m.text })),
        }),
      });

      const agentMsgObj: ChatMessage = {
        id: `a-${Date.now()}`,
        sender: 'agent',
        text: res.message,
        intent: res.intent,
        products: res.products,
        cart: res.cart,
        approval_card: res.approval_card,
        payment_success: res.payment_success,
        suggested_followups: res.suggested_followups,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, agentMsgObj]);

      // If a payment was auto-approved and executed, refresh policy spending metrics
      if (res.payment_success) {
        const updatedPolicy = await apiRequest<ConsentPolicy>('/agent-runtime/commerce/consent/', { token });
        setPolicy(updatedPolicy);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'agent',
          text: `I encountered an issue processing your request: ${err.message || 'Network error'}. Please verify you are logged in.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveTransaction = async (intentId: string) => {
    try {
      setApproving(true);
      const res = await apiRequest<PaymentSuccessData>('/agent-runtime/commerce/approve/', {
        token,
        method: 'POST',
        body: JSON.stringify({ intent_id: intentId }),
      });

      // Update message with payment success
      setMessages((prev) =>
        prev.map((m) => {
          if (m.approval_card && m.approval_card.intent_id === intentId) {
            return {
              ...m,
              approval_card: undefined,
              payment_success: res,
              text: `✅ **Payment Authorized & Executed!**\n\nOrder **#ORD-${res.order_id}** is confirmed for **₹${res.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}**.\nReference: \`${res.payment_reference}\`.\nEstimated Delivery: **${res.delivery_eta}**.`,
              suggested_followups: ['Track order status', 'Download tax receipt', 'Shop more'],
            };
          }
          return m;
        })
      );

      // Refresh policy spend
      const updatedPolicy = await apiRequest<ConsentPolicy>('/agent-runtime/commerce/consent/', { token });
      setPolicy(updatedPolicy);
    } catch (err: any) {
      alert(`Payment execution failed: ${err.message}`);
    } finally {
      setApproving(false);
    }
  };

  const handleRejectTransaction = async (intentId: string) => {
    try {
      await apiRequest<any>('/agent-runtime/commerce/reject/', {
        token,
        method: 'POST',
        body: JSON.stringify({ intent_id: intentId, reason: 'Rejected by user from approval card' }),
      });

      setMessages((prev) =>
        prev.map((m) => {
          if (m.approval_card && m.approval_card.intent_id === intentId) {
            return {
              ...m,
              approval_card: undefined,
              text: '❌ **Transaction Cancelled.** You rejected the payment request. Your cart items remain saved.',
              suggested_followups: ['Search other products', 'Adjust consent limits'],
            };
          }
          return m;
        })
      );
    } catch (err: any) {
      alert(`Failed to reject: ${err.message}`);
    }
  };

  const handleSavePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setUpdatingPolicy(true);
      const res = await apiRequest<any>('/agent-runtime/commerce/consent/', {
        token,
        method: 'POST',
        body: JSON.stringify(policy),
      });
      setPolicyNotice('Consent limits updated successfully!');
      setTimeout(() => setPolicyNotice(null), 3500);
    } catch (err: any) {
      setPolicyNotice(`Failed to update: ${err.message}`);
    } finally {
      setUpdatingPolicy(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 sm:py-8 space-y-6">
      
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-3xl bg-surface border border-border/80 shadow-xs">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/30 tracking-wider uppercase">
              <Sparkles className="w-3.5 h-3.5 animate-pulse" />
              Autonomous Payment Assistant
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-primary tracking-tight">
            Agentic Commerce Studio
          </h1>
          <p className="text-xs sm:text-sm text-secondary max-w-2xl">
            Conversational shopping with deterministic price calculations, catalog filtering, and consent-based payment authorization.
          </p>
        </div>

        {/* Consent Status Badge & Drawer Toggle */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setShowPolicyDrawer(!showPolicyDrawer)}
            className="px-4 py-2.5 rounded-2xl text-xs font-bold border border-indigo-500/30 bg-indigo-500/5 hover:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 transition flex items-center gap-2 cursor-pointer"
          >
            <Sliders className="w-4 h-4" />
            <span>Consent Authorization Policy</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Left Chat & Right Live Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Column: Conversational Assistant (8 Cols) */}
        <div className="lg:col-span-8 flex flex-col h-[750px] rounded-3xl bg-surface border border-border/80 shadow-xs overflow-hidden">
          
          {/* Chat Stream Header */}
          <div className="p-4 border-b border-border flex items-center justify-between bg-muted/30">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center shadow-xs">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-primary">Autonomous Commerce Assistant</h3>
                <p className="text-[10px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1 font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Consent Firewall Active
                </p>
              </div>
            </div>

            <div className="text-[11px] font-mono text-secondary bg-surface px-2.5 py-1 rounded-lg border border-border">
              Auto: &lt;₹{policy.approval_threshold.toLocaleString()} • Confirm: ₹{policy.approval_threshold.toLocaleString()}-₹{policy.per_transaction_limit.toLocaleString()}
            </div>
          </div>

          {/* Messages Stream */}
          <div className="flex-1 p-4 sm:p-6 overflow-y-auto space-y-6">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-3 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {m.sender === 'agent' && (
                  <div className="w-8 h-8 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div className={`space-y-3 max-w-[85%] sm:max-w-[75%] ${m.sender === 'user' ? 'items-end' : 'items-start'}`}>
                  
                  {/* Bubble */}
                  <div
                    className={`p-4 rounded-3xl text-xs sm:text-sm leading-relaxed ${
                      m.sender === 'user'
                        ? 'bg-primary text-surface font-medium rounded-tr-xs'
                        : 'bg-background border border-border/80 text-secondary rounded-tl-xs'
                    }`}
                  >
                    <div className="whitespace-pre-line">
                      {m.text.split('\n').map((line, i) => {
                        // Bold markdown parsing
                        const parts = line.split(/(\*\*.*?\*\*)/g);
                        return (
                          <span key={i} className="block">
                            {parts.map((p, j) => {
                              if (p.startsWith('**') && p.endsWith('**')) {
                                return <strong key={j} className="text-primary font-bold">{p.slice(2, -2)}</strong>;
                              }
                              return p;
                            })}
                          </span>
                        );
                      })}
                    </div>
                  </div>

                  {/* ── EMBEDDED PRODUCT RECOMMENDATIONS ── */}
                  {m.products && m.products.length > 0 && (
                    <div className="space-y-3 pt-1">
                      <div className="flex items-center gap-1.5 text-[11px] font-bold text-primary uppercase tracking-wider">
                        <Package className="w-3.5 h-3.5 text-indigo-500" />
                        <span>Recommended Catalog Matches</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {m.products.slice(0, 4).map((prod) => (
                          <div
                            key={prod.id}
                            className="p-3 rounded-2xl bg-surface border border-border/80 hover:border-indigo-500/40 transition flex flex-col justify-between space-y-2 shadow-2xs"
                          >
                            <div className="flex items-start gap-3">
                              <img
                                src={prod.image_url}
                                alt={prod.name}
                                className="w-14 h-14 object-cover rounded-xl shrink-0 bg-muted"
                              />
                              <div className="space-y-0.5 overflow-hidden">
                                <h4 className="text-xs font-bold text-primary truncate" title={prod.name}>
                                  {prod.name}
                                </h4>
                                <p className="text-[10px] text-secondary font-medium">
                                  {prod.brand} • {prod.battery_life}
                                </p>
                                <div className="flex items-baseline gap-1.5 pt-0.5">
                                  <span className="text-xs font-black font-mono text-primary">
                                    ₹{prod.price.toLocaleString('en-IN')}
                                  </span>
                                  {prod.original_price > prod.price && (
                                    <span className="text-[10px] text-secondary line-through font-mono">
                                      ₹{prod.original_price.toLocaleString('en-IN')}
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>

                            <div className="pt-1 flex items-center justify-between border-t border-border/50 text-[10px]">
                              <span className="text-amber-600 font-bold">★ {prod.rating}</span>
                              <button
                                type="button"
                                onClick={() => handleSendMessage(`Add ${prod.name} to cart and checkout`)}
                                className="px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold transition cursor-pointer"
                              >
                                Add & Pay
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* ── EXPLICIT TRANSACTION APPROVAL CARD ── */}
                  {m.approval_card && (
                    <div className="p-5 rounded-3xl bg-gradient-to-b from-indigo-500/5 to-purple-500/5 border-2 border-indigo-500/30 space-y-4 shadow-md">
                      
                      {/* Card Header */}
                      <div className="flex items-center justify-between border-b border-indigo-500/20 pb-3">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-bold text-xs shadow-xs">
                            ⚡
                          </div>
                          <div>
                            <h4 className="text-xs font-black uppercase text-indigo-600 dark:text-indigo-400 tracking-wider">
                              Agent Wants to Pay
                            </h4>
                            <p className="text-[10px] text-secondary">Consent Authorization Gate Required</p>
                          </div>
                        </div>

                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
                          {m.approval_card.risk} RISK
                        </span>
                      </div>

                      {/* Line Items & Details */}
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between py-1 border-b border-border/40">
                          <span className="text-secondary font-medium">Merchant:</span>
                          <span className="font-bold text-primary text-right">{m.approval_card.merchant}</span>
                        </div>
                        <div className="flex justify-between py-1 border-b border-border/40">
                          <span className="text-secondary font-medium">Product:</span>
                          <span className="font-bold text-primary text-right max-w-[65%] truncate">{m.approval_card.product}</span>
                        </div>
                        <div className="flex justify-between py-1 border-b border-border/40">
                          <span className="text-secondary font-medium">Payment Method:</span>
                          <span className="font-mono text-primary font-semibold">{m.approval_card.payment_method}</span>
                        </div>
                        <div className="flex justify-between py-1 border-b border-border/40">
                          <span className="text-secondary font-medium">Reason:</span>
                          <span className="text-secondary text-right">{m.approval_card.reason}</span>
                        </div>
                        <div className="flex justify-between py-1 border-b border-indigo-500/20">
                          <span className="text-indigo-600 dark:text-indigo-400 font-bold">Policy Rule:</span>
                          <span className="text-[11px] text-indigo-600 dark:text-indigo-400 font-medium text-right max-w-[65%]">
                            {m.approval_card.policy}
                          </span>
                        </div>
                        <div className="flex justify-between items-baseline pt-2">
                          <span className="text-sm font-bold text-primary">Total Payable:</span>
                          <span className="text-xl font-black font-mono text-indigo-600 dark:text-indigo-400">
                            ₹{m.approval_card.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                          </span>
                        </div>
                      </div>

                      {/* Approval / Rejection Actions */}
                      <div className="flex items-center gap-3 pt-2">
                        <button
                          type="button"
                          disabled={approving}
                          onClick={() => handleRejectTransaction(m.approval_card!.intent_id)}
                          className="flex-1 py-2.5 rounded-2xl text-xs font-bold bg-muted hover:bg-border text-secondary transition cursor-pointer disabled:opacity-50"
                        >
                          Reject
                        </button>
                        <button
                          type="button"
                          disabled={approving}
                          onClick={() => handleApproveTransaction(m.approval_card!.intent_id)}
                          className="flex-1 py-2.5 rounded-2xl text-xs font-black bg-gradient-to-r from-indigo-600 to-purple-600 hover:opacity-95 text-white shadow-lg shadow-indigo-600/25 transition cursor-pointer flex items-center justify-center gap-1.5 disabled:opacity-50"
                        >
                          {approving ? (
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <CheckCircle2 className="w-3.5 h-3.5" />
                          )}
                          <span>Approve & Pay</span>
                        </button>
                      </div>

                    </div>
                  )}

                  {/* ── PAYMENT SUCCESS BANNER ── */}
                  {m.payment_success && (
                    <div className="p-4 rounded-3xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-800 dark:text-emerald-200 text-xs space-y-2">
                      <div className="flex items-center gap-2 font-bold text-emerald-600 dark:text-emerald-400">
                        <CheckCircle2 className="w-4 h-4 shrink-0" />
                        <span>Order #ORD-{m.payment_success.order_id} Confirmed</span>
                      </div>
                      <p className="text-[11px] text-secondary">
                        Payment reference: <code className="font-mono bg-surface px-1 py-0.5 rounded">{m.payment_success.payment_reference}</code>
                      </p>
                      <div className="flex items-center justify-between pt-1">
                        <span className="font-semibold text-primary">Delivery in {m.payment_success.delivery_eta}</span>
                        <Link
                          to={`/orders/${m.payment_success.order_id}`}
                          className="font-bold underline text-indigo-600 hover:text-indigo-500 flex items-center gap-1"
                        >
                          <span>View Order</span>
                          <ExternalLink className="w-3 h-3" />
                        </Link>
                      </div>
                    </div>
                  )}

                  {/* Suggested Followups */}
                  {m.suggested_followups && m.suggested_followups.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {m.suggested_followups.map((sug, sIdx) => (
                        <button
                          key={sIdx}
                          type="button"
                          onClick={() => handleSendMessage(sug)}
                          className="px-3 py-1 rounded-xl text-[11px] font-medium bg-muted hover:bg-border text-secondary hover:text-primary transition cursor-pointer"
                        >
                          {sug}
                        </button>
                      ))}
                    </div>
                  )}

                  <span className="text-[9px] text-secondary px-1">{m.timestamp}</span>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-indigo-500/10 text-indigo-600 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 animate-spin" />
                </div>
                <div className="p-3.5 rounded-2xl bg-muted/60 text-xs text-secondary flex items-center gap-2">
                  <RefreshCw className="w-3 h-3 animate-spin text-indigo-500" />
                  <span>Evaluating catalog & consent policies...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <div className="p-4 border-t border-border bg-surface">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Ask me to search, compare, or checkout (e.g. 'I need wireless headphones under ₹5,000')..."
                className="flex-1 px-4 py-3 rounded-2xl bg-background border border-border text-xs sm:text-sm text-primary placeholder:text-secondary focus:outline-none focus:border-indigo-500"
              />
              <button
                type="submit"
                disabled={loading || !inputMessage.trim()}
                className="p-3 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:opacity-95 text-white disabled:opacity-50 transition cursor-pointer shadow-md"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>

        </div>

        {/* Right Column: Consent Firewall & Guardrails Panel (4 Cols) */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Policy Overview Card */}
          <div className="p-6 rounded-3xl bg-surface border border-border/80 shadow-xs space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-500" />
                <h3 className="text-sm font-bold text-primary uppercase tracking-wider">
                  Payment Consent Model
                </h3>
              </div>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 border border-emerald-500/20">
                ACTIVE
              </span>
            </div>

            <p className="text-xs text-secondary leading-relaxed">
              Your autonomous agent can only transact within deterministic parameters that you configure.
            </p>

            <div className="space-y-3 pt-1">
              
              {/* Bracket 1: Auto Approve */}
              <div className="p-3 rounded-2xl bg-emerald-500/5 border border-emerald-500/20 flex items-center justify-between">
                <div>
                  <div className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400">
                    Auto-Approve Ceiling
                  </div>
                  <div className="text-[10px] text-secondary">₹0 — ₹{(policy.approval_threshold - 1).toLocaleString()}</div>
                </div>
                <span className="font-mono font-bold text-xs text-emerald-600">&lt; ₹{policy.approval_threshold.toLocaleString()}</span>
              </div>

              {/* Bracket 2: Require Confirmation */}
              <div className="p-3 rounded-2xl bg-amber-500/5 border border-amber-500/20 flex items-center justify-between">
                <div>
                  <div className="text-[11px] font-bold text-amber-600 dark:text-amber-400">
                    Confirmation Bracket
                  </div>
                  <div className="text-[10px] text-secondary">Presents approval card</div>
                </div>
                <span className="font-mono font-bold text-xs text-amber-600">
                  ₹{policy.approval_threshold.toLocaleString()} — ₹{policy.per_transaction_limit.toLocaleString()}
                </span>
              </div>

              {/* Bracket 3: Block */}
              <div className="p-3 rounded-2xl bg-rose-500/5 border border-rose-500/20 flex items-center justify-between">
                <div>
                  <div className="text-[11px] font-bold text-rose-600 dark:text-rose-400">
                    Blocked Limit
                  </div>
                  <div className="text-[10px] text-secondary">Rejected by firewall</div>
                </div>
                <span className="font-mono font-bold text-xs text-rose-600">&gt; ₹{policy.per_transaction_limit.toLocaleString()}</span>
              </div>

            </div>

            {/* Daily Spent Meter */}
            <div className="pt-2 space-y-1.5 border-t border-border">
              <div className="flex justify-between text-xs">
                <span className="text-secondary font-medium">Daily Spend Tracking:</span>
                <span className="font-mono font-bold text-primary">
                  ₹{policy.daily_spent.toLocaleString()} / ₹{policy.daily_limit.toLocaleString()}
                </span>
              </div>
              <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                <div
                  style={{ width: `${Math.min((policy.daily_spent / policy.daily_limit) * 100, 100)}%` }}
                  className="h-full bg-indigo-600 rounded-full"
                />
              </div>
            </div>

            <button
              type="button"
              onClick={() => setShowPolicyDrawer(true)}
              className="w-full py-2.5 rounded-2xl text-xs font-bold border border-border hover:bg-muted text-primary transition cursor-pointer flex items-center justify-center gap-1.5"
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>Configure Limits & Categories</span>
            </button>
          </div>

          {/* Quick Commerce Starters */}
          <div className="p-6 rounded-3xl bg-surface border border-border/80 shadow-xs space-y-3">
            <h3 className="text-xs font-bold text-primary uppercase tracking-wider flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-indigo-500" />
              <span>Quick Scenarios</span>
            </h3>
            
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => handleSendMessage('I need wireless headphones under ₹5,000')}
                className="w-full p-3 rounded-2xl bg-background hover:bg-muted border border-border text-left transition cursor-pointer group"
              >
                <div className="text-xs font-bold text-primary group-hover:text-indigo-600 flex items-center justify-between">
                  <span>Wireless headphones under ₹5,000</span>
                  <ChevronRight className="w-3 h-3 text-secondary group-hover:translate-x-0.5 transition" />
                </div>
                <p className="text-[11px] text-secondary mt-0.5">Search catalog, filter by price, compare specs.</p>
              </button>

              <button
                type="button"
                onClick={() => handleSendMessage('Compare Sony WH-CH520 vs boAt Rockerz 450 Pro')}
                className="w-full p-3 rounded-2xl bg-background hover:bg-muted border border-border text-left transition cursor-pointer group"
              >
                <div className="text-xs font-bold text-primary group-hover:text-indigo-600 flex items-center justify-between">
                  <span>Compare Sony vs boAt Rockerz</span>
                  <ChevronRight className="w-3 h-3 text-secondary group-hover:translate-x-0.5 transition" />
                </div>
                <p className="text-[11px] text-secondary mt-0.5">Side-by-side battery and sound comparison.</p>
              </button>

              <button
                type="button"
                onClick={() => handleSendMessage('Add Sony to cart and checkout')}
                className="w-full p-3 rounded-2xl bg-background hover:bg-muted border border-border text-left transition cursor-pointer group"
              >
                <div className="text-xs font-bold text-primary group-hover:text-indigo-600 flex items-center justify-between">
                  <span>Add Sony & Trigger Approval Card</span>
                  <ChevronRight className="w-3 h-3 text-secondary group-hover:translate-x-0.5 transition" />
                </div>
                <p className="text-[11px] text-secondary mt-0.5">Calculates ₹4,040 and requests confirmation.</p>
              </button>
            </div>
          </div>

        </div>

      </div>

      {/* ── CONSENT POLICY CONFIGURATION DRAWER / MODAL ── */}
      {showPolicyDrawer && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-3xl max-w-md w-full p-6 sm:p-7 space-y-5 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-indigo-500" />
                <h3 className="text-sm font-bold text-primary">Edit Payment Consent Limits</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowPolicyDrawer(false)}
                className="text-secondary hover:text-primary text-xs font-bold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            {policyNotice && (
              <div className="p-3 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-900 dark:text-indigo-200 text-xs font-medium">
                {policyNotice}
              </div>
            )}

            <form onSubmit={handleSavePolicy} className="space-y-4 text-xs">
              <div>
                <label className="block text-secondary font-bold mb-1">
                  Per-Transaction Ceiling (Block if exceeded)
                </label>
                <input
                  type="number"
                  value={policy.per_transaction_limit}
                  onChange={(e) => setPolicy({ ...policy, per_transaction_limit: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary font-mono"
                />
                <p className="text-[10px] text-secondary mt-1">Default: ₹5,000</p>
              </div>

              <div>
                <label className="block text-secondary font-bold mb-1">
                  Auto-Approve Threshold (Auto-execute if below)
                </label>
                <input
                  type="number"
                  value={policy.approval_threshold}
                  onChange={(e) => setPolicy({ ...policy, approval_threshold: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary font-mono"
                />
                <p className="text-[10px] text-secondary mt-1">
                  Default: ₹2,000 (Amounts between ₹{policy.approval_threshold} and ₹{policy.per_transaction_limit} require card confirmation)
                </p>
              </div>

              <div>
                <label className="block text-secondary font-bold mb-1">Daily Total Spend Limit</label>
                <input
                  type="number"
                  value={policy.daily_limit}
                  onChange={(e) => setPolicy({ ...policy, daily_limit: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary font-mono"
                />
              </div>

              <div>
                <label className="block text-secondary font-bold mb-1">Monthly Total Spend Limit</label>
                <input
                  type="number"
                  value={policy.monthly_limit}
                  onChange={(e) => setPolicy({ ...policy, monthly_limit: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary font-mono"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowPolicyDrawer(false)}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-secondary hover:bg-muted"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updatingPolicy}
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs cursor-pointer flex items-center gap-1.5"
                >
                  {updatingPolicy && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  <span>Save Consent Settings</span>
                </button>
              </div>
            </form>

          </div>
        </div>
      )}

    </div>
  );
}
