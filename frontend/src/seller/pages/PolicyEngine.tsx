import React, { useState, useEffect } from "react";
import { ShieldAlert, Save, RefreshCw } from "lucide-react";
import Button from "../components/ui/Button";
import { apiRequest, unwrapList } from "../../lib/api";

export default function PolicyEngine() {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const fetchConfig = async () => {
    try {
      setLoading(true);
      // Since it's a singleton, the URL returns a list or an object or paginated results.
      const response = await apiRequest<any>("/intelligence/config/");
      const items = unwrapList(response);
      if (items.length > 0) {
        setConfig(items[0]);
      } else if (response && typeof response === "object" && !Array.isArray(response) && !response.results) {
        setConfig(response);
      } else {
        setConfig(null);
      }
    } catch (err) {
      console.error("Error fetching config:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const handleSave = async () => {
    if (!config || !config.id) return;
    setSaving(true);
    try {
      await apiRequest(`/intelligence/config/${config.id}/`, {
        method: "PUT",
        body: JSON.stringify(config),
      });
      alert("Policies saved successfully!");
    } catch (err) {
      console.error("Error saving config:", err);
      alert("Failed to save policies.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="min-h-[85vh] p-8 text-gray-900 dark:text-white">Loading policies...</div>;
  }
  return (
    <div className="min-h-[85vh] bg-gradient-to-br from-white via-gray-50 to-white dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 rounded-3xl p-8 border border-gray-200 dark:border-gray-800 shadow-2xl text-gray-900 dark:text-white transition-colors duration-300">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-3">
            <ShieldAlert className="h-8 w-8 text-indigo-500" />
            Agent Policy Engine
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2 text-sm max-w-2xl">
            Configure boundaries, budget limits, and approval workflows for AI agents.
          </p>
        </div>
        <div className="flex gap-3">
          <Button onClick={fetchConfig} className="bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-800 dark:text-white rounded-xl px-4 py-2 text-sm shadow-sm border border-gray-300 dark:border-gray-700">
            <RefreshCw className="h-4 w-4 mr-2" /> Reset
          </Button>
          <Button onClick={handleSave} disabled={saving} className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl px-4 py-2 font-bold shadow-sm">
            <Save className="h-4 w-4 mr-2" /> {saving ? "Saving..." : "Save Policies"}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-6">
          <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/60 shadow-inner">
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4 border-b border-gray-200 dark:border-gray-800 pb-2">Sales Agent Guardrails</h3>
            <div className="space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-semibold text-gray-800 dark:text-gray-200">Max Discount Limit</label>
                <p className="text-xs text-gray-500">Maximum discount % agents can offer.</p>
              </div>
              <input type="number" value={config?.max_discount_percent || 0} onChange={(e) => setConfig({...config, max_discount_percent: e.target.value})} className="w-20 bg-white dark:bg-gray-950 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-1.5 text-sm text-center" />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-semibold text-gray-800 dark:text-gray-200">Auto-Approval Threshold</label>
                <p className="text-xs text-gray-500">Discounts under this % are auto-approved.</p>
              </div>
              <input type="number" value={config?.auto_approval_threshold || 0} onChange={(e) => setConfig({...config, auto_approval_threshold: e.target.value})} className="w-20 bg-white dark:bg-gray-950 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-1.5 text-sm text-center" />
            </div>

            <div className="flex items-center gap-3 pt-2">
              <input type="checkbox" checked={config?.allow_ai_negotiation || false} onChange={(e) => setConfig({...config, allow_ai_negotiation: e.target.checked})} className="rounded border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-indigo-600 dark:text-indigo-500 focus:ring-indigo-500 w-4 h-4" />
              <label className="text-sm text-gray-700 dark:text-gray-300">Allow AI to negotiate dynamically</label>
            </div>
          </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/60 shadow-inner">
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4 border-b border-gray-200 dark:border-gray-800 pb-2">Approval Workflows</h3>
            <div className="space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-semibold text-gray-800 dark:text-gray-200">Require User Confirmation</label>
                <p className="text-xs text-gray-500">Must the buyer manually confirm quotes?</p>
              </div>
              <div className="relative inline-block w-10 mr-2 align-middle select-none transition duration-200 ease-in">
                <input type="checkbox" checked={config?.require_user_confirmation || false} onChange={(e) => setConfig({...config, require_user_confirmation: e.target.checked})} name="toggle" id="toggle1" className="toggle-checkbox absolute block w-5 h-5 rounded-full bg-white border-4 appearance-none cursor-pointer" />
                <label htmlFor="toggle1" className="toggle-label block overflow-hidden h-5 rounded-full bg-indigo-500 cursor-pointer"></label>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-semibold text-gray-800 dark:text-gray-200">Max Transaction Value</label>
                <p className="text-xs text-gray-500">Any order above this requires admin approval.</p>
              </div>
              <input type="number" value={config?.max_ai_order_value || 0} onChange={(e) => setConfig({...config, max_ai_order_value: e.target.value})} className="w-24 bg-white dark:bg-gray-950 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-1.5 text-sm text-center" />
            </div>
          </div>
        </div>
      </div>
      </div>
      
      <style>{`
        .toggle-checkbox:checked { right: 0; border-color: #6366f1; }
        .toggle-checkbox:checked + .toggle-label { background-color: #6366f1; }
        .toggle-checkbox { right: 50%; border-color: #374151; }
        .toggle-label { background-color: #374151; }
      `}</style>
    </div>
  );
}
