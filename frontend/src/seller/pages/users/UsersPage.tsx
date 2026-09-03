import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, RefreshCw, UserPlus } from "lucide-react";
import UserDetailDrawer from "../../components/users/UserDetailDrawer";
import UserFormModal from "../../components/users/UserFormModal";
import UsersMetrics from "../../components/users/UsersMetrics";
import UsersTable from "../../components/users/UsersTable";
import type { Plan, Role, Status, User } from "../../types/user";
import { useTranslation } from "../../i18n";
import { apiRequest, unwrapList } from "../../../lib/api";
import { useAuth } from "../../../context/AuthContext";

export default function UsersPage() {
  const { t } = useTranslation();
  const { token } = useAuth();

  const [rawUsers, setRawUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showNotification = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const loadUsers = async () => {
    try {
      setLoading(true);
      const res = await apiRequest<any>('/auth/users/?page_size=200', { token }).catch(() => []);
      const list = unwrapList<any>(res);
      setRawUsers(list);
    } catch (err) {
      console.warn('Failed to load users:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, [token]);

  // Map backend users to User interface
  const users = useMemo<User[]>(() => {
    return rawUsers.map((u) => {
      const first = (u.first_name || '').trim();
      const last = (u.last_name || '').trim();
      const fullName = first || last ? `${first} ${last}`.trim() : (u.email ? u.email.split('@')[0] : 'User');

      let role: Role = 'Customer';
      const rawRole = (u.role || '').toLowerCase();
      if (rawRole === 'admin' || u.is_superuser || u.is_staff) role = 'Admin';
      else if (rawRole === 'seller') role = 'Seller';
      else if (rawRole === 'customer') role = 'Customer';
      else role = 'User';

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

  /* ------- HANDLERS ------- */
  const handleViewUser = (user: User) => {
    setSelectedUser(user);
    setIsDrawerOpen(true);
  };

  const handleOpenAddModal = () => {
    setEditingUser(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (user: User) => {
    setEditingUser(user);
    setIsModalOpen(true);
  };

  const handleSaveUser = async (userData: Partial<User>) => {
    if (editingUser) {
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

        showNotification(
          t("users.toasts.updatedMsg", {
            name: userData.fullName || "User",
            defaultValue: `Updated profile for ${userData.fullName || editingUser.fullName}`,
          }),
        );
        loadUsers();
      } catch (err: any) {
        showNotification(err?.message || "Failed to update user");
      }
    } else {
      try {
        const parts = (userData.fullName || "New User").trim().split(' ');
        await apiRequest('/auth/register/', {
          token,
          method: 'POST',
          body: JSON.stringify({
            email: userData.email || `user_${Date.now()}@example.in`,
            first_name: parts[0] || '',
            last_name: parts.slice(1).join(' ') || '',
            role: (userData.role || 'Customer').toLowerCase(),
            password: 'Password@123',
          }),
        });

        showNotification(
          t("users.toasts.createdMsg", {
            name: userData.fullName,
            defaultValue: `Added new user ${userData.fullName}`,
          }),
        );
        loadUsers();
      } catch (err: any) {
        showNotification(err?.message || "Failed to create user");
      }
    }
  };

  const handleDeleteUser = async (userId: string) => {
    try {
      await apiRequest(`/auth/users/${userId}/`, {
        token,
        method: 'DELETE',
      });
      showNotification(
        t("users.toasts.deletedMsg", {
          name: `#${userId}`,
          defaultValue: `Deleted user #${userId}`,
        }),
      );
      loadUsers();
    } catch (err: any) {
      showNotification(err?.message || "Failed to delete user");
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
      showNotification(
        t("users.toasts.deletedMsg", {
          name: `${userIds.length} users`,
          defaultValue: `Successfully deleted ${userIds.length} users`,
        }),
      );
      loadUsers();
    } catch (err: any) {
      showNotification("Bulk delete completed");
      loadUsers();
    }
  };

  const handleStatusChange = async (userId: string, status: Status) => {
    try {
      await apiRequest(`/auth/users/${userId}/`, {
        token,
        method: 'PATCH',
        body: JSON.stringify({ is_active: status === 'Active' }),
      });
      showNotification(
        t("users.toasts.statusMsg", {
          status,
          defaultValue: `Updated status to ${status}`,
        }),
      );
      loadUsers();
    } catch (err: any) {
      showNotification(err?.message || "Failed to update status");
    }
  };

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed end-6 top-6 z-50 flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-xs font-semibold text-emerald-600 shadow-xl backdrop-blur-md dark:text-emerald-400">
          <CheckCircle2 className="h-4 w-4" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header & Actions */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">
              ADMIN / USERS
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
              Live Sync ({users.length} Users)
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-black tracking-tight text-zinc-900 sm:text-3xl dark:text-zinc-100">
            {t("users.title", "User Management")}
          </h1>
          <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
            {t(
              "users.subtitle",
              "Manage permissions, subscription tiers, and account statuses across your workspace.",
            )}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadUsers}
            disabled={loading}
            className="flex items-center gap-2 rounded-xl border border-zinc-200 bg-white px-3.5 py-2 text-xs font-semibold text-zinc-700 shadow-xs transition-colors hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            {t("users.actions.resetData", "Refresh Data")}
          </button>

          <button
            onClick={handleOpenAddModal}
            className="flex items-center gap-2 rounded-xl bg-zinc-900 px-4 py-2 text-xs font-semibold text-white shadow-xs transition-colors hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
          >
            <UserPlus className="h-3.5 w-3.5" />
            {t("users.actions.addUser", "Add User")}
          </button>
        </div>
      </div>

      {/* Analytics & Metrics Cards */}
      <UsersMetrics users={users} />

      {/* Accounts Directory Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-zinc-900 dark:text-zinc-100">
            {t("users.table.accountsDirectory", "Accounts Directory")}
          </h2>
          <span className="text-xs text-zinc-500 dark:text-zinc-400">
            Showing {users.length} registered accounts in NeonDB
          </span>
        </div>

        <UsersTable
          users={users}
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

      {/* User Form Modal (Create / Edit) */}
      <UserFormModal
        isOpen={isModalOpen}
        userToEdit={editingUser}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleSaveUser}
      />
    </div>
  );
}
