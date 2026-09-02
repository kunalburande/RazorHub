import React from "react";
import { Link } from "react-router-dom";
import {
  Package,
  Users,
  FileText,
  ShoppingCart,
  CreditCard,
  BarChart2,
  Bot,
  ShieldAlert,
  RotateCcw,
  ClipboardList
} from "lucide-react";

const modules = [
  { name: "Catalog", href: "/seller/products", icon: <Package />, desc: "Products & inventory" },
  { name: "Customers", href: "/seller/users", icon: <Users />, desc: "Customer profiles" },
  { name: "Orders", href: "/seller/orders", icon: <FileText />, desc: "Order management" },
  { name: "Cart", href: "/seller/cart", icon: <ShoppingCart />, desc: "Cart & quotes" },
  { name: "Payments", href: "/seller/payments", icon: <CreditCard />, desc: "Razorpay integration" },
  { name: "Revenue", href: "/seller/revenue", icon: <BarChart2 />, desc: "Revenue intelligence" },
  { name: "Agents", href: "/seller/agents", icon: <Bot />, desc: "AI agent console" },
  { name: "Policies", href: "/seller/policies", icon: <ShieldAlert />, desc: "Policy engine" },
  { name: "Recovery", href: "/seller/recovery", icon: <RotateCcw />, desc: "Cart & payment recovery" },
  { name: "Audit", href: "/seller/audit", icon: <ClipboardList />, desc: "Event audit trail" },
];

export default function MerchantOSDashboard() {
  return (
    <div className="min-h-[85vh] bg-gradient-to-br from-white via-gray-50 to-white dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 rounded-3xl p-8 border border-gray-200 dark:border-gray-800 shadow-2xl transition-colors duration-300">
      <div className="mb-12">
        <h1 className="text-4xl font-extrabold text-gray-900 dark:text-white tracking-tight">
          RazorHub<span className="text-blue-500">Seller</span>
        </h1>
        <p className="text-base text-gray-600 dark:text-gray-400 mt-2">
          AI Growth & Agentic Commerce Platform
        </p>
      </div>

      <div className="mb-10">
        <h2 className="text-xl font-bold text-gray-800 dark:text-gray-200">Store Modules</h2>
        <p className="text-sm text-gray-500 mt-1">
          Every money action is explainable, bounded, and gated.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
        {modules.map((m) => (
          <Link
            key={m.name}
            to={m.href}
            className="group flex flex-col p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50 hover:bg-white dark:hover:bg-gray-800/80 hover:border-blue-200 dark:hover:border-gray-700 hover:shadow-[0_0_20px_rgba(59,130,246,0.15)] transition-all duration-300"
          >
            <div className="text-gray-500 dark:text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-500 transition-colors mb-5 [&>svg]:w-9 [&>svg]:h-9">
              {m.icon}
            </div>
            <h3 className="text-gray-900 dark:text-white font-bold group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors text-xl">
              {m.name}
            </h3>
            <p className="text-sm text-gray-500 mt-2">{m.desc}</p>
          </Link>
        ))}
      </div>

      <section className="mt-16 p-6 rounded-2xl border border-amber-200 dark:border-amber-900/40 bg-amber-50 dark:bg-amber-950/20 shadow-inner">
        <h3 className="text-amber-600 dark:text-amber-500 font-bold flex items-center gap-2">
          ⚡ Architecture Rule
        </h3>
        <p className="text-sm text-amber-800 dark:text-amber-200/80 mt-2 leading-relaxed">
          LLMs may reason and propose actions, but deterministic code validates
          money, inventory, price, budget, consent, policy, and payment actions
          before execution.
        </p>
      </section>
    </div>
  );
}
