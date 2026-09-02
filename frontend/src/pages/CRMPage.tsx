import { useEffect, useMemo, useState } from 'react';
import { apiRequest, unwrapList } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { useTranslation } from '../i18n/LocaleContext';
import {
  Ticket as TicketIcon,
  MessageSquare,
  Users,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  AlertCircle,
  Plus,
  RefreshCw,
  Send,
  UserCheck,
  TrendingUp,
  Mail,
  Phone,
  Building,
  Shield,
  X,
} from 'lucide-react';

interface Ticket {
  id: number;
  customer_email: string;
  subject: string;
  description?: string;
  status: 'open' | 'pending' | 'resolved';
  priority: 'low' | 'medium' | 'high';
  created_at: string;
  order?: number | null;
}

interface Lead {
  id: number;
  name: string;
  email: string;
  phone: string;
  source: string;
  status: 'new' | 'contacted' | 'qualified' | 'closed';
  notes: string;
  created_at: string;
}

export default function CRMPage() {
  const { token, user } = useAuth();
  const { t } = useTranslation();

  const [activeTab, setActiveTab] = useState<'tickets' | 'leads'>('tickets');
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // New ticket modal
  const [showNewTicketModal, setShowNewTicketModal] = useState(false);
  const [newSubject, setNewSubject] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newPriority, setNewPriority] = useState<'low' | 'medium' | 'high'>('medium');
  const [submitting, setSubmitting] = useState(false);

  function loadData() {
    setLoading(true);
    setError('');
    Promise.all([
      apiRequest<any>('/crm/tickets/', { token }),
      apiRequest<any>('/crm/leads/', { token }),
    ])
      .then(([ticketsRes, leadsRes]) => {
        setTickets(unwrapList<Ticket>(ticketsRes));
        setLeads(unwrapList<Lead>(leadsRes));
      })
      .catch((err) => {
        console.error('Failed to load CRM data:', err);
        setError('Could not load CRM tickets and leads from database.');
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadData();
  }, [token]);

  async function updateTicketStatus(id: number, status: Ticket['status']) {
    setError('');
    try {
      await apiRequest(`/crm/tickets/${id}/`, {
        token,
        method: 'PATCH',
        body: JSON.stringify({ status }),
      });
      setSuccessMsg(`Ticket #${id} status changed to "${status}".`);
      setTimeout(() => setSuccessMsg(''), 3500);
      loadData();
    } catch (err: any) {
      setError(err?.message || 'Could not update ticket status.');
    }
  }

  async function updateTicketPriority(id: number, priority: Ticket['priority']) {
    setError('');
    try {
      await apiRequest(`/crm/tickets/${id}/`, {
        token,
        method: 'PATCH',
        body: JSON.stringify({ priority }),
      });
      setSuccessMsg(`Ticket #${id} priority set to "${priority}".`);
      setTimeout(() => setSuccessMsg(''), 3500);
      loadData();
    } catch (err: any) {
      setError(err?.message || 'Could not update ticket priority.');
    }
  }

  async function updateLeadStatus(id: number, status: Lead['status']) {
    setError('');
    try {
      await apiRequest(`/crm/leads/${id}/`, {
        token,
        method: 'PATCH',
        body: JSON.stringify({ status }),
      });
      setSuccessMsg(`Lead #${id} updated to "${status}".`);
      setTimeout(() => setSuccessMsg(''), 3500);
      loadData();
    } catch (err: any) {
      setError(err?.message || 'Could not update lead status.');
    }
  }

  async function handleCreateTicket(e: React.FormEvent) {
    e.preventDefault();
    if (!newSubject.trim()) return;

    setSubmitting(true);
    setError('');
    try {
      await apiRequest('/crm/tickets/', {
        token,
        method: 'POST',
        body: JSON.stringify({
          subject: newSubject.trim(),
          description: newDescription.trim(),
          priority: newPriority,
          status: 'open',
        }),
      });
      setSuccessMsg('New support ticket created successfully.');
      setTimeout(() => setSuccessMsg(''), 3500);
      setShowNewTicketModal(false);
      setNewSubject('');
      setNewDescription('');
      loadData();
    } catch (err: any) {
      setError(err?.message || 'Failed to create ticket.');
    } finally {
      setSubmitting(false);
    }
  }

  // Filtered tickets
  const filteredTickets = useMemo(() => {
    return tickets.filter((t) => {
      const q = searchQuery.toLowerCase();
      const matchSearch =
        !q ||
        t.subject.toLowerCase().includes(q) ||
        (t.customer_email || '').toLowerCase().includes(q) ||
        (t.description || '').toLowerCase().includes(q);

      if (!matchSearch) return false;
      if (statusFilter !== 'all' && t.status !== statusFilter) return false;
      return true;
    });
  }, [tickets, searchQuery, statusFilter]);

  // Filtered leads
  const filteredLeads = useMemo(() => {
    return leads.filter((l) => {
      const q = searchQuery.toLowerCase();
      const matchSearch =
        !q ||
        l.name.toLowerCase().includes(q) ||
        (l.email || '').toLowerCase().includes(q) ||
        (l.phone || '').toLowerCase().includes(q) ||
        (l.notes || '').toLowerCase().includes(q);

      if (!matchSearch) return false;
      if (statusFilter !== 'all' && l.status !== statusFilter) return false;
      return true;
    });
  }, [leads, searchQuery, statusFilter]);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="rounded-3xl border border-border/80 bg-surface/90 backdrop-blur-md p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-indigo-500 mb-1">
            <MessageSquare className="h-4 w-4" />
            <span>Customer Relationship & Support Operations</span>
          </div>
          <h1 className="text-2xl font-extrabold text-primary">CRM & Support Desk</h1>
          <p className="text-xs text-secondary mt-1">
            Manage customer support inquiries, track commercial leads, resolve seller tickets, and oversee resolution metrics.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-2 bg-muted/60 hover:bg-muted border border-border text-xs font-bold text-primary px-3.5 py-2 rounded-xl transition-all shadow-2xs active:scale-95 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            type="button"
            onClick={() => setShowNewTicketModal(true)}
            className="flex items-center gap-1.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:opacity-95 text-white text-xs font-bold px-4 py-2 rounded-xl transition-all shadow-md shadow-indigo-500/25 active:scale-95 cursor-pointer"
          >
            <Plus className="h-4 w-4" />
            <span>New Ticket</span>
          </button>
        </div>
      </div>

      {/* Status Alerts */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 text-xs font-semibold flex items-center gap-2 shadow-xs">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {successMsg && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-xs font-semibold flex items-center gap-2 shadow-xs">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl border border-border/80 bg-surface shadow-2xs flex items-center gap-3">
          <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
            <TicketIcon className="h-5 w-5" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-secondary uppercase">Total Tickets</p>
            <p className="text-xl font-black text-primary">{tickets.length}</p>
          </div>
        </div>

        <div className="p-4 rounded-2xl border border-border/80 bg-surface shadow-2xs flex items-center gap-3">
          <div className="p-3 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400">
            <Clock className="h-5 w-5" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-secondary uppercase">Open / Pending</p>
            <p className="text-xl font-black text-primary">
              {tickets.filter((t) => t.status !== 'resolved').length}
            </p>
          </div>
        </div>

        <div className="p-4 rounded-2xl border border-border/80 bg-surface shadow-2xs flex items-center gap-3">
          <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 className="h-5 w-5" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-secondary uppercase">Resolved</p>
            <p className="text-xl font-black text-primary">
              {tickets.filter((t) => t.status === 'resolved').length}
            </p>
          </div>
        </div>

        <div className="p-4 rounded-2xl border border-border/80 bg-surface shadow-2xs flex items-center gap-3">
          <div className="p-3 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400">
            <TrendingUp className="h-5 w-5" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-secondary uppercase">Enterprise Leads</p>
            <p className="text-xl font-black text-primary">{leads.length}</p>
          </div>
        </div>
      </div>

      {/* Tabs & Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
        <div className="flex items-center gap-2">
          {/* Main Tab Switcher */}
          <div className="flex items-center gap-1.5 bg-muted/60 p-1 rounded-2xl border border-border/70 text-xs font-semibold">
            <button
              type="button"
              onClick={() => {
                setActiveTab('tickets');
                setStatusFilter('all');
              }}
              className={`px-3.5 py-1.5 rounded-xl transition-all cursor-pointer ${
                activeTab === 'tickets'
                  ? 'bg-surface dark:bg-zinc-800 text-primary shadow-xs font-bold'
                  : 'text-secondary hover:text-primary'
              }`}
            >
              Support Tickets ({tickets.length})
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveTab('leads');
                setStatusFilter('all');
              }}
              className={`px-3.5 py-1.5 rounded-xl transition-all cursor-pointer ${
                activeTab === 'leads'
                  ? 'bg-surface dark:bg-zinc-800 text-primary shadow-xs font-bold'
                  : 'text-secondary hover:text-primary'
              }`}
            >
              Commercial Leads ({leads.length})
            </button>
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-surface border border-border/80 rounded-2xl px-3 py-1.5 text-xs font-semibold text-primary outline-none focus:ring-1 focus:ring-accent"
          >
            <option value="all">All Statuses</option>
            {activeTab === 'tickets' ? (
              <>
                <option value="open">Open</option>
                <option value="pending">Pending</option>
                <option value="resolved">Resolved</option>
              </>
            ) : (
              <>
                <option value="new">New</option>
                <option value="contacted">Contacted</option>
                <option value="qualified">Qualified</option>
                <option value="closed">Closed</option>
              </>
            )}
          </select>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="h-4 w-4 text-secondary absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={`Search ${activeTab === 'tickets' ? 'subject, customer...' : 'leads, company...'}`}
            className="w-full bg-surface border border-border/80 rounded-2xl pl-9 pr-4 py-2 text-xs text-primary focus:outline-none focus:ring-2 focus:ring-accent/40"
          />
        </div>
      </div>

      {/* ── TAB 1: SUPPORT TICKETS ── */}
      {activeTab === 'tickets' && (
        <section className="rounded-3xl border border-border/80 bg-surface shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-border/60 bg-surface/50 flex items-center justify-between">
            <h2 className="font-bold text-sm text-primary flex items-center gap-2">
              <TicketIcon className="h-4 w-4 text-indigo-500" />
              <span>Customer & Seller Support Tickets ({filteredTickets.length})</span>
            </h2>
            <span className="text-xs text-secondary">Live NeonDB Sync</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[780px] text-left text-xs">
              <thead className="bg-muted/30 text-secondary uppercase font-bold text-[10px] border-b border-border/60">
                <tr>
                  <th className="py-3 px-6">Ticket / Subject</th>
                  <th className="py-3 px-4">Customer Email</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-6 text-right">Update Resolution</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filteredTickets.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-secondary">
                      No support tickets found matching current filters.
                    </td>
                  </tr>
                ) : (
                  filteredTickets.map((ticket) => (
                    <tr key={ticket.id} className="hover:bg-muted/20 transition-colors">
                      <td className="py-3.5 px-6">
                        <span className="block font-bold text-primary">{ticket.subject}</span>
                        {ticket.description && (
                          <span className="block text-[11px] text-secondary line-clamp-1 max-w-md mt-0.5">
                            {ticket.description}
                          </span>
                        )}
                        <span className="block text-[10px] text-secondary font-mono mt-0.5">
                          ID #{ticket.id} • {new Date(ticket.created_at).toLocaleDateString()}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-medium text-secondary">{ticket.customer_email || '—'}</td>
                      <td className="py-3.5 px-4">
                        <select
                          value={ticket.priority}
                          onChange={(e) =>
                            updateTicketPriority(ticket.id, e.target.value as Ticket['priority'])
                          }
                          className={`rounded-full px-2.5 py-1 text-[10px] font-bold border outline-none cursor-pointer ${
                            ticket.priority === 'high'
                              ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20'
                              : ticket.priority === 'medium'
                              ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20'
                              : 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20'
                          }`}
                        >
                          <option value="low">Low Priority</option>
                          <option value="medium">Medium Priority</option>
                          <option value="high">High Priority</option>
                        </select>
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1 text-[10px] font-bold px-2.5 py-1 rounded-full ${
                            ticket.status === 'resolved'
                              ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
                              : ticket.status === 'pending'
                              ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                              : 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20'
                          }`}
                        >
                          <span className="capitalize">{ticket.status}</span>
                        </span>
                      </td>
                      <td className="py-3.5 px-6 text-right">
                        <select
                          value={ticket.status}
                          onChange={(e) =>
                            updateTicketStatus(ticket.id, e.target.value as Ticket['status'])
                          }
                          className="bg-surface border border-border/80 rounded-xl px-2.5 py-1.5 text-xs font-semibold text-primary outline-none focus:ring-1 focus:ring-accent cursor-pointer"
                        >
                          <option value="open">Mark Open</option>
                          <option value="pending">Mark Pending</option>
                          <option value="resolved">Mark Resolved</option>
                        </select>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* ── TAB 2: COMMERCIAL LEADS ── */}
      {activeTab === 'leads' && (
        <section className="rounded-3xl border border-border/80 bg-surface shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-border/60 bg-surface/50 flex items-center justify-between">
            <h2 className="font-bold text-sm text-primary flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-purple-500" />
              <span>Commercial & Enterprise Inquiries ({filteredLeads.length})</span>
            </h2>
            <span className="text-xs text-secondary">Lead Pipeline</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[780px] text-left text-xs">
              <thead className="bg-muted/30 text-secondary uppercase font-bold text-[10px] border-b border-border/60">
                <tr>
                  <th className="py-3 px-6">Lead Name</th>
                  <th className="py-3 px-4">Contact Details</th>
                  <th className="py-3 px-4">Source Channel</th>
                  <th className="py-3 px-4">Pipeline Status</th>
                  <th className="py-3 px-6 text-right">Advance Stage</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filteredLeads.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-secondary">
                      No commercial leads found.
                    </td>
                  </tr>
                ) : (
                  filteredLeads.map((lead) => (
                    <tr key={lead.id} className="hover:bg-muted/20 transition-colors">
                      <td className="py-3.5 px-6">
                        <span className="block font-bold text-primary">{lead.name}</span>
                        {lead.notes && (
                          <span className="block text-[11px] text-secondary line-clamp-1 max-w-md mt-0.5">
                            {lead.notes}
                          </span>
                        )}
                        <span className="block text-[10px] text-secondary font-mono mt-0.5">
                          ID #{lead.id} • {new Date(lead.created_at).toLocaleDateString()}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-medium text-secondary">
                        <div className="space-y-0.5">
                          {lead.email && <div className="flex items-center gap-1.5"><Mail className="h-3 w-3" /> {lead.email}</div>}
                          {lead.phone && <div className="flex items-center gap-1.5"><Phone className="h-3 w-3" /> {lead.phone}</div>}
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="font-mono text-[11px] bg-muted/60 px-2 py-0.5 rounded-md text-primary capitalize">
                          {lead.source.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1 text-[10px] font-bold px-2.5 py-1 rounded-full capitalize ${
                            lead.status === 'qualified'
                              ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
                              : lead.status === 'contacted'
                              ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20'
                              : lead.status === 'closed'
                              ? 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20'
                              : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                          }`}
                        >
                          {lead.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-6 text-right">
                        <select
                          value={lead.status}
                          onChange={(e) =>
                            updateLeadStatus(lead.id, e.target.value as Lead['status'])
                          }
                          className="bg-surface border border-border/80 rounded-xl px-2.5 py-1.5 text-xs font-semibold text-primary outline-none focus:ring-1 focus:ring-accent cursor-pointer"
                        >
                          <option value="new">New</option>
                          <option value="contacted">Contacted</option>
                          <option value="qualified">Qualified</option>
                          <option value="closed">Closed / Won</option>
                        </select>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* ── CREATE TICKET MODAL ── */}
      {showNewTicketModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-md rounded-3xl border border-border bg-surface p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border/60 pb-3">
              <h3 className="font-bold text-base text-primary flex items-center gap-2">
                <TicketIcon className="h-4.5 w-4.5 text-indigo-500" />
                <span>Create Support Ticket</span>
              </h3>
              <button
                type="button"
                onClick={() => setShowNewTicketModal(false)}
                className="p-1 rounded-lg text-secondary hover:text-primary hover:bg-muted"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleCreateTicket} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-primary mb-1">Subject / Issue Title</label>
                <input
                  type="text"
                  required
                  value={newSubject}
                  onChange={(e) => setNewSubject(e.target.value)}
                  placeholder="e.g. Inquiry regarding order shipment #1042"
                  className="w-full bg-background border border-border rounded-xl px-3.5 py-2 text-xs text-primary focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-primary mb-1">Detailed Description</label>
                <textarea
                  rows={3}
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="Provide context or instructions for resolution..."
                  className="w-full bg-background border border-border rounded-xl px-3.5 py-2 text-xs text-primary focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-primary mb-1">Priority Level</label>
                <select
                  value={newPriority}
                  onChange={(e) => setNewPriority(e.target.value as any)}
                  className="w-full bg-background border border-border rounded-xl px-3.5 py-2 text-xs font-semibold text-primary focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
                >
                  <option value="low">Low Priority</option>
                  <option value="medium">Medium Priority</option>
                  <option value="high">High Priority</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewTicketModal(false)}
                  className="px-4 py-2 text-xs font-bold text-secondary hover:text-primary rounded-xl border border-border"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || !newSubject.trim()}
                  className="px-4 py-2 text-xs font-bold text-white bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl shadow-md disabled:opacity-50"
                >
                  {submitting ? 'Creating...' : 'Submit Ticket'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
