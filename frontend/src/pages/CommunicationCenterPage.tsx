import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Bell,
  Mail,
  MessageSquare,
  Smartphone,
  Send,
  Shield,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Sliders,
  Check,
  X,
  Lock,
  Clock,
  ExternalLink,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { apiRequest } from '../lib/api';
import { useAuth } from '../context/AuthContext';

interface CommunicationPref {
  id: string;
  email_enabled: boolean;
  sms_enabled: boolean;
  whatsapp_enabled: boolean;
  in_app_enabled: boolean;
  telegram_enabled: boolean;
  telegram_chat_id: string;
  is_opted_out_all: boolean;
  daily_frequency_limit: number;
  quiet_hours_start: number;
  quiet_hours_end: number;
}

interface ConsentRecord {
  id: string;
  purpose: string;
  is_granted: boolean;
  granted_at: string;
  revoked_at?: string | null;
}

interface CommEvent {
  id: string;
  channel: string;
  purpose: string;
  template_name: string;
  recipient: string;
  rendered_content: string;
  status: string;
  immutable_data: any;
  blocked_reason?: string;
  duration_ms: number;
  created_at: string;
}

export default function CommunicationCenterPage() {
  const { token, user } = useAuth();
  const [pref, setPref] = useState<CommunicationPref | null>(null);
  const [consents, setConsents] = useState<ConsentRecord[]>([]);
  const [events, setEvents] = useState<CommEvent[]>([]);
  const [inAppNotifs, setInAppNotifs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [statusFeedback, setStatusFeedback] = useState<string | null>(null);

  // Test Dispatch Form
  const [testChannel, setTestChannel] = useState('IN_APP');
  const [testTemplate, setTestTemplate] = useState('payment_recovery');
  const [dispatching, setDispatching] = useState(false);
  const [dispatchResult, setDispatchResult] = useState<any>(null);

  useEffect(() => {
    loadData();
  }, [token]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [pData, cData, eData, nData] = await Promise.all([
        apiRequest<CommunicationPref>('/agent-runtime/communication/preferences/', { token }),
        apiRequest<ConsentRecord[]>('/agent-runtime/communication/consents/', { token }),
        apiRequest<CommEvent[]>('/agent-runtime/communication/events/', { token }),
        apiRequest<any>('/crm/notifications/', { token }).catch(() => []),
      ]);

      setPref(pData);
      setConsents(Array.isArray(cData) ? cData : []);
      setEvents(Array.isArray(eData) ? eData : []);
      setInAppNotifs(Array.isArray(nData) ? nData : nData.results || []);
    } catch (err: any) {
      console.error('Failed to load communication data', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePreference = async (partial: Partial<CommunicationPref>) => {
    try {
      setUpdating(true);
      const updated = await apiRequest<CommunicationPref>('/agent-runtime/communication/preferences/', {
        token,
        method: 'PATCH',
        body: JSON.stringify(partial),
      });
      setPref(updated);
      setStatusFeedback('Preferences successfully saved.');
      setTimeout(() => setStatusFeedback(null), 3000);
    } catch (err: any) {
      alert(`Update failed: ${err.message}`);
    } finally {
      setUpdating(false);
    }
  };

  const handleToggleConsent = async (purpose: string, is_granted: boolean) => {
    try {
      await apiRequest<ConsentRecord>('/agent-runtime/communication/consents/', {
        token,
        method: 'POST',
        body: JSON.stringify({ purpose, is_granted }),
      });
      await loadData();
    } catch (err: any) {
      alert(`Consent update failed: ${err.message}`);
    }
  };

  const handleTestDispatch = async () => {
    try {
      setDispatching(true);
      setDispatchResult(null);

      let sampleData: any = {};
      if (testTemplate === 'payment_recovery') {
        sampleData = {
          order_id: 'ORD-991',
          amount: 3499.0,
          payment_link: 'https://razorhub.test/checkout/991',
          discount_limit: 10,
        };
      } else if (testTemplate === 'invoice_reminder') {
        sampleData = {
          invoice_number: 'INV-204',
          amount_due: 18500.0,
          due_date: '2026-09-15',
          bank_details: 'HDFC Corporate **** 3210',
        };
      } else if (testTemplate === 'payment_confirmation') {
        sampleData = {
          transaction_id: 'TXN-777',
          amount_paid: 2499.0,
          tax_invoice_id: 'GST-777',
        };
      } else if (testTemplate === 'payout_approval') {
        sampleData = {
          payout_id: 'PO-888',
          beneficiary_name: 'Rahul Sharma',
          amount: 18500.0,
          utr_reference: 'UTR-HDFC-991',
        };
      } else if (testTemplate === 'risk_alert') {
        sampleData = {
          alert_code: 'SEC_NEW_DEVICE',
          incident_timestamp: '2026-09-03 18:35 IST',
          security_escalation_link: 'https://razorhub.test/security/lock',
        };
      } else {
        sampleData = {
          current_balance: 2845000.0,
          burn_rate: 420000.0,
          runway_months: 6.8,
          forecasted_inflow: 84200.0,
        };
      }

      const res = await apiRequest<any>('/agent-runtime/communication/send/', {
        token,
        method: 'POST',
        body: JSON.stringify({
          channel: testChannel,
          template_name: testTemplate,
          immutable_data: sampleData,
          personal_greeting: 'Greetings',
        }),
      });

      setDispatchResult(res);
      await loadData();
    } catch (err: any) {
      setDispatchResult({ success: false, reason: err.message });
    } finally {
      setDispatching(false);
    }
  };

  const getStatusBadge = (st: string) => {
    if (st === 'DISPATCHED') {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600 border border-emerald-500/30">
          DISPATCHED
        </span>
      );
    }
    return (
      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/15 text-rose-600 border border-rose-500/30">
        {st}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center text-secondary">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-indigo-600 mb-3" />
        <p className="text-sm font-bold">Loading Outbound Communication Center...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link to="/dashboard" className="text-xs font-bold text-secondary hover:text-primary transition">
              Dashboard
            </Link>
            <span className="text-secondary text-xs">/</span>
            <span className="text-xs font-bold text-indigo-600">Communication Center</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-primary flex items-center gap-3">
            <Bell className="w-8 h-8 text-indigo-600" />
            Outbound Communication & Consent Governance
          </h1>
          <p className="text-xs sm:text-sm text-secondary mt-1 max-w-3xl">
            Control delivery channels (Email, SMS, WhatsApp, In-App, Telegram), set frequency limits, manage consent per purpose, and enforce zero contact for opted-out users.
          </p>
        </div>

        {statusFeedback && (
          <div className="px-4 py-2 rounded-2xl bg-emerald-500/10 text-emerald-600 border border-emerald-500/30 text-xs font-bold flex items-center gap-2">
            <Check className="w-4 h-4" /> {statusFeedback}
          </div>
        )}
      </div>

      {/* Global Opt-Out Alert Banner */}
      {pref?.is_opted_out_all && (
        <div className="p-5 rounded-3xl bg-rose-500/10 border-2 border-rose-500/40 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-6 h-6 text-rose-600 shrink-0" />
            <div>
              <h3 className="text-sm font-black text-rose-800 dark:text-rose-300 uppercase tracking-wider">
                Emergency Global Opt-Out Active
              </h3>
              <p className="text-xs text-rose-700/80 dark:text-rose-400">
                All outbound communications from agents and services are strictly prohibited.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => handleUpdatePreference({ is_opted_out_all: false })}
            className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs shadow-sm transition cursor-pointer shrink-0"
          >
            Resume Communications
          </button>
        </div>
      )}

      {/* ── Main 3-Column Layout ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: Channel Toggles & Consent (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          {/* Channel Preferences Card */}
          <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs space-y-5">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h2 className="text-sm font-black text-primary uppercase tracking-wider">Channel Toggles</h2>
              <Sliders className="w-4 h-4 text-indigo-600" />
            </div>

            <div className="space-y-3">
              {/* In-App */}
              <div className="flex items-center justify-between p-3 rounded-2xl bg-background border border-border">
                <div className="flex items-center gap-2.5">
                  <Bell className="w-4 h-4 text-indigo-500" />
                  <span className="text-xs font-bold text-primary">In-App Alerts</span>
                </div>
                <input
                  type="checkbox"
                  checked={pref?.in_app_enabled || false}
                  onChange={(e) => handleUpdatePreference({ in_app_enabled: e.target.checked })}
                  className="w-4 h-4 accent-indigo-600 cursor-pointer"
                />
              </div>

              {/* Email */}
              <div className="flex items-center justify-between p-3 rounded-2xl bg-background border border-border">
                <div className="flex items-center gap-2.5">
                  <Mail className="w-4 h-4 text-purple-500" />
                  <span className="text-xs font-bold text-primary">Email Notifications</span>
                </div>
                <input
                  type="checkbox"
                  checked={pref?.email_enabled || false}
                  onChange={(e) => handleUpdatePreference({ email_enabled: e.target.checked })}
                  className="w-4 h-4 accent-indigo-600 cursor-pointer"
                />
              </div>

              {/* SMS */}
              <div className="flex items-center justify-between p-3 rounded-2xl bg-background border border-border">
                <div className="flex items-center gap-2.5">
                  <Smartphone className="w-4 h-4 text-emerald-500" />
                  <span className="text-xs font-bold text-primary">SMS Text</span>
                </div>
                <input
                  type="checkbox"
                  checked={pref?.sms_enabled || false}
                  onChange={(e) => handleUpdatePreference({ sms_enabled: e.target.checked })}
                  className="w-4 h-4 accent-indigo-600 cursor-pointer"
                />
              </div>

              {/* WhatsApp */}
              <div className="flex items-center justify-between p-3 rounded-2xl bg-background border border-border">
                <div className="flex items-center gap-2.5">
                  <MessageSquare className="w-4 h-4 text-green-500" />
                  <span className="text-xs font-bold text-primary">WhatsApp Business</span>
                </div>
                <input
                  type="checkbox"
                  checked={pref?.whatsapp_enabled || false}
                  onChange={(e) => handleUpdatePreference({ whatsapp_enabled: e.target.checked })}
                  className="w-4 h-4 accent-indigo-600 cursor-pointer"
                />
              </div>

              {/* Telegram */}
              <div className="flex items-center justify-between p-3 rounded-2xl bg-background border border-border">
                <div className="flex items-center gap-2.5">
                  <Send className="w-4 h-4 text-cyan-500" />
                  <span className="text-xs font-bold text-primary">Telegram Bot</span>
                </div>
                <input
                  type="checkbox"
                  checked={pref?.telegram_enabled || false}
                  onChange={(e) => handleUpdatePreference({ telegram_enabled: e.target.checked })}
                  className="w-4 h-4 accent-indigo-600 cursor-pointer"
                />
              </div>
            </div>

            {/* Daily Frequency Limit */}
            <div className="pt-2 border-t border-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-secondary">Daily Limit (24h)</span>
                <span className="font-mono font-black text-xs text-primary">{pref?.daily_frequency_limit} msgs/day</span>
              </div>
              <input
                type="range"
                min="1"
                max="20"
                value={pref?.daily_frequency_limit || 5}
                onChange={(e) => handleUpdatePreference({ daily_frequency_limit: parseInt(e.target.value) })}
                className="w-full accent-indigo-600 cursor-pointer"
              />
            </div>

            {/* Global Opt-Out Button */}
            {!pref?.is_opted_out_all && (
              <button
                type="button"
                onClick={() => handleUpdatePreference({ is_opted_out_all: true })}
                className="w-full py-2.5 rounded-2xl bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-rose-600 dark:text-rose-400 text-xs font-black transition cursor-pointer"
              >
                Opt Out of All Outbound Communications
              </button>
            )}
          </div>

          {/* Purpose-Based Consent Management Card */}
          <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs space-y-4">
            <div className="border-b border-border pb-3">
              <h2 className="text-sm font-black text-primary uppercase tracking-wider">Purpose Consents</h2>
              <p className="text-[11px] text-secondary">Agents cannot contact users without explicit purpose consent.</p>
            </div>

            <div className="space-y-2 text-xs">
              {[
                { purpose: 'TRANSACTIONAL', label: 'Transactional Receipts & Invoices' },
                { purpose: 'COLLECTIONS', label: 'Overdue Debtor Invoices & Recovery' },
                { purpose: 'SECURITY_ALERTS', label: 'Security & Anomaly Sentinel Alerts' },
                { purpose: 'ACCOUNT_UPDATES', label: 'Treasury & Corporate Banking Notices' },
                { purpose: 'MARKETING', label: 'Product News & Promotional Updates' },
              ].map((item) => {
                const rec = consents.find((c) => c.purpose === item.purpose);
                const isGranted = rec ? rec.is_granted : false;
                return (
                  <div key={item.purpose} className="flex items-center justify-between p-2.5 rounded-xl bg-background border border-border">
                    <span className="font-medium text-primary text-[11px]">{item.label}</span>
                    <button
                      type="button"
                      onClick={() => handleToggleConsent(item.purpose, !isGranted)}
                      className={`px-2.5 py-1 rounded-lg text-[10px] font-black cursor-pointer transition ${
                        isGranted ? 'bg-emerald-500/20 text-emerald-600' : 'bg-muted text-secondary'
                      }`}
                    >
                      {isGranted ? 'GRANTED' : 'REVOKED'}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Center: Live In-App Notifications Feed (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-black uppercase tracking-wider text-secondary">
              In-App Notification Feed ({inAppNotifs.length})
            </h2>
            <span className="text-[11px] text-emerald-600 font-bold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Real Application Hub
            </span>
          </div>

          <div className="space-y-3">
            {inAppNotifs.length === 0 ? (
              <div className="p-8 rounded-3xl bg-surface border border-border text-center text-secondary text-xs">
                No in-app notifications found.
              </div>
            ) : (
              inAppNotifs.slice(0, 8).map((notif: any) => (
                <div key={notif.id} className="p-4 rounded-2xl bg-surface border border-border space-y-1.5 shadow-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-muted text-secondary font-bold">
                      {notif.notification_type || 'NOTIFICATION'}
                    </span>
                    <span className="text-[10px] text-secondary">
                      {notif.created_at ? new Date(notif.created_at).toLocaleTimeString() : 'Just now'}
                    </span>
                  </div>
                  <p className="text-xs text-primary font-medium leading-relaxed">{notif.body}</p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right: Sandbox Test Dispatcher (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          <div className="p-6 rounded-3xl bg-surface border border-border shadow-xl space-y-4">
            <div className="border-b border-border pb-3 flex items-center justify-between">
              <h2 className="text-sm font-black text-primary uppercase tracking-wider flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-600" /> Test Dispatch Firewall
              </h2>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-bold text-secondary mb-1">Target Channel</label>
                <select
                  value={testChannel}
                  onChange={(e) => setTestChannel(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary outline-none"
                >
                  <option value="IN_APP">IN_APP (Real CRM Notification)</option>
                  <option value="EMAIL">EMAIL (Mock SMTP)</option>
                  <option value="SMS">SMS (Mock Gateway)</option>
                  <option value="WHATSAPP">WHATSAPP (Mock Cloud API)</option>
                  <option value="TELEGRAM">TELEGRAM (Mock Bot)</option>
                </select>
              </div>

              <div>
                <label className="block font-bold text-secondary mb-1">Governed Template</label>
                <select
                  value={testTemplate}
                  onChange={(e) => setTestTemplate(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-primary outline-none"
                >
                  <option value="payment_recovery">payment_recovery (ORD-991 • ₹3,499)</option>
                  <option value="invoice_reminder">invoice_reminder (INV-204 • ₹18,500)</option>
                  <option value="payment_confirmation">payment_confirmation (TXN-777 • ₹2,499)</option>
                  <option value="payout_approval">payout_approval (PO-888 • ₹18,500)</option>
                  <option value="risk_alert">risk_alert (SEC_NEW_DEVICE)</option>
                  <option value="cashflow_alert">cashflow_alert (₹28.45L Balance)</option>
                </select>
              </div>

              <button
                type="button"
                disabled={dispatching}
                onClick={handleTestDispatch}
                className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-md transition cursor-pointer flex items-center justify-center gap-2"
              >
                {dispatching ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                <span>Dispatch Governed Message</span>
              </button>

              {dispatchResult && (
                <div
                  className={`p-3 rounded-xl border text-xs space-y-1 ${
                    dispatchResult.success
                      ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-800 dark:text-emerald-200'
                      : 'bg-rose-500/10 border-rose-500/30 text-rose-800 dark:text-rose-200'
                  }`}
                >
                  <div className="flex items-center justify-between font-bold">
                    <span>{dispatchResult.success ? 'DISPATCH SUCCESS' : 'FIREWALL HALT'}</span>
                    <span>{dispatchResult.status}</span>
                  </div>
                  {dispatchResult.reason && <p className="text-[11px]">{dispatchResult.reason}</p>}
                </div>
              )}
            </div>
          </div>

          {/* Forensic Audit Events */}
          <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs space-y-3">
            <h3 className="text-sm font-black text-primary uppercase tracking-wider">Forensic Audit Log</h3>
            <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
              {events.slice(0, 6).map((ev) => (
                <div key={ev.id} className="p-2.5 rounded-xl bg-background border border-border text-[11px] space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-primary">{ev.channel}</span>
                    {getStatusBadge(ev.status)}
                  </div>
                  <div className="text-secondary truncate">{ev.template_name}</div>
                  {ev.blocked_reason && <div className="text-rose-500 text-[10px]">{ev.blocked_reason}</div>}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
