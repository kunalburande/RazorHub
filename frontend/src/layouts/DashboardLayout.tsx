import { Link, NavLink, Outlet } from 'react-router-dom';
import { BarChart3, Bell, Bot, Building2, ClipboardList, Heart, LayoutDashboard, Package, Settings, Sparkles, Store, Ticket, Users } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import ThemeToggle from '../components/ThemeToggle';
import { useTranslation } from '../i18n/LocaleContext';
import BrandLogo from '../components/BrandLogo';

export default function DashboardLayout() {
  const { user, logout } = useAuth();
  const { t } = useTranslation();
  const role = user?.effective_role || 'customer';

  const roleNav = {
    customer: [
      { to: '/dashboard', label: t('dashboard.navAccount', { defaultValue: 'Account' }), icon: LayoutDashboard },
      { to: '/wishlist', label: t('nav.wishlist', { defaultValue: 'Wishlist' }), icon: Heart },
      { to: '/ai', label: t('dashboard.navAI', { defaultValue: 'AI' }), icon: Sparkles },
      { to: '/dashboard/orders', label: t('dashboard.navOrders', { defaultValue: 'Orders' }), icon: ClipboardList },
      { to: '/dashboard/tickets', label: t('dashboard.navSupport', { defaultValue: 'Support' }), icon: Ticket },
    ],
    seller: [
      { to: '/seller', label: t('dashboard.navDashboard', { defaultValue: 'Dashboard' }), icon: BarChart3 },
      { to: '/agents', label: 'Agent Studio', icon: Bot },
      { to: '/banking', label: 'Banking', icon: Building2 },
      { to: '/seller', label: t('dashboard.navProducts', { defaultValue: 'Products' }), icon: Package },
      { to: '/seller/orders', label: t('dashboard.navOrders', { defaultValue: 'Orders' }), icon: ClipboardList },
      { to: '/seller/users', label: t('dashboard.navCustomers', { defaultValue: 'Customers' }), icon: Users },
      { to: '/seller/settings', label: t('nav.settings', { defaultValue: 'Settings' }), icon: Settings },
    ],
    admin: [
      { to: '/admin', label: t('dashboard.navOverview', { defaultValue: 'Overview' }), icon: LayoutDashboard },
      { to: '/agents', label: 'Agent Studio', icon: Bot },
      { to: '/ai', label: t('dashboard.navAI', { defaultValue: 'AI' }), icon: Sparkles },
      { to: '/admin/users', label: t('dashboard.navUsers', { defaultValue: 'Users' }), icon: Users },
      { to: '/admin/orders', label: t('dashboard.navOrders', { defaultValue: 'Orders' }), icon: ClipboardList },
      { to: '/admin/crm', label: t('dashboard.navCrm', { defaultValue: 'CRM' }), icon: Bell },
      { to: '/admin/settings', label: t('dashboard.navSettings', { defaultValue: 'Settings' }), icon: Settings },
    ],
  };


  const nav = roleNav[role];

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b border-border bg-surface">
        <div className="mx-auto flex h-16 max-w-[1360px] w-full items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link to="/" className="group flex items-center transition-transform hover:opacity-95 active:scale-95">
            <BrandLogo size="md" />
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <span className="hidden text-secondary sm:inline">{user?.email}</span>
            <ThemeToggle />
            <button type="button" onClick={logout} className="font-semibold text-accent">
              {t('dashboard.logout', { defaultValue: 'Logout' })}
            </button>
          </div>
        </div>
      </div>

      {role === 'customer' ? (
        <Outlet />
      ) : (
        <div className="mx-auto grid max-w-[1360px] w-full min-w-0 grid-cols-1 gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[240px_minmax(0,1fr)] lg:px-8">
          <aside className="rounded-lg border border-border bg-surface p-3 lg:sticky lg:top-20 lg:h-fit">
            <div className="mb-3 flex items-center gap-2 px-3 py-2 text-sm font-bold uppercase text-secondary">
              <Store className="h-4 w-4" />
              {t(`dashboard.role${role.charAt(0).toUpperCase() + role.slice(1)}`, { defaultValue: role })}
            </div>
            <nav className="grid gap-1">
              {nav.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end
                    className={({ isActive }) =>
                      `flex items-center gap-3 rounded-md px-3 py-2 text-sm font-semibold transition-colors ${
                        isActive ? 'bg-accent text-background' : 'text-secondary hover:bg-background hover:text-primary'
                      }`
                    }
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </NavLink>
                );
              })}
            </nav>
          </aside>

          <main className="min-w-0 w-full overflow-hidden">
            <Outlet />
          </main>
        </div>
      )}
    </div>
  );
}
