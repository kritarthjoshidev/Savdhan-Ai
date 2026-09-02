import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Filter, ChevronLeft, ChevronRight } from 'lucide-react';
import { listIncidents, updateIncident } from '../utils/api';
import { useToast } from '../components/Toast';
import IncidentTable from '../components/IncidentTable';
import IncidentDetailDrawer from '../components/IncidentDetailDrawer';
import { IntrusionAlertBar } from '../components/Toast';
import alertSocket from '../utils/ws';

export default function Incidents() {
  const toast = useToast();
  const [incidents, setIncidents]     = useState([]);
  const [loading, setLoading]         = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [camFilter, setCamFilter]     = useState('');
  const [hoursFilter, setHoursFilter] = useState(24);
  const [page, setPage]               = useState(0);
  const [selected, setSelected]       = useState(null);
  const [intrusionAlerts, setIntrusionAlerts] = useState([]);
  const limit = 20;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listIncidents({
        skip:       page * limit,
        limit,
        status:     statusFilter || undefined,
        source_cam: camFilter    || undefined,
        hours:      hoursFilter,
      });
      setIncidents(Array.isArray(data) ? data : data.incidents || []);
    } catch (e) {
      toast(e.message, 'error');
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter, camFilter, hoursFilter, toast]);

  useEffect(() => { load(); }, [load]);

  // Subscribe to WS for live refresh + INTRUSION toasts
  useEffect(() => {
    alertSocket.connect();
    const unsub = alertSocket.subscribe((msg) => {
      if (msg.event === 'INTRUSION') {
        setIntrusionAlerts(prev => [{ ...msg, _ts: new Date().toLocaleTimeString() }, ...prev].slice(0, 5));
        load(); // refresh table
      } else if (msg.event === 'new_incident' || msg.event === 'incident_updated') {
        load();
      }
    });
    return unsub;
  }, [load]);

  // ── Confirmed update — only mutates local state after successful PATCH ──────
  const handleVerify = async (id) => {
    try {
      const updated = await updateIncident(id, {
        status: 'verified',
        meta: { reviewer_note: 'Reviewed by operator' },
      });
      toast('Incident verified', 'success');
      setIncidents(prev => prev.map(i => i.id === id ? { ...i, status: 'verified' } : i));
      if (selected?.id === id) setSelected(null);
    } catch (e) {
      toast(`Failed to verify: ${e.message}`, 'error');
    }
  };

  const handleReject = async (id) => {
    try {
      await updateIncident(id, {
        status: 'rejected',
        meta: { reviewer_note: 'Reviewed by operator' },
      });
      toast('Incident rejected', 'warning');
      setIncidents(prev => prev.map(i => i.id === id ? { ...i, status: 'rejected' } : i));
      if (selected?.id === id) setSelected(null);
    } catch (e) {
      toast(`Failed to reject: ${e.message}`, 'error');
    }
  };

  // Confirmed update from drawer
  const handleDrawerUpdate = (updated) => {
    setIncidents(prev => prev.map(i => i.id === updated.id ? { ...i, ...updated } : i));
    setSelected(null);
  };

  // Camera options derived from real incident source_cam values
  const cameras = [...new Set(incidents.map(i => i.source_cam))];

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>

      <AnimatePresence>
        {intrusionAlerts.length > 0 && (
          <IntrusionAlertBar
            alerts={intrusionAlerts}
            onDismiss={(i) => setIntrusionAlerts(p => p.filter((_, idx) => idx !== i))}
          />
        )}
      </AnimatePresence>

      <div className="page-header">
        <h1>Incidents</h1>
        <p>Manage and review INTRUSION detections across all sources</p>
      </div>

      {/* Filters */}
      <motion.div
        className="filters-row"
        initial={{ y: -10, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}
      >
        <select
          className="select"
          value={statusFilter}
          onChange={e => { setStatusFilter(e.target.value); setPage(0); }}
          aria-label="Filter by status"
        >
          <option value="">All Status</option>
          <option value="pending">Pending</option>
          <option value="verified">Verified</option>
          <option value="rejected">Rejected</option>
        </select>

        <select
          className="select"
          value={camFilter}
          onChange={e => { setCamFilter(e.target.value); setPage(0); }}
          aria-label="Filter by camera"
        >
          <option value="">All Cameras</option>
          {cameras.map(c => <option key={c} value={c}>{c}</option>)}
        </select>

        <select
          className="select"
          value={hoursFilter}
          onChange={e => { setHoursFilter(Number(e.target.value)); setPage(0); }}
          aria-label="Filter by time range"
        >
          <option value={24}>Last 24 hours</option>
          <option value={168}>Last 7 days</option>
          <option value={720}>Last 30 days</option>
        </select>

        <button
          className="btn btn-ghost btn-sm"
          onClick={() => { setStatusFilter(''); setCamFilter(''); setHoursFilter(24); setPage(0); }}
          aria-label="Reset all filters"
        >
          <Filter size={13} /> Reset
        </button>
      </motion.div>

      {/* Table */}
      <motion.div initial={{ y: 15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}>
        <IncidentTable
          incidents={incidents}
          loading={loading}
          onView={setSelected}
          onVerify={handleVerify}
          onReject={handleReject}
        />
      </motion.div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-2" style={{ padding: '8px 4px' }}>
        <span className="text-muted text-sm">Page {page + 1} — {incidents.length} results</span>
        <div className="flex gap-2">
          <button
            className="btn btn-ghost btn-sm"
            disabled={page === 0}
            onClick={() => setPage(p => Math.max(0, p - 1))}
            aria-label="Previous page"
          >
            <ChevronLeft size={13} /> Prev
          </button>
          <button
            className="btn btn-ghost btn-sm"
            disabled={incidents.length < limit}
            onClick={() => setPage(p => p + 1)}
            aria-label="Next page"
          >
            Next <ChevronRight size={13} />
          </button>
        </div>
      </div>

      {/* Detail Drawer */}
      <AnimatePresence>
        {selected && (
          <IncidentDetailDrawer
            incident={selected}
            onClose={() => setSelected(null)}
            onUpdate={handleDrawerUpdate}
          />
        )}
      </AnimatePresence>
    </motion.div>
  );
}
