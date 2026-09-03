import { useState, useEffect, useMemo, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { apiRequest, API_BASE } from '../lib/api';
import { API, price } from '../lib/products';
import type { ProductType } from '../lib/products';

export interface ProductItem {
  id: string;
  name: string;
  brand: string;
  category: string;
  price: number;
  original_price: number;
  rating: number;
  reviews_count: number;
  battery_life?: string;
  features?: string[];
  merchant?: string;
  in_stock: boolean;
  image_url: string;
  slug?: string;
}

export interface ApprovalCardData {
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

export interface PaymentSuccessData {
  success: boolean;
  order_id: number;
  amount: number;
  payment_reference: string;
  status: string;
  delivery_eta: string;
  receipt_url: string;
}

export interface ChatMessage {
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

export interface ConsentPolicy {
  per_transaction_limit: number;
  approval_threshold: number;
  daily_limit: number;
  monthly_limit: number;
  allowed_categories: string[];
  daily_spent: number;
  monthly_spent: number;
}

export type CanvasTabType = 'products' | 'compare' | 'cart' | 'deals' | 'policy' | 'role_intel';

export function useAgenticCommerce() {
  const { user, token } = useAuth();
  const { items: cartItems, totalPrice, addToCart, removeFromCart, updateQuantity, clearCart } = useCart();

  const role = user?.effective_role || 'customer';

  // State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [approving, setApproving] = useState(false);
  const [canvasTab, setCanvasTab] = useState<CanvasTabType>('products');
  const [comparisonList, setComparisonList] = useState<ProductType[]>([]);
  const [catalog, setCatalog] = useState<ProductType[]>([]);
  const [policy, setPolicy] = useState<ConsentPolicy>({
    per_transaction_limit: 5000,
    approval_threshold: 2000,
    daily_limit: 10000,
    monthly_limit: 50000,
    allowed_categories: ['electronics', 'accessories', 'apparel', 'home'],
    daily_spent: 0,
    monthly_spent: 0,
  });
  const [policyNotice, setPolicyNotice] = useState<string | null>(null);

  // Role Configuration
  const roleConfig = useMemo(() => {
    if (role === 'admin') {
      return {
        roleTitle: 'Admin Command Engine',
        roleBadge: 'NeonDB Active • Governance Firewall',
        roleIntelTabLabel: 'Governance & Risk',
        welcomeMessage:
          "Welcome, **Platform Administrator**.\n\nI can inspect cross-merchant GMV, run transaction risk audits, monitor pending governance disbursements, and verify NeonDB infrastructure health.\n\nTry asking: *\"Show today's platform GMV and orders\"*",
        scenarios: [
          "Show platform GMV and orders today",
          "Any pending governance payout approvals?",
          "Show high-risk transactions flagged today",
          "Check NeonDB infrastructure health",
        ],
      };
    }
    if (role === 'seller') {
      return {
        roleTitle: 'Seller Copilot & Intelligence',
        roleBadge: 'Merchant OS • Store Catalog & Receivables',
        roleIntelTabLabel: 'Store Inventory',
        welcomeMessage:
          "Welcome, **Merchant Partner**.\n\nI can analyze your store catalog, flag low-inventory SKUs, inspect debtor receivables, and simulate competitive pricing optimizations.\n\nTry asking: *\"Which products have low stock?\"*",
        scenarios: [
          "Which products have low stock?",
          "Show overdue invoices for collection",
          "Analyze today's store revenue",
          "Compare top selling categories",
        ],
      };
    }
    return {
      roleTitle: 'Agentic Commerce & Payment Assistant',
      roleBadge: 'Consent Firewall Active • Auto-Approve < ₹2,000',
      roleIntelTabLabel: 'Shopping Canvas',
      welcomeMessage:
        "Hello! I'm your **Agentic Commerce & Payment Assistant**.\n\nI can search our live catalog, compare technical specs, prepare your cart, and execute simulated payments under your **Consent Authorization Policy**.\n\nTry asking: *\"I need wireless headphones under ₹5,000\"*",
      scenarios: [
        "I need wireless headphones under ₹5,000",
        "Compare Sony WH-CH520 vs JBL Tune 510BT",
        "Show active flash deals",
        "Show my consent limits",
      ],
    };
  }, [role]);

  // Load Catalog
  useEffect(() => {
    fetch(`${API}/items/`)
      .then(res => res.json())
      .then(data => {
        const list = Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];
        setCatalog(list);
      })
      .catch(() => setCatalog([]));
  }, []);

  // Flash deals
  const flashDeals = useMemo(() => {
    return catalog.filter(p => p.is_featured || (p.discount_price && Number(p.discount_price) < Number(p.price))).slice(0, 12);
  }, [catalog]);

  // Load initial consent policy
  useEffect(() => {
    if (token) {
      apiRequest<ConsentPolicy>('/agent-runtime/commerce/consent/', { token })
        .then(res => setPolicy(res))
        .catch(() => {});
    }

    setMessages([
      {
        id: 'welcome',
        sender: 'agent',
        text: roleConfig.welcomeMessage,
        suggested_followups: roleConfig.scenarios,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  }, [token, roleConfig]);

  // Send Message
  const sendMessage = useCallback(async (msgText: string) => {
    const text = msgText.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    const lower = text.toLowerCase();
    if (lower.includes('compare') || lower.includes('vs')) {
      setCanvasTab('compare');
    } else if (lower.includes('cart') || lower.includes('bag')) {
      setCanvasTab('cart');
    } else if (lower.includes('deal') || lower.includes('discount') || lower.includes('sale')) {
      setCanvasTab('deals');
    } else if (lower.includes('consent') || lower.includes('limit') || lower.includes('policy')) {
      setCanvasTab('policy');
    }

    try {
      // 1. Try Agentic Commerce Service first
      const res = await apiRequest<any>('/agent-runtime/commerce/chat/', {
        token,
        method: 'POST',
        body: JSON.stringify({
          message: text,
          history: messages.slice(-4).map(m => ({ role: m.sender, content: m.text })),
        }),
      });

      const agentMsg: ChatMessage = {
        id: `a-${Date.now()}`,
        sender: 'agent',
        text: res.message || 'I processed your request.',
        intent: res.intent,
        products: res.products,
        cart: res.cart,
        approval_card: res.approval_card,
        payment_success: res.payment_success,
        suggested_followups: res.suggested_followups || roleConfig.scenarios,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages(prev => [...prev, agentMsg]);

      // If products found, auto-switch to products canvas tab
      if (res.products && res.products.length > 0) {
        setCanvasTab('products');
      }

      // If payment succeeded, refresh policy
      if (res.payment_success && token) {
        apiRequest<ConsentPolicy>('/agent-runtime/commerce/consent/', { token })
          .then(p => setPolicy(p))
          .catch(() => {});
      }
    } catch (err: any) {
      // 2. Fallback to /ai/chat/ endpoint if agent-runtime encountered issue
      try {
        const cartContext = {
          items: cartItems.map(i => ({
            name: i.product.name,
            slug: i.product.slug,
            price: String(price(i.product)),
            quantity: i.quantity,
          })),
          total: totalPrice,
        };

        const res = await fetch(`${API_BASE}/ai/chat/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: [{ role: 'user', content: text }],
            context: { cart: cartContext, role },
          }),
        });

        const data = await res.json();
        setMessages(prev => [
          ...prev,
          {
            id: `a-${Date.now()}`,
            sender: 'agent',
            text: data.content || data.response || "Here are the top results from our live catalog.",
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      } catch (fallbackErr) {
        setMessages(prev => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            sender: 'agent',
            text: `I encountered an issue processing your request: ${err.message || 'Network error'}.`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      }
    } finally {
      setLoading(false);
    }
  }, [loading, messages, token, roleConfig, cartItems, totalPrice, role]);

  // Approve Transaction
  const approveTransaction = useCallback(async (intentId: string) => {
    try {
      setApproving(true);
      const res = await apiRequest<PaymentSuccessData>('/agent-runtime/commerce/approve/', {
        token,
        method: 'POST',
        body: JSON.stringify({ intent_id: intentId }),
      });

      setMessages(prev =>
        prev.map(m => {
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

      // Refresh policy metrics
      if (token) {
        const updatedPolicy = await apiRequest<ConsentPolicy>('/agent-runtime/commerce/consent/', { token });
        setPolicy(updatedPolicy);
      }
    } catch (err: any) {
      alert(`Payment execution failed: ${err.message}`);
    } finally {
      setApproving(false);
    }
  }, [token]);

  // Reject Transaction
  const rejectTransaction = useCallback(async (intentId: string) => {
    try {
      await apiRequest<any>('/agent-runtime/commerce/reject/', {
        token,
        method: 'POST',
        body: JSON.stringify({ intent_id: intentId, reason: 'Rejected by user from approval card' }),
      });

      setMessages(prev =>
        prev.map(m => {
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
      alert(`Failed to reject transaction: ${err.message}`);
    }
  }, [token]);

  // Save Policy
  const savePolicy = useCallback(async (newPolicy: ConsentPolicy) => {
    try {
      const res = await apiRequest<any>('/agent-runtime/commerce/consent/', {
        token,
        method: 'POST',
        body: JSON.stringify(newPolicy),
      });
      setPolicy(prev => ({ ...prev, ...newPolicy }));
      setPolicyNotice('Consent limits updated successfully!');
      setTimeout(() => setPolicyNotice(null), 3500);
      return res;
    } catch (err: any) {
      setPolicyNotice(`Failed to update: ${err.message}`);
      throw err;
    }
  }, [token]);

  // Comparison helpers
  const addToCompare = useCallback((product: ProductType) => {
    setComparisonList(prev => {
      if (prev.some(p => p.id === product.id)) return prev;
      if (prev.length >= 4) {
        return [...prev.slice(1), product];
      }
      return [...prev, product];
    });
    setCanvasTab('compare');
  }, []);

  const removeFromCompare = useCallback((productId: string | number) => {
    setComparisonList(prev => prev.filter(p => p.id !== productId));
  }, []);

  const clearCompare = useCallback(() => {
    setComparisonList([]);
  }, []);

  const resetChat = useCallback(() => {
    setMessages([
      {
        id: 'welcome',
        sender: 'agent',
        text: roleConfig.welcomeMessage,
        suggested_followups: roleConfig.scenarios,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  }, [roleConfig]);

  return {
    user,
    role,
    roleConfig,
    messages,
    loading,
    approving,
    canvasTab,
    setCanvasTab,
    comparisonList,
    catalog,
    flashDeals,
    policy,
    setPolicy,
    policyNotice,
    cartItems,
    totalPrice,
    addToCart,
    removeFromCart,
    updateQuantity,
    clearCart,
    sendMessage,
    approveTransaction,
    rejectTransaction,
    savePolicy,
    addToCompare,
    removeFromCompare,
    clearCompare,
    resetChat,
  };
}
