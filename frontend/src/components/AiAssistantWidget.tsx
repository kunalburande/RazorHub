import { useEffect, useMemo, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import {
  Send,
  X,
  ShoppingCart,
  Check,
  Sparkles,
  CreditCard,
  ArrowRight,
  ShieldCheck,
  Tag,
  RefreshCw,
  Search,
  Scale,
  Package,
  Flame,
  Bot,
  Layers,
  ChevronRight,
  Maximize2,
  Minimize2,
  ExternalLink,
  Plus,
  Minus,
  Trash2,
  SlidersHorizontal,
  CheckCircle2,
  Zap,
  TrendingUp,
  Cpu,
  Shirt,
  Footprints,
  ShoppingBag,
} from 'lucide-react';

import { useCart } from '../context/CartContext';
import { useTranslation } from '../i18n/LocaleContext';
import { Link, useNavigate } from 'react-router-dom';
import { API_BASE } from '../lib/api';
import { API, productImage, price, formatPrice } from '../lib/products';
import type { ProductType } from '../lib/products';

interface ChatMessage {
  id: string;
  role: 'assistant' | 'user';
  text: string;
  agent?: string;
  toolCalls?: any[];
  actionType?: 'products' | 'cart' | 'compare' | 'deals' | 'general';
  suggestedFollowups?: string[];
}

export default function AiAssistantWidget() {
  const { items, addToCart, removeFromCart, updateQuantity, totalPrice, totalCount } = useCart();
  const { t } = useTranslation();
  const navigate = useNavigate();

  // Widget visibility
  const [open, setOpen] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Chat State
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Canvas / Workspace State
  const [activeTab, setActiveTab] = useState<'products' | 'compare' | 'cart' | 'deals'>('products');
  const [canvasProducts, setCanvasProducts] = useState<ProductType[]>([]);
  const [compareList, setCompareList] = useState<ProductType[]>([]);
  const [catalog, setCatalog] = useState<ProductType[]>([]);
  const [canvasSearch, setCanvasSearch] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [addedAnimationSlug, setAddedAnimationSlug] = useState<string | null>(null);

  // Chat History
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const saved = window.localStorage.getItem('razorhub-ai-messages-v2');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      } catch {
        // ignore
      }
    }
    return [
      {
        id: 'welcome',
        role: 'assistant',
        agent: 'Orchestrator',
        text: "Hi! I'm RazorHub AI — your autonomous shopping assistant. Ask me to find products, compare specs, check discounts, or manage your cart in real-time.",
        suggestedFollowups: [
          'Find laptops under ₹60,000',
          'Compare Samsung Galaxy vs iPhone',
          'Show top rated sneakers',
          'What deals are active today?',
        ],
      },
    ];
  });

  // Save chat to localStorage
  useEffect(() => {
    window.localStorage.setItem('razorhub-ai-messages-v2', JSON.stringify(messages));
  }, [messages]);

  // Listen to custom toggle events from Navbar or other buttons
  useEffect(() => {
    const handleToggle = () => setOpen(prev => !prev);
    const handleOpen = () => setOpen(true);
    const handleClose = () => setOpen(false);

    window.addEventListener('toggle-ai-studio', handleToggle);
    window.addEventListener('open-ai-studio', handleOpen);
    window.addEventListener('close-ai-studio', handleClose);

    return () => {
      window.removeEventListener('toggle-ai-studio', handleToggle);
      window.removeEventListener('open-ai-studio', handleOpen);
      window.removeEventListener('close-ai-studio', handleClose);
    };
  }, []);

  // Keyboard shortcut (Escape to close, Ctrl+K or Cmd+K to toggle)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        setOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open]);

  // Scroll chat to bottom
  useEffect(() => {
    if (open) {
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
      }, 100);
    }
  }, [messages, open, loading]);

  // Fetch product catalog for instant local intelligence & recommendations
  useEffect(() => {
    fetch(`${API}/items/`)
      .then(res => res.json())
      .then(data => {
        const list = Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];
        setCatalog(list);
      })
      .catch(() => setCatalog([]));
  }, []);

  // Product lookup map
  const allProductsMap = useMemo(() => {
    const map = new Map<string, ProductType>();
    for (const ci of items) {
      if (ci.product.slug) map.set(ci.product.slug, ci.product);
    }
    for (const p of catalog) {
      if (p.slug) map.set(p.slug, p);
    }
    return map;
  }, [catalog, items]);

  // Flash deals from catalog
  const flashDeals = useMemo(() => {
    return catalog.filter(p => p.is_featured || (p.discount_price && Number(p.discount_price) < Number(p.price))).slice(0, 12);
  }, [catalog]);

  // Helper to extract products from AI response or query matches
  const findMatchingProducts = (query: string, rawProducts?: any[]): ProductType[] => {
    if (rawProducts && Array.isArray(rawProducts) && rawProducts.length > 0) {
      return rawProducts.map((p: any) => {
        if (typeof p === 'object' && p.id && p.name) return p as ProductType;
        const found = allProductsMap.get(p.slug || p.id);
        return found || (p as ProductType);
      });
    }

    const q = query.toLowerCase();
    const tokens = q.split(/\s+/).filter(t => t.length > 2);
    if (tokens.length === 0) return [];

    return catalog
      .filter(p => {
        const name = (p.name || '').toLowerCase();
        const cat = (p.category?.name || p.category?.slug || '').toLowerCase();
        const desc = (p.description || '').toLowerCase();
        return tokens.some(tok => name.includes(tok) || cat.includes(tok) || desc.includes(tok));
      })
      .slice(0, 16);
  };

  // Send message handler
  async function handleSendMessage(inputText: string) {
    const trimmed = inputText.trim();
    if (!trimmed || loading) return;

    const userMsg: ChatMessage = { id: Date.now().toString(), role: 'user', text: trimmed };
    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setMessage('');
    setLoading(true);

    // Context analysis for intent
    const lower = trimmed.toLowerCase();
    const isCartQuery = lower.includes('cart') || lower.includes('checkout') || lower.includes('bag');
    const isCompareQuery = lower.includes('compare') || lower.includes('vs') || lower.includes('difference');
    const isDealsQuery = lower.includes('deal') || lower.includes('discount') || lower.includes('sale') || lower.includes('offer');

    try {
      const cartContext = {
        items: items.map(i => ({
          name: i.product.name,
          slug: i.product.slug,
          price: String(price(i.product)),
          quantity: i.quantity,
        })),
        total: totalPrice,
      };

      const historyPayload = newHistory.map(m => ({
        role: m.role === 'assistant' ? 'assistant' : 'user',
        content: m.text,
      }));

      const res = await fetch(`${API_BASE}/ai/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: historyPayload,
          context: {
            cart: cartContext,
            platform: 'razorhub',
          },
        }),
      });

      if (!res.ok) throw new Error('API Error');
      const data = await res.json();

      const replyText = data.content || data.response || "Here are the top results from our live catalog.";
      const returnedProducts = data.productCards || (data.response?.results ? data.response.results : undefined);

      // Match products for canvas display
      const matched = findMatchingProducts(trimmed, returnedProducts);

      if (matched.length > 0) {
        setCanvasProducts(matched);
        setActiveTab('products');
      } else if (isCartQuery) {
        setActiveTab('cart');
      } else if (isDealsQuery) {
        setActiveTab('deals');
      } else if (isCompareQuery && canvasProducts.length >= 2) {
        setCompareList(canvasProducts.slice(0, 3));
        setActiveTab('compare');
      }

      // Generate smart follow-up suggestions
      const followups: string[] = [];
      if (matched.length > 0) {
        followups.push(`Sort ${matched.length} items by lowest price`);
        if (matched.length >= 2) {
          followups.push(`Compare ${matched[0].name.split(' ').slice(0, 2).join(' ')} vs ${matched[1].name.split(' ').slice(0, 2).join(' ')}`);
        }
        followups.push(`Add ${matched[0].name.split(' ').slice(0, 2).join(' ')} to cart`);
      } else if (isCartQuery) {
        followups.push('Proceed to one-click checkout');
        followups.push('Apply available coupon codes');
      } else {
        followups.push('Show latest electronics deals');
        followups.push('Find laptops under ₹50,000');
      }

      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          agent: data.agent ? `${data.agent.charAt(0).toUpperCase() + data.agent.slice(1)} Agent` : 'Shopping Agent',
          text: replyText,
          toolCalls: data.toolCalls,
          actionType: isCartQuery ? 'cart' : matched.length > 0 ? 'products' : 'general',
          suggestedFollowups: followups.slice(0, 3),
        },
      ]);
    } catch (err) {
      console.error(err);
      // Local fallback search using catalog
      const localMatched = findMatchingProducts(trimmed);
      if (localMatched.length > 0) {
        setCanvasProducts(localMatched);
        setActiveTab('products');
      }

      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          agent: 'Search Agent',
          text: localMatched.length > 0
            ? `I found ${localMatched.length} products matching "${trimmed}" in our live catalog. You can interact with them directly on the canvas.`
            : "I'm ready to help. Try asking for specific products (e.g. 'Air Fryer', 'Samsung S25 Ultra', 'Classmate Notebooks').",
          suggestedFollowups: [
            'Show top rated electronics',
            'Find groceries & snacks',
            'Summarize my cart',
          ],
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleFormSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    handleSendMessage(message);
  }

  function handleAddToCartWithAnimation(p: ProductType) {
    addToCart(p, 1);
    setAddedAnimationSlug(p.slug);
    setTimeout(() => setAddedAnimationSlug(null), 1800);
  }

  function toggleCompare(p: ProductType) {
    setCompareList(prev => {
      const exists = prev.some(item => item.id === p.id);
      if (exists) {
        return prev.filter(item => item.id !== p.id);
      }
      if (prev.length >= 4) {
        return [...prev.slice(1), p];
      }
      return [...prev, p];
    });
    setActiveTab('compare');
  }

  function resetChat() {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        agent: 'Orchestrator',
        text: "Hi! I'm RazorHub AI — your autonomous shopping assistant. Ask me to find products, compare specs, check discounts, or manage your cart in real-time.",
        suggestedFollowups: [
          'Find laptops under ₹60,000',
          'Compare Samsung Galaxy vs iPhone',
          'Show top rated sneakers',
          'What deals are active today?',
        ],
      },
    ]);
    setCanvasProducts([]);
    setCompareList([]);
  }

  // Filtered canvas products based on in-canvas search bar
  const displayedCanvasProducts = useMemo(() => {
    if (!canvasSearch.trim()) return canvasProducts;
    const q = canvasSearch.toLowerCase();
    return canvasProducts.filter(p =>
      (p.name || '').toLowerCase().includes(q) ||
      (p.category?.name || '').toLowerCase().includes(q)
    );
  }, [canvasProducts, canvasSearch]);

  return (
    <>
      {/* ── Floating Launcher Pill Button (when Studio is closed) ── */}
      {!open && (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 rounded-full bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-600 px-4 py-3 text-sm font-bold text-white shadow-2xl shadow-indigo-500/40 hover:scale-105 hover:shadow-indigo-500/60 active:scale-95 transition-all duration-300 group cursor-pointer border border-white/20"
          aria-label="Open AI Shopping Studio"
        >
          <div className="relative">
            <Sparkles className="h-5 w-5 text-amber-300 animate-pulse" />
            <span className="absolute -top-1 -right-1 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
          </div>
          <span className="tracking-wide">AI Shop</span>
        </button>
      )}

      {/* ── Dual-Window Floating AI Shopping Studio (when open) ── */}
      {open && (
        <div className="fixed inset-0 z-[85] pointer-events-none transition-all duration-300">
          {/* Subtle Ambient Backdrop */}
          <div
            onClick={() => setOpen(false)}
            className="absolute inset-0 bg-black/40 backdrop-blur-xs pointer-events-auto transition-opacity animate-in fade-in duration-300"
          />

          {/* Floating Dual-Window Container */}
          <div className="absolute top-[76px] lg:top-[84px] bottom-6 left-4 lg:left-6 right-4 lg:right-6 flex flex-col lg:flex-row gap-5 max-w-[1720px] mx-auto pointer-events-none">

            {/* ════════════════════════════════════════════════════════════
                WINDOW 1 (LEFT): AI CANVAS & LIVE RESULTS STUDIO
            ════════════════════════════════════════════════════════════ */}
            <div className={`pointer-events-auto flex-1 h-full min-h-0 rounded-3xl bg-surface/95 dark:bg-zinc-900/95 backdrop-blur-2xl border border-border/80 shadow-[0_25px_70px_-15px_rgba(0,0,0,0.35)] flex flex-col overflow-hidden transition-all duration-300 animate-in fade-in slide-in-from-left-4 ${
              isFullscreen ? 'fixed inset-4 z-[90]' : ''
            }`}>
              {/* Canvas Header */}
              <div className="px-6 py-4 border-b border-border/60 bg-surface/50 dark:bg-zinc-900/50 flex flex-wrap items-center justify-between gap-3 shrink-0">
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-2xl bg-gradient-to-tr from-indigo-500/20 via-purple-500/20 to-pink-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-500 shadow-sm">
                    <Sparkles className="h-4.5 w-4.5 text-indigo-600 dark:text-indigo-400" />
                  </div>
                  <div>
                    <h2 className="text-sm font-bold text-primary flex items-center gap-2">
                      <span>AI Shopping Canvas</span>
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        Live Synchronized
                      </span>
                    </h2>
                    <p className="text-xs text-secondary hidden sm:block">
                      Interactive results, comparisons, active deals & instant cart updates
                    </p>
                  </div>
                </div>

                {/* Canvas Tab Navigation */}
                <div className="flex items-center gap-1.5 bg-muted/60 p-1 rounded-2xl border border-border/60 text-xs font-semibold">
                  <button
                    type="button"
                    onClick={() => setActiveTab('products')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all ${
                      activeTab === 'products'
                        ? 'bg-surface dark:bg-zinc-800 text-primary shadow-sm font-bold'
                        : 'text-secondary hover:text-primary'
                    }`}
                  >
                    <Layers className="h-3.5 w-3.5" />
                    <span>Products ({canvasProducts.length})</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setActiveTab('compare')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all ${
                      activeTab === 'compare'
                        ? 'bg-surface dark:bg-zinc-800 text-primary shadow-sm font-bold'
                        : 'text-secondary hover:text-primary'
                    }`}
                  >
                    <Scale className="h-3.5 w-3.5" />
                    <span>Compare ({compareList.length})</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setActiveTab('cart')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all ${
                      activeTab === 'cart'
                        ? 'bg-surface dark:bg-zinc-800 text-primary shadow-sm font-bold'
                        : 'text-secondary hover:text-primary'
                    }`}
                  >
                    <ShoppingCart className="h-3.5 w-3.5" />
                    <span>Cart ({totalCount})</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setActiveTab('deals')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all ${
                      activeTab === 'deals'
                        ? 'bg-surface dark:bg-zinc-800 text-primary shadow-sm font-bold'
                        : 'text-secondary hover:text-primary'
                    }`}
                  >
                    <Flame className="h-3.5 w-3.5 text-amber-500" />
                    <span>Deals</span>
                  </button>
                </div>

                {/* Right Canvas Tools */}
                <div className="flex items-center gap-2">
                  {activeTab === 'products' && canvasProducts.length > 0 && (
                    <div className="relative hidden md:block">
                      <Search className="h-3.5 w-3.5 text-secondary absolute left-2.5 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        value={canvasSearch}
                        onChange={e => setCanvasSearch(e.target.value)}
                        placeholder="Filter results..."
                        className="w-36 lg:w-48 bg-muted/40 border border-border/60 rounded-xl pl-8 pr-3 py-1 text-xs text-primary focus:outline-none focus:ring-1 focus:ring-accent"
                      />
                    </div>
                  )}

                  <button
                    type="button"
                    onClick={() => setIsFullscreen(!isFullscreen)}
                    className="p-1.5 rounded-xl text-secondary hover:text-primary hover:bg-muted/60 transition-colors hidden sm:inline-flex"
                    title={isFullscreen ? 'Exit Fullscreen' : 'Expand Canvas'}
                  >
                    {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* Canvas Body Container */}
              <div className="flex-1 overflow-y-auto p-6 scrollbar-thin">
                {/* ── TAB 1: PRODUCTS / RESULTS ── */}
                {activeTab === 'products' && (
                  <>
                    {canvasProducts.length === 0 ? (
                      /* ── Clean Ambient Initial Empty State ── */
                      <div className="h-full flex flex-col items-center justify-center text-center p-6 max-w-2xl mx-auto my-auto animate-in fade-in zoom-in-95 duration-500">
                        <div className="relative mb-6">
                          <div className="h-24 w-24 rounded-3xl bg-gradient-to-tr from-indigo-500/20 via-purple-500/20 to-pink-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-500 shadow-2xl shadow-indigo-500/20 animate-pulse">
                            <Bot className="h-12 w-12 text-indigo-600 dark:text-indigo-400" />
                          </div>
                          <div className="absolute -bottom-2 -right-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow">
                            Autonomous AI
                          </div>
                        </div>

                        <h3 className="text-2xl font-extrabold text-primary mb-2">
                          Ready to Explore RazorHub Catalog
                        </h3>
                        <p className="text-sm text-secondary mb-8 max-w-md">
                          Ask the AI agent in the chat on the right. Live products, spec comparisons, stock statuses, and cart items will populate here instantly.
                        </p>

                        {/* Interactive Suggestion Cards */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full text-left">
                          <button
                            type="button"
                            onClick={() => handleSendMessage('Find top gaming laptops with high performance')}
                            className="group p-4 rounded-2xl border border-border/80 bg-surface/50 hover:bg-surface hover:border-indigo-500/50 transition-all shadow-xs hover:shadow-md cursor-pointer"
                          >
                            <div className="flex items-center gap-3 mb-2">
                              <div className="p-2 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform">
                                <Cpu className="h-4 w-4" />
                              </div>
                              <span className="text-xs font-bold text-primary">Laptops & Tech</span>
                            </div>
                            <p className="text-xs text-secondary">"Find top gaming laptops with high performance"</p>
                          </button>

                          <button
                            type="button"
                            onClick={() => handleSendMessage('Compare Samsung Galaxy S25 Ultra vs iPhone 16')}
                            className="group p-4 rounded-2xl border border-border/80 bg-surface/50 hover:bg-surface hover:border-purple-500/50 transition-all shadow-xs hover:shadow-md cursor-pointer"
                          >
                            <div className="flex items-center gap-3 mb-2">
                              <div className="p-2 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 group-hover:scale-110 transition-transform">
                                <Scale className="h-4 w-4" />
                              </div>
                              <span className="text-xs font-bold text-primary">Device Comparison</span>
                            </div>
                            <p className="text-xs text-secondary">"Compare Samsung S25 Ultra vs iPhone 16"</p>
                          </button>

                          <button
                            type="button"
                            onClick={() => handleSendMessage('Show trending sneakers and sports footwear')}
                            className="group p-4 rounded-2xl border border-border/80 bg-surface/50 hover:bg-surface hover:border-emerald-500/50 transition-all shadow-xs hover:shadow-md cursor-pointer"
                          >
                            <div className="flex items-center gap-3 mb-2">
                              <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 group-hover:scale-110 transition-transform">
                                <Footprints className="h-4 w-4" />
                              </div>
                              <span className="text-xs font-bold text-primary">Sneakers & Shoes</span>
                            </div>
                            <p className="text-xs text-secondary">"Show trending sneakers and sports footwear"</p>
                          </button>

                          <button
                            type="button"
                            onClick={() => handleSendMessage('Find best deals on clothing and apparel')}
                            className="group p-4 rounded-2xl border border-border/80 bg-surface/50 hover:bg-surface hover:border-pink-500/50 transition-all shadow-xs hover:shadow-md cursor-pointer"
                          >
                            <div className="flex items-center gap-3 mb-2">
                              <div className="p-2 rounded-xl bg-pink-500/10 text-pink-600 dark:text-pink-400 group-hover:scale-110 transition-transform">
                                <Shirt className="h-4 w-4" />
                              </div>
                              <span className="text-xs font-bold text-primary">Fashion & Deals</span>
                            </div>
                            <p className="text-xs text-secondary">"Find best deals on clothing and apparel"</p>
                          </button>
                        </div>
                      </div>
                    ) : (
                      /* ── Populated Product Cards Grid ── */
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-bold text-secondary uppercase tracking-wider">
                            Showing {displayedCanvasProducts.length} Recommended Products
                          </p>
                          <button
                            type="button"
                            onClick={() => setCanvasProducts([])}
                            className="text-xs text-secondary hover:text-rose-500 transition-colors cursor-pointer"
                          >
                            Clear Results
                          </button>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                          {displayedCanvasProducts.map(prod => {
                            const isAdded = addedAnimationSlug === prod.slug;
                            const inCompare = compareList.some(c => c.id === prod.id);
                            const productPrice = price(prod);

                            return (
                              <div
                                key={prod.id}
                                className="group relative rounded-2xl border border-border/80 bg-surface p-3.5 shadow-xs hover:shadow-xl hover:border-indigo-500/40 transition-all duration-300 flex flex-col justify-between"
                              >
                                <div>
                                  {/* Product Image & Badges */}
                                  <div className="relative aspect-square w-full rounded-xl overflow-hidden bg-muted/30 mb-3">
                                    <img
                                      src={productImage(prod)}
                                      alt={prod.name}
                                      className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-500"
                                      loading="lazy"
                                    />
                                    <span className="absolute top-2 left-2 inline-flex items-center gap-1 bg-emerald-500/90 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-xs backdrop-blur-xs">
                                      <Check className="h-3 w-3" /> In Stock
                                    </span>
                                    {prod.category && (
                                      <span className="absolute top-2 right-2 bg-black/60 text-white text-[10px] font-semibold px-2 py-0.5 rounded-full backdrop-blur-xs">
                                        {prod.category.name}
                                      </span>
                                    )}
                                  </div>

                                  {/* Title & Price */}
                                  <Link
                                    to={`/product/${prod.slug}`}
                                    className="block font-bold text-sm text-primary group-hover:text-accent transition-colors line-clamp-2 mb-1.5"
                                  >
                                    {prod.name}
                                  </Link>

                                  <div className="flex items-baseline gap-2 mb-3">
                                    <span className="text-base font-black text-accent">
                                      {formatPrice(productPrice)}
                                    </span>
                                    {prod.discount_price && Number(prod.discount_price) < Number(prod.price) && (
                                      <span className="text-xs text-secondary line-through">
                                        {formatPrice(Number(prod.price))}
                                      </span>
                                    )}
                                    <span className="ml-auto text-xs font-bold text-amber-500 flex items-center gap-0.5">
                                      ★ {prod.rating || prod.average_rating || 4.7}
                                    </span>
                                  </div>
                                </div>

                                {/* Actions Row */}
                                <div className="flex items-center gap-2 pt-2 border-t border-border/60">
                                  <button
                                    type="button"
                                    onClick={() => handleAddToCartWithAnimation(prod)}
                                    className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl text-xs font-bold transition-all shadow-xs cursor-pointer ${
                                      isAdded
                                        ? 'bg-emerald-600 text-white'
                                        : 'bg-accent hover:opacity-90 text-white'
                                    }`}
                                  >
                                    {isAdded ? (
                                      <>
                                        <Check className="h-3.5 w-3.5" /> Added!
                                      </>
                                    ) : (
                                      <>
                                        <ShoppingCart className="h-3.5 w-3.5" /> Add to Cart
                                      </>
                                    )}
                                  </button>

                                  <button
                                    type="button"
                                    onClick={() => toggleCompare(prod)}
                                    className={`p-2 rounded-xl border text-xs font-bold transition-colors cursor-pointer ${
                                      inCompare
                                        ? 'bg-indigo-500/10 border-indigo-500 text-indigo-600 dark:text-indigo-400'
                                        : 'border-border/80 text-secondary hover:text-primary hover:bg-muted/60'
                                    }`}
                                    title="Compare specs"
                                  >
                                    <Scale className="h-4 w-4" />
                                  </button>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </>
                )}

                {/* ── TAB 2: SPEC COMPARISON ── */}
                {activeTab === 'compare' && (
                  <div className="space-y-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-bold text-primary flex items-center gap-2">
                          <Scale className="h-5 w-5 text-indigo-500" />
                          Side-by-Side Product Comparison
                        </h3>
                        <p className="text-xs text-secondary">
                          Compare specifications, prices, ratings, and features across chosen items.
                        </p>
                      </div>
                      {compareList.length > 0 && (
                        <button
                          type="button"
                          onClick={() => setCompareList([])}
                          className="text-xs text-secondary hover:text-rose-500 transition-colors"
                        >
                          Clear Comparison
                        </button>
                      )}
                    </div>

                    {compareList.length === 0 ? (
                      <div className="text-center py-16 text-secondary">
                        <Scale className="h-12 w-12 mx-auto mb-3 opacity-30" />
                        <p className="font-semibold mb-1">No products selected for comparison.</p>
                        <p className="text-xs">Click the comparison icon on any product in the results tab to add it here.</p>
                      </div>
                    ) : (
                      <div className="overflow-x-auto pb-4">
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 min-w-[600px]">
                          {compareList.map(prod => (
                            <div
                              key={prod.id}
                              className="rounded-2xl border border-border bg-surface p-4 flex flex-col justify-between shadow-sm"
                            >
                              <div>
                                <div className="relative aspect-video rounded-xl overflow-hidden bg-muted/40 mb-3">
                                  <img src={productImage(prod)} alt={prod.name} className="h-full w-full object-cover" />
                                </div>
                                <h4 className="font-bold text-sm text-primary mb-2 line-clamp-2">{prod.name}</h4>
                                <div className="space-y-2 text-xs divide-y divide-border/60">
                                  <div className="flex justify-between py-1.5">
                                    <span className="text-secondary">Price:</span>
                                    <span className="font-bold text-accent">{formatPrice(price(prod))}</span>
                                  </div>
                                  <div className="flex justify-between py-1.5">
                                    <span className="text-secondary">Category:</span>
                                    <span className="font-semibold text-primary">{prod.category?.name || 'General'}</span>
                                  </div>
                                  <div className="flex justify-between py-1.5">
                                    <span className="text-secondary">Rating:</span>
                                    <span className="font-bold text-amber-500">★ {prod.rating || 4.8}</span>
                                  </div>
                                  <div className="flex justify-between py-1.5">
                                    <span className="text-secondary">Stock:</span>
                                    <span className="font-semibold text-emerald-600">In Stock ({prod.stock || 25})</span>
                                  </div>
                                  <div className="flex justify-between py-1.5">
                                    <span className="text-secondary">Delivery:</span>
                                    <span className="font-semibold text-primary">3-5 Business Days</span>
                                  </div>
                                </div>
                              </div>

                              <button
                                type="button"
                                onClick={() => handleAddToCartWithAnimation(prod)}
                                className="mt-4 w-full py-2 bg-accent hover:opacity-90 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 shadow-sm"
                              >
                                <ShoppingCart className="h-3.5 w-3.5" />
                                Add to Cart
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* ── TAB 3: LIVE CART & INSTANT CHECKOUT ── */}
                {activeTab === 'cart' && (
                  <div className="space-y-6 max-w-2xl mx-auto">
                    <div className="flex items-center justify-between border-b border-border/60 pb-3">
                      <div>
                        <h3 className="text-lg font-bold text-primary flex items-center gap-2">
                          <ShoppingCart className="h-5 w-5 text-indigo-500" />
                          Live Cart & Instant Checkout
                        </h3>
                        <p className="text-xs text-secondary">
                          {totalCount} item{totalCount !== 1 ? 's' : ''} in your session
                        </p>
                      </div>
                      <Link
                        to="/cart"
                        onClick={() => setOpen(false)}
                        className="text-xs font-bold text-accent hover:underline flex items-center gap-1"
                      >
                        Full Cart View <ExternalLink className="h-3.5 w-3.5" />
                      </Link>
                    </div>

                    {items.length === 0 ? (
                      <div className="text-center py-16 text-secondary">
                        <ShoppingBag className="h-12 w-12 mx-auto mb-3 opacity-30" />
                        <p className="font-semibold mb-1">Your cart is currently empty.</p>
                        <p className="text-xs">Ask the AI agent to find and add items to your cart.</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="divide-y divide-border/60 rounded-2xl border border-border bg-surface p-4 space-y-3">
                          {items.map(item => (
                            <div key={item.product.id} className="flex items-center gap-3 pt-3 first:pt-0">
                              <img
                                src={productImage(item.product)}
                                alt={item.product.name}
                                className="h-14 w-14 rounded-xl object-cover bg-muted/30 shrink-0"
                              />
                              <div className="flex-1 min-w-0">
                                <h4 className="font-bold text-xs text-primary truncate">{item.product.name}</h4>
                                <p className="text-xs font-extrabold text-accent">{formatPrice(price(item.product))}</p>
                              </div>
                              <div className="flex items-center gap-2">
                                <button
                                  type="button"
                                  onClick={() => updateQuantity(item.product.id, item.quantity - 1)}
                                  className="p-1 rounded-lg border border-border text-secondary hover:text-primary"
                                >
                                  <Minus className="h-3 w-3" />
                                </button>
                                <span className="text-xs font-bold w-4 text-center">{item.quantity}</span>
                                <button
                                  type="button"
                                  onClick={() => updateQuantity(item.product.id, item.quantity + 1)}
                                  className="p-1 rounded-lg border border-border text-secondary hover:text-primary"
                                >
                                  <Plus className="h-3 w-3" />
                                </button>
                                <button
                                  type="button"
                                  onClick={() => removeFromCart(item.product.id)}
                                  className="p-1.5 text-secondary hover:text-rose-500 transition-colors ml-1"
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>

                        {/* Order Summary Box */}
                        <div className="rounded-2xl border border-border/80 bg-surface/70 p-4 space-y-2 text-xs">
                          <div className="flex justify-between text-secondary">
                            <span>Subtotal:</span>
                            <span className="font-semibold text-primary">{formatPrice(totalPrice)}</span>
                          </div>
                          <div className="flex justify-between text-secondary">
                            <span>Delivery:</span>
                            <span className="font-semibold text-emerald-600">FREE</span>
                          </div>
                          <div className="flex justify-between text-sm font-bold pt-2 border-t border-border">
                            <span>Estimated Total:</span>
                            <span className="text-accent text-base">{formatPrice(totalPrice)}</span>
                          </div>
                        </div>

                        {/* Checkout CTA */}
                        <button
                          type="button"
                          onClick={() => {
                            setOpen(false);
                            navigate('/checkout');
                          }}
                          className="w-full py-3.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-bold rounded-2xl shadow-lg shadow-emerald-600/25 flex items-center justify-center gap-2 cursor-pointer transition-all active:scale-98"
                        >
                          <CreditCard className="h-4 w-4" />
                          Proceed to Autonomous Checkout
                          <ArrowRight className="h-4 w-4" />
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* ── TAB 4: FLASH DEALS ── */}
                {activeTab === 'deals' && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-bold text-primary flex items-center gap-2">
                        <Flame className="h-5 w-5 text-amber-500" />
                        Today's Active Flash Deals
                      </h3>
                      <span className="text-xs text-emerald-600 font-semibold">Verified NeonDB Pricing</span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                      {flashDeals.map(prod => (
                        <div
                          key={prod.id}
                          className="group relative rounded-2xl border border-border bg-surface p-3 shadow-sm hover:shadow-lg transition-all"
                        >
                          <div className="relative aspect-square rounded-xl overflow-hidden bg-muted/40 mb-2.5">
                            <img src={productImage(prod)} alt={prod.name} className="h-full w-full object-cover group-hover:scale-105 transition-transform" />
                            <span className="absolute top-2 left-2 bg-rose-600 text-white text-[10px] font-black px-2 py-0.5 rounded-full shadow-xs">
                              FLASH DEAL
                            </span>
                          </div>
                          <h4 className="font-bold text-xs text-primary truncate mb-1">{prod.name}</h4>
                          <div className="flex items-baseline justify-between mb-3">
                            <span className="text-sm font-black text-accent">{formatPrice(price(prod))}</span>
                            <span className="text-xs text-secondary line-through">{formatPrice(Number(prod.price))}</span>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleAddToCartWithAnimation(prod)}
                            className="w-full py-1.5 bg-accent hover:opacity-90 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1"
                          >
                            <ShoppingCart className="h-3 w-3" /> Grab Deal
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* ════════════════════════════════════════════════════════════
                WINDOW 2 (RIGHT): RAZORHUB AI CONVERSATIONAL AGENT
            ════════════════════════════════════════════════════════════ */}
            <div className="pointer-events-auto w-full lg:w-[400px] xl:w-[440px] shrink-0 h-full min-h-0 rounded-3xl bg-surface/95 dark:bg-zinc-900/95 backdrop-blur-2xl border border-border/80 shadow-[0_25px_70px_-15px_rgba(0,0,0,0.35)] flex flex-col overflow-hidden transition-all duration-300 animate-in fade-in slide-in-from-right-4">
              {/* Chat Header */}
              <div className="px-5 py-4 border-b border-border/60 bg-surface/50 dark:bg-zinc-900/50 flex items-center justify-between gap-3 shrink-0">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <div className="h-9 w-9 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/25">
                      <Sparkles className="h-4.5 w-4.5" />
                    </div>
                    <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-emerald-500 ring-2 ring-surface" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-primary flex items-center gap-1.5">
                      RazorHub AI
                    </h3>
                    <p className="text-[11px] text-secondary">
                      Multi-Agent Commerce Engine
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={resetChat}
                    className="p-1.5 text-xs text-secondary hover:text-primary hover:bg-muted/60 rounded-xl transition-colors"
                    title="New conversation"
                  >
                    <RefreshCw className="h-3.5 w-3.5" />
                  </button>

                  <button
                    type="button"
                    onClick={() => setOpen(false)}
                    className="p-1.5 text-secondary hover:text-primary hover:bg-muted/60 rounded-xl transition-colors cursor-pointer"
                    title="Close studio"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Chat Messages Stream */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
                {messages.map(msg => (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} space-y-1.5`}
                  >
                    {/* Agent Identification Badge */}
                    {msg.role === 'assistant' && (
                      <span className="text-[10px] font-bold text-indigo-500 dark:text-indigo-400 flex items-center gap-1 pl-1">
                        <Bot className="h-3 w-3" />
                        {msg.agent || 'RazorHub Agent'}
                      </span>
                    )}

                    {/* Message Bubble */}
                    <div
                      className={`max-w-[88%] rounded-2xl px-4 py-2.5 text-xs leading-relaxed ${
                        msg.role === 'user'
                          ? 'bg-gradient-to-tr from-indigo-600 to-purple-600 text-white rounded-br-xs shadow-sm font-medium'
                          : 'bg-muted/60 dark:bg-zinc-800/80 text-primary rounded-bl-xs border border-border/50'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.text}</p>
                    </div>

                    {/* Follow-up Suggestion Chips */}
                    {msg.role === 'assistant' && msg.suggestedFollowups && msg.suggestedFollowups.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1 pl-1 max-w-[95%]">
                        {msg.suggestedFollowups.map((chip, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => handleSendMessage(chip)}
                            className="inline-flex items-center gap-1 text-[11px] font-semibold text-secondary hover:text-primary bg-surface dark:bg-zinc-800/60 border border-border/70 hover:border-indigo-500/40 px-2.5 py-1 rounded-full shadow-2xs hover:shadow-xs transition-all active:scale-95 cursor-pointer text-left"
                          >
                            <span>{chip}</span>
                            <ChevronRight className="h-2.5 w-2.5 opacity-60" />
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}

                {/* Loading / Thinking indicator */}
                {loading && (
                  <div className="flex flex-col items-start space-y-1.5">
                    <span className="text-[10px] font-bold text-indigo-500 flex items-center gap-1 pl-1">
                      <Bot className="h-3 w-3 animate-spin" />
                      Orchestrating...
                    </span>
                    <div className="bg-muted/60 rounded-2xl rounded-bl-xs px-4 py-3 flex gap-1.5 items-center border border-border/40">
                      <span className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" />
                      <span className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce [animation-delay:0.2s]" />
                      <span className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce [animation-delay:0.4s]" />
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input Container */}
              <div className="p-3.5 border-t border-border/60 bg-surface/50 dark:bg-zinc-900/50 shrink-0">
                <form onSubmit={handleFormSubmit} className="relative flex items-center">
                  <input
                    type="text"
                    value={message}
                    onChange={e => setMessage(e.target.value)}
                    placeholder="Ask RazorHub AI..."
                    disabled={loading}
                    className="w-full bg-background border border-border/80 rounded-full py-2.5 pl-4 pr-11 text-xs text-primary placeholder:text-secondary/70 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-all"
                  />
                  <button
                    type="submit"
                    disabled={!message.trim() || loading}
                    className="absolute right-1.5 p-2 bg-gradient-to-tr from-indigo-600 to-purple-600 text-white rounded-full disabled:opacity-40 hover:opacity-95 active:scale-95 transition-all shadow-sm cursor-pointer"
                    aria-label="Send query"
                  >
                    <Send className="h-3.5 w-3.5" />
                  </button>
                </form>
              </div>
            </div>

          </div>
        </div>
      )}
    </>
  );
}
