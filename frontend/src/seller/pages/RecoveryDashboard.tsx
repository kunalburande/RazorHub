import React, { useState, useEffect } from "react";
import { RotateCcw, AlertTriangle, CheckCircle2 } from "lucide-react";
import Button from "../components/ui/Button";
import { apiRequest, unwrapList } from "../../lib/api";

export default function RecoveryDashboard() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await apiRequest<any>("/intelligence/recovery/");
        setTasks(unwrapList(response));
      } catch (err) {
        console.error("Error fetching recovery tasks:", err);
        setTasks([]);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);


  return (
    <div className="min-h-[85vh] bg-gradient-to-br from-white via-gray-50 to-white dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 rounded-3xl p-8 border border-gray-200 dark:border-gray-800 shadow-2xl text-gray-900 dark:text-white transition-colors duration-300">
      <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-3">
            <RotateCcw className="h-8 w-8 text-orange-500" />
            Revenue Recovery
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2 text-sm max-w-2xl">
            Monitor and manage AI-driven cart abandonment and payment failure recovery campaigns.
          </p>
        </div>
        <Button className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl px-4 py-2 font-bold shadow-sm">
          Start Campaign
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-orange-50 dark:bg-orange-950/20 shadow-inner relative overflow-hidden">
          <div className="absolute -right-4 -bottom-4 text-orange-200/50 dark:text-orange-900/30">
            <AlertTriangle className="w-32 h-32" />
          </div>
          <h3 className="text-sm font-semibold text-orange-800 dark:text-orange-500 relative z-10">Active Cart Recoveries</h3>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2 relative z-10">{tasks.filter((t: any) => t.status === 'in_progress').length}</p>
        </div>
        
        <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/60 shadow-inner relative overflow-hidden">
          <div className="absolute -right-4 -bottom-4 text-gray-200 dark:text-gray-800/30">
            <RotateCcw className="w-32 h-32" />
          </div>
          <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 relative z-10">Pending Payment Retries</h3>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2 relative z-10">0</p>
        </div>

        <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-green-50 dark:bg-green-950/20 shadow-inner relative overflow-hidden">
          <div className="absolute -right-4 -bottom-4 text-green-200/50 dark:text-green-900/30">
            <CheckCircle2 className="w-32 h-32" />
          </div>
          <h3 className="text-sm font-semibold text-green-800 dark:text-green-500 relative z-10">Total Recovered</h3>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2 relative z-10">₹{tasks.filter((t: any) => t.status === 'completed').length * 1500}</p>
        </div>
      </div>

      <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900/60 rounded-2xl overflow-hidden shadow-inner">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/80">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">Recent Recovery Actions</h3>
        </div>
        <div className="divide-y divide-gray-200 dark:divide-gray-800">
          {loading ? (
            <div className="p-6 text-center text-gray-500">Loading recovery tasks...</div>
          ) : tasks.map((task) => (
            <div key={task.id} className="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-full ${
                  task.status === 'completed' ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-500' : 
                  task.status === 'failed' ? 'bg-rose-100 dark:bg-rose-900/30 text-rose-600 dark:text-rose-500' : 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-500'
                }`}>
                  {task.status === 'completed' ? <CheckCircle2 className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
                </div>
                <div>
                  <h4 className="font-bold text-gray-900 dark:text-gray-200">{task.customer_email || "N/A"}</h4>
                  <p className="text-sm text-gray-500">Value: ₹{task.cart_value || 0}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Action: {task.agent_action || "Pending"}</p>
                <p className={`text-xs font-bold mt-1 ${
                  task.status === 'completed' ? 'text-emerald-600 dark:text-emerald-400' : 
                  task.status === 'failed' ? 'text-rose-600 dark:text-rose-400' : 'text-amber-600 dark:text-amber-400'
                }`}>
                  Status: {task.status}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
