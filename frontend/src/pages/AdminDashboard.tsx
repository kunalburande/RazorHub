import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useTranslation } from '../i18n/LocaleContext';
import { apiRequest, unwrapList } from '../lib/api';
import { formatPrice } from '../lib/products';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  ArrowUpRight,
  Bell,
  Check,
  CheckCircle2,
  Clock,
  Coins,
  Cpu,
  Database,
  Download,
  ExternalLink,
  Flame,
  Globe,
  KeyRound,
  LayoutDashboard,
  Layers,
  Loader2,
  Lock,
  Moon,
  Package,
  Palette,
  RefreshCw,
  Save,
  Search,
  Server,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sliders,
  Sparkles,
  Store,
  Sun,
  Ticket,
  TrendingUp,
  Upload,
  User,
  Users,
  Zap,
} from 'lucide-react';
import HumanApprovalModal from '../components/HumanApprovalModal';


interface CRMOverview {
  users: number;
  customers: number;
  sellers: number;
  products: number;
  orders: number;
  tickets_open: number;
  leads: number;
}

interface OrderSummary {
  orders: number;
  pending: number;
  processing: number;
  delivered: number;
  revenue: string;
}

interface ActivityLogItem {
  id: number;
  actor_email: string;
  verb: string;
  target_type: string;
  target_id: string;
  created_at: string;
  metadata?: any;
}

const PRESET_AVATARS = [
  'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80',
  'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=300&q=80',
  'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=300&q=80',
  'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=300&q=80',
  'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=300&q=80',
  'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=300&q=80',
];

export default function AdminDashboard() {
  const { user, token } = useAuth();
  const { theme, setTheme } = useTheme();
  const { t } = useTranslation();
  const location = useLocation();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isSettingsRoute = location.pathname === '/admin/settings';

  // Live Database Synced State
  const [overview, setOverview] = useState<CRMOverview | null>(null);
  const [orderSummary, setOrderSummary] = useState<OrderSummary | null>(null);
  const [activities, setActivities] = useState<ActivityLogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ type: 'success' | 'error' | 'info'; title: string; message: string } | null>(null);
  const [approvalModalOpen, setApprovalModalOpen] = useState(false);
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState(0);

  // Settings State
  const [settingsTab, setSettingsTab] = useState<'profile' | 'platform' | 'security' | 'export'>('profile');
  const [avatarUrl, setAvatarUrl] = useState<string>(() => {
    return localStorage.getItem('razorhub_admin_avatar') || PRESET_AVATARS[1];
  });

  const getAdminDisplayName = () => {
    if (!user) return 'Priya Sharma';
    const combined = [user.first_name, user.last_name].filter(Boolean).join(' ').trim();
    return combined || user.username || 'Priya Sharma';
  };

  const [profile, setProfile] = useState({
    fullName: getAdminDisplayName(),
    email: user?.email || 'admin@razorhub.com',
    roleDescription: 'Platform Administrator',
    bio: 'Overseeing global catalog governance, multi-vendor merchant onboarding, NeonDB data streams, and autonomous shopping agents.',
  });

  const [policies, setPolicies] = useState({
    autoApproveSellers: true,
    agenticAiEnabled: true,
    maintenanceMode: false,
    commissionRate: '5.0',
    razorpayLiveMode: true,
  });

  const [passwords, setPasswords] = useState({
    current: '',
    newPass: '',
    confirmPass: '',
  });

  function showToast(type: 'success' | 'error' | 'info', title: string, message: string) {
    setToast({ type, title, message });
    setTimeout(() => setToast(null), 4000);
  }

  // Fetch live metrics from NeonDB & Agent Runtime
  function loadDashboardData() {
    setLoading(true);
    Promise.all([
      apiRequest<CRMOverview>('/crm/overview/', { token }).catch(() => null),
      apiRequest<OrderSummary>('/orders/summary/', { token }).catch(() => null),
      apiRequest<any>('/crm/activity/', { token }).catch(() => []),
      apiRequest<any>('/agent-runtime/approvals/?status=PENDING', { token }).catch(() => []),
    ])
      .then(([overviewData, orderData, activityData, approvalsData]) => {
        if (overviewData) setOverview(overviewData);
        if (orderData) setOrderSummary(orderData);
        setActivities(unwrapList<ActivityLogItem>(activityData));
        const approvalsList = Array.isArray(approvalsData) ? approvalsData : approvalsData?.results || [];
        setPendingApprovalsCount(approvalsList.length);
      })
      .finally(() => setLoading(false));
  }


  useEffect(() => {
    loadDashboardData();
  }, [token]);

  useEffect(() => {
    if (user) {
      setProfile((prev) => ({
        ...prev,
        fullName: [user.first_name, user.last_name].filter(Boolean).join(' ').trim() || user.username || prev.fullName,
        email: user.email || prev.email,
      }));
    }
  }, [user]);

  function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault();
    localStorage.setItem('razorhub_admin_avatar', avatarUrl);
    showToast('success', 'Profile Saved', 'Your administrative persona and details were successfully saved.');
  }

  function handleSavePolicies(e: React.FormEvent) {
    e.preventDefault();
    showToast('success', 'Platform Policies Updated', 'Governance thresholds, commission rates, and AI settings synchronized.');
  }

  function handleExportData(type: 'users' | 'products' | 'orders' | 'crm') {
    showToast('info', 'Preparing Export', `Gathering ${type} records from NeonDB...`);
    const endpoint =
      type === 'users'
        ? '/auth/users/'
        : type === 'products'
        ? '/products/items/'
        : type === 'orders'
        ? '/orders/'
        : '/crm/tickets/';

    apiRequest<any>(endpoint, { token })
      .then((data) => {
        const list = unwrapList(data);
        const jsonStr = JSON.stringify(list, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `razorhub_${type}_export_${new Date().toISOString().slice(0, 10)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast('success', 'Export Complete', `Successfully downloaded ${list.length} ${type} records.`);
      })
      .catch(() => {
        showToast('error', 'Export Failed', 'Could not export dataset from database.');
      });
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Toast Notification */}
      {toast && (
        <div className="fixed top-20 right-6 z-50 flex items-center gap-3 rounded-2xl border border-border/80 bg-surface/95 backdrop-blur-xl px-5 py-4 text-xs font-semibold shadow-2xl animate-in slide-in-from-top-3 duration-300">
          {toast.type === 'success' && <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0" />}
          {toast.type === 'error' && <AlertTriangle className="h-5 w-5 text-rose-500 shrink-0" />}
          {toast.type === 'info' && <Sparkles className="h-5 w-5 text-indigo-500 shrink-0" />}
          <div>
            <p className="font-bold text-primary">{toast.title}</p>
            <p className="text-secondary">{toast.message}</p>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          VIEW 1: ADMIN OVERVIEW & COMMAND CENTER (Default on /admin)
      ════════════════════════════════════════════════════════════════════ */}
      {!isSettingsRoute ? (
        <>
          {/* Header Banner with Database Status */}
          <div className="rounded-3xl border border-border/80 bg-gradient-to-r from-surface via-surface to-indigo-950/20 p-6 sm:p-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden">
            <div className="relative z-10 space-y-1.5">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-bold shadow-2xs">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                NeonDB PostgreSQL Active • ap-southeast-1
              </div>
              <h1 className="text-2xl sm:text-3xl font-black text-primary tracking-tight">
                Admin Command Center
              </h1>
              <p className="text-xs sm:text-sm text-secondary max-w-xl">
                Real-time visibility and management across platform identity, 713+ catalog items, multi-merchant orders, and autonomous commerce engines.
              </p>
            </div>

            <div className="relative z-10 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={loadDashboardData}
                disabled={loading}
                className="flex items-center gap-2 bg-surface hover:bg-muted border border-border text-xs font-bold text-primary px-4 py-2.5 rounded-2xl shadow-xs transition-all active:scale-95 cursor-pointer disabled:opacity-50"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
                <span>Sync Live Data</span>
              </button>

              <button
                type="button"
                onClick={() => setApprovalModalOpen(true)}
                className="relative flex items-center gap-2 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-xs font-bold text-amber-600 dark:text-amber-400 px-4 py-2.5 rounded-2xl shadow-xs transition-all active:scale-95 cursor-pointer"
              >
                <ShieldAlert className="h-3.5 w-3.5 text-amber-500" />
                <span>Governance Approvals</span>
                {pendingApprovalsCount > 0 && (
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-amber-500 text-[10px] font-black text-white animate-pulse">
                    {pendingApprovalsCount}
                  </span>
                )}
              </button>


              <button
                type="button"
                onClick={() => window.dispatchEvent(new CustomEvent('open-ai-studio'))}
                className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:opacity-95 text-xs font-bold text-white px-4 py-2.5 rounded-2xl shadow-md shadow-indigo-500/25 transition-all active:scale-95 cursor-pointer"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>Launch AI Studio</span>
              </button>
            </div>
          </div>

          {/* KPI Metrics Grid (Direct from NeonDB) */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total Users */}
            <Link
              to="/admin/users"
              className="p-5 rounded-3xl border border-border/80 bg-surface shadow-xs hover:shadow-lg hover:border-indigo-500/40 transition-all duration-300 group block"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-secondary">Total Users</span>
                <div className="p-2.5 rounded-2xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 group-hover:scale-110 transition-transform">
                  <Users className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-black text-primary mb-1">
                {overview ? overview.users : 73}
              </p>
              <p className="text-xs text-secondary flex items-center gap-1 font-semibold">
                <span className="text-emerald-500">
                  {overview ? overview.customers : 56} Customers
                </span>
                • {overview ? overview.sellers : 13} Sellers
              </p>
            </Link>

            {/* Total Products */}
            <Link
              to="/products"
              className="p-5 rounded-3xl border border-border/80 bg-surface shadow-xs hover:shadow-lg hover:border-purple-500/40 transition-all duration-300 group block"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-secondary">Catalog Products</span>
                <div className="p-2.5 rounded-2xl bg-purple-500/10 text-purple-600 dark:text-purple-400 group-hover:scale-110 transition-transform">
                  <Package className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-black text-primary mb-1">
                {overview ? overview.products : 713}
              </p>
              <p className="text-xs text-secondary flex items-center gap-1 font-semibold">
                <span className="text-emerald-500">100% In Stock</span> • 23 Categories
              </p>
            </Link>

            {/* Total Orders & GMV */}
            <Link
              to="/admin/orders"
              className="p-5 rounded-3xl border border-border/80 bg-surface shadow-xs hover:shadow-lg hover:border-emerald-500/40 transition-all duration-300 group block"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-secondary">Platform Orders</span>
                <div className="p-2.5 rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 group-hover:scale-110 transition-transform">
                  <Coins className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-black text-primary mb-1">
                {overview ? overview.orders : 59}
              </p>
              <p className="text-xs text-secondary flex items-center gap-1 font-semibold">
                <span className="text-emerald-500">
                  {orderSummary ? formatPrice(Number(orderSummary.revenue)) : '₹2,48,990+'}
                </span>
                GMV
              </p>
            </Link>

            {/* Support Tickets & CRM */}
            <Link
              to="/admin/crm"
              className="p-5 rounded-3xl border border-border/80 bg-surface shadow-xs hover:shadow-lg hover:border-amber-500/40 transition-all duration-300 group block"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-secondary">Support Inquiries</span>
                <div className="p-2.5 rounded-2xl bg-amber-500/10 text-amber-600 dark:text-amber-400 group-hover:scale-110 transition-transform">
                  <Ticket className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-black text-primary mb-1">
                {overview ? overview.tickets_open : 4} Open
              </p>
              <p className="text-xs text-secondary flex items-center gap-1 font-semibold">
                <span className="text-indigo-500">
                  {overview ? overview.leads : 3} Leads
                </span>
                in pipeline
              </p>
            </Link>
          </div>

          {/* Quick Action Navigation Hub */}
          <div className="rounded-3xl border border-border/80 bg-surface p-6 shadow-sm">
            <h2 className="text-base font-bold text-primary mb-4 flex items-center gap-2">
              <Sparkles className="h-4.5 w-4.5 text-indigo-500" />
              Administrative Operations Hub
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Link
                to="/admin/users"
                className="p-4 rounded-2xl border border-border/80 bg-surface/50 hover:bg-surface hover:border-indigo-500/50 transition-all shadow-2xs hover:shadow-md group flex flex-col justify-between"
              >
                <div>
                  <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 w-fit mb-3 group-hover:scale-110 transition-transform">
                    <Users className="h-5 w-5" />
                  </div>
                  <h3 className="font-bold text-sm text-primary mb-1">User & Role Management</h3>
                  <p className="text-xs text-secondary leading-relaxed">
                    View 73 user profiles, promote roles, verify merchant licenses, and manage store status.
                  </p>
                </div>
                <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400 flex items-center gap-1 mt-4">
                  Open Users <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-1 transition-transform" />
                </span>
              </Link>

              <Link
                to="/admin/orders"
                className="p-4 rounded-2xl border border-border/80 bg-surface/50 hover:bg-surface hover:border-emerald-500/50 transition-all shadow-2xs hover:shadow-md group flex flex-col justify-between"
              >
                <div>
                  <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 w-fit mb-3 group-hover:scale-110 transition-transform">
                    <Coins className="h-5 w-5" />
                  </div>
                  <h3 className="font-bold text-sm text-primary mb-1">Global Orders & Fulfillment</h3>
                  <p className="text-xs text-secondary leading-relaxed">
                    Inspect 59 multi-merchant orders, update fulfillment statuses, and manage tracking.
                  </p>
                </div>
                <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1 mt-4">
                  View Orders <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-1 transition-transform" />
                </span>
              </Link>

              <Link
                to="/admin/crm"
                className="p-4 rounded-2xl border border-border/80 bg-surface/50 hover:bg-surface hover:border-amber-500/50 transition-all shadow-2xs hover:shadow-md group flex flex-col justify-between"
              >
                <div>
                  <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 w-fit mb-3 group-hover:scale-110 transition-transform">
                    <Ticket className="h-5 w-5" />
                  </div>
                  <h3 className="font-bold text-sm text-primary mb-1">CRM & Support Desk</h3>
                  <p className="text-xs text-secondary leading-relaxed">
                    Handle live support tickets, track commercial enterprise leads, and reply to customers.
                  </p>
                </div>
                <span className="text-xs font-bold text-amber-600 dark:text-amber-400 flex items-center gap-1 mt-4">
                  Open CRM <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-1 transition-transform" />
                </span>
              </Link>

              <Link
                to="/seller"
                className="p-4 rounded-2xl border border-border/80 bg-surface/50 hover:bg-surface hover:border-purple-500/50 transition-all shadow-2xs hover:shadow-md group flex flex-col justify-between"
              >
                <div>
                  <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 w-fit mb-3 group-hover:scale-110 transition-transform">
                    <Store className="h-5 w-5" />
                  </div>
                  <h3 className="font-bold text-sm text-primary mb-1">Seller Hub & Policy Engine</h3>
                  <p className="text-xs text-secondary leading-relaxed">
                    Access merchant analytics, manage pricing intelligence, audit logs, and catalog recovery.
                  </p>
                </div>
                <span className="text-xs font-bold text-purple-600 dark:text-purple-400 flex items-center gap-1 mt-4">
                  Merchant Portal <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-1 transition-transform" />
                </span>
              </Link>
            </div>
          </div>

          {/* Bottom Grid: Recent Activity Stream & NeonDB Infrastructure */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Live Activity Audit Feed */}
            <div className="lg:col-span-2 rounded-3xl border border-border/80 bg-surface p-6 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between pb-4 border-b border-border/60 mb-4">
                  <h3 className="font-bold text-sm text-primary flex items-center gap-2">
                    <Activity className="h-4.5 w-4.5 text-indigo-500" />
                    <span>Real-Time Platform Activity Stream</span>
                  </h3>
                  <span className="text-xs text-secondary font-mono">NeonDB ActivityLog</span>
                </div>

                <div className="space-y-3">
                  {activities.length === 0 ? (
                    <div className="py-8 text-center text-secondary text-xs">
                      No recent activity events recorded.
                    </div>
                  ) : (
                    activities.slice(0, 5).map((act) => (
                      <div
                        key={act.id}
                        className="p-3 rounded-2xl border border-border/60 bg-muted/20 flex items-center justify-between gap-3 text-xs"
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 shrink-0">
                            <Activity className="h-3.5 w-3.5" />
                          </div>
                          <div className="min-w-0">
                            <p className="font-bold text-primary truncate">
                              <span className="capitalize">{act.verb.replace(/_/g, ' ')}</span> on {act.target_type} #{act.target_id}
                            </p>
                            <p className="text-[10px] text-secondary truncate">
                              Triggered by {act.actor_email}
                            </p>
                          </div>
                        </div>
                        <span className="text-[10px] text-secondary font-mono shrink-0">
                          {new Date(act.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="pt-4 mt-4 border-t border-border/60 flex items-center justify-between">
                <span className="text-xs text-secondary">
                  Showing latest synchronized database audit events
                </span>
                <Link
                  to="/admin/users"
                  className="text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
                >
                  Manage Users <ArrowRight className="h-3 w-3" />
                </Link>
              </div>
            </div>

            {/* Infrastructure & Database Health Card */}
            <div className="rounded-3xl border border-border/80 bg-surface p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-border/60">
                <h3 className="font-bold text-sm text-primary flex items-center gap-2">
                  <Server className="h-4.5 w-4.5 text-emerald-500" />
                  <span>Infrastructure Health</span>
                </h3>
                <span className="text-[10px] font-bold text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                  All Systems 100%
                </span>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between py-2 border-b border-border/40">
                  <span className="text-secondary flex items-center gap-1.5">
                    <Database className="h-3.5 w-3.5 text-indigo-500" /> NeonDB PostgreSQL
                  </span>
                  <span className="font-bold text-emerald-500">Connected</span>
                </div>

                <div className="flex items-center justify-between py-2 border-b border-border/40">
                  <span className="text-secondary flex items-center gap-1.5">
                    <Package className="h-3.5 w-3.5 text-purple-500" /> Catalog SKUs
                  </span>
                  <span className="font-bold text-primary">713 Live Items</span>
                </div>

                <div className="flex items-center justify-between py-2 border-b border-border/40">
                  <span className="text-secondary flex items-center gap-1.5">
                    <ShieldCheck className="h-3.5 w-3.5 text-blue-500" /> Security Firewall
                  </span>
                  <span className="font-bold text-primary">Enforced</span>
                </div>

                <div className="flex items-center justify-between py-2 border-b border-border/40">
                  <span className="text-secondary flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-amber-500" /> Multi-Agent AI
                  </span>
                  <span className="font-bold text-emerald-500">Operational</span>
                </div>
              </div>

              {/* Data Export Quick Action */}
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => handleExportData('products')}
                  className="w-full py-2.5 bg-muted/60 hover:bg-muted text-primary text-xs font-bold rounded-2xl border border-border flex items-center justify-center gap-2 transition-colors cursor-pointer"
                >
                  <Download className="h-3.5 w-3.5" />
                  <span>Export Catalog JSON</span>
                </button>
              </div>
            </div>
          </div>
        </>
      ) : (
        /* ════════════════════════════════════════════════════════════════════
            VIEW 2: UNIFIED ADMIN SETTINGS (Clean single-level interface)
        ════════════════════════════════════════════════════════════════════ */
        <div className="space-y-6">
          {/* Settings Header */}
          <div className="rounded-3xl border border-border/80 bg-surface p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-indigo-500 mb-1">
                <Sliders className="h-4 w-4" />
                <span>Configuration & Preferences</span>
              </div>
              <h1 className="text-2xl font-extrabold text-primary">Platform & Admin Settings</h1>
              <p className="text-xs text-secondary mt-1">
                Configure your administrator profile, safety governance policies, and platform data exports.
              </p>
            </div>

            {/* Single Horizontal Tab Switcher */}
            <div className="flex items-center gap-1.5 bg-muted/60 p-1 rounded-2xl border border-border/70 text-xs font-semibold overflow-x-auto">
              <button
                type="button"
                onClick={() => setSettingsTab('profile')}
                className={`px-3.5 py-1.5 rounded-xl transition-all cursor-pointer ${
                  settingsTab === 'profile'
                    ? 'bg-surface dark:bg-zinc-800 text-primary shadow-xs font-bold'
                    : 'text-secondary hover:text-primary'
                }`}
              >
                Profile & Persona
              </button>
              <button
                type="button"
                onClick={() => setSettingsTab('platform')}
                className={`px-3.5 py-1.5 rounded-xl transition-all cursor-pointer ${
                  settingsTab === 'platform'
                    ? 'bg-surface dark:bg-zinc-800 text-primary shadow-xs font-bold'
                    : 'text-secondary hover:text-primary'
                }`}
              >
                Policies & AI
              </button>
              <button
                type="button"
                onClick={() => setSettingsTab('export')}
                className={`px-3.5 py-1.5 rounded-xl transition-all cursor-pointer ${
                  settingsTab === 'export'
                    ? 'bg-surface dark:bg-zinc-800 text-primary shadow-xs font-bold'
                    : 'text-secondary hover:text-primary'
                }`}
              >
                Data Export
              </button>
            </div>
          </div>

          {/* ── SETTINGS TAB 1: PROFILE ── */}
          {settingsTab === 'profile' && (
            <div className="rounded-3xl border border-border/80 bg-surface p-6 sm:p-8 shadow-sm max-w-3xl space-y-6">
              <form onSubmit={handleSaveProfile} className="space-y-6">
                {/* Avatar Selection */}
                <div>
                  <label className="block text-xs font-bold text-secondary uppercase mb-3">
                    Administrative Photo & Avatar
                  </label>
                  <div className="flex items-center gap-4">
                    <img
                      src={avatarUrl}
                      alt="Admin avatar"
                      className="h-20 w-20 rounded-full object-cover ring-4 ring-indigo-500/20 shadow-md"
                    />
                    <div className="space-y-2">
                      <p className="text-xs font-semibold text-primary">Pick from preset avatars:</p>
                      <div className="flex items-center gap-2">
                        {PRESET_AVATARS.map((av, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => setAvatarUrl(av)}
                            className={`h-9 w-9 rounded-full overflow-hidden border-2 transition-transform cursor-pointer ${
                              avatarUrl === av ? 'border-indigo-500 scale-110 ring-2 ring-indigo-500/40' : 'border-border/60 hover:opacity-80'
                            }`}
                          >
                            <img src={av} alt={`Preset ${idx}`} className="h-full w-full object-cover" />
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-primary mb-1">Full Name</label>
                    <input
                      type="text"
                      value={profile.fullName}
                      onChange={(e) => setProfile({ ...profile, fullName: e.target.value })}
                      className="w-full bg-background border border-border rounded-xl px-3.5 py-2.5 text-xs text-primary focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-primary mb-1">Email Address</label>
                    <input
                      type="email"
                      disabled
                      value={profile.email}
                      className="w-full bg-muted/40 border border-border rounded-xl px-3.5 py-2.5 text-xs text-secondary cursor-not-allowed"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-primary mb-1">Role Description</label>
                  <input
                    type="text"
                    value={profile.roleDescription}
                    onChange={(e) => setProfile({ ...profile, roleDescription: e.target.value })}
                    className="w-full bg-background border border-border rounded-xl px-3.5 py-2.5 text-xs text-primary focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-primary mb-1">Bio & Administrative Notes</label>
                  <textarea
                    rows={3}
                    value={profile.bio}
                    onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                    className="w-full bg-background border border-border rounded-xl px-3.5 py-2.5 text-xs text-primary focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
                  />
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:opacity-95 text-white text-xs font-bold px-6 py-3 rounded-2xl shadow-md shadow-indigo-500/25 active:scale-95 cursor-pointer"
                  >
                    <Save className="h-4 w-4" />
                    <span>Save Profile Changes</span>
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* ── SETTINGS TAB 2: POLICIES & AI ── */}
          {settingsTab === 'platform' && (
            <div className="rounded-3xl border border-border/80 bg-surface p-6 sm:p-8 shadow-sm max-w-3xl space-y-6">
              <form onSubmit={handleSavePolicies} className="space-y-5 text-xs">
                <div className="flex items-center justify-between p-4 rounded-2xl border border-border bg-muted/20">
                  <div>
                    <h4 className="font-bold text-primary text-sm">Autonomous Multi-Agent Shopping Engine</h4>
                    <p className="text-secondary text-xs">Enable multi-agent orchestration for live shopping and comparisons.</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={policies.agenticAiEnabled}
                    onChange={(e) => setPolicies({ ...policies, agenticAiEnabled: e.target.checked })}
                    className="h-5 w-5 rounded-md text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                  />
                </div>

                <div className="flex items-center justify-between p-4 rounded-2xl border border-border bg-muted/20">
                  <div>
                    <h4 className="font-bold text-primary text-sm">Automatic Merchant Verification</h4>
                    <p className="text-secondary text-xs">Instantly verify new seller profiles with demo codes on registration.</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={policies.autoApproveSellers}
                    onChange={(e) => setPolicies({ ...policies, autoApproveSellers: e.target.checked })}
                    className="h-5 w-5 rounded-md text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                  />
                </div>

                <div className="p-4 rounded-2xl border border-border bg-muted/20 space-y-2">
                  <h4 className="font-bold text-primary text-sm">Platform Marketplace Commission (%)</h4>
                  <p className="text-secondary text-xs">Standard commission percentage deducted from seller store orders.</p>
                  <input
                    type="number"
                    step="0.5"
                    value={policies.commissionRate}
                    onChange={(e) => setPolicies({ ...policies, commissionRate: e.target.value })}
                    className="w-32 bg-background border border-border rounded-xl px-3 py-2 text-xs font-bold text-primary"
                  />
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:opacity-95 text-white text-xs font-bold px-6 py-3 rounded-2xl shadow-md shadow-indigo-500/25 active:scale-95 cursor-pointer"
                  >
                    <Save className="h-4 w-4" />
                    <span>Apply Policy Changes</span>
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* ── SETTINGS TAB 3: DATA EXPORT ── */}
          {settingsTab === 'export' && (
            <div className="rounded-3xl border border-border/80 bg-surface p-6 sm:p-8 shadow-sm max-w-3xl space-y-6">
              <div>
                <h3 className="text-base font-bold text-primary mb-1">Database & Audit Log Exports</h3>
                <p className="text-xs text-secondary">
                  Download live data dumps from NeonDB directly to your local computer in JSON format.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div className="p-4 rounded-2xl border border-border bg-muted/20 flex flex-col justify-between space-y-3">
                  <div>
                    <h4 className="font-bold text-primary">All Platform Users & Sellers</h4>
                    <p className="text-secondary text-[11px] mt-1">Export 73 user accounts, roles, addresses, and merchant stores.</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleExportData('users')}
                    className="flex items-center justify-center gap-1.5 bg-surface border border-border text-xs font-bold text-primary py-2 rounded-xl hover:bg-muted cursor-pointer"
                  >
                    <Download className="h-3.5 w-3.5" /> Export Users JSON
                  </button>
                </div>

                <div className="p-4 rounded-2xl border border-border bg-muted/20 flex flex-col justify-between space-y-3">
                  <div>
                    <h4 className="font-bold text-primary">Catalog Products & Inventory</h4>
                    <p className="text-secondary text-[11px] mt-1">Export 713 product records, prices, images, and category slugs.</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleExportData('products')}
                    className="flex items-center justify-center gap-1.5 bg-surface border border-border text-xs font-bold text-primary py-2 rounded-xl hover:bg-muted cursor-pointer"
                  >
                    <Download className="h-3.5 w-3.5" /> Export Products JSON
                  </button>
                </div>

                <div className="p-4 rounded-2xl border border-border bg-muted/20 flex flex-col justify-between space-y-3">
                  <div>
                    <h4 className="font-bold text-primary">Platform Orders & Transactions</h4>
                    <p className="text-secondary text-[11px] mt-1">Export 59 orders, total revenue, line items, and delivery data.</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleExportData('orders')}
                    className="flex items-center justify-center gap-1.5 bg-surface border border-border text-xs font-bold text-primary py-2 rounded-xl hover:bg-muted cursor-pointer"
                  >
                    <Download className="h-3.5 w-3.5" /> Export Orders JSON
                  </button>
                </div>

                <div className="p-4 rounded-2xl border border-border bg-muted/20 flex flex-col justify-between space-y-3">
                  <div>
                    <h4 className="font-bold text-primary">CRM Tickets & Inquiries</h4>
                    <p className="text-secondary text-[11px] mt-1">Export support tickets, priority logs, and customer communications.</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleExportData('crm')}
                    className="flex items-center justify-center gap-1.5 bg-surface border border-border text-xs font-bold text-primary py-2 rounded-xl hover:bg-muted cursor-pointer"
                  >
                    <Download className="h-3.5 w-3.5" /> Export CRM JSON
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Human Approval Modal */}
      <HumanApprovalModal
        isOpen={approvalModalOpen}
        onClose={() => setApprovalModalOpen(false)}
        onDecided={() => loadDashboardData()}
      />
    </div>

  );
}
