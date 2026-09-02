import React, { useState } from "react";
import { Bot, Play, Pause, Settings, Activity } from "lucide-react";
import Button from "../components/ui/Button";

const mockAgents = [
  { id: "agt_1", name: "Sales Agent", status: "Active", tasks: 124, lastActive: "2 mins ago" },
  { id: "agt_2", name: "Support Agent", status: "Active", tasks: 89, lastActive: "5 mins ago" },
  { id: "agt_3", name: "Recovery Agent", status: "Paused", tasks: 0, lastActive: "2 days ago" },
];

export default function AgentsConsole() {
  return (
    <div className="min-h-[85vh] bg-gradient-to-br from-white via-gray-50 to-white dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 rounded-3xl p-8 border border-gray-200 dark:border-gray-800 shadow-2xl text-gray-900 dark:text-white transition-colors duration-300">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-3">
            <Bot className="h-8 w-8 text-blue-500" />
            AI Agent Console
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2 text-sm">
            Manage your autonomous store agents and monitor their performance.
          </p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700 text-white rounded-xl px-4 py-2 font-bold shadow-sm">
          + Deploy New Agent
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {mockAgents.map((agent) => (
          <div key={agent.id} className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/60 shadow-inner">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{agent.name}</h3>
              <span className={`px-2.5 py-1 text-xs font-bold rounded-md ${agent.status === 'Active' ? 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800' : 'bg-gray-200 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-700'}`}>
                {agent.status}
              </span>
            </div>
            
            <div className="space-y-3 mb-6">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Tasks Handled:</span>
                <span className="text-gray-900 dark:text-gray-200 font-semibold">{agent.tasks}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Last Active:</span>
                <span className="text-gray-900 dark:text-gray-200">{agent.lastActive}</span>
              </div>
            </div>

            <div className="flex gap-2">
              <Button className="flex-1 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 text-xs py-1.5 rounded-lg border border-gray-200 dark:border-gray-700">
                <Settings className="w-4 h-4 mr-1" /> Configure
              </Button>
              {agent.status === "Active" ? (
                <Button className="flex-1 bg-amber-50 dark:bg-amber-900/30 hover:bg-amber-100 dark:hover:bg-amber-900/50 text-amber-700 dark:text-amber-500 text-xs py-1.5 rounded-lg border border-amber-200 dark:border-amber-900/50">
                  <Pause className="w-4 h-4 mr-1" /> Pause
                </Button>
              ) : (
                <Button className="flex-1 bg-green-50 dark:bg-green-900/30 hover:bg-green-100 dark:hover:bg-green-900/50 text-green-700 dark:text-green-500 text-xs py-1.5 rounded-lg border border-green-200 dark:border-green-900/50">
                  <Play className="w-4 h-4 mr-1" /> Resume
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/40">
        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
          <Activity className="h-5 w-5 text-gray-500 dark:text-gray-400" />
          Live Agent Activity Stream
        </h3>
        <div className="space-y-4">
          <div className="flex gap-4 items-center text-sm p-3 rounded-xl bg-white dark:bg-gray-800/30 border border-gray-200 dark:border-gray-800/50">
            <span className="text-gray-500 w-24">10:42 AM</span>
            <span className="px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs border border-blue-200 dark:border-blue-800/50">Sales Agent</span>
            <span className="text-gray-700 dark:text-gray-300">Responded to product inquiry for "Wireless Earbuds"</span>
          </div>
          <div className="flex gap-4 items-center text-sm p-3 rounded-xl bg-white dark:bg-gray-800/30 border border-gray-200 dark:border-gray-800/50">
            <span className="text-gray-500 w-24">10:38 AM</span>
            <span className="px-2 py-0.5 rounded bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 text-xs border border-purple-200 dark:border-purple-800/50">Support Agent</span>
            <span className="text-gray-700 dark:text-gray-300">Authorized a 10% discount for cart abandonment</span>
          </div>
          <div className="flex gap-4 items-center text-sm p-3 rounded-xl bg-white dark:bg-gray-800/30 border border-gray-200 dark:border-gray-800/50">
            <span className="text-gray-500 w-24">09:15 AM</span>
            <span className="px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs border border-blue-200 dark:border-blue-800/50">Sales Agent</span>
            <span className="text-gray-700 dark:text-gray-300">Generated quote #Q-8821 for customer</span>
          </div>
        </div>
      </div>
    </div>
  );
}
