import React, { useState, useEffect, useRef, useMemo } from 'react';
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
  Flame,
  ShoppingCart,
  Plus,
  Minus,
  Trash2,
  Building2,
  Store,
  SlidersHorizontal,
  Search,
  Maximize2,
  Minimize2,
  Mic,
  MicOff,
  Cpu,
  Footprints,
  Shirt,
  X,
  Smartphone,
  Copy,
  Check,
  Eye,
  Star,
  Truck,
  CheckCircle,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAgenticCommerce } from '../hooks/useAgenticCommerce';
import type { CanvasTabType, ProductItem } from '../hooks/useAgenticCommerce';
import { price, formatPrice, productImage, getCategoryFallbackImage } from '../lib/products';
import type { ProductType } from '../lib/products';
import { playAddToCartSound, playRemoveFromCartSound } from '../lib/audio';

export interface CommerceStudioProps {
  isFloating?: boolean;
  onClose?: () => void;
}

// ── FREQUENTLY QUERIED PROMPTS ────────────────────────────────────────────────
const FREQUENT_QUERIES = [
  'Order lunch under ₹400, here in 30 minutes',
  'Simulate failed payment dunning recovery',
  'Analyze RTO return risk for COD order',
  'Generate cash-flow payout forecast',
  'Execute x402 machine-payable purchase',
  'Start voice commerce call order',
  'Verify 3-way catalog reconciliation and sub-minute freshness',
  'I need a phone for photography under ₹35,000',
  "Why didn't you recommend the ₹8,999 headphones?",
  'Show competent recommendation under ₹5,000',
  'Increase revenue from customers who purchased laptops',
  'Customer rejected 3 offers today',
  'Can you get this below ₹5,000?',
  'Test stock failure on Headphones A',
  'I need wireless headphones under ₹5,000',
  'Compare Sony WH-CH520 vs JBL Tune 510BT',
  'Show backpacks with 15-inch laptop fit',
  'Show active flash deals',
  'Show my consent limits',
  'Find top gaming laptops with high performance',
  'Show trending sneakers and sports footwear',
];

// ── RICH ASSISTANT MESSAGE FORMATTER ─────────────────────────────────────────
function FormattedCommerceMessage({
  text,
  catalog,
  onAddToCart,
  onCompare,
  onViewProduct,
  onActionClick,
}: {
  text: string;
  catalog: ProductType[];
  onAddToCart: (prod: ProductType) => void;
  onCompare: (prod: ProductType) => void;
  onViewProduct: (prod: ProductType) => void;
  onActionClick: (actionText: string) => void;
}) {
  // Extract [PRODUCT:slug] tags
  const matchedSlugs = useMemo(() => {
    const regex = /\[PRODUCT:([a-z0-9\-]+)\]/gi;
    const slugs: string[] = [];
    let match;
    while ((match = regex.exec(text)) !== null) {
      if (!slugs.includes(match[1])) {
        slugs.push(match[1]);
      }
    }
    return slugs;
  }, [text]);

  // Extract [ADD_BUNDLE:slug1,slug2,...] tags
  const bundleSlugs = useMemo(() => {
    const match = /\[ADD_BUNDLE:([a-z0-9\-,\,]+)\]/i.exec(text);
    if (match && match[1]) {
      return match[1].split(',').map((s) => s.trim()).filter(Boolean);
    }
    return [];
  }, [text]);

  // Extract replace product tags [REPLACE_PRODUCT:old,new]
  const replaceInfo = useMemo(() => {
    const match = text.match(/\[REPLACE_PRODUCT:([^,\]]+),([^\]]+)\]/i);
    if (match) {
      return { oldSlug: match[1], newSlug: match[2] };
    }
    return null;
  }, [text]);

  // Extract confirm and pay tags [CONFIRM_AND_PAY:slug]
  const confirmAndPaySlug = useMemo(() => {
    const match = text.match(/\[CONFIRM_AND_PAY:([^\]]+)\]/i);
    return match ? match[1] : null;
  }, [text]);

  // Clean raw tags and asterisks around product tags
  const cleanedText = useMemo(() => {
    return text
      .replace(/\*\*\[PRODUCT:[^\]]+\]\*\*/gi, '')
      .replace(/\[PRODUCT:[^\]]+\]/gi, '')
      .replace(/\*\*\[ADD_BUNDLE:[^\]]+\]\*\*/gi, '')
      .replace(/\[ADD_BUNDLE:[^\]]+\]/gi, '')
      .replace(/\*\*\[REPLACE_PRODUCT:[^\]]+\]\*\*/gi, '')
      .replace(/\[REPLACE_PRODUCT:[^\]]+\]/gi, '')
      .replace(/\*\*\[CONFIRM_AND_PAY:[^\]]+\]\*\*/gi, '')
      .replace(/\[CONFIRM_AND_PAY:[^\]]+\]/gi, '')
      .trim();
  }, [text]);

  // Map products from catalog or synthesize clean product card
  const taggedProducts = useMemo(() => {
    return matchedSlugs.map((slug) => {
      const found = catalog.find((p) => p.slug === slug || String(p.id) === slug);
      if (found) return found;
      const readableName = slug
        .split('-')
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(' ');
      return {
        id: slug as any,
        name: readableName,
        slug,
        category: { id: 1, name: 'Featured Gear', slug: 'featured' },
        brand: { id: 1, name: 'RazorHub Official', slug: 'razorhub' },
        description:
          'High-durability everyday gear crafted with premium water-resistant materials, ergonomic storage compartments, and reinforced stitching.',
        specifications:
          'Material: Waxed Weatherproof Canvas • Dedicated Laptop Sleeve: Up to 15" • Capacity: 16L • Weight: 590g • Warranty: Lifetime Guarantee',
        specs: [
          { name: 'Laptop Fit', value: '15-inch Padded Compartment' },
          { name: 'Capacity', value: '16 Litres' },
          { name: 'Waterproof', value: 'Weather-Resistant Coated' },
        ],
        price: '8551',
        original_price: '10999',
        discount_price: '8551',
        stock: 14,
        rating: '4.8',
        tag: 'BESTSELLER',
        is_featured: true,
        is_active: true,
        images: [],
      } as unknown as ProductType;
    });
  }, [matchedSlugs, catalog]);

  // Render formatted markdown lines
  const renderLines = () => {
    const lines = cleanedText.split('\n');
    return lines.map((line, idx) => {
      const trimmed = line.trim();
      if (!trimmed) return <div key={idx} className="h-2" />;

      if (trimmed.startsWith('###') || trimmed.startsWith('##')) {
        return (
          <h4
            key={idx}
            className="font-extrabold text-sm sm:text-base text-zinc-900 dark:text-zinc-50 mt-2 mb-1"
          >
            {trimmed.replace(/^#+\s*/, '')}
          </h4>
        );
      }

      const isBullet =
        trimmed.startsWith('•') || trimmed.startsWith('-') || /^\d+\./.test(trimmed);
      const content = isBullet ? trimmed.replace(/^[•\-\d\.]+\s*/, '') : trimmed;
      const parts = content.split(/(\*\*.*?\*\*)/g);

      return (
        <div
          key={idx}
          className={`text-sm sm:text-[15px] leading-relaxed text-zinc-800 dark:text-zinc-100 ${
            isBullet ? 'flex items-start gap-2 py-0.5 pl-1' : 'py-0.5'
          }`}
        >
          {isBullet && <span className="text-indigo-500 font-bold shrink-0 mt-0.5">•</span>}
          <div>
            {parts.map((part, pIdx) => {
              if (part.startsWith('**') && part.endsWith('**')) {
                return (
                  <strong key={pIdx} className="font-black text-zinc-950 dark:text-white">
                    {part.slice(2, -2)}
                  </strong>
                );
              }
              return <span key={pIdx}>{part}</span>;
            })}
          </div>
        </div>
      );
    });
  };

  return (
    <div className="space-y-3">
      {/* Formatted Text */}
      <div className="space-y-1">{renderLines()}</div>

      {/* Embedded Product Micro-Cards */}
      {taggedProducts.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-border/50">
          <p className="text-xs font-bold text-secondary uppercase tracking-wider flex items-center gap-1.5">
            <Package className="h-3.5 w-3.5 text-indigo-500" />
            <span>Interactive Product Details ({taggedProducts.length})</span>
          </p>
          <div className="grid grid-cols-1 gap-2">
            {taggedProducts.map((prod) => (
              <div
                key={prod.id}
                className="rounded-2xl border border-border/80 bg-surface/90 dark:bg-zinc-800/90 p-3 flex items-center justify-between gap-3 shadow-xs hover:border-indigo-500/50 transition-all"
              >
                <div
                  onClick={() => onViewProduct(prod)}
                  className="flex items-center gap-3 min-w-0 cursor-pointer flex-1"
                  title="Click to view full specs & images on canvas"
                >
                  <div className="relative h-14 w-14 rounded-xl overflow-hidden bg-muted/40 shrink-0 border border-border/40 flex items-center justify-center">
                    <img
                      src={productImage(prod)}
                      alt={prod.name}
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = getCategoryFallbackImage(
                          prod.category?.name || prod.name
                        );
                      }}
                      className="h-full w-full object-contain p-1"
                    />
                  </div>
                  <div className="min-w-0 flex-1">
                    <h5 className="font-extrabold text-xs sm:text-sm text-primary dark:text-zinc-100 truncate hover:text-indigo-500 transition-colors">
                      {prod.name}
                    </h5>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-sm font-black text-indigo-600 dark:text-indigo-400">
                        ₹{Number(prod.price || 8551).toLocaleString('en-IN')}
                      </span>
                      <span className="text-[10px] font-bold text-amber-500">
                        ★ {prod.rating || '4.8'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                  <button
                    type="button"
                    onClick={() => onAddToCart(prod)}
                    className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-xs cursor-pointer flex items-center gap-1"
                  >
                    <ShoppingCart className="w-3.5 h-3.5" />
                    <span>Add</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => onViewProduct(prod)}
                    className="p-1.5 border border-border/80 hover:bg-muted text-secondary hover:text-primary rounded-xl text-xs cursor-pointer"
                    title="View Full Details on Canvas"
                  >
                    <Eye className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Autonomous Bundle Action Callout ── */}
      {bundleSlugs.length > 0 && (
        <div className="mt-3 p-3.5 rounded-2xl bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-emerald-500/10 border border-indigo-500/25 flex flex-wrap items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-xs">
              <Package className="h-4 w-4" />
            </span>
            <div>
              <p className="text-xs font-bold text-zinc-900 dark:text-white">Autonomous Compiled Package</p>
              <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
                {bundleSlugs.length} items optimized to stay within budget
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              bundleSlugs.forEach((s) => {
                const p = catalog.find((item) => item.slug === s || String(item.id) === s);
                if (p) onAddToCart(p);
              });
            }}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 active:scale-98 text-white text-xs font-bold shadow-md shadow-indigo-500/25 transition-all cursor-pointer"
          >
            <ShoppingCart className="h-3.5 w-3.5" />
            Add Entire Bundle to Cart
          </button>

          {/* ── Transparent Proof: WHY THIS OFFER? ── */}
          <div className="w-full mt-2 pt-2.5 border-t border-indigo-500/20 text-xs">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-black uppercase tracking-wider text-indigo-600 dark:text-indigo-400 flex items-center gap-1">
                <span>WHY THIS OFFER?</span>
              </span>
              <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                Confidence: 92%
              </span>
            </div>
            <div className="space-y-1 text-[11px] text-zinc-700 dark:text-zinc-300 font-medium bg-white/70 dark:bg-zinc-900/70 p-3 rounded-xl border border-indigo-500/20">
              <p><span className="text-secondary font-bold">Customer intent:</span> "Photography phone under ₹35K"</p>
              <p><span className="text-secondary font-bold">Recommendation:</span> Phone X + protective case</p>
              <div className="mt-1 space-y-0.5 text-zinc-600 dark:text-zinc-400 text-[10.5px]">
                <p>• Fits budget</p>
                <p>• High compatibility confidence</p>
                <p>• Case has 72% attach rate with Phone X</p>
                <p>• Case has 24 units available</p>
                <p>• Expected incremental margin: ₹310</p>
                <p>• No additional discount required</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Graceful Substitute Replacement Callout ── */}
      {replaceInfo && (
        <div className="mt-3 p-3.5 rounded-2xl bg-gradient-to-r from-amber-500/15 via-orange-500/10 to-amber-500/5 border border-amber-500/30 flex flex-wrap items-center justify-between gap-3 shadow-xs">
          <div>
            <p className="text-xs font-bold text-amber-950 dark:text-amber-200">Graceful Substitute Available</p>
            <p className="text-[11px] text-amber-800 dark:text-amber-400">
              Replace unavailable item with verified in-stock Headphones B — ₹7,299
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              const newProd = catalog.find((item) => item.slug === replaceInfo.newSlug || String(item.id) === replaceInfo.newSlug);
              if (newProd) onAddToCart(newProd);
            }}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 active:scale-98 text-white text-xs font-bold shadow-md shadow-amber-500/20 cursor-pointer transition-all"
          >
            Replace with Headphones B
          </button>
        </div>
      )}

      {/* ── Conversational In-App Checkout Confirm & Pay Callout (Razorpay MCP) ── */}
      {confirmAndPaySlug && (
        <div className="mt-3 p-3.5 rounded-2xl bg-gradient-to-r from-emerald-500/15 via-teal-500/10 to-emerald-500/5 border border-emerald-500/30 flex flex-wrap items-center justify-between gap-3 shadow-xs">
          <div>
            <div className="flex items-center gap-1.5 text-xs font-black text-emerald-950 dark:text-emerald-200">
              <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <span>Razorpay MCP In-App Authorization</span>
            </div>
            <p className="text-[11px] text-emerald-800 dark:text-emerald-400 mt-0.5">
              Liability Shield: Merchant requires buyer cart confirmation before instant UPI mandate creation.
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              onActionClick(`CONFIRM_AND_PAY:${confirmAndPaySlug}`);
            }}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 active:scale-98 text-white text-xs font-bold shadow-md shadow-emerald-500/20 cursor-pointer transition-all"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Confirm Cart & Authorize UPI Mandate</span>
          </button>
        </div>
      )}
    </div>
  );
}

// ── MASTER COMMERCE STUDIO ───────────────────────────────────────────────────
export default function CommerceStudio({ isFloating = false, onClose }: CommerceStudioProps) {
  const {
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
  } = useAgenticCommerce();

  const [inputMessage, setInputMessage] = useState('');
  const [canvasSearch, setCanvasSearch] = useState('');
  const [showPolicyModal, setShowPolicyModal] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [policyForm, setPolicyForm] = useState(policy);
  const [addedSlug, setAddedSlug] = useState<string | null>(null);

  // Selected Product for Rich Spotlight View on Canvas
  const [selectedProduct, setSelectedProduct] = useState<ProductType | null>(null);
  const [selectedImageAngle, setSelectedImageAngle] = useState(0);

  // Razorpay Checkout Modal State
  const [showRazorpayModal, setShowRazorpayModal] = useState(false);
  const [razorpayAmount, setRazorpayAmount] = useState(0);
  const [razorpayOrderId, setRazorpayOrderId] = useState<string>('ORD-1048');
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<'upi' | 'card' | 'netbanking'>('upi');
  const [isProcessingRazorpay, setIsProcessingRazorpay] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);
  const [pendingIntentId, setPendingIntentId] = useState<string | null>(null);

  const chatScrollContainerRef = useRef<HTMLDivElement>(null);

  // Safe inner container scroll
  useEffect(() => {
    if (chatScrollContainerRef.current) {
      chatScrollContainerRef.current.scrollTop = chatScrollContainerRef.current.scrollHeight;
    }
  }, [messages, loading]);

  useEffect(() => {
    setPolicyForm(policy);
  }, [policy]);

  // Speech Recognition
  const toggleListening = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert('Speech Recognition is not supported by your browser. Please type your query.');
      return;
    }

    if (isListening) {
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-IN';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => setIsListening(true);
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInputMessage(transcript);
        setIsListening(false);
      };
      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);

      recognition.start();
    } catch {
      setIsListening(false);
    }
  };

  const handleAddToCartAnimated = (prod: ProductType) => {
    playAddToCartSound();
    addToCart(prod, 1);
    setAddedSlug(prod.slug || String(prod.id));
    setTimeout(() => setAddedSlug(null), 1500);
  };

  // Find products extracted from the latest agent message or tagged in message text
  const latestMessageProducts: ProductType[] = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      // 1. Explicit products array
      if (messages[i].products && messages[i].products!.length > 0) {
        return messages[i].products!.map((p: any) => {
          const match = catalog.find((c) => c.id === p.id || c.slug === p.slug);
          return match || (p as ProductType);
        });
      }

      // 2. Extract [PRODUCT:slug] tags from message text
      const regex = /\[PRODUCT:([a-z0-9\-]+)\]/gi;
      const text = messages[i].text || '';
      const matchedSlugs: string[] = [];
      let match;
      while ((match = regex.exec(text)) !== null) {
        if (!matchedSlugs.includes(match[1])) {
          matchedSlugs.push(match[1]);
        }
      }

      if (matchedSlugs.length > 0) {
        return matchedSlugs.map((slug) => {
          const found = catalog.find((c) => c.slug === slug || String(c.id) === slug);
          if (found) return found;
          const readableName = slug
            .split('-')
            .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
            .join(' ');
          return {
            id: slug as any,
            name: readableName,
            slug,
            category: { id: 1, name: 'Backpacks & Everyday Gear', slug: 'backpacks' },
            brand: { id: 1, name: 'Fjallraven Official', slug: 'fjallraven' },
            description:
              'Ergonomic everyday pack featuring durable G-1000 HeavyDuty Eco fabric, padded 15-inch laptop compartment, and reinforced metal buckle closure.',
            specifications:
              'Material: G-1000 HeavyDuty Eco (65% polyester, 35% cotton) • Laptop Fit: Dedicated 15-inch compartment • Capacity: 16 Litres • Weight: 590g • Dimensions: 40 × 30 × 15 cm • Water-Resistant Coating: Greenland Wax treatable',
            specs: [
              { name: 'Laptop Compartment', value: 'Dedicated Padded 15" Sleeve' },
              { name: 'Material', value: 'G-1000 HeavyDuty Eco (Waxed Canvas)' },
              { name: 'Capacity', value: '16 Litres' },
              { name: 'Closure', value: 'Foldover Top with Metal Buckle' },
              { name: 'Warranty', value: 'Lifetime Manufacturer Guarantee' },
              { name: 'Water Resistance', value: 'Greenland Wax Treatable Coating' },
            ],
            price: '8551',
            original_price: '10999',
            discount_price: '8551',
            stock: 14,
            rating: '4.8',
            tag: 'BESTSELLER',
            is_featured: true,
            is_active: true,
            images: [],
          } as any;
        });
      }
    }
    return [];
  }, [messages, catalog]);

  // Canvas displayed products
  const displayedProducts = useMemo(() => {
    let base: any[] = latestMessageProducts;
    if (canvasSearch.trim()) {
      const q = canvasSearch.toLowerCase();
      base = (latestMessageProducts.length > 0 ? latestMessageProducts : catalog).filter(
        (p: any) =>
          (p.name || '').toLowerCase().includes(q) ||
          (p.category?.name || p.category || '').toLowerCase().includes(q)
      );
    }
    return base;
  }, [latestMessageProducts, catalog, canvasSearch]);

  // Set default spotlight product when displayed products update
  useEffect(() => {
    if (displayedProducts.length > 0) {
      setSelectedProduct(displayedProducts[0]);
      setSelectedImageAngle(0);
    } else {
      setSelectedProduct(null);
    }
  }, [displayedProducts]);

  const handlePolicySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await savePolicy(policyForm);
    setShowPolicyModal(false);
  };

  // Open Razorpay Modal
  const openRazorpayModal = (amount: number, intentId?: string) => {
    const finalAmount = amount > 0 ? amount : totalPrice > 0 ? totalPrice : 8551;
    setRazorpayAmount(finalAmount);
    setRazorpayOrderId(`ORD-${Math.floor(1000 + Math.random() * 9000)}`);
    setPendingIntentId(intentId || null);
    setShowRazorpayModal(true);
  };

  // Complete Razorpay Payment
  const handleCompleteRazorpayPayment = async () => {
    setIsProcessingRazorpay(true);
    setTimeout(async () => {
      try {
        if (pendingIntentId) {
          await approveTransaction(pendingIntentId);
        } else {
          sendMessage(`I have completed payment of ₹${razorpayAmount} via Razorpay UPI.`);
        }
      } catch (err) {
        // Handled in hook
      } finally {
        setIsProcessingRazorpay(false);
        setShowRazorpayModal(false);
      }
    }, 1200);
  };

  // Copy Razorpay Direct Link
  const handleCopyRazorpayLink = () => {
    const link = `https://rzp.io/l/razorhub_pay_${razorpayOrderId}`;
    navigator.clipboard.writeText(link);
    setLinkCopied(true);
    setTimeout(() => setLinkCopied(false), 2500);
  };

  // Dynamic Contextual Action Buttons based on Prompt, Results, and Cart
  const contextualActionButtons = useMemo(() => {
    const lastMsg = messages[messages.length - 1];
    const lastText = (lastMsg?.text || '').toLowerCase();
    const hasProducts = displayedProducts.length > 0;
    const hasApproval = Boolean(lastMsg?.approval_card);
    const hasPaymentSuccess = Boolean(lastMsg?.payment_success);
    const isCartContext =
      lastText.includes('cart summary') ||
      lastText.includes('your current cart') ||
      lastText.includes('ready to proceed') ||
      lastText.includes('proceed to continue') ||
      (cartItems.length > 0 && (lastText.includes('cart') || lastText.includes('item')));

    // Case 1: Payment Success State
    if (hasPaymentSuccess) {
      return [
        { label: 'View Orders', action: '/orders', icon: Package, isNav: true, variant: 'emerald' },
        { label: 'Continue Shopping', action: 'Show top trending tech products', icon: ShoppingBag, variant: 'indigo' },
        { label: 'New Search', action: 'NEW_CHAT_ACTION', icon: RefreshCw, variant: 'muted' },
      ];
    }

    // Case 2: Confirmation / Approval Card Active
    if (hasApproval && lastMsg?.approval_card) {
      const card = lastMsg.approval_card;
      return [
        {
          label: `Pay ₹${card.amount.toLocaleString()} with Razorpay`,
          action: 'TRIGGER_RAZORPAY',
          icon: CreditCard,
          variant: 'razorpay',
        },
        {
          label: 'Approve & Pay',
          action: `APPROVE_INTENT_${card.intent_id}`,
          icon: CheckCircle2,
          variant: 'emerald',
        },
        {
          label: 'Cash on Delivery (COD)',
          action: 'I want to pay using Cash on Delivery (COD)',
          icon: DollarSign,
          variant: 'muted',
        },
        {
          label: 'Reject / Cancel',
          action: `REJECT_INTENT_${card.intent_id}`,
          icon: XCircle,
          variant: 'rose',
        },
      ];
    }

    // Case 3: Cart / Checkout Context
    if (isCartContext || lastText.includes('checkout')) {
      return [
        {
          label: 'Proceed to Checkout',
          action: 'Proceed with checkout for my bag items',
          icon: Zap,
          variant: 'gradient',
        },
        { label: 'Pay via Razorpay', action: 'TRIGGER_RAZORPAY', icon: CreditCard, variant: 'razorpay' },
        {
          label: 'Cash on Delivery (COD)',
          action: 'Place order using Cash on Delivery (COD)',
          icon: DollarSign,
          variant: 'muted',
        },
        { label: 'Change / Edit Order', action: 'OPEN_CART_CANVAS', icon: ShoppingCart, variant: 'muted' },
        { label: 'Cancel Order', action: 'Cancel my current order', icon: X, variant: 'rose' },
      ];
    }

    // Case 4: Product Search Results Displayed
    if (hasProducts) {
      const firstProd = displayedProducts[0];
      return [
        {
          label: `Add ${firstProd.name.slice(0, 22)}... to Cart`,
          action: `ADD_PRODUCT_${firstProd.id}`,
          icon: ShoppingCart,
          variant: 'indigo',
        },
        { label: 'Instant Buy (Razorpay)', action: 'TRIGGER_RAZORPAY', icon: CreditCard, variant: 'razorpay' },
        { label: 'Compare Specs on Canvas', action: 'OPEN_COMPARE_CANVAS', icon: Scale, variant: 'muted' },
        { label: 'Show Active Flash Deals', action: 'Show active flash deals', icon: Flame, variant: 'amber' },
        { label: 'Filter Under ₹5,000', action: 'Show products under ₹5,000', icon: Search, variant: 'muted' },
      ];
    }

    // Case 5: Initial / Default Greeting State (Frequently Queried Prompts)
    return [
      {
        label: 'Wireless headphones under ₹5,000',
        action: 'I need wireless headphones under ₹5,000',
        icon: Zap,
        variant: 'muted',
      },
      {
        label: 'Compare Sony WH-CH520 vs JBL Tune 510BT',
        action: 'Compare Sony WH-CH520 vs JBL Tune 510BT',
        icon: Scale,
        variant: 'muted',
      },
      { label: 'Backpacks for 15-inch laptop', action: 'Show backpacks with 15-inch laptop fit', icon: Package, variant: 'muted' },
      { label: 'Show active flash deals', action: 'Show active flash deals', icon: Flame, variant: 'amber' },
      { label: 'Show my consent limits', action: 'Show my consent limits', icon: ShieldCheck, variant: 'muted' },
    ];
  }, [messages, displayedProducts, cartItems]);

  // Action Click Handler from dynamic buttons
  const handleActionClick = (action: string) => {
    if (action === 'TRIGGER_RAZORPAY') {
      openRazorpayModal(totalPrice);
    } else if (action === 'OPEN_CART_CANVAS') {
      setCanvasTab('cart');
    } else if (action === 'OPEN_COMPARE_CANVAS') {
      setCanvasTab('compare');
    } else if (action === 'NEW_CHAT_ACTION') {
      resetChat();
    } else if (action.startsWith('ADD_PRODUCT_')) {
      const prodId = action.replace('ADD_PRODUCT_', '');
      const found = displayedProducts.find((p) => String(p.id) === prodId);
      if (found) handleAddToCartAnimated(found);
    } else if (action.startsWith('APPROVE_INTENT_')) {
      const intentId = action.replace('APPROVE_INTENT_', '');
      approveTransaction(intentId);
    } else if (action.startsWith('REJECT_INTENT_')) {
      const intentId = action.replace('REJECT_INTENT_', '');
      rejectTransaction(intentId);
    } else {
      sendMessage(action);
    }
  };

  // Gallery angle images for spotlight product
  const spotlightGalleryImages = useMemo(() => {
    if (!selectedProduct) return [];
    const baseImg = productImage(selectedProduct);
    const catFallback = getCategoryFallbackImage(selectedProduct.category?.name || selectedProduct.name);
    return [
      baseImg,
      catFallback,
      'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&auto=format&fit=crop&q=80',
      'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=800&auto=format&fit=crop&q=80',
    ];
  }, [selectedProduct]);

  return (
    <div className={`w-full ${isFloating ? 'h-full flex flex-col' : 'max-w-[1720px] mx-auto px-4 sm:px-6 py-6 space-y-4'}`}>
      
      {/* ── Studio Header Bar ── */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 sm:p-5 rounded-3xl bg-surface/95 dark:bg-zinc-900/95 border border-border/80 shadow-xs shrink-0">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base sm:text-lg font-black text-primary">RazorHub AI Commerce Studio</h2>
              <span className="inline-flex items-center gap-1 text-[10px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 px-2.5 py-0.5 rounded-full">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Live Synchronized
              </span>
            </div>
            <p className="text-xs text-secondary hidden sm:block">
              {roleConfig.roleBadge} • Autonomous Multi-Agent Gateway
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={resetChat}
            className="px-3.5 py-2 rounded-2xl text-xs font-bold border border-border/80 bg-surface hover:bg-muted text-secondary hover:text-primary transition flex items-center gap-1.5 cursor-pointer shadow-2xs"
            title="Reset Session"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>New Chat</span>
          </button>

          {isFloating && onClose && (
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-2xl border border-border/80 bg-surface hover:bg-muted text-secondary hover:text-primary transition cursor-pointer shadow-2xs"
              title="Close Studio"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* ── Main Dual-Pane Studio Grid with Matched Heights ── */}
      <div className={`grid grid-cols-1 lg:grid-cols-12 gap-5 ${isFloating ? 'flex-1 min-h-0' : 'h-[780px] lg:h-[840px]'} min-h-[640px]`}>

        {/* ══════════════════════════════════════════════════════════════
            LEFT PANE: LIVE SYNCHRONIZED CANVAS (7 COLS)
        ══════════════════════════════════════════════════════════════ */}
        <div className="lg:col-span-7 xl:col-span-7 h-full min-h-0 rounded-3xl bg-surface/95 dark:bg-zinc-900/95 border border-border/80 shadow-xs flex flex-col overflow-hidden">
          
          {/* Canvas Top Bar */}
          <div className="px-5 py-4 border-b border-border/80 bg-surface/50 flex flex-wrap items-center justify-between gap-3 shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="h-8 w-8 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                <Sparkles className="h-4 w-4" />
              </div>
              <h3 className="text-sm sm:text-base font-black text-primary">AI Shopping Canvas</h3>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-2xl border border-border/80 text-xs sm:text-sm font-bold overflow-x-auto scrollbar-none">
              <button
                type="button"
                onClick={() => setCanvasTab('products')}
                className={`px-3 py-1.5 rounded-xl transition cursor-pointer whitespace-nowrap ${
                  canvasTab === 'products'
                    ? 'bg-surface dark:bg-zinc-800 text-primary shadow-xs font-black'
                    : 'text-secondary hover:text-primary'
                }`}
              >
                Products ({displayedProducts.length})
              </button>

              <button
                type="button"
                onClick={() => setCanvasTab('compare')}
                className={`px-3 py-1.5 rounded-xl transition cursor-pointer whitespace-nowrap ${
                  canvasTab === 'compare'
                    ? 'bg-surface dark:bg-zinc-800 text-primary shadow-xs font-black'
                    : 'text-secondary hover:text-primary'
                }`}
              >
                Compare ({comparisonList.length})
              </button>

              <button
                type="button"
                onClick={() => setCanvasTab('cart')}
                className={`px-3 py-1.5 rounded-xl transition cursor-pointer whitespace-nowrap ${
                  canvasTab === 'cart'
                    ? 'bg-surface dark:bg-zinc-800 text-primary shadow-xs font-black'
                    : 'text-secondary hover:text-primary'
                }`}
              >
                Cart ({cartItems.length})
              </button>

              <button
                type="button"
                onClick={() => setCanvasTab('deals')}
                className={`px-3 py-1.5 rounded-xl transition cursor-pointer whitespace-nowrap ${
                  canvasTab === 'deals'
                    ? 'bg-surface dark:bg-zinc-800 text-primary shadow-xs font-black'
                    : 'text-secondary hover:text-primary'
                }`}
              >
                Deals
              </button>

              <button
                type="button"
                onClick={() => setCanvasTab('policy')}
                className={`px-3 py-1.5 rounded-xl transition cursor-pointer whitespace-nowrap ${
                  canvasTab === 'policy'
                    ? 'bg-surface dark:bg-zinc-800 text-primary shadow-xs font-black'
                    : 'text-secondary hover:text-primary'
                }`}
              >
                Policy
              </button>
            </div>

            {/* Filter Input */}
            {canvasTab === 'products' && (
              <div className="relative hidden xl:block">
                <Search className="w-3.5 h-3.5 text-secondary absolute left-2.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={canvasSearch}
                  onChange={(e) => setCanvasSearch(e.target.value)}
                  placeholder="Filter canvas..."
                  className="w-36 h-8 rounded-xl bg-muted/40 border border-border/80 pl-8 pr-2.5 text-xs text-primary focus:outline-none focus:border-indigo-500"
                />
              </div>
            )}
          </div>

          {/* Canvas Body Container */}
          <div className="flex-1 overflow-y-auto p-5 sm:p-6 scrollbar-thin">
            
            {/* ── TAB 1: PRODUCTS (WITH RICH SPOTLIGHT & DETAILS) ── */}
            {canvasTab === 'products' && (
              <div className="h-full flex flex-col space-y-6">
                {displayedProducts.length === 0 ? (
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
                    <p className="text-xs sm:text-sm text-secondary mb-8 max-w-md">
                      Ask the AI agent in the chat on the right. Live products, multi-angle images, spec comparisons, stock statuses, and cart items will populate here instantly.
                    </p>

                    {/* Interactive Category Shortcut Cards */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full text-left">
                      <button
                        type="button"
                        onClick={() => sendMessage('Find top gaming laptops with high performance')}
                        className="group p-4 rounded-2xl border border-border/80 bg-surface hover:bg-muted/50 hover:border-indigo-500/50 transition-all shadow-xs hover:shadow-md cursor-pointer"
                      >
                        <div className="flex items-center gap-3 mb-2">
                          <div className="p-2 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform">
                            <Cpu className="h-4 w-4" />
                          </div>
                          <span className="text-xs font-bold text-primary">Laptops &amp; Tech</span>
                        </div>
                        <p className="text-xs text-secondary">"Find top gaming laptops with high performance"</p>
                      </button>

                      <button
                        type="button"
                        onClick={() => sendMessage('Compare Samsung Galaxy S25 Ultra vs iPhone 16')}
                        className="group p-4 rounded-2xl border border-border/80 bg-surface hover:bg-muted/50 hover:border-purple-500/50 transition-all shadow-xs hover:shadow-md cursor-pointer"
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
                        onClick={() => sendMessage('Show trending sneakers and sports footwear')}
                        className="group p-4 rounded-2xl border border-border/80 bg-surface hover:bg-muted/50 hover:border-emerald-500/50 transition-all shadow-xs hover:shadow-md cursor-pointer"
                      >
                        <div className="flex items-center gap-3 mb-2">
                          <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 group-hover:scale-110 transition-transform">
                            <Footprints className="h-4 w-4" />
                          </div>
                          <span className="text-xs font-bold text-primary">Sneakers &amp; Shoes</span>
                        </div>
                        <p className="text-xs text-secondary">"Show trending sneakers and sports footwear"</p>
                      </button>

                      <button
                        type="button"
                        onClick={() => sendMessage('Find best deals on clothing and apparel')}
                        className="group p-4 rounded-2xl border border-border/80 bg-surface hover:bg-muted/50 hover:border-pink-500/50 transition-all shadow-xs hover:shadow-md cursor-pointer"
                      >
                        <div className="flex items-center gap-3 mb-2">
                          <div className="p-2 rounded-xl bg-pink-500/10 text-pink-600 dark:text-pink-400 group-hover:scale-110 transition-transform">
                            <Shirt className="h-4 w-4" />
                          </div>
                          <span className="text-xs font-bold text-primary">Fashion &amp; Deals</span>
                        </div>
                        <p className="text-xs text-secondary">"Find best deals on clothing and apparel"</p>
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-6 animate-in fade-in duration-300">
                    
                    {/* ── RICH PRODUCT SPOTLIGHT CARD WITH IMAGES & FULL DETAILS ── */}
                    {selectedProduct && (
                      <div className="rounded-3xl border border-border/90 bg-surface/90 dark:bg-zinc-800/80 p-5 sm:p-6 shadow-md hover:border-indigo-500/40 transition-all space-y-5">
                        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3">
                          <div className="flex items-center gap-2">
                            <span className="px-3 py-1 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 border border-indigo-500/30">
                              {typeof selectedProduct.brand === 'object' ? selectedProduct.brand?.name : (selectedProduct.brand as any) || 'Featured Result'}
                            </span>
                            <span className="text-xs text-secondary font-semibold">
                              {selectedProduct.category?.name || 'Category'}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 text-xs">
                            <span className="flex items-center gap-1 font-bold text-emerald-600 dark:text-emerald-400">
                              <CheckCircle className="w-3.5 h-3.5" />
                              <span>Verified Stock</span>
                            </span>
                            <span className="text-secondary">•</span>
                            <span className="flex items-center gap-1 text-secondary font-medium">
                              <Truck className="w-3.5 h-3.5 text-indigo-500" />
                              <span>Next Day Delivery</span>
                            </span>
                          </div>
                        </div>

                        {/* Dual Column Spotlight Body: Gallery + Specs */}
                        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
                          
                          {/* Left: Interactive Multi-Angle Gallery */}
                          <div className="md:col-span-5 space-y-3">
                            <div className="relative aspect-[4/3] w-full rounded-2xl overflow-hidden bg-muted/40 dark:bg-zinc-900/60 p-3 border border-border/80 flex items-center justify-center group/img">
                              <img
                                src={spotlightGalleryImages[selectedImageAngle] || productImage(selectedProduct)}
                                alt={selectedProduct.name}
                                onError={(e) => {
                                  (e.target as HTMLImageElement).src = getCategoryFallbackImage(
                                    selectedProduct.category?.name || selectedProduct.name
                                  );
                                }}
                                className="h-full w-full object-contain group-hover/img:scale-105 transition-transform duration-500"
                              />
                              <span className="absolute top-2.5 right-2.5 px-2.5 py-1 rounded-lg text-xs font-black bg-surface/90 dark:bg-zinc-900/90 text-primary border border-border backdrop-blur-xs shadow-xs">
                                ★ {selectedProduct.rating || '4.8'}
                              </span>
                            </div>

                            {/* Gallery Thumbnails */}
                            <div className="grid grid-cols-4 gap-2">
                              {spotlightGalleryImages.map((imgUrl, aIdx) => (
                                <button
                                  key={aIdx}
                                  type="button"
                                  onClick={() => setSelectedImageAngle(aIdx)}
                                  className={`aspect-square rounded-xl overflow-hidden p-1 border transition-all cursor-pointer bg-muted/30 ${
                                    selectedImageAngle === aIdx
                                      ? 'border-indigo-600 ring-2 ring-indigo-600/30'
                                      : 'border-border/70 opacity-70 hover:opacity-100 hover:border-indigo-500/40'
                                  }`}
                                >
                                  <img
                                    src={imgUrl}
                                    alt={`Angle ${aIdx + 1}`}
                                    className="h-full w-full object-contain"
                                  />
                                </button>
                              ))}
                            </div>
                          </div>

                          {/* Right: Rich Specifications & Pricing Details */}
                          <div className="md:col-span-7 space-y-4">
                            <div>
                              <h3 className="text-base sm:text-xl font-extrabold text-primary leading-snug">
                                {selectedProduct.name}
                              </h3>
                              <p className="text-xs sm:text-sm text-secondary mt-1 leading-relaxed">
                                {selectedProduct.description ||
                                  'Engineered with premium components, rigorous quality standards, and full manufacturer warranty coverage.'}
                              </p>
                            </div>

                            {/* Detailed Specs Key-Value Grid */}
                            <div className="grid grid-cols-2 gap-2.5 p-3.5 rounded-2xl bg-muted/40 dark:bg-zinc-900/40 border border-border/70 text-xs">
                              <div className="space-y-0.5">
                                <span className="text-[10px] uppercase font-bold text-secondary">Warranty</span>
                                <p className="font-bold text-primary">1-Year Official Coverage</p>
                              </div>
                              <div className="space-y-0.5">
                                <span className="text-[10px] uppercase font-bold text-secondary">Dispatch Status</span>
                                <p className="font-bold text-emerald-600">Ships in 24 Hours</p>
                              </div>
                              <div className="space-y-0.5">
                                <span className="text-[10px] uppercase font-bold text-secondary">Return Policy</span>
                                <p className="font-bold text-primary">7 Days Replacement</p>
                              </div>
                              <div className="space-y-0.5">
                                <span className="text-[10px] uppercase font-bold text-secondary">Customer Rating</span>
                                <p className="font-bold text-amber-500">★ 4.8 (428 Reviews)</p>
                              </div>
                            </div>

                            {/* Price Breakdown */}
                            <div className="flex items-baseline gap-3 pt-1">
                              <span className="text-2xl sm:text-3xl font-black text-indigo-600 dark:text-indigo-400">
                                ₹{Number(selectedProduct.price || 8551).toLocaleString('en-IN')}
                              </span>
                              <span className="text-sm text-secondary line-through">
                                ₹{Number((selectedProduct as any).original_price || 10999).toLocaleString('en-IN')}
                              </span>
                              <span className="px-2.5 py-0.5 rounded-lg text-xs font-black bg-rose-500/15 text-rose-600 border border-rose-500/25">
                                22% OFF
                              </span>
                            </div>

                            {/* Action Buttons */}
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-2">
                              <button
                                type="button"
                                onClick={() => handleAddToCartAnimated(selectedProduct)}
                                className={`py-2.5 px-3 rounded-2xl font-bold text-xs transition flex items-center justify-center gap-1.5 cursor-pointer shadow-md ${
                                  addedSlug === (selectedProduct.slug || String(selectedProduct.id))
                                    ? 'bg-emerald-600 text-white'
                                    : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                                }`}
                              >
                                <ShoppingCart className="w-4 h-4" />
                                <span>{addedSlug === (selectedProduct.slug || String(selectedProduct.id)) ? 'Added to Cart' : 'Add to Cart'}</span>
                              </button>

                              <button
                                type="button"
                                onClick={() => openRazorpayModal(Number(selectedProduct.price || 8551))}
                                className="py-2.5 px-3 rounded-2xl bg-[#0C2340] hover:bg-[#143560] text-white font-bold text-xs shadow-md transition cursor-pointer flex items-center justify-center gap-1.5 border border-[#3395FF]/40"
                              >
                                <CreditCard className="w-4 h-4 text-[#3395FF]" />
                                <span>Instant Buy</span>
                              </button>

                              <button
                                type="button"
                                onClick={() => {
                                  addToCompare(selectedProduct);
                                  setCanvasTab('compare');
                                }}
                                className="py-2.5 px-3 rounded-2xl border border-border bg-surface hover:bg-muted font-bold text-xs text-secondary hover:text-primary transition flex items-center justify-center gap-1.5 cursor-pointer"
                              >
                                <Scale className="w-4 h-4" />
                                <span>Compare</span>
                              </button>
                            </div>
                          </div>

                        </div>
                      </div>
                    )}

                    {/* ── ALL RESULTED PRODUCTS GRID ── */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs sm:text-sm font-black text-primary flex items-center gap-1.5">
                          <span>Live Catalog Matches</span>
                          <span className="text-secondary font-medium">({displayedProducts.length} items)</span>
                        </h4>
                        {comparisonList.length > 0 && (
                          <button
                            onClick={() => setCanvasTab('compare')}
                            className="text-xs text-indigo-600 font-bold hover:underline"
                          >
                            Compare {comparisonList.length} items →
                          </button>
                        )}
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                        {displayedProducts.map((p: any) => {
                          const isAdded = addedSlug === (p.slug || String(p.id));
                          const isCompared = comparisonList.some((c) => c.id === p.id);
                          const isSelected = selectedProduct?.id === p.id;
                          const prodPrice = p.price || 0;
                          const origPrice = p.original_price || p.mrp || 0;
                          const discount = origPrice > prodPrice ? Math.round(((origPrice - prodPrice) / origPrice) * 100) : 0;
                          const pImage = p.image_url || productImage(p);

                          return (
                            <div
                              key={p.id}
                              onClick={() => {
                                setSelectedProduct(p);
                                setSelectedImageAngle(0);
                              }}
                              className={`rounded-2xl border bg-surface p-4 shadow-2xs hover:shadow-md transition flex flex-col justify-between group cursor-pointer ${
                                isSelected ? 'border-indigo-600 ring-2 ring-indigo-500/20' : 'border-border/80 hover:border-indigo-500/40'
                              }`}
                            >
                              <div className="space-y-3">
                                {/* Image & Badges */}
                                <div className="relative aspect-[4/3] w-full rounded-xl overflow-hidden bg-muted/30 dark:bg-zinc-800/40 p-2.5 flex items-center justify-center">
                                  <img
                                    src={pImage}
                                    alt={p.name}
                                    onError={(e) => {
                                      (e.target as HTMLImageElement).src = getCategoryFallbackImage(p.category?.name || p.name);
                                    }}
                                    className="h-full w-full object-contain group-hover:scale-105 transition-transform duration-300"
                                    loading="lazy"
                                  />
                                  {discount > 0 && (
                                    <span className="absolute top-2 left-2 px-2 py-0.5 rounded-md text-[10px] font-black bg-rose-500 text-white shadow-xs">
                                      {discount}% OFF
                                    </span>
                                  )}
                                  <span className="absolute top-2 right-2 px-2 py-0.5 rounded-md text-[10px] font-bold bg-surface/90 text-primary border border-border backdrop-blur-xs">
                                    ★ {p.rating || '4.5'}
                                  </span>
                                </div>

                                {/* Info with High-Contrast Typography */}
                                <div className="space-y-1">
                                  <span className="text-[10px] uppercase font-bold text-indigo-500 dark:text-indigo-400 tracking-wider">
                                    {p.brand?.name || p.brand || 'RazorHub Official'}
                                  </span>
                                  <h3 className="text-xs sm:text-sm font-extrabold text-zinc-900 dark:text-zinc-50 line-clamp-2 mt-0.5 leading-snug">
                                    {p.name}
                                  </h3>
                                  <p className="text-[11px] text-secondary line-clamp-1">
                                    {p.description || 'Verified authentic item in RazorHub inventory'}
                                  </p>
                                </div>
                              </div>

                              {/* Price & Action Buttons */}
                              <div className="pt-3 border-t border-border mt-3 space-y-2.5">
                                <div className="flex items-baseline gap-2">
                                  <span className="text-base font-black text-indigo-600 dark:text-indigo-400">
                                    ₹{Number(prodPrice).toLocaleString('en-IN')}
                                  </span>
                                  {origPrice > prodPrice && (
                                    <span className="text-xs text-zinc-400 dark:text-zinc-500 line-through">
                                      ₹{Number(origPrice).toLocaleString('en-IN')}
                                    </span>
                                  )}
                                </div>

                                <div className="grid grid-cols-2 gap-2">
                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleAddToCartAnimated(p);
                                    }}
                                    className={`py-2 px-2 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1 cursor-pointer ${
                                      isAdded
                                        ? 'bg-emerald-600 text-white shadow-md'
                                        : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm'
                                    }`}
                                  >
                                    {isAdded ? (
                                      <>
                                        <CheckCircle2 className="w-3.5 h-3.5" />
                                        <span>Added</span>
                                      </>
                                    ) : (
                                      <>
                                        <ShoppingCart className="w-3.5 h-3.5" />
                                        <span>Add Cart</span>
                                      </>
                                    )}
                                  </button>

                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      isCompared ? removeFromCompare(p.id) : addToCompare(p);
                                    }}
                                    className={`py-2 px-2 rounded-xl text-xs font-bold border transition flex items-center justify-center gap-1 cursor-pointer ${
                                      isCompared
                                        ? 'bg-amber-500/15 border-amber-500/30 text-amber-600'
                                        : 'bg-surface border-border text-secondary hover:text-primary hover:bg-muted'
                                    }`}
                                  >
                                    <Scale className="w-3.5 h-3.5" />
                                    <span>{isCompared ? 'Compared' : 'Compare'}</span>
                                  </button>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                  </div>
                )}
              </div>
            )}

            {/* ── TAB 2: COMPARE ── */}
            {canvasTab === 'compare' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm sm:text-base font-black text-primary">Side-by-Side Specification Comparison</h3>
                    <p className="text-xs text-secondary">Compare hardware, battery life, prices, and warranties</p>
                  </div>
                  {comparisonList.length > 0 && (
                    <button
                      onClick={clearCompare}
                      className="text-xs text-rose-500 font-bold hover:underline cursor-pointer"
                    >
                      Clear Comparison
                    </button>
                  )}
                </div>

                {comparisonList.length === 0 ? (
                  <div className="p-12 text-center border border-dashed border-border rounded-3xl space-y-3">
                    <Scale className="w-10 h-10 text-secondary/40 mx-auto" />
                    <h4 className="text-sm font-bold text-primary">No products selected for comparison</h4>
                    <p className="text-xs text-secondary max-w-sm mx-auto">
                      Click the "Compare" button on any product card or ask the AI to "Compare Sony WH-CH520 vs JBL Tune 510BT".
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs sm:text-sm text-left border-collapse">
                      <thead>
                        <tr className="border-b border-border">
                          <th className="p-3 text-secondary uppercase font-bold w-32">Attribute</th>
                          {comparisonList.map((prod) => (
                            <th key={prod.id} className="p-3 min-w-[180px]">
                              <div className="space-y-2">
                                <div className="h-20 w-20 rounded-xl bg-muted/40 p-2 mx-auto">
                                  <img
                                    src={productImage(prod)}
                                    alt={prod.name}
                                    className="h-full w-full object-contain"
                                  />
                                </div>
                                <div className="text-center">
                                  <h4 className="font-bold text-primary truncate">{prod.name}</h4>
                                  <span className="text-indigo-600 font-black">
                                    ₹{price(prod).toLocaleString('en-IN')}
                                  </span>
                                </div>
                                <button
                                  type="button"
                                  onClick={() => removeFromCompare(prod.id)}
                                  className="w-full text-[10px] text-rose-500 hover:underline cursor-pointer"
                                >
                                  Remove
                                </button>
                              </div>
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        <tr>
                          <td className="p-3 font-bold text-secondary">Brand</td>
                          {comparisonList.map((p) => (
                            <td key={p.id} className="p-3 font-medium text-primary">
                              {p.brand?.name || 'Standard'}
                            </td>
                          ))}
                        </tr>
                        <tr>
                          <td className="p-3 font-bold text-secondary">Category</td>
                          {comparisonList.map((p) => (
                            <td key={p.id} className="p-3 font-medium text-primary">
                              {p.category?.name || 'Electronics'}
                            </td>
                          ))}
                        </tr>
                        <tr>
                          <td className="p-3 font-bold text-secondary">Rating</td>
                          {comparisonList.map((p) => (
                            <td key={p.id} className="p-3 font-medium text-emerald-600">
                              ★ {p.rating || '4.5'}
                            </td>
                          ))}
                        </tr>
                        <tr>
                          <td className="p-3 font-bold text-secondary">Stock Status</td>
                          {comparisonList.map((p) => (
                            <td key={p.id} className="p-3 font-medium">
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-600">
                                In Stock
                              </span>
                            </td>
                          ))}
                        </tr>
                        <tr>
                          <td className="p-3 font-bold text-secondary">Action</td>
                          {comparisonList.map((p) => (
                            <td key={p.id} className="p-3">
                              <button
                                type="button"
                                onClick={() => handleAddToCartAnimated(p)}
                                className="w-full py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold cursor-pointer"
                              >
                                Add to Cart
                              </button>
                            </td>
                          ))}
                        </tr>
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* ── TAB 3: CART ── */}
            {canvasTab === 'cart' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm sm:text-base font-black text-primary">Active Cart Session</h3>
                    <p className="text-xs text-secondary">{cartItems.length} unique items in your checkout bag</p>
                  </div>
                  {cartItems.length > 0 && (
                    <button
                      onClick={clearCart}
                      className="text-xs text-rose-500 font-bold hover:underline cursor-pointer"
                    >
                      Clear Bag
                    </button>
                  )}
                </div>

                {cartItems.length === 0 ? (
                  <div className="p-12 text-center border border-dashed border-border rounded-3xl space-y-3">
                    <ShoppingCart className="w-10 h-10 text-secondary/40 mx-auto" />
                    <h4 className="text-sm font-bold text-primary">Your bag is currently empty</h4>
                    <p className="text-xs text-secondary max-w-sm mx-auto">
                      Ask the AI to "Add Fjallraven backpack to cart" or browse products in the live catalog.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="divide-y divide-border border border-border rounded-2xl bg-surface overflow-hidden">
                      {cartItems.map((item) => (
                        <div key={item.product.id} className="p-4 flex items-center justify-between gap-4">
                          <div className="flex items-center gap-3 min-w-0">
                            <div className="h-12 w-12 rounded-xl bg-muted/40 p-1 shrink-0 flex items-center justify-center">
                              <img
                                src={productImage(item.product)}
                                alt={item.product.name}
                                className="h-full w-full object-contain"
                              />
                            </div>
                            <div className="min-w-0">
                              <h4 className="font-extrabold text-xs sm:text-sm text-primary truncate">
                                {item.product.name}
                              </h4>
                              <p className="text-xs text-indigo-600 font-bold">
                                ₹{price(item.product).toLocaleString('en-IN')}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-3 shrink-0">
                            <div className="flex items-center border border-border rounded-xl">
                              <button
                                onClick={() => updateQuantity(item.product.id, Math.max(1, item.quantity - 1))}
                                className="p-1.5 hover:bg-muted text-secondary cursor-pointer"
                              >
                                <Minus className="w-3.5 h-3.5" />
                              </button>
                              <span className="px-2.5 text-xs font-bold text-primary">{item.quantity}</span>
                              <button
                                onClick={() => updateQuantity(item.product.id, item.quantity + 1)}
                                className="p-1.5 hover:bg-muted text-secondary cursor-pointer"
                              >
                                <Plus className="w-3.5 h-3.5" />
                              </button>
                            </div>
                            <button
                              onClick={() => removeFromCart(item.product.id)}
                              className="p-1.5 text-rose-500 hover:bg-rose-500/10 rounded-xl cursor-pointer"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="p-4 rounded-2xl bg-muted/30 border border-border space-y-2">
                      <div className="flex justify-between text-xs text-secondary">
                        <span>Cart Subtotal</span>
                        <span className="font-bold text-primary">₹{totalPrice.toLocaleString('en-IN')}</span>
                      </div>
                      <div className="flex justify-between text-xs text-secondary">
                        <span>Delivery</span>
                        <span className="font-bold text-emerald-600">FREE</span>
                      </div>
                      <div className="pt-2 border-t border-border flex justify-between text-sm font-black text-primary">
                        <span>Total Payable</span>
                        <span>₹{totalPrice.toLocaleString('en-IN')}</span>
                      </div>

                      <div className="grid grid-cols-2 gap-2 pt-2">
                        <button
                          type="button"
                          onClick={() => sendMessage(`Proceed to checkout cart total ₹${totalPrice}`)}
                          className="py-3 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:opacity-95 text-white text-xs font-black shadow-md transition cursor-pointer flex items-center justify-center gap-1.5"
                        >
                          <Zap className="w-4 h-4 text-amber-300" />
                          <span>AI Checkout</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => openRazorpayModal(totalPrice)}
                          className="py-3 rounded-2xl bg-[#0C2340] hover:bg-[#143560] text-white text-xs font-black shadow-md transition cursor-pointer flex items-center justify-center gap-1.5 border border-[#3395FF]/40"
                        >
                          <CreditCard className="w-4 h-4 text-[#3395FF]" />
                          <span>Pay via Razorpay</span>
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ── TAB 4: DEALS ── */}
            {canvasTab === 'deals' && (
              <div className="space-y-4">
                <h3 className="text-sm sm:text-base font-black text-primary flex items-center gap-1.5">
                  <Flame className="w-4 h-4 text-amber-500" />
                  <span>Exclusive Flash Discounts &amp; Offers</span>
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                  {flashDeals.map((prod) => (
                    <div
                      key={prod.id}
                      className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4 flex flex-col justify-between"
                    >
                      <div className="space-y-2">
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-black bg-amber-500 text-white w-fit">
                          FEATURED DEAL
                        </span>
                        <h4 className="text-xs sm:text-sm font-black text-primary">{prod.name}</h4>
                        <div className="text-sm sm:text-base font-black text-indigo-600">
                          ₹{price(prod).toLocaleString('en-IN')}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleAddToCartAnimated(prod)}
                        className="mt-3 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold cursor-pointer"
                      >
                        Grab Deal
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── TAB 5: POLICY ── */}
            {canvasTab === 'policy' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm sm:text-base font-black text-primary flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4 text-emerald-500" />
                      <span>Payment Consent Authorization Model</span>
                    </h3>
                    <p className="text-xs text-secondary">
                      Deterministic thresholds governing agent autonomy and human-in-the-loop approvals
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowPolicyModal(true)}
                    className="px-3.5 py-1.5 rounded-xl border border-border bg-surface text-xs font-bold text-primary hover:bg-muted cursor-pointer"
                  >
                    Edit Limits
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="p-4 rounded-2xl bg-emerald-500/5 border border-emerald-500/20 space-y-1">
                    <span className="text-xs font-bold text-emerald-600">Auto-Approve Ceiling</span>
                    <div className="text-lg font-black text-emerald-700 dark:text-emerald-300">
                      &lt; ₹{policy.approval_threshold.toLocaleString()}
                    </div>
                    <p className="text-[11px] text-secondary">Transactions execute immediately without confirmation.</p>
                  </div>

                  <div className="p-4 rounded-2xl bg-amber-500/5 border border-amber-500/20 space-y-1">
                    <span className="text-xs font-bold text-amber-600">Confirmation Bracket</span>
                    <div className="text-lg font-black text-amber-700 dark:text-amber-300">
                      ₹{policy.approval_threshold.toLocaleString()} — ₹{policy.per_transaction_limit.toLocaleString()}
                    </div>
                    <p className="text-[11px] text-secondary">Requires interactive Approval Card confirmation.</p>
                  </div>

                  <div className="p-4 rounded-2xl bg-rose-500/5 border border-rose-500/20 space-y-1">
                    <span className="text-xs font-bold text-rose-600">Hard Block Limit</span>
                    <div className="text-lg font-black text-rose-700 dark:text-rose-300">
                      &gt; ₹{policy.per_transaction_limit.toLocaleString()}
                    </div>
                    <p className="text-[11px] text-secondary">Automatically blocked by the governance firewall.</p>
                  </div>
                </div>

                {/* Daily Spending Bar */}
                <div className="p-5 rounded-2xl border border-border bg-surface space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-primary">Daily Spending Limit Tracker</span>
                    <span className="font-mono text-secondary">
                      ₹{policy.daily_spent.toLocaleString()} / ₹{policy.daily_limit.toLocaleString()}
                    </span>
                  </div>
                  <div className="h-2.5 w-full rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full bg-indigo-600 rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.min(100, (policy.daily_spent / Math.max(1, policy.daily_limit)) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>

        {/* ══════════════════════════════════════════════════════════════
            RIGHT PANE: CONVERSATIONAL COMMERCE AGENT (5 COLS)
        ══════════════════════════════════════════════════════════════ */}
        <div className="lg:col-span-5 xl:col-span-5 h-full min-h-0 rounded-3xl bg-surface/95 dark:bg-zinc-900/95 border border-border/80 shadow-xs flex flex-col overflow-hidden">
          
          {/* Chat Header */}
          <div className="px-5 py-4 border-b border-border/80 bg-surface/50 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center shadow-md">
                <Bot className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm sm:text-base font-black text-primary flex items-center gap-1.5">
                  <span>{roleConfig.roleTitle}</span>
                  <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                </h3>
                <span className="text-[11px] font-mono text-secondary">
                  Autonomous Commerce Engine
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={resetChat}
              className="p-1.5 rounded-xl text-secondary hover:text-primary hover:bg-muted transition cursor-pointer"
              title="Clear conversation"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>

          {/* Frequently Queried Prompts Ribbon */}
          <div className="px-4 py-2 border-b border-border/60 bg-muted/20 flex items-center gap-1.5 overflow-x-auto scrollbar-none shrink-0">
            <span className="text-[10px] font-bold text-secondary uppercase tracking-wider whitespace-nowrap flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-indigo-500" />
              <span>Trending:</span>
            </span>
            {FREQUENT_QUERIES.map((query, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => sendMessage(query)}
                className="px-2.5 py-1 rounded-xl text-[11px] font-semibold bg-surface border border-border/80 text-secondary hover:text-indigo-600 dark:hover:text-indigo-400 hover:border-indigo-500/40 transition whitespace-nowrap cursor-pointer shadow-2xs"
              >
                {query}
              </button>
            ))}
          </div>

          {/* Chat Messages Stream */}
          <div ref={chatScrollContainerRef} className="flex-1 overflow-y-auto p-5 space-y-4 scrollbar-thin">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-3 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {m.sender === 'agent' && (
                  <div className="w-8 h-8 rounded-xl bg-indigo-500/10 text-indigo-600 flex items-center justify-center shrink-0 mt-0.5">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`max-w-[88%] space-y-3 ${
                    m.sender === 'user'
                      ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-3.5 sm:p-4 rounded-3xl rounded-tr-xs shadow-sm text-sm sm:text-[15px] leading-relaxed'
                      : 'bg-muted/40 dark:bg-zinc-800/80 border border-border/80 p-4 sm:p-4.5 rounded-3xl rounded-tl-xs shadow-2xs text-sm sm:text-[15px] text-primary'
                  }`}
                >
                  {/* Intent Tag */}
                  {m.intent && (
                    <div className="inline-block px-2.5 py-0.5 rounded-md text-[10px] font-extrabold uppercase tracking-wider bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 border border-indigo-500/25">
                      {m.intent}
                    </div>
                  )}

                  {/* Formatted Message Body */}
                  {m.sender === 'user' ? (
                    <div className="whitespace-pre-wrap leading-relaxed">{m.text}</div>
                  ) : (
                    <FormattedCommerceMessage
                      text={m.text}
                      catalog={catalog}
                      onAddToCart={handleAddToCartAnimated}
                      onCompare={(prod) => {
                        addToCompare(prod);
                        setCanvasTab('compare');
                      }}
                      onViewProduct={(prod) => {
                        setSelectedProduct(prod);
                        setSelectedImageAngle(0);
                        setCanvasTab('products');
                      }}
                      onActionClick={handleActionClick}
                    />
                  )}

                  {/* ── APPROVAL CARD ── */}
                  {m.approval_card && (
                    <div className="rounded-2xl border border-amber-500/30 bg-amber-500/5 p-4 space-y-3 animate-in fade-in">
                      <div className="flex items-center justify-between border-b border-amber-500/20 pb-2">
                        <span className="text-[10px] font-black uppercase tracking-wider text-amber-600 flex items-center gap-1">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          <span>Confirmation Required</span>
                        </span>
                        <span className="text-[10px] font-bold text-secondary">
                          Policy: {m.approval_card.policy}
                        </span>
                      </div>

                      <div className="space-y-1">
                        <div className="text-sm font-black text-primary">{m.approval_card.product}</div>
                        <div className="text-xs text-secondary">Merchant: {m.approval_card.merchant}</div>
                        <div className="text-base font-black text-indigo-600 dark:text-indigo-400">
                          ₹{m.approval_card.amount.toLocaleString('en-IN')}
                        </div>
                      </div>

                      <div className="flex items-center gap-2 pt-2 border-t border-amber-500/20">
                        <button
                          type="button"
                          disabled={approving}
                          onClick={() => rejectTransaction(m.approval_card!.intent_id)}
                          className="flex-1 py-2 rounded-xl text-xs font-bold bg-muted hover:bg-border text-secondary cursor-pointer disabled:opacity-50"
                        >
                          Reject
                        </button>

                        <button
                          type="button"
                          disabled={approving}
                          onClick={() => openRazorpayModal(m.approval_card!.amount, m.approval_card!.intent_id)}
                          className="flex-1 py-2 rounded-xl text-xs font-black bg-[#0C2340] hover:bg-[#143560] text-white shadow-md cursor-pointer flex items-center justify-center gap-1 border border-[#3395FF]/40 disabled:opacity-50"
                        >
                          <CreditCard className="w-3.5 h-3.5 text-[#3395FF]" />
                          <span>Pay Razorpay</span>
                        </button>

                        <button
                          type="button"
                          disabled={approving}
                          onClick={() => approveTransaction(m.approval_card!.intent_id)}
                          className="flex-1 py-2 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-700 text-white shadow-md cursor-pointer flex items-center justify-center gap-1 disabled:opacity-50"
                        >
                          {approving ? (
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <CheckCircle2 className="w-3.5 h-3.5" />
                          )}
                          <span>Approve</span>
                        </button>
                      </div>
                    </div>
                  )}

                  {/* ── PAYMENT SUCCESS BANNER ── */}
                  {m.payment_success && (
                    <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-4 space-y-2">
                      <div className="flex items-center gap-1.5 text-sm font-black text-emerald-600">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Order #ORD-{m.payment_success.order_id} Confirmed!</span>
                      </div>
                      <p className="text-xs text-secondary">
                        Reference: <code className="font-mono bg-surface px-1.5 py-0.5 rounded">{m.payment_success.payment_reference}</code>
                      </p>
                      <div className="flex items-center justify-between text-xs pt-1">
                        <span className="font-semibold text-primary">ETA: {m.payment_success.delivery_eta}</span>
                        <Link
                          to={`/orders`}
                          className="font-bold underline text-indigo-600 flex items-center gap-1"
                        >
                          <span>View Orders</span>
                          <ExternalLink className="w-3 h-3" />
                        </Link>
                      </div>
                    </div>
                  )}

                  <span className="text-[10px] text-secondary block pt-1">{m.timestamp}</span>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-indigo-500/10 text-indigo-600 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 animate-spin" />
                </div>
                <div className="p-3 rounded-2xl bg-muted/50 text-xs text-secondary flex items-center gap-2">
                  <RefreshCw className="w-3 h-3 animate-spin text-indigo-500" />
                  <span>Evaluating live catalog &amp; consent firewalls...</span>
                </div>
              </div>
            )}
          </div>

          {/* Chat Input & Dynamic Contextual Buttons Area */}
          <div className="p-4 border-t border-border/80 bg-surface/90 dark:bg-zinc-900/90 space-y-2.5 shrink-0">
            
            {/* Contextual Action Buttons based on Result & Prompt */}
            <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none pb-1">
              {contextualActionButtons.map((btn, idx) => {
                const IconComponent = btn.icon;
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleActionClick(btn.action)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer flex items-center gap-1.5 border shadow-2xs ${
                      btn.variant === 'gradient'
                        ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white border-transparent shadow-sm hover:opacity-95'
                        : btn.variant === 'razorpay'
                        ? 'bg-[#0C2340] hover:bg-[#143560] text-white border-[#3395FF]/40 shadow-sm'
                        : btn.variant === 'emerald'
                        ? 'bg-emerald-600 hover:bg-emerald-700 text-white border-emerald-600 shadow-sm'
                        : btn.variant === 'rose'
                        ? 'bg-rose-500/10 hover:bg-rose-500 text-rose-600 hover:text-white border-rose-500/20'
                        : btn.variant === 'amber'
                        ? 'bg-amber-500/10 hover:bg-amber-500 text-amber-600 hover:text-white border-amber-500/20'
                        : btn.variant === 'indigo'
                        ? 'bg-indigo-600 text-white hover:bg-indigo-700 border-indigo-600 shadow-xs'
                        : 'bg-muted/70 hover:bg-indigo-600 hover:text-white text-secondary hover:text-primary border-border/70'
                    }`}
                  >
                    {IconComponent && <IconComponent className="w-3.5 h-3.5" />}
                    <span>{btn.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Chat Input Bar */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (inputMessage.trim() && !loading) {
                  sendMessage(inputMessage);
                  setInputMessage('');
                }
              }}
              className="flex items-end gap-2"
            >
              <textarea
                rows={1}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (inputMessage.trim() && !loading) {
                      sendMessage(inputMessage);
                      setInputMessage('');
                    }
                  }
                }}
                placeholder={`Ask ${roleConfig.roleTitle}...`}
                className="flex-1 max-h-32 min-h-[46px] py-3 px-4 rounded-2xl bg-background border border-border/80 text-sm text-primary placeholder:text-secondary focus:outline-none focus:border-indigo-500 resize-none leading-relaxed transition-all"
              />

              <button
                type="button"
                onClick={toggleListening}
                className={`p-3 rounded-2xl border transition cursor-pointer shrink-0 ${
                  isListening
                    ? 'bg-rose-500 text-white border-rose-600 animate-pulse'
                    : 'bg-muted border-border/80 text-secondary hover:text-primary'
                }`}
                title={isListening ? 'Stop listening' : 'Voice search'}
              >
                {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>

              <button
                type="submit"
                disabled={loading || !inputMessage.trim()}
                className="p-3 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-40 transition cursor-pointer shadow-md shrink-0"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>

        </div>

      </div>

      {/* ── POLICY CONFIGURATION MODAL ── */}
      {showPolicyModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in">
          <div className="w-full max-w-md rounded-3xl bg-surface border border-border p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-black text-primary">Configure Consent Limits</h3>
              <button
                onClick={() => setShowPolicyModal(false)}
                className="text-secondary hover:text-primary cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handlePolicySubmit} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="font-bold text-secondary">Auto-Approve Threshold (₹)</label>
                <input
                  type="number"
                  value={policyForm.approval_threshold}
                  onChange={(e) =>
                    setPolicyForm({ ...policyForm, approval_threshold: Number(e.target.value) })
                  }
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary"
                />
              </div>

              <div className="space-y-1">
                <label className="font-bold text-secondary">Per-Transaction Hard Limit (₹)</label>
                <input
                  type="number"
                  value={policyForm.per_transaction_limit}
                  onChange={(e) =>
                    setPolicyForm({ ...policyForm, per_transaction_limit: Number(e.target.value) })
                  }
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary"
                />
              </div>

              <div className="space-y-1">
                <label className="font-bold text-secondary">Daily Spending Limit (₹)</label>
                <input
                  type="number"
                  value={policyForm.daily_limit}
                  onChange={(e) =>
                    setPolicyForm({ ...policyForm, daily_limit: Number(e.target.value) })
                  }
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowPolicyModal(false)}
                  className="px-4 py-2 rounded-xl border border-border text-secondary cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-indigo-600 text-white font-bold cursor-pointer"
                >
                  Save Policy
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── RAZORPAY CHECKOUT POPUP MODAL ── */}
      {showRazorpayModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-md p-4 animate-in fade-in duration-200 pointer-events-auto">
          <div className="relative w-full max-w-md rounded-3xl border border-border/80 bg-surface p-6 shadow-2xl space-y-4">
            <button
              type="button"
              onClick={() => {
                setShowRazorpayModal(false);
                setIsProcessingRazorpay(false);
              }}
              className="absolute right-4 top-4 rounded-xl p-1.5 text-secondary hover:bg-muted hover:text-primary transition-colors cursor-pointer"
            >
              ✕
            </button>

            {/* Header with Razorpay Logo */}
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#0C2340] text-white font-black text-xl shadow-md">
                <span className="text-[#3395FF]">R</span>
              </div>
              <div>
                <h3 className="text-base font-black text-primary">Razorpay Checkout</h3>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#3395FF]/10 text-[#3395FF] border border-[#3395FF]/25">
                    RazorHub Gateway
                  </span>
                  <span className="text-[11px] text-secondary">Live/Sandbox Mode</span>
                </div>
              </div>
            </div>

            {/* Payable Amount Box */}
            <div className="rounded-2xl border border-border/80 bg-muted/40 p-4 text-center space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-secondary">Payable Amount</span>
              <p className="text-3xl font-black text-primary">₹{razorpayAmount.toLocaleString('en-IN')}</p>
              <p className="text-xs text-secondary">Order ID: #{razorpayOrderId}</p>
            </div>

            {/* Payment Method Selector */}
            <div className="space-y-2">
              <p className="text-xs font-bold text-secondary uppercase tracking-wider">Select Payment Method</p>

              <button
                type="button"
                onClick={() => setSelectedPaymentMethod('upi')}
                className={`flex w-full items-center justify-between rounded-2xl border p-3 text-left transition-all cursor-pointer ${
                  selectedPaymentMethod === 'upi'
                    ? 'border-indigo-500 bg-indigo-500/10 ring-1 ring-indigo-500'
                    : 'border-border/80 bg-background hover:bg-muted/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-xl">📱</span>
                  <div>
                    <p className="text-xs font-bold text-primary">UPI (Google Pay / PhonePe / Paytm)</p>
                    <p className="text-[11px] text-secondary">Test VPA: <code className="bg-muted px-1 rounded">success@razorpay</code></p>
                  </div>
                </div>
                <div className="flex h-4 w-4 items-center justify-center rounded-full border border-border">
                  {selectedPaymentMethod === 'upi' && <div className="h-2 w-2 rounded-full bg-indigo-600" />}
                </div>
              </button>

              <button
                type="button"
                onClick={() => setSelectedPaymentMethod('card')}
                className={`flex w-full items-center justify-between rounded-2xl border p-3 text-left transition-all cursor-pointer ${
                  selectedPaymentMethod === 'card'
                    ? 'border-indigo-500 bg-indigo-500/10 ring-1 ring-indigo-500'
                    : 'border-border/80 bg-background hover:bg-muted/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-xl">💳</span>
                  <div>
                    <p className="text-xs font-bold text-primary">Credit / Debit Card</p>
                    <p className="text-[11px] text-secondary">Visa, Mastercard, RuPay (Test: 4242 4242 4242)</p>
                  </div>
                </div>
                <div className="flex h-4 w-4 items-center justify-center rounded-full border border-border">
                  {selectedPaymentMethod === 'card' && <div className="h-2 w-2 rounded-full bg-indigo-600" />}
                </div>
              </button>

              <button
                type="button"
                onClick={() => setSelectedPaymentMethod('netbanking')}
                className={`flex w-full items-center justify-between rounded-2xl border p-3 text-left transition-all cursor-pointer ${
                  selectedPaymentMethod === 'netbanking'
                    ? 'border-indigo-500 bg-indigo-500/10 ring-1 ring-indigo-500'
                    : 'border-border/80 bg-background hover:bg-muted/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-xl">🏦</span>
                  <div>
                    <p className="text-xs font-bold text-primary">NetBanking</p>
                    <p className="text-[11px] text-secondary">HDFC, ICICI, SBI, Axis, Kotak</p>
                  </div>
                </div>
                <div className="flex h-4 w-4 items-center justify-center rounded-full border border-border">
                  {selectedPaymentMethod === 'netbanking' && <div className="h-2 w-2 rounded-full bg-indigo-600" />}
                </div>
              </button>
            </div>

            {/* Action Buttons */}
            <div className="space-y-2 pt-2">
              <button
                type="button"
                disabled={isProcessingRazorpay}
                onClick={handleCompleteRazorpayPayment}
                className="w-full py-3 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:opacity-95 text-white text-xs font-black shadow-lg shadow-indigo-600/25 transition cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isProcessingRazorpay ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Verifying Payment with Razorpay...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4" />
                    <span>Pay ₹{razorpayAmount.toLocaleString('en-IN')} via Razorpay</span>
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={handleCopyRazorpayLink}
                className="w-full py-2.5 rounded-2xl border border-border/80 text-xs font-bold text-secondary hover:text-primary hover:bg-muted transition cursor-pointer flex items-center justify-center gap-1.5"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>{linkCopied ? '✓ Payment Link Copied to Clipboard!' : 'Copy Razorpay Direct Payment Link'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
