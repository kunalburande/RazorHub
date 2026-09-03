import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Layers,
  Search,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Zap,
  Shield,
  ShieldCheck,
  Send,
  CreditCard,
  Building2,
  BookOpen,
  Mail,
  MessageSquare,
  BarChart3,
  Truck,
  ExternalLink,
  ArrowRight,
  Terminal,
  Play,
  Check,
  Bot,
} from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';

interface Connector {
  id: string;
  name: string;
  slug: string;
  connector_type: string;
  description: string;
  status: string;
  is_mock: boolean;
  version: string;
  capabilities: Array<{
    id: string;
    capability: string;
    name: string;
    description: string;
  }>;
  active_agents_count: number;
}

export default function AgentConnectorsPage() {
  const { token } = useAuth();
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState('ALL');

  // Interactive Sandbox State
  const [activeConnector, setActiveConnector] = useState<Connector | null>(null);
  const [selectedCapability, setSelectedCapability] = useState('READ');
  const [actionName, setActionName] = useState('get_products');
  const [testParamsJson, setTestParamsJson] = useState('{}');
  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [executionError, setExecutionError] = useState<string | null>(null);

  useEffect(() => {
    loadConnectors();
  }, [token]);

  const loadConnectors = async () => {
    try {
      setLoading(true);
      const res = await apiRequest<any>('/agent-runtime/connectors/', { token });
      const list = Array.isArray(res) ? res : res.results || [];
      setConnectors(list);
      if (list.length > 0 && !activeConnector) {
        setActiveConnector(list[0]);
        if (list[0].capabilities.length > 0) {
          setSelectedCapability(list[0].capabilities[0].capability);
        }
      }
    } catch (err: any) {
      console.error('Failed to load connectors', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectConnector = (conn: Connector) => {
    setActiveConnector(conn);
    setExecutionResult(null);
    setExecutionError(null);
    if (conn.capabilities.length > 0) {
      setSelectedCapability(conn.capabilities[0].capability);
    }
    // Set smart action defaults
    if (conn.slug === 'mock-commerce') {
      setActionName('get_products');
      setTestParamsJson('{}');
    } else if (conn.slug === 'mock-payment') {
      setActionName('create_payment_intent');
      setTestParamsJson('{"amount": 4999.0}');
    } else if (conn.slug === 'mock-banking') {
      setActionName('get_balance');
      setTestParamsJson('{}');
    } else if (conn.slug === 'mock-accounting') {
      setActionName('get_chart_of_accounts');
      setTestParamsJson('{}');
    } else if (conn.slug === 'mock-email') {
      setActionName('send_email');
      setTestParamsJson('{"recipient": "finance@client.test", "subject": "Quarterly Statement"}');
    } else if (conn.slug === 'mock-whatsapp') {
      setActionName('send_whatsapp_message');
      setTestParamsJson('{"phone": "+919876543210", "template": "invoice_reminder"}');
    } else {
      setActionName('test_ping');
      setTestParamsJson('{}');
    }
  };

  const handleTestExecute = async () => {
    if (!activeConnector) return;
    try {
      setExecuting(true);
      setExecutionResult(null);
      setExecutionError(null);

      let parsedParams = {};
      try {
        parsedParams = JSON.parse(testParamsJson);
      } catch (e) {
        setExecutionError('Invalid JSON parameters.');
        setExecuting(false);
        return;
      }

      const res = await apiRequest<any>(`/agent-runtime/connectors/${activeConnector.id}/test_execute/`, {
        token,
        method: 'POST',
        body: JSON.stringify({
          capability: selectedCapability,
          action: actionName,
          params: parsedParams,
        }),
      });

      if (res.success) {
        setExecutionResult(res.result);
      } else {
        setExecutionError(res.error || 'Execution failed');
      }
    } catch (err: any) {
      setExecutionError(err.message || 'Execution error');
    } finally {
      setExecuting(false);
    }
  };

  const getConnectorIcon = (type: string) => {
    switch (type) {
      case 'PaymentGateway':
        return <CreditCard className="w-5 h-5 text-indigo-500" />;
      case 'Commerce':
        return <Zap className="w-5 h-5 text-emerald-500" />;
      case 'Banking':
        return <Building2 className="w-5 h-5 text-cyan-500" />;
      case 'Accounting':
        return <BookOpen className="w-5 h-5 text-amber-500" />;
      case 'Communication':
        return <Mail className="w-5 h-5 text-purple-500" />;
      case 'Analytics':
        return <BarChart3 className="w-5 h-5 text-blue-500" />;
      default:
        return <Layers className="w-5 h-5 text-secondary" />;
    }
  };

  const filteredConnectors = connectors.filter((c) => {
    const matchesSearch =
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.connector_type.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = selectedType === 'ALL' || c.connector_type === selectedType;
    return matchesSearch && matchesType;
  });

  const uniqueTypes = ['ALL', 'PaymentGateway', 'Commerce', 'Banking', 'Accounting', 'Communication', 'Analytics'];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* ── Top Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link to="/agents" className="text-xs font-bold text-secondary hover:text-primary transition">
              Agent Studio
            </Link>
            <span className="text-secondary text-xs">/</span>
            <span className="text-xs font-bold text-indigo-600">Connectors Architecture</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-primary flex items-center gap-3">
            <Layers className="w-8 h-8 text-indigo-600" />
            Integrations & Connector Registry
          </h1>
          <p className="text-xs sm:text-sm text-secondary mt-1 max-w-3xl">
            Standardized interfaces for Payment Gateways, Commerce Engines, Business Banking, Accounting, and Communications. Agents require explicit authorization to invoke each connector.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/agents"
            className="px-4 py-2.5 rounded-2xl bg-surface hover:bg-muted border border-border text-xs font-bold text-primary transition"
          >
            ← Back to Agents
          </Link>
        </div>
      </div>

      {/* ── Filter Bar & Type Chips ── */}
      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-secondary absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search connectors or capabilities..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-2xl bg-surface border border-border text-xs text-primary placeholder:text-secondary focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none w-full md:w-auto">
          {uniqueTypes.map((t) => (
            <button
              key={t}
              onClick={() => setSelectedType(t)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer ${
                selectedType === t
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-surface border border-border text-secondary hover:text-primary'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* ── Main Layout: Connector Cards Grid + Live Sandbox ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Connector Catalog (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-black uppercase tracking-wider text-secondary">
              Registered Connectors ({filteredConnectors.length})
            </h2>
            <span className="text-[11px] text-secondary">Zero-Trust Scoping Enforced</span>
          </div>

          {loading ? (
            <div className="p-12 text-center text-secondary flex flex-col items-center gap-2">
              <RefreshCw className="w-6 h-6 animate-spin text-indigo-600" />
              <span className="text-xs font-bold">Discovering Connectors...</span>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3.5">
              {filteredConnectors.map((c) => {
                const isSelected = activeConnector?.id === c.id;
                return (
                  <div
                    key={c.id}
                    onClick={() => handleSelectConnector(c)}
                    className={`p-5 rounded-3xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-surface border-2 border-indigo-600 shadow-md ring-2 ring-indigo-500/20'
                        : 'bg-surface border-border hover:border-indigo-500/50 hover:shadow-xs'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-2xl bg-muted flex items-center justify-center shrink-0">
                          {getConnectorIcon(c.connector_type)}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="text-sm font-black text-primary">{c.name}</h3>
                            {c.is_mock ? (
                              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-500/15 text-amber-600 border border-amber-500/30">
                                MOCK SANDBOX
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-indigo-500/15 text-indigo-600 border border-indigo-500/30">
                                EXTERNAL API
                              </span>
                            )}
                          </div>
                          <span className="text-[11px] font-mono text-secondary">{c.connector_type} • v{c.version}</span>
                        </div>
                      </div>

                      <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600 border border-emerald-500/30 flex items-center gap-1 shrink-0">
                        <CheckCircle2 className="w-3 h-3" /> ACTIVE
                      </span>
                    </div>

                    <p className="text-xs text-secondary mt-3 leading-relaxed">{c.description}</p>

                    {/* Capability Badges */}
                    <div className="mt-4 pt-3 border-t border-border/60 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex flex-wrap gap-1">
                        {c.capabilities?.map((cap, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 rounded-md text-[10px] font-black font-mono bg-muted text-primary"
                          >
                            {cap.capability}
                          </span>
                        ))}
                      </div>

                      <span className="text-[11px] text-secondary flex items-center gap-1 font-medium">
                        <Bot className="w-3.5 h-3.5 text-indigo-500" />
                        {c.active_agents_count || 0} Linked Agents
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Live Testing Sandbox (5 cols) */}
        <div className="lg:col-span-5 sticky top-6">
          <div className="p-6 rounded-3xl bg-surface border border-border shadow-xl space-y-6">
            <div className="flex items-center justify-between border-b border-border pb-4">
              <div className="flex items-center gap-2.5">
                <Terminal className="w-5 h-5 text-indigo-600" />
                <h3 className="text-sm font-black text-primary">Connector Test Sandbox</h3>
              </div>
              {activeConnector && (
                <span className="text-xs font-mono font-bold text-indigo-600 bg-indigo-500/10 px-2.5 py-1 rounded-xl">
                  {activeConnector.slug}
                </span>
              )}
            </div>

            {activeConnector ? (
              <div className="space-y-4">
                {/* Capability Selector */}
                <div>
                  <label className="block text-xs font-bold text-secondary mb-1.5">Capability Type</label>
                  <div className="grid grid-cols-3 gap-1.5">
                    {activeConnector.capabilities?.map((cap, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => setSelectedCapability(cap.capability)}
                        className={`px-3 py-2 rounded-xl text-xs font-mono font-bold transition cursor-pointer ${
                          selectedCapability === cap.capability
                            ? 'bg-indigo-600 text-white shadow-sm'
                            : 'bg-muted/70 text-secondary hover:text-primary'
                        }`}
                      >
                        {cap.capability}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Action Name */}
                <div>
                  <label className="block text-xs font-bold text-secondary mb-1">Target Action</label>
                  <input
                    type="text"
                    value={actionName}
                    onChange={(e) => setActionName(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl bg-background border border-border text-xs font-mono text-primary focus:outline-none focus:border-indigo-500"
                    placeholder="e.g. get_products, create_payout"
                  />
                </div>

                {/* Input Parameters JSON */}
                <div>
                  <label className="block text-xs font-bold text-secondary mb-1">JSON Payload (Params)</label>
                  <textarea
                    rows={4}
                    value={testParamsJson}
                    onChange={(e) => setTestParamsJson(e.target.value)}
                    className="w-full p-3 rounded-xl bg-background border border-border text-xs font-mono text-primary focus:outline-none focus:border-indigo-500"
                    placeholder="{}"
                  />
                </div>

                {/* Run Button */}
                <button
                  type="button"
                  disabled={executing}
                  onClick={handleTestExecute}
                  className="w-full py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white font-black text-xs shadow-md transition cursor-pointer flex items-center justify-center gap-2 active:scale-98 disabled:opacity-50"
                >
                  {executing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
                  <span>Execute Connector Capability</span>
                </button>

                {/* Error Banner */}
                {executionError && (
                  <div className="p-3.5 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 text-xs flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    <span>{executionError}</span>
                  </div>
                )}

                {/* Result Output */}
                {executionResult && (
                  <div className="p-4 rounded-2xl bg-background border border-border space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-bold text-emerald-600 flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> 200 OK — Execution Response
                      </span>
                      <span className="text-[10px] font-mono text-secondary">Logged in ConnectorExecution</span>
                    </div>
                    <pre className="text-[11px] font-mono text-primary overflow-x-auto p-2.5 rounded-xl bg-muted/40 max-h-52">
                      {JSON.stringify(executionResult, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-secondary text-center py-8">Select a connector from the list to test.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
