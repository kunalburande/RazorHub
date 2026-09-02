import React from "react";
import { BarChart2, TrendingUp, DollarSign } from "lucide-react";
import Button from "../components/ui/Button";

export default function RevenueIntelligence() {
  return (
    <div className="min-h-[85vh] bg-gradient-to-br from-white via-gray-50 to-white dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 rounded-3xl p-8 border border-gray-200 dark:border-gray-800 shadow-2xl text-gray-900 dark:text-white transition-colors duration-300">
      <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-3">
            <BarChart2 className="h-8 w-8 text-pink-500" />
            Revenue Intelligence
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2 text-sm">
            Deep insights into organic vs agent-driven sales.
          </p>
        </div>
        <Button className="bg-pink-600 hover:bg-pink-700 text-white rounded-xl px-4 py-2 font-bold shadow-sm">
          Download Report
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/60 shadow-inner relative overflow-hidden">
          <div className="absolute -right-4 -bottom-4 text-gray-200 dark:text-gray-800/30">
            <DollarSign className="w-32 h-32" />
          </div>
          <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 relative z-10">Total Revenue (30d)</h3>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2 relative z-10">₹8,45,200</p>
          <p className="text-xs text-green-600 dark:text-green-400 mt-2 flex items-center gap-1 relative z-10">
            <TrendingUp className="w-3 h-3" /> +12.5% vs last month
          </p>
        </div>
        
        <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/60 shadow-inner relative overflow-hidden">
          <div className="absolute -right-4 -bottom-4 text-gray-200 dark:text-gray-800/30">
            <BarChart2 className="w-32 h-32" />
          </div>
          <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 relative z-10">AI-Assisted Sales</h3>
          <p className="text-3xl font-bold text-pink-600 dark:text-pink-400 mt-2 relative z-10">₹3,12,500</p>
          <p className="text-xs text-green-600 dark:text-green-400 mt-2 flex items-center gap-1 relative z-10">
            <TrendingUp className="w-3 h-3" /> 37% of total revenue
          </p>
        </div>

        <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/60 shadow-inner">
          <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400">Avg Order Value</h3>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">₹4,200</p>
          <div className="mt-3 text-xs text-gray-500">
            <div className="flex justify-between mb-1">
              <span>Organic AOV:</span>
              <span className="text-gray-700 dark:text-gray-300">₹3,800</span>
            </div>
            <div className="flex justify-between">
              <span>AI AOV:</span>
              <span className="text-pink-600 dark:text-pink-400 font-bold">₹4,900</span>
            </div>
          </div>
        </div>
      </div>

      <div className="p-8 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50/30 dark:bg-gray-900/40 text-center flex flex-col items-center justify-center min-h-[300px]">
        <BarChart2 className="w-16 h-16 text-gray-300 dark:text-gray-700 mb-4" />
        <h3 className="text-xl font-bold text-gray-700 dark:text-gray-400">Advanced Charting Coming Soon</h3>
        <p className="text-sm text-gray-500 dark:text-gray-600 mt-2 max-w-md">
          Recharts integration for detailed time-series visualization of agent performance, 
          discount margins, and category-wise sales splits is currently being provisioned.
        </p>
      </div>
    </div>
  );
}
