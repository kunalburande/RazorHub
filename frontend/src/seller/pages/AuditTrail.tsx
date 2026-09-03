import React, { useState, useEffect, useMemo } from "react";
import { ClipboardList, Search, Filter } from "lucide-react";
import Button from "../components/ui/Button";
import { apiRequest, unwrapList } from "../../lib/api";

interface AuditEvent {
  id: string;
  event_id: string;
  created_at: string;
  agent: string;
  action: string;
  details: string;
  status: 'Success' | 'Failed' | 'Pending';
}

export default function AuditTrail() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    apiRequest<any>("/intelligence/audit/")
      .then((data) => {
        setEvents(unwrapList<AuditEvent>(data));
      })
      .catch((err) => {
        console.error("Error fetching audit events:", err);
        setEvents([]);
      })
      .finally(() => setLoading(false));
  }, []);

  const safeEvents = Array.isArray(events) ? events : [];
  const filteredEvents = useMemo(() => {
    if (!search.trim()) return safeEvents;
    const q = search.toLowerCase();
    return safeEvents.filter(
      (ev) =>
        ev.event_id?.toLowerCase().includes(q) ||
        ev.action?.toLowerCase().includes(q) ||
        ev.agent?.toLowerCase().includes(q) ||
        ev.details?.toLowerCase().includes(q) ||
        ev.status?.toLowerCase().includes(q)
    );
  }, [safeEvents, search]);

  return (
    <div className="min-h-[85vh] bg-gradient-to-br from-white via-gray-50 to-white dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 rounded-3xl p-8 border border-gray-200 dark:border-gray-800 shadow-2xl text-gray-900 dark:text-white transition-colors duration-300">
      <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-3">
            <ClipboardList className="h-8 w-8 text-teal-500" />
            Audit Trail
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2 text-sm max-w-2xl">
            A tamper-proof ledger of every action, negotiation, and policy check performed by RazorHub agents.
          </p>
        </div>
        <div className="flex gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search events..."
              className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-xl pl-9 pr-4 py-2 text-sm text-gray-900 dark:text-white focus:ring-teal-500 focus:outline-none"
            />
          </div>
          <Button className="bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-800 dark:text-white rounded-xl px-4 py-2 text-sm shadow-sm border border-gray-300 dark:border-gray-700">
            <Filter className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900/60 shadow-inner">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-600 dark:text-gray-400">
            <thead className="bg-gray-50 dark:bg-gray-800/50 text-xs uppercase text-gray-500 dark:text-gray-500 font-semibold border-b border-gray-200 dark:border-gray-800">
              <tr>
                <th className="px-6 py-4">Event ID</th>
                <th className="px-6 py-4">Timestamp</th>
                <th className="px-6 py-4">Agent</th>
                <th className="px-6 py-4">Action</th>
                <th className="px-6 py-4">Details</th>
                <th className="px-6 py-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">Loading audit trail...</td>
                </tr>
              ) : filteredEvents.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-8 text-center text-gray-500">No events recorded yet.</td></tr>
              ) : filteredEvents.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                  <td className="px-6 py-4 font-mono text-gray-900 dark:text-gray-300">{log.event_id}</td>
                  <td className="px-6 py-4">{new Date(log.created_at).toLocaleString()}</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 rounded bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 text-xs">
                      {log.agent || "System"}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-medium text-gray-200">{log.action}</td>
                  <td className="px-6 py-4 text-gray-400 truncate max-w-xs">{log.details}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 text-xs font-bold rounded-md ${
                      log.status === 'Success' ? 'text-green-400 bg-green-900/20' : 
                      log.status === 'Failed' ? 'text-rose-400 bg-rose-900/20' : 
                      'text-amber-400 bg-amber-900/20'
                    }`}>
                      {log.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
