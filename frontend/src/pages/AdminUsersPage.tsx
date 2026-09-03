import { useEffect, useMemo, useState } from 'react';
import { apiRequest, unwrapList } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { useTranslation } from '../i18n/LocaleContext';
import {
  CheckCircle2,
  RefreshCw,
  UserPlus,
  Shield,
  Users as UsersIcon,
  Store,
  AlertTriangle,
} from 'lucide-react';
import UsersMetrics from '../seller/components/users/UsersMetrics';
import UsersTable from '../seller/components/users/UsersTable';
import UserDetailDrawer from '../seller/components/users/UserDetailDrawer';
import UserFormModal from '../seller/components/users/UserFormModal';
import type { Plan, Role, Status, User as TableUser } from '../seller/types/user';

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

  const [rawUsers, setRawUsers] = useState<any[]>([]);
  const [sellers, setSellers] = useState<SellerProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Modal & Drawer State
  const [selectedUser, setSelectedUser] = useState<TableUser | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<TableUser | null>(null);

  const showNotification = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  function loadData() {
    setLoading(true);
    setError('');
    Promise.all([
      apiRequest<any>('/auth/users/?page_size=200', { token }),
      apiRequest<any>('/sellers/profiles/?page_size=200', { token }),
    ])
      .then(([usersRes, sellersRes]) => {
        const userList = unwrapList<any>(usersRes);
        const sellerList = unwrapList<SellerProfile>(sellersRes);
        setRawUsers(userList);
        setSellers(sellerList);
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

  // Map raw backend Django users to TableUser interface
  const mappedUsers = useMemo<TableUser[]>(() => {
    return rawUsers.map((u) => {
      const first = (u.first_name || '').trim();
      const last = (u.last_name || '').trim();
      const fullName = first || last ? `${first} ${last}`.trim() : (u.email ? u.email.split('@')[0] : 'User');

      let role: Role = 'Customer';
      const rawRole = (u.role || '').toLowerCase();
      if (rawRole === 'admin' || u.is_superuser || u.is_staff) {
        role = 'Admin';
      } else if (rawRole === 'seller') {
        role = 'Seller';
      } else if (rawRole === 'customer') {
        role = 'Customer';
      } else {
        role = 'User';
      }

      let plan: Plan = 'Free';
      if (role === 'Admin') plan = 'Enterprise';
      else if (role === 'Seller') plan = 'Pro';
      else plan = 'Free';

      const status: Status = u.is_active !== false ? 'Active' : 'Inactive';

      return {
        id: String(u.id),
        avatar:
          u.avatar ||
          `https://ui-avatars.com/api/?name=${encodeURIComponent(fullName)}&background=3b82f6&color=fff`,
        fullName,
        email: u.email || '',
        role,
        plan,
        status,
        country: 'India',
        joinedAt: u.date_joined || new Date().toISOString(),
        lastLogin: u.last_login || u.date_joined || new Date().toISOString(),
      };
    });
  }, [rawUsers]);

  // Handlers
  const handleViewUser = (user: TableUser) => {
    setSelectedUser(user);
    setIsDrawerOpen(true);
  };

  const handleOpenAddModal = () => {
    setEditingUser(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (user: TableUser) => {
    setEditingUser(user);
    setIsModalOpen(true);
  };

  const handleSaveUser = async (userData: Partial<TableUser>) => {
    if (editingUser) {
      // Live Backend Update
      try {
        const patchPayload: Record<string, any> = {};
        if (userData.fullName) {
          const parts = userData.fullName.trim().split(' ');
          patchPayload.first_name = parts[0] || '';
          patchPayload.last_name = parts.slice(1).join(' ') || '';
        }
        if (userData.email) patchPayload.email = userData.email;
        if (userData.role) patchPayload.role = userData.role.toLowerCase();
        if (userData.status) patchPayload.is_active = userData.status === 'Active';

        await apiRequest(`/auth/users/${editingUser.id}/`, {
          token,
          method: 'PATCH',
          body: JSON.stringify(patchPayload),
        });

        showNotification(`Updated profile for ${userData.fullName || editingUser.fullName}`);
        loadData();
      } catch (err: any) {
        showNotification(err?.message || 'Failed to update user profile in database.');
      }
    } else {
      // Live Backend Create
      try {
        const parts = (userData.fullName || 'New User').trim().split(' ');
        const createPayload = {
          email: userData.email || `user_${Date.now()}@example.in`,
          first_name: parts[0] || '',
          last_name: parts.slice(1).join(' ') || '',
          role: (userData.role || 'Customer').toLowerCase(),
          password: 'Password@123',
        };

        await apiRequest('/auth/register/', {
          token,
          method: 'POST',
          body: JSON.stringify(createPayload),
        });

        showNotification(`Added new user ${userData.fullName} to database.`);
        loadData();
      } catch (err: any) {
        showNotification(err?.message || 'Failed to create user in database.');
      }
    }
  };

  const handleDeleteUser = async (userId: string) => {
    try {
      await apiRequest(`/auth/users/${userId}/`, {
        token,
        method: 'DELETE',
      });
      showNotification(`Deleted user #${userId} from database.`);
      loadData();
    } catch (err: any) {
      showNotification(err?.message || 'Failed to delete user.');
    }
  };

  const handleBulkDelete = async (userIds: string[]) => {
    try {
      for (const id of userIds) {
        await apiRequest(`/auth/users/${id}/`, {
          token,
          method: 'DELETE',
        }).catch(() => {});
      }
      showNotification(`Deleted ${userIds.length} users successfully.`);
      loadData();
    } catch (err: any) {
      showNotification('Bulk delete finished with some notices.');
      loadData();
    }
  };

  const handleStatusChange = async (userId: string, status: Status) => {
    try {
      await apiRequest(`/auth/users/${userId}/`, {
        token,
        method: 'PATCH',
        body: JSON.stringify({ is_active: status === 'Active' }),
      });
      showNotification(`User #${userId} status set to "${status}".`);
      loadData();
    } catch (err: any) {
      showNotification(err?.message || 'Failed to update user status.');
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50/50 p-4 transition-colors duration-300 sm:p-6 lg:p-8 dark:bg-zinc-950">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Toast Notification */}
        {toastMessage && (
          <div className="fixed right-6 top-6 z-50 flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-xs font-semibold text-emerald-600 shadow-xl backdrop-blur-md dark:text-emerald-400">
            <CheckCircle2 className="h-4 w-4" />
            <span>{toastMessage}</span>
          </div>
        )}

        {/* Header with Breadcrumb & Action Buttons */}
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">
                ADMIN / USERS
              </span>
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
                Live Sync ({mappedUsers.length} Users)
              </span>
            </div>
            <h1 className="mt-1 text-2xl font-black tracking-tight text-zinc-900 sm:text-3xl dark:text-zinc-100">
              User Management
            </h1>
            <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
              Manage permissions, roles, and account statuses across your workspace.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={loadData}
              disabled={loading}
              className="flex items-center gap-2 rounded-xl border border-zinc-200 bg-white px-3.5 py-2 text-xs font-semibold text-zinc-700 shadow-xs transition-colors hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh Data
            </button>

            <button
              onClick={handleOpenAddModal}
              className="flex items-center gap-2 rounded-xl bg-zinc-900 px-4 py-2 text-xs font-semibold text-white shadow-xs transition-colors hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              <UserPlus className="h-3.5 w-3.5" />
              Add User
            </button>
          </div>
        </div>

        {/* Error Notice */}
        {error && (
          <div className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-medium text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-400">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <p>{error}</p>
          </div>
        )}

        {/* Top Metric Cards & Charts */}
        <UsersMetrics users={mappedUsers} />

        {/* Accounts Directory Table */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-zinc-900 dark:text-zinc-100">
              Accounts Directory
            </h2>
            <span className="text-xs text-zinc-500 dark:text-zinc-400">
              Showing {mappedUsers.length} registered accounts in NeonDB
            </span>
          </div>

          <UsersTable
            users={mappedUsers}
            onViewUser={handleViewUser}
            onEditUser={handleOpenEditModal}
            onDeleteUser={handleDeleteUser}
            onBulkDelete={handleBulkDelete}
            onStatusChange={handleStatusChange}
          />
        </div>

        {/* User Detail Drawer */}
        <UserDetailDrawer
          user={selectedUser}
          isOpen={isDrawerOpen}
          onClose={() => setIsDrawerOpen(false)}
          onEdit={(user) => {
            setIsDrawerOpen(false);
            handleOpenEditModal(user);
          }}
          onStatusChange={handleStatusChange}
          onDelete={handleDeleteUser}
        />

        {/* User Create / Edit Modal */}
        <UserFormModal
          isOpen={isModalOpen}
          userToEdit={editingUser}
          onClose={() => setIsModalOpen(false)}
          onSubmit={handleSaveUser}
        />
      </div>
    </div>
  );
}
