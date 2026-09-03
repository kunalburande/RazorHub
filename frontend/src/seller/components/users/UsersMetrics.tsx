import { useMemo } from "react";

import {
  ShieldCheck,
  ShoppingBag,
  Store,
  TrendingUp,
  UserCheck,
  Users,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useTranslation } from "../../i18n";
import type { User } from "../../types/user";

interface UsersMetricsProps {
  users: User[];
}

export default function UsersMetrics({ users }: UsersMetricsProps) {
  const { t } = useTranslation();
  const stats = useMemo(() => {
    const total = users.length;
    const active = users.filter((u) => u.status === "Active").length;
    const customers = users.filter((u) => u.role === "Customer" || u.role === "User").length;
    const sellers = users.filter((u) => u.role === "Seller").length;
    const admins = users.filter((u) => u.role === "Admin").length;
    const activeRate = total ? Math.round((active / total) * 100) : 0;
    const customerRate = total ? Math.round((customers / total) * 100) : 0;
    const sellerRate = total ? Math.round((sellers / total) * 100) : 0;

    return {
      total,
      active,
      customers,
      sellers,
      admins,
      activeRate,
      customerRate,
      sellerRate,
    };
  }, [users]);

  // Compute real monthly user onboarding data from actual users joined date
  const monthlyData = useMemo(() => {
    const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth();

    const data = [];
    for (let i = 5; i >= 0; i--) {
      const targetDate = new Date(currentYear, currentMonth - i, 1);
      const mLabel = monthNames[targetDate.getMonth()];
      const endOfTargetMonth = new Date(targetDate.getFullYear(), targetDate.getMonth() + 1, 0, 23, 59, 59);

      const cumulativeUsers = users.filter((u) => {
        const join = new Date(u.joinedAt);
        return !isNaN(join.getTime()) && join <= endOfTargetMonth;
      }).length;

      const activeInMonth = users.filter((u) => {
        const join = new Date(u.joinedAt);
        return !isNaN(join.getTime()) && join <= endOfTargetMonth && u.status === "Active";
      }).length;

      data.push({
        month: mLabel,
        users: cumulativeUsers,
        active: activeInMonth,
      });
    }
    return data;
  }, [users]);

  // Platform User Role Breakdown Data
  const roleData = useMemo(() => {
    return [
      {
        name: "Customer",
        label: t("common.customer", "Customers"),
        value: stats.customers,
        color: "#06b6d4", // Cyan
      },
      {
        name: "Seller",
        label: t("common.seller", "Sellers"),
        value: stats.sellers,
        color: "#10b981", // Emerald
      },
      {
        name: "Admin",
        label: t("common.admin", "Admins"),
        value: stats.admins,
        color: "#8b5cf6", // Violet
      },
    ];
  }, [stats, t]);

  return (
    <div className="space-y-6">
      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Card 1: Total Accounts */}
        <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs backdrop-blur-md transition-all hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900/80 dark:hover:border-zinc-700">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium tracking-wider text-zinc-500 uppercase dark:text-zinc-400">
              {t("users.metrics.totalUsers", "Total Accounts")}
            </span>
            <div className="rounded-lg bg-zinc-100 p-2 text-zinc-700 dark:bg-zinc-800/80 dark:text-zinc-300">
              <Users className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              {stats.total}
            </span>
            <span className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 dark:text-blue-400">
              <TrendingUp className="h-3 w-3" /> Live
            </span>
          </div>
          <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
            Registered platform accounts
          </p>
          <div className="mt-3 h-8">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={monthlyData}>
                <defs>
                  <linearGradient
                    id="totalGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Area
                  type="monotone"
                  dataKey="users"
                  stroke="#3b82f6"
                  strokeWidth={1.5}
                  fill="url(#totalGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Card 2: Active Users */}
        <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs backdrop-blur-md transition-all hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900/80 dark:hover:border-zinc-700">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium tracking-wider text-zinc-500 uppercase dark:text-zinc-400">
              {t("users.metrics.activeNow", "Active Users")}
            </span>
            <div className="rounded-lg bg-emerald-500/10 p-2 text-emerald-600 dark:text-emerald-400">
              <UserCheck className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              {stats.active}
            </span>
            <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">
              {stats.activeRate}% {t("common.active", "active")}
            </span>
          </div>
          <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
            {t("users.metrics.onlineSessions", "LoggedIn in last 30 days")}
          </p>
          <div className="mt-3 h-8">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={monthlyData}>
                <defs>
                  <linearGradient
                    id="activeGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Area
                  type="monotone"
                  dataKey="active"
                  stroke="#10b981"
                  strokeWidth={1.5}
                  fill="url(#activeGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Card 3: Customers & Buyers */}
        <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs backdrop-blur-md transition-all hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900/80 dark:hover:border-zinc-700">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium tracking-wider text-zinc-500 uppercase dark:text-zinc-400">
              Customers & Buyers
            </span>
            <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-600 dark:text-cyan-400">
              <ShoppingBag className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              {stats.customers}
            </span>
            <span className="text-xs font-medium text-cyan-600 dark:text-cyan-400">
              {stats.customerRate}% of accounts
            </span>
          </div>
          <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
            Active shoppers browsing the marketplace
          </p>
          <div className="mt-4 flex h-2 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
            <div
              className="bg-cyan-500"
              style={{
                width: `${stats.customerRate}%`,
              }}
            />
          </div>
        </div>

        {/* Card 4: Verified Merchants */}
        <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs backdrop-blur-md transition-all hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900/80 dark:hover:border-zinc-700">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium tracking-wider text-zinc-500 uppercase dark:text-zinc-400">
              Verified Merchants
            </span>
            <div className="rounded-lg bg-emerald-500/10 p-2 text-emerald-600 dark:text-emerald-400">
              <Store className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              {stats.sellers}
            </span>
            <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
              Store Owners
            </span>
          </div>
          <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
            Active multi-vendor storefronts
          </p>
          <div className="mt-3 flex items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
            <span>Store KYC Verified</span>
          </div>
        </div>
      </div>

      {/* Visual Charts Grid */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* User Growth Trend Chart */}
        <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs backdrop-blur-md lg:col-span-2 dark:border-zinc-800 dark:bg-zinc-900/80">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                {t(
                  "users.metrics.cumulativeVsActive",
                  "User Acquisition & Activity Trend",
                )}
              </h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                Real registered accounts vs active sessions
              </p>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-xs bg-blue-500" />
                <span className="text-zinc-600 dark:text-zinc-400">
                  {t("users.metrics.totalLegend", "Total")}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-xs bg-emerald-500" />
                <span className="text-zinc-600 dark:text-zinc-400">
                  {t("users.metrics.activeLegend", "Active")}
                </span>
              </div>
            </div>
          </div>
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={monthlyData}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="growthTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="growthActive" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="month"
                  stroke="#a1a1aa"
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: "#e4e4e7" }}
                />
                <YAxis
                  stroke="#a1a1aa"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "rgba(24, 24, 27, 0.95)",
                    borderColor: "#3f3f46",
                    borderRadius: "8px",
                    color: "#f4f4f5",
                    fontSize: "12px",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="users"
                  name={t("users.metrics.totalLegend", "Total Accounts")}
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#growthTotal)"
                />
                <Area
                  type="monotone"
                  dataKey="active"
                  name={t("users.metrics.activeLegend", "Active Users")}
                  stroke="#10b981"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#growthActive)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* User Role Breakdown Pie Chart */}
        <div className="flex flex-col justify-between rounded-xl border border-zinc-200 bg-white p-5 shadow-xs backdrop-blur-md dark:border-zinc-800 dark:bg-zinc-900/80">
          <div>
            <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
              Platform Role Distribution
            </h3>
            <p className="mb-2 text-xs text-zinc-500 dark:text-zinc-400">
              Breakdown across Customers, Sellers, and Staff
            </p>
          </div>

          <div className="my-2 flex h-44 w-full items-center justify-center">
            {stats.total === 0 ? (
              <div className="text-center text-xs text-zinc-500 dark:text-zinc-400">
                No accounts registered yet
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={roleData}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={70}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {roleData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.color}
                        stroke="transparent"
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "rgba(24, 24, 27, 0.95)",
                      borderColor: "#3f3f46",
                      borderRadius: "8px",
                      color: "#f4f4f5",
                      fontSize: "12px",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="grid grid-cols-3 gap-2 border-t border-zinc-100 pt-2 dark:border-zinc-800/80">
            {roleData.map((item) => (
              <div key={item.name} className="text-center">
                <div className="flex items-center justify-center gap-1 text-[11px] text-zinc-500 dark:text-zinc-400">
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  {item.label}
                </div>
                <div className="mt-0.5 text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                  {item.value}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
