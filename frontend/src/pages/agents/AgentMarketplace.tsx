import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ShoppingBag,
  Sparkles,
  Bot,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  RefreshCw,
  Search,
  Check,
  Download,
  ExternalLink,
  Wrench,
  Sliders,
  CreditCard,
  Building2,
  FileText,
  DollarSign,
  TrendingUp,
  AlertCircle,
  HelpCircle,
  Zap,
} from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';

export interface MarketplaceTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  automation_level: 'AUTONOMOUS' | 'SEMI_AUTONOMOUS' | 'HUMAN_IN_THE_LOOP';
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  approval_mode: string;
  capabilities: string[];
  tools_used: string[];
  system_prompt: string;
  is_installed: boolean;
  installed_agent_id?: string | null;
  governance_policy?: {
    max_transaction_amount?: string | number;
    daily_spend_limit?: string | number;
    require_approval_above?: string | number;
    require_double_confirmation?: boolean;
  };
}

export default function AgentMarketplace() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<MarketplaceTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [installingId, setInstallingId] = useState<string | null>(null);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);
  const [errorNotice, setErrorNotice] = useState<string | null>(null);

  const fetchMarketplace = async () => {
    setLoading(true);
    try {
      const data = await apiRequest<MarketplaceTemplate[]>('/agent-runtime/agents/marketplace/', { token });
      setTemplates(Array.isArray(data) ? data : []);
    } catch (err: any) {
      console.error('Failed to load marketplace templates:', err);
      setErrorNotice(err.message || 'Failed to load agent marketplace');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMarketplace();
  }, [token]);

  const handleInstall = async (tmpl: MarketplaceTemplate) => {
    setInstallingId(tmpl.id);
    setErrorNotice(null);
    setSuccessNotice(null);
    try {
      const res = await apiRequest<any>('/agent-runtime/agents/install/', {
        token,
        method: 'POST',
        body: JSON.stringify({
          template_id: tmpl.id,
          auto_activate: true,
        }),
      });

      setSuccessNotice(`Agent '${tmpl.name}' installed and activated successfully!`);
      setTimeout(() => setSuccessNotice(null), 4000);

      // Refresh list to update installed status
      await fetchMarketplace();
    } catch (err: any) {
      setErrorNotice(err.message || 'Failed to install agent.');
    } finally {
      setInstallingId(null);
    }
  };

  const categories = [
    'ALL',
    'PAYMENTS',
    'CUSTOMERS',
    'REFUNDS',
    'ANALYTICS',
    'INVOICES',
    'PAYOUTS',
    'BANKING',
    'RISK',
  ];

  const filtered = templates.filter((t) => {
    const matchesCat = selectedCategory === 'ALL' || t.category.toUpperCase() === selectedCategory;
    const matchesSearch =
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.tools_used.some((tool) => tool.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCat && matchesSearch;
  });

  const getRiskBadge = (level: string) => {
    switch (level.toUpperCase()) {
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30">
            <ShieldAlert className="w-3 h-3" />
            CRITICAL RISK
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
            <AlertTriangle className="w-3 h-3" />
            HIGH RISK
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30">
            <ShieldCheck className="w-3 h-3" />
            MEDIUM RISK
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
            <ShieldCheck className="w-3 h-3" />
            LOW RISK
          </span>
        );
    }
  };

  const getAutomationBadge = (level: string) => {
    switch (level) {
      case 'AUTONOMOUS':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
            <Zap className="w-3 h-3" />
            Fully Autonomous
          </span>
        );
      case 'SEMI_AUTONOMOUS':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-purple-500/15 text-purple-600 dark:text-purple-400 border border-purple-500/20">
            <Sliders className="w-3 h-3" />
            Semi-Autonomous
          </span>
        );
      case 'HUMAN_IN_THE_LOOP':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/20">
            <AlertCircle className="w-3 h-3" />
            Human in the Loop
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-8 pb-16">
      
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-950 text-white p-8 sm:p-10 shadow-xl border border-indigo-500/20">
        <div className="absolute right-0 top-0 w-96 h-96 bg-indigo-500/15 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-cyan-400">
            <Sparkles className="w-4 h-4" />
            Verified Prebuilt Agents Registry
          </div>
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight">
            Agent Marketplace
          </h1>
          <p className="text-sm sm:text-base text-gray-300">
            Discover and install enterprise-grade AI agents tuned for financial operations, dunning orchestration, and automated reconciliation. Installing directly provisions a dedicated runtime configuration with zero-trust guardrails.
          </p>
        </div>

        <div className="mt-6 flex items-center gap-4 text-xs text-gray-400">
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            8 Production-Ready Agent Templates
          </span>
          <span>•</span>
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            Deterministic Policy Enforced
          </span>
        </div>
      </div>

      {/* Notifications */}
      {successNotice && (
        <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 text-sm flex items-center gap-3 animate-in fade-in">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <div className="flex-1 font-medium">{successNotice}</div>
          <Link
            to="/agents"
            className="text-xs font-bold text-emerald-700 dark:text-emerald-300 underline hover:opacity-80"
          >
            Go to My Agents →
          </Link>
        </div>
      )}

      {errorNotice && (
        <div className="p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200 text-sm flex items-center gap-3 animate-in fade-in">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <span>{errorNotice}</span>
        </div>
      )}

      {/* Search & Category Filter Bar */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by agent name, capability, or tool..."
              className="w-full pl-10 pr-4 py-2.5 rounded-2xl border border-border bg-surface text-primary text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition"
            />
          </div>

          <div className="text-xs text-secondary font-medium">
            Showing <strong className="text-primary">{filtered.length}</strong> of {templates.length} templates
          </div>
        </div>

        {/* Category Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                selectedCategory === cat
                  ? 'bg-primary text-surface shadow-sm'
                  : 'bg-surface hover:bg-muted text-secondary hover:text-primary border border-border'
              }`}
            >
              {cat === 'ALL' ? 'All Categories' : cat}
            </button>
          ))}
        </div>
      </div>

      {/* Marketplace Cards Grid */}
      {loading ? (
        <div className="py-24 text-center space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin text-indigo-500 mx-auto" />
          <p className="text-sm text-secondary">Loading verified agent marketplace catalog...</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="py-20 text-center rounded-3xl border border-dashed border-border p-8 space-y-3">
          <Search className="w-8 h-8 text-gray-400 mx-auto" />
          <h3 className="text-base font-bold text-primary">No Matching Agents</h3>
          <p className="text-xs text-secondary">Try adjusting your search terms or category filter.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filtered.map((tmpl) => {
            const isInstalling = installingId === tmpl.id;
            return (
              <div
                key={tmpl.id}
                className="group relative rounded-3xl border border-border/80 bg-surface hover:border-indigo-500/50 hover:shadow-2xl transition-all duration-300 p-6 sm:p-7 flex flex-col justify-between"
              >
                <div>
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-3 rounded-2xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 group-hover:scale-105 transition-transform">
                        <Bot className="w-7 h-7" />
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-primary group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                          {tmpl.name}
                        </h3>
                        <span className="text-xs font-semibold text-secondary uppercase tracking-wider">
                          {tmpl.category}
                        </span>
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-1.5">
                      {getRiskBadge(tmpl.risk_level)}
                      {getAutomationBadge(tmpl.automation_level)}
                    </div>
                  </div>

                  {/* Description */}
                  <p className="text-xs sm:text-sm text-secondary leading-relaxed">
                    {tmpl.description}
                  </p>

                  {/* Capabilities List */}
                  <div className="mt-5 space-y-2">
                    <span className="text-xs font-bold text-primary uppercase tracking-wide">
                      Core Capabilities
                    </span>
                    <ul className="space-y-1.5">
                      {tmpl.capabilities.map((cap, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-xs text-secondary">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 mt-0.5 shrink-0" />
                          <span>{cap}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Tools Used */}
                  <div className="mt-5 space-y-2">
                    <span className="text-xs font-bold text-primary uppercase tracking-wide">
                      MCP Tools Connected ({tmpl.tools_used.length})
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {tmpl.tools_used.map((toolName) => (
                        <span
                          key={toolName}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-mono bg-muted text-secondary border border-border"
                        >
                          <Wrench className="w-3 h-3 text-indigo-500" />
                          {toolName}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Guardrail Policy Summary */}
                  {tmpl.governance_policy && (
                    <div className="mt-4 p-3 rounded-xl bg-gray-50 dark:bg-gray-900/60 border border-border text-[11px] text-secondary grid grid-cols-2 gap-2">
                      <div>
                        <span>Max Transaction: </span>
                        <strong className="text-primary font-mono">
                          ₹{tmpl.governance_policy.max_transaction_amount || '0'}
                        </strong>
                      </div>
                      <div>
                        <span>Approval Above: </span>
                        <strong className="text-primary font-mono">
                          ₹{tmpl.governance_policy.require_approval_above || '0'}
                        </strong>
                      </div>
                    </div>
                  )}
                </div>

                {/* Card Footer: Install / Installed Status */}
                <div className="mt-6 pt-5 border-t border-border flex items-center justify-between gap-3">
                  <div className="text-xs font-medium text-secondary">
                    {tmpl.is_installed ? (
                      <span className="inline-flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-bold">
                        <Check className="w-4 h-4" />
                        Installed & Active
                      </span>
                    ) : (
                      <span>Ready to provision</span>
                    )}
                  </div>

                  {tmpl.is_installed && tmpl.installed_agent_id ? (
                    <Link
                      to={`/agents/${tmpl.installed_agent_id}`}
                      className="px-4 py-2.5 rounded-xl text-xs font-bold bg-surface hover:bg-muted border border-border text-primary transition flex items-center gap-1.5"
                    >
                      <span>Manage Agent</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  ) : (
                    <button
                      type="button"
                      disabled={isInstalling}
                      onClick={() => handleInstall(tmpl)}
                      className="px-5 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white shadow-md shadow-indigo-600/20 transition flex items-center gap-2 cursor-pointer disabled:opacity-50"
                    >
                      {isInstalling ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Provisioning Agent...</span>
                        </>
                      ) : (
                        <>
                          <Download className="w-3.5 h-3.5" />
                          <span>Install Agent</span>
                        </>
                      )}
                    </button>
                  )}
                </div>

              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}
