import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  Mail,
  MessageSquare,
  ShieldQuestion,
  Search,
  BookOpen,
  ChevronDown,
  ShoppingBag,
  Store,
  Building2,
  Shield,
  LifeBuoy,
  FileText,
  Clock,
  ExternalLink,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';

interface FAQItem {
  question: string;
  answer: string;
  category: 'customer' | 'seller' | 'banking' | 'security';
}

const FAQS: FAQItem[] = [
  // Customer FAQs
  {
    category: 'customer',
    question: 'How do I place an order and what payment methods are accepted?',
    answer:
      'Browse our catalog or use our AI Shopping Assistant to select items. Add them to your cart and proceed to checkout. RazorHub supports 100+ payment methods including Razorpay (UPI, Google Pay, PhonePe, NetBanking, Credit/Debit cards) as well as Cash on Delivery (COD) for eligible pincodes.',
  },
  {
    category: 'customer',
    question: 'How can I track my order delivery in real time?',
    answer:
      'After completing your purchase, visit your Customer Dashboard (/dashboard) and click "My Orders". You can inspect real-time fulfillment stages: Pending, Processing, Shipped, and Delivered, complete with tracking identifiers.',
  },
  {
    category: 'customer',
    question: 'What is the return and refund turnaround time?',
    answer:
      'Refunds are processed automatically via Razorpay upon seller return approval. UPI and NetBanking refunds credit to your original payment method within 2 to 4 business hours. Credit/Debit card refunds typically reflect within 3–5 business days.',
  },
  {
    category: 'customer',
    question: 'How does the AI Shopping Assistant help me find products?',
    answer:
      'Our AI Assistant (/ai) understands conversational search prompts such as "Find budget gaming laptops under ₹60,000" or "Organic cold-pressed oils". It filters live catalog inventory, checks verified stock levels, and generates direct checkout links.',
  },

  // Seller FAQs
  {
    category: 'seller',
    question: 'How do I onboard as a seller on RazorHub?',
    answer:
      'Sign up for an account, switch your role or navigate to Seller Central (/seller). Complete your store profile with GST/PAN details and business address. Once verified by our administration team, your storefront goes live immediately.',
  },
  {
    category: 'seller',
    question: 'How do I add and manage catalog products?',
    answer:
      'From the Seller Central (/seller/products), click "+ Add Catalog Product". Provide the title, category, pricing, inventory stock, specifications, and primary image. Your product syncs instantly across our global storefront and AI search embeddings.',
  },
  {
    category: 'seller',
    question: 'How are seller payouts disbursed and tracked?',
    answer:
      'Merchant balances from fulfilled customer orders are settled directly via our Agentic Business Banking layer. You can view pending receivables, ledger credits, and disbursement references with automated UTR generation.',
  },

  // Banking FAQs
  {
    category: 'banking',
    question: 'What is the Agentic Business Banking suite?',
    answer:
      'Our Business Banking suite (/banking) provides autonomous financial intelligence: an automated debtor receivables agent, verified vendor disbursements with governance limits, automated double-entry bookkeeping, and real-time cash runway forecasting.',
  },
  {
    category: 'banking',
    question: 'How does human-in-the-loop governance protect disbursements?',
    answer:
      'Autonomous payout agents cannot disburse funds unconditionally. High-value transactions or risk-flagged invoices trigger an interactive Human Approval card requiring explicit authorization by a finance administrator before execution.',
  },
  {
    category: 'banking',
    question: 'How does the Explainable Financial Risk Engine work?',
    answer:
      'The Risk Engine (/risk-engine) evaluates transactions across 11 deterministic dimensions including transaction velocity, device mismatch, impossible travel, and customer dispute history, generating transparent 0–100 risk scores that cannot be overridden by unrestricted LLMs.',
  },

  // Security FAQs
  {
    category: 'security',
    question: 'How are API keys and financial credentials protected?',
    answer:
      'All agent execution telemetry is routed through a zero-trust SecretScrubber before being saved to audit logs or database tables. API tokens, webhook secrets, and private credentials are automatically redacted with cryptographic masking.',
  },
  {
    category: 'security',
    question: 'How is user data protected under DPDP and privacy standards?',
    answer:
      'User data is encrypted at rest and in transit via TLS 1.3. We adhere strictly to data minimization standards. Users can inspect their communication consent, opt-out preferences, or request account deletion directly from settings.',
  },
];

export default function HelpPage() {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'customer' | 'seller' | 'banking' | 'security'>('all');
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const filteredFaqs = useMemo(() => {
    return FAQS.filter((faq) => {
      const matchCat = selectedCategory === 'all' || faq.category === selectedCategory;
      const q = searchQuery.toLowerCase();
      const matchQuery =
        !q || faq.question.toLowerCase().includes(q) || faq.answer.toLowerCase().includes(q);
      return matchCat && matchQuery;
    });
  }, [searchQuery, selectedCategory]);

  return (
    <div className="min-h-screen bg-background text-primary pb-20 font-sans transition-colors">
      
      {/* ── Hero Banner ── */}
      <div className="border-b border-border bg-gradient-to-b from-surface via-surface to-background/50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-accent/10 text-accent border border-accent/20">
            <LifeBuoy className="w-3.5 h-3.5" />
            <span>RazorHub Support &amp; Knowledge Center</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-primary">
            How can we help you today?
          </h1>
          <p className="text-sm text-secondary max-w-2xl mx-auto">
            Search our comprehensive guides, explore answers across shopping, merchant tools, and autonomous banking, or contact our dedicated support specialists.
          </p>

          {/* Search Input */}
          <div className="relative max-w-xl mx-auto mt-6">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-secondary" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search answers (e.g. tracking, refunds, seller payout, risk engine)..."
              className="w-full h-12 rounded-2xl border border-border bg-surface pl-11 pr-4 text-sm text-primary placeholder:text-secondary/70 shadow-md focus:border-accent focus:outline-none transition-all"
            />
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 pt-10 space-y-10">

        {/* ── Category Filter Pills ── */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none justify-start sm:justify-center">
          {[
            { id: 'all', label: 'All FAQs', icon: ShieldQuestion },
            { id: 'customer', label: 'Customers & Orders', icon: ShoppingBag },
            { id: 'seller', label: 'Sellers & Merchants', icon: Store },
            { id: 'banking', label: 'Agentic Banking & Treasury', icon: Building2 },
            { id: 'security', label: 'Security & Privacy', icon: Shield },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = selectedCategory === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => {
                  setSelectedCategory(tab.id as any);
                  setOpenIndex(null);
                }}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-2xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
                  isActive
                    ? 'bg-accent text-white shadow-md shadow-accent/20'
                    : 'bg-surface border border-border text-secondary hover:text-primary hover:bg-muted'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* ── FAQ Accordion List ── */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-black text-primary">
              Frequently Asked Questions ({filteredFaqs.length})
            </h2>
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="text-xs text-accent font-bold hover:underline cursor-pointer"
              >
                Clear Search
              </button>
            )}
          </div>

          {filteredFaqs.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-border bg-surface/50 p-12 text-center space-y-3">
              <ShieldQuestion className="h-10 w-10 text-secondary/40 mx-auto" />
              <h3 className="font-bold text-primary">No results found for "{searchQuery}"</h3>
              <p className="text-xs text-secondary max-w-sm mx-auto">
                Try searching for broader keywords or contact our team directly via email or ticketing.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredFaqs.map((faq, idx) => {
                const isOpen = openIndex === idx;
                return (
                  <div
                    key={idx}
                    className="rounded-2xl border border-border bg-surface transition-all overflow-hidden shadow-2xs"
                  >
                    <button
                      type="button"
                      onClick={() => setOpenIndex(isOpen ? null : idx)}
                      className="w-full flex items-center justify-between p-5 text-left transition-colors hover:bg-muted/30"
                    >
                      <span className="text-sm font-bold text-primary pr-4">
                        {faq.question}
                      </span>
                      <ChevronDown
                        className={`h-4 w-4 shrink-0 text-secondary transition-transform duration-200 ${
                          isOpen ? 'rotate-180 text-accent' : ''
                        }`}
                      />
                    </button>
                    {isOpen && (
                      <div className="px-5 pb-5 text-xs sm:text-sm text-secondary leading-relaxed border-t border-border/50 pt-3 bg-muted/10 animate-in fade-in">
                        {faq.answer}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* ── Direct Support Channels ── */}
        <div className="pt-6 border-t border-border">
          <div className="mb-6">
            <h3 className="text-lg font-black text-primary">Still need assistance?</h3>
            <p className="text-xs text-secondary mt-1">
              Our engineering, merchant onboarding, and customer care teams are available 24/7.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            {/* Email Support */}
            <div className="rounded-2xl border border-border bg-surface p-5 shadow-xs flex flex-col justify-between">
              <div>
                <div className="p-3 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 w-fit mb-3">
                  <Mail className="h-5 w-5" />
                </div>
                <h4 className="text-sm font-bold text-primary">Customer Care</h4>
                <p className="text-xs text-secondary mt-1">For order queries, refunds, and payments assistance.</p>
              </div>
              <a
                href="mailto:support@razorhub.in"
                className="mt-4 text-xs font-bold text-accent hover:underline flex items-center gap-1"
              >
                support@razorhub.in <ExternalLink className="h-3 w-3" />
              </a>
            </div>

            {/* Official Communications */}
            <div className="rounded-2xl border border-border bg-surface p-5 shadow-xs flex flex-col justify-between">
              <div>
                <div className="p-3 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 w-fit mb-3">
                  <MessageSquare className="h-5 w-5" />
                </div>
                <h4 className="text-sm font-bold text-primary">Official Office</h4>
                <p className="text-xs text-secondary mt-1">Merchant licensing, partnership, and corporate treasury inquiries.</p>
              </div>
              <a
                href="mailto:razorhubofficial@gmail.com"
                className="mt-4 text-xs font-bold text-accent hover:underline flex items-center gap-1 truncate"
              >
                razorhubofficial@gmail.com <ExternalLink className="h-3 w-3 shrink-0" />
              </a>
            </div>

            {/* CRM Tickets */}
            <div className="rounded-2xl border border-border bg-surface p-5 shadow-xs flex flex-col justify-between">
              <div>
                <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 w-fit mb-3">
                  <FileText className="h-5 w-5" />
                </div>
                <h4 className="text-sm font-bold text-primary">Support Tickets</h4>
                <p className="text-xs text-secondary mt-1">Track priority tickets and live resolutions in your dashboard.</p>
              </div>
              <Link
                to={user ? '/dashboard/tickets' : '/login'}
                className="mt-4 text-xs font-bold text-accent hover:underline flex items-center gap-1"
              >
                Open Ticket Desk →
              </Link>
            </div>
          </div>
        </div>

        {/* ── Link to Documentation Banner ── */}
        <div className="rounded-3xl border border-indigo-500/20 bg-gradient-to-r from-indigo-950/20 via-surface to-purple-950/20 p-6 sm:p-8 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="space-y-1 text-center sm:text-left">
            <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
              Developer &amp; Architecture Documentation
            </span>
            <h3 className="text-lg sm:text-xl font-black text-primary">
              Looking for technical integration guides &amp; APIs?
            </h3>
            <p className="text-xs text-secondary">
              Review full architecture blueprints, MCP connectors, Agentic Banking workflows, and Risk Engine algorithms.
            </p>
          </div>
          <Link
            to="/docs"
            className="flex items-center gap-2 rounded-2xl bg-indigo-600 hover:bg-indigo-700 px-5 py-3 text-xs font-bold text-white shadow-md shadow-indigo-500/25 transition-all shrink-0 cursor-pointer"
          >
            <BookOpen className="h-4 w-4" />
            <span>Browse Full Documentation</span>
          </Link>
        </div>

      </div>
    </div>
  );
}

