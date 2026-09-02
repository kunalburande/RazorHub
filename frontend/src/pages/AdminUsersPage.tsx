import { useEffect, useMemo, useState } from 'react';
import { apiRequest, unwrapList } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import type { User } from '../context/AuthContext';
import { useTranslation } from '../i18n/LocaleContext';
import {
  Users,
  Store,
  Shield,
  Search,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  UserCheck,
  UserX,
  Filter,
  ArrowUpDown,
  Mail,
  Phone,
  Calendar,
  Building,
} from 'lucide-react';

interface SellerProfile {
  id: number;
  user_email: string;
  business_name: string;
  phone: string;
  status: 'pending' | 'verified' | 'suspended';
  store?: { name: string; is_active: boolean } | null;
  created_at?: string;
}

export default function AdminUsersPage() {
  const { token, user: currentUser } = useAuth();
  const { t } = useTranslation();

  const [users, setUsers] = useState<User[]>([]);
  const [sellers, setSellers] = useState<SellerProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const [activeTab, setActiveTab] = useState<'all' | 'sellers' | 'customers' | 'admins'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  function loadData() {
    setLoading(true);
    setError('');
    Promise.all([
      apiRequest<any>('/auth/users/', { token }),
      apiRequest<any>('/sellers/profiles/', { token }),
    ])
      .then(([usersRes, sellersRes]) => {
        setUsers(unwrapList<User>(usersRes));
        setSellers(unwrapList<SellerProfile>(sellersRes));
      })
      .catch((err) => {
        console.error('Failed to load admin data:', err);
        setError('Could not load live user and seller data from database.');
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadData();
  }, [token]);

  async function updateSellerStatus(id: number, status: SellerProfile['status']) {
    setUpdatingId(id);
    setError('');
    setSuccessMsg('');
    try {
      await apiRequest(`/sellers/profiles/${id}/`, {
        token,
        method: 'PATCH',
        body: JSON.stringify({ status }),
      });
      setSuccessMsg(`Seller profile #${id} updated to "${status}" successfully.`);
      setTimeout(() => setSuccessMsg(''), 4000);
      loadData();
    } catch (err: any) {
      setError(err?.message || 'Could not update seller status.');
    } finally {
      setUpdatingId(null);
    }
  }

  async function updateUserRole(userId: number, newRole: 'customer' | 'seller' | 'admin') {
    setUpdatingId(userId);
    setError('');
    setSuccessMsg('');
    try {
      await apiRequest(`/auth/users/${userId}/`, {
        token,
        method: 'PATCH',
        body: JSON.stringify({ role: newRole }),
      });
      setSuccessMsg(`User #${userId} role updated to "${newRole}".`);
      setTimeout(() => setSuccessMsg(''), 4000);
      loadData();
    } catch (err: any) {
      setError(err?.message || 'Could not update user role.');
    } finally {
      setUpdatingId(null);
    }
  }

  // Filtered lists
  const filteredUsers = useMemo(() => {
    return users.filter((u) => {
      const q = searchQuery.toLowerCase();
      const matchSearch =
        !q ||
        u.email.toLowerCase().includes(q) ||
        (u.first_name || '').toLowerCase().includes(q) ||
        (u.last_name || '').toLowerCase().includes(q) ||
        (u.username || '').toLowerCase().includes(q);

      if (!matchSearch) return false;

      const userRole = u.effective_role || u.role;
      if (activeTab === 'customers') return userRole === 'customer';
      if (activeTab === 'sellers') return userRole === 'seller';
      if (activeTab === 'admins') return userRole === 'admin';
      return true;
    });
  }, [users, searchQuery, activeTab]);

  const filteredSellers = useMemo(() => {
    return sellers.filter((s) => {
      const q = searchQuery.toLowerCase();
      return (
        !q ||
        s.business_name.toLowerCase().includes(q) ||
        s.user_email.toLowerCase().includes(q) ||
        (s.store?.name || '').toLowerCase().includes(q)
      );
    });
  }, [sellers, searchQuery]);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="rounded-3xl border border-border/80 bg-surface/90 backdrop-blur-md p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-indigo-500 mb-1">
            <Users className="h-4 w-4" />
            <span>Identity & Access Governance</span>
          </div>
          <h1 className="text-2xl font-extrabold text-primary">User & Merchant Management</h1>
          <p className="text-xs text-secondary mt-1">
            Manage all platform users, promote accounts, verify seller merchant licenses, and oversee access roles.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-2 bg-muted/60 hover:bg-muted border border-border text-xs font-bold text-primary px-3.5 py-2 rounded-xl transition-all shadow-2xs active:scale-95 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh NeonDB</span>
          </button>
        </div>
      </div>

      {/* Status Toasts */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 text-xs font-semibold flex items-center gap-2 shadow-xs">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {successMsg && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-xs font-semibold flex items-center gap-2 shadow-xs">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* KPI Stats Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl border border-border/80 bg-surface shadow-2xs flex items-center gap-3">
          <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
            <Users className="h-5 w-5" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-secondary uppercase">Total Users</p>
            <p className="text-xl font-black text-primary">{users.length}</p>
          </div>
        </div>

        <div className="p-4 rounded-2xl border border-border/80 bg-surface shadow-2xs flex items-center gap-3">
          <div className="p-3 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400">
            <Store className="h-5 w-5" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-secondary uppercase">Sellers / Stores</p>
            <p className="text-xl font-black text-primary">{sellers.length}</p>
          </div>
        </div>

        <div className="p-4 rounded-2xl border border-border/80 bg-surface shadow-2xs flex items-center gap-3">
          <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <UserCheck className="h-5 w-5" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-secondary uppercase">Customers</p>
            <p className="text-xl font-black text-primary">
              {users.filter((u) => (u.effective_role || u.role) === 'customer').length}
            </p>
          </div>
        </div>

        <div className="p-4 rounded-2xl border border-border/80 bg-surface shadow-2xs flex items-center gap-3">
          <div className="p-3 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-secondary uppercase">Administrators</p>
            <p className="text-xl font-black text-primary">
              {users.filter((u) => (u.effective_role || u.role) === 'admin').length}
            </p>
          </div>
        </div>
      </div>

      {/* Tabs & Search Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
        {/* Role Tabs */}
        <div className="flex items-center gap-1.5 bg-muted/60 p-1 rounded-2xl border border-border/70 text-xs font-semibold overflow-x-auto">
          <button
            type="button"
            onClick={() => setActiveTab('all')}
            className={`px-3.5 py-1.5 rounded-xl transition-all cursor-pointer ${
              activeTab === 'all'
                ? 'bg-surface dark:bg-zinc-800 text-primary shadow-xs font-bold'
                : 'text-secondary hover:text-primary'
            }`}
          >
            All Users ({users.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('sellers')}
            className={`px-3.5 py-1.5 rounded-xl transition-all cursor-pointer ${
              activeTab === 'sellers'
                ? 'bg-surface dark:bg-zinc-800 text-primary shadow-xs font-bold'
                : 'text-secondary hover:text-primary'
            }`}
          >
            Sellers ({sellers.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('customers')}
            className={`px-3.5 py-1.5 rounded-xl transition-all cursor-pointer ${
              activeTab === 'customers'
                ? 'bg-surface dark:bg-zinc-800 text-primary shadow-xs font-bold'
                : 'text-secondary hover:text-primary'
            }`}
          >
            Customers ({users.filter((u) => (u.effective_role || u.role) === 'customer').length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('admins')}
            className={`px-3.5 py-1.5 rounded-xl transition-all cursor-pointer ${
              activeTab === 'admins'
                ? 'bg-surface dark:bg-zinc-800 text-primary shadow-xs font-bold'
                : 'text-secondary hover:text-primary'
            }`}
          >
            Admins ({users.filter((u) => (u.effective_role || u.role) === 'admin').length})
          </button>
        </div>

        {/* Search Bar */}
        <div className="relative w-full sm:w-72">
          <Search className="h-4 w-4 text-secondary absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search email, name, store..."
            className="w-full bg-surface border border-border/80 rounded-2xl pl-9 pr-4 py-2 text-xs text-primary focus:outline-none focus:ring-2 focus:ring-accent/40"
          />
        </div>
      </div>

      {/* ── SECTION 1: SELLER PROFILES & STORE VERIFICATION ── */}
      {activeTab === 'sellers' ? (
        <section className="rounded-3xl border border-border/80 bg-surface shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-border/60 bg-surface/50 flex items-center justify-between">
            <h2 className="font-bold text-sm text-primary flex items-center gap-2">
              <Store className="h-4 w-4 text-purple-500" />
              <span>Merchant Profiles & Store Verification ({filteredSellers.length})</span>
            </h2>
            <span className="text-xs text-secondary">Real-time status synced with NeonDB</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-xs">
              <thead className="bg-muted/30 text-secondary uppercase font-bold text-[10px] border-b border-border/60">
                <tr>
                  <th className="py-3 px-6">Business / Store</th>
                  <th className="py-3 px-4">Merchant Email</th>
                  <th className="py-3 px-4">Store Slug</th>
                  <th className="py-3 px-4">Verification Status</th>
                  <th className="py-3 px-6 text-right">Admin Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filteredSellers.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-secondary">
                      No merchant profiles found matching search criteria.
                    </td>
                  </tr>
                ) : (
                  filteredSellers.map((seller) => (
                    <tr key={seller.id} className="hover:bg-muted/20 transition-colors">
                      <td className="py-3.5 px-6 font-bold text-primary">
                        <div className="flex items-center gap-2.5">
                          <div className="h-7 w-7 rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold text-xs">
                            {seller.business_name.charAt(0)}
                          </div>
                          <div>
                            <span className="block font-bold">{seller.business_name}</span>
                            <span className="block text-[10px] text-secondary">ID #{seller.id}</span>
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 font-medium text-secondary">{seller.user_email}</td>
                      <td className="py-3.5 px-4">
                        <span className="font-mono text-[11px] bg-muted/60 px-2 py-0.5 rounded-md text-primary">
                          {seller.store?.name || 'Default Store'}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1 text-[10px] font-bold px-2.5 py-1 rounded-full ${
                            seller.status === 'verified'
                              ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
                              : seller.status === 'suspended'
                              ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20'
                              : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                          }`}
                        >
                          {seller.status === 'verified' && <CheckCircle2 className="h-3 w-3" />}
                          {seller.status === 'suspended' && <XCircle className="h-3 w-3" />}
                          {seller.status === 'pending' && <AlertTriangle className="h-3 w-3" />}
                          <span className="capitalize">{seller.status}</span>
                        </span>
                      </td>
                      <td className="py-3.5 px-6 text-right">
                        <select
                          value={seller.status}
                          disabled={updatingId === seller.id}
                          onChange={(e) => updateSellerStatus(seller.id, e.target.value as SellerProfile['status'])}
                          className="bg-surface border border-border/80 rounded-xl px-2.5 py-1.5 text-xs font-semibold text-primary outline-none focus:ring-1 focus:ring-accent cursor-pointer disabled:opacity-50"
                        >
                          <option value="verified">Verify Store</option>
                          <option value="pending">Mark Pending</option>
                          <option value="suspended">Suspend Store</option>
                        </select>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      ) : (
        /* ── SECTION 2: GLOBAL USERS TABLE (All / Customers / Admins) ── */
        <section className="rounded-3xl border border-border/80 bg-surface shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-border/60 bg-surface/50 flex items-center justify-between">
            <h2 className="font-bold text-sm text-primary flex items-center gap-2">
              <Users className="h-4 w-4 text-indigo-500" />
              <span>Platform Users Directory ({filteredUsers.length})</span>
            </h2>
            <span className="text-xs text-secondary">Authenticated via NeonDB</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-xs">
              <thead className="bg-muted/30 text-secondary uppercase font-bold text-[10px] border-b border-border/60">
                <tr>
                  <th className="py-3 px-6">User Account</th>
                  <th className="py-3 px-4">Full Name</th>
                  <th className="py-3 px-4">Current Role</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-6 text-right">Manage Role</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-secondary">
                      No users found matching your search.
                    </td>
                  </tr>
                ) : (
                  filteredUsers.map((u) => {
                    const role = u.effective_role || u.role;
                    const isCurrent = currentUser?.id === u.id;

                    return (
                      <tr key={u.id} className="hover:bg-muted/20 transition-colors">
                        <td className="py-3.5 px-6">
                          <div className="flex items-center gap-2.5">
                            <div className="h-7 w-7 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 text-white flex items-center justify-center font-bold text-[11px] shadow-2xs">
                              {u.email.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <span className="block font-bold text-primary">{u.email}</span>
                              <span className="block text-[10px] text-secondary">
                                User ID #{u.id} {isCurrent ? '• (You)' : ''}
                              </span>
                            </div>
                          </div>
                        </td>
                        <td className="py-3.5 px-4 font-semibold text-primary">
                          {[u.first_name, u.last_name].filter(Boolean).join(' ') || u.username || '—'}
                        </td>
                        <td className="py-3.5 px-4">
                          <span
                            className={`inline-flex items-center gap-1 text-[10px] font-bold px-2.5 py-0.5 rounded-full capitalize ${
                              role === 'admin'
                                ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                                : role === 'seller'
                                ? 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20'
                                : 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20'
                            }`}
                          >
                            {role}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                            Active
                          </span>
                        </td>
                        <td className="py-3.5 px-6 text-right">
                          <select
                            value={role}
                            disabled={isCurrent || updatingId === u.id}
                            onChange={(e) =>
                              updateUserRole(u.id, e.target.value as 'customer' | 'seller' | 'admin')
                            }
                            className="bg-surface border border-border/80 rounded-xl px-2.5 py-1.5 text-xs font-semibold text-primary outline-none focus:ring-1 focus:ring-accent cursor-pointer disabled:opacity-40"
                          >
                            <option value="customer">Customer</option>
                            <option value="seller">Seller</option>
                            <option value="admin">Administrator</option>
                          </select>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
