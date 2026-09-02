import { useEffect, useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle, ShieldCheck, Clock, Activity,
  TrendingUp, Crosshair, Zap, Eye, ScanSearch,
  ChevronRight, RefreshCw, GitBranch, Server,
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import { listIncidents, checkHealth } from '../utils/api';
import alertSocket from '../utils/ws';
import ConnectionStatus from '../components/ConnectionStatus';
import MetricCard from '../components/MetricCard';
import EmptyState from '../components/EmptyState';
import { IntrusionBadge, StatusBadge } from '../components/StatusBadge';
import { IntrusionAlertBar } from '../components/Toast';

const stagger = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.06 } } };
const fadeUp  = { hidden: { opacity: 0, y: 18 }, show: { opacity: 1, y: 0, transition: { duration: 0.4 } } };

// ── Pipeline stages — explanatory only, not fake live metrics ─────────────────
const PIPELINE_STAGES = [
  { icon: GitBranch,  label: 'Motion Gate',             desc: 'Skips static frames before inference runs.', color: 'cyan' },
  { icon: Eye,        label: 'CLAHE Enhancement',        desc: 'Contrast-Limited Adaptive Histogram Equalization for low-light scenes.', color: 'blue' },
  { icon: ScanSearch, label: 'YOLO-World Detection',    desc: 'Zero-shot detection: person, vehicle, weapon, backpack.', color: 'purple' },
  { icon: Crosshair,  label: 'Virtual Fence / Tripwire', desc: 'Directional crossing: above→below = INTRUSION.', color: 'amber' },
  { icon: Zap,        label: 'OSNet Re-ID',             desc: 'Person re-identification across frames and cameras.', color: 'green' },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const [incidents, setIncidents]       = useState([]);
  const [loading, setLoading]           = useState(true);
  const [backendOk, setBackendOk]       = useState(null); // null=checking
  const [liveAlerts, setLiveAlerts]     = useState([]);
  const [intrusionAlerts, setIntrusionAlerts] = useState([]);
  const alertsRef = useRef([]);
  const intrusionRef = useRef([]);

  const load = useCallback(async () => {
    try {
      await checkHealth();
      setBackendOk(true);
      const data = await listIncidents({ limit: 100, hours: 24 });
      setIncidents(Array.isArray(data) ? data : data.incidents || []);
    } catch {
      setBackendOk(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    load();
    const iv = setInterval(() => { if (mounted) load(); }, 30_000);

    alertSocket.connect();
    const unsub = alertSocket.subscribe((msg) => {
      const entry = { ...msg, _ts: new Date().toLocaleTimeString() };

      // Live feed
      alertsRef.current = [entry, ...alertsRef.current].slice(0, 30);
      setLiveAlerts([...alertsRef.current]);

      // INTRUSION prominently shown
      if (msg.event === 'INTRUSION') {
        intrusionRef.current = [entry, ...intrusionRef.current].slice(0, 5);
        setIntrusionAlerts([...intrusionRef.current]);
        // Refresh incident data
        if (mounted) load();
      }
    });

    return () => { mounted = false; clearInterval(iv); unsub(); };
  }, [load]);

  // ── Derived metrics (from real data only) ─────────────────────────────────
  const total    = incidents.length;
  const pending  = incidents.filter(i => i.status === 'pending').length;
  const verified = incidents.filter(i => i.status === 'verified').length;
  const rejected = incidents.filter(i => i.status === 'rejected').length;
  // Camera sources from real incident source_cam — no fake count
  const cameras  = [...new Set(incidents.map(i => i.source_cam))];

  // Chart data — group by hour
  const chartData = (() => {
    const hours = {};
    incidents.forEach(inc => {
      const d = new Date(inc.timestamp || inc.created_at);
      const key = `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:00`;
      hours[key] = (hours[key] || 0) + 1;
    });
    return Object.entries(hours).slice(-12).map(([time, count]) => ({ time, count }));
  })();

  const recent = [...incidents].sort((a, b) =>
    new Date(b.timestamp || b.created_at) - new Date(a.timestamp || a.created_at)
  ).slice(0, 8);

  const dismissIntrusion = (idx) => {
    setIntrusionAlerts(prev => prev.filter((_, i) => i !== idx));
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>

      {/* INTRUSION alert bar */}
      <AnimatePresence>
        {intrusionAlerts.length > 0 && (
          <IntrusionAlertBar alerts={intrusionAlerts} onDismiss={dismissIntrusion} />
        )}
      </AnimatePresence>

      {/* Page header */}
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h1>Border Surveillance Command Center</h1>
            <p>SSB Border Monitoring — real-time YOLO-World + Virtual Fence pipeline</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            {/* Backend health pill */}
            <span
              className={`health-pill ${backendOk === true ? 'health-ok' : backendOk === false ? 'health-err' : 'health-checking'}`}
              role="status"
              aria-label={backendOk === true ? 'Backend online' : backendOk === false ? 'Backend offline' : 'Checking backend'}
            >
              <span className="health-pill-dot" aria-hidden="true" />
              {backendOk === true ? 'Backend Online' : backendOk === false ? 'Backend Offline' : 'Checking…'}
            </span>
            {/* WS status */}
            <ConnectionStatus />
            {/* Refresh */}
            <button
              className="btn btn-ghost btn-sm"
              onClick={load}
              title="Refresh data"
              aria-label="Refresh dashboard data"
            >
              <RefreshCw size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Metric cards */}
      <motion.div className="stats-grid" variants={stagger} initial="hidden" animate="show">
        {[
          { icon: AlertTriangle, color: 'red',    label: '24h Incidents',   value: total },
          { icon: Clock,         color: 'amber',  label: 'Pending Review',  value: pending },
          { icon: ShieldCheck,   color: 'green',  label: 'Verified',        value: verified },
          { icon: Activity,      color: 'gray',   label: 'Rejected',        value: rejected },
          { icon: Server,        color: 'cyan',   label: 'Active Sources',  value: cameras.length },
        ].map((s, i) => (
          <motion.div key={i} variants={fadeUp} whileHover={{ y: -3, boxShadow: '0 0 24px rgba(6,182,212,0.14)' }}>
            <MetricCard {...s} loading={loading} />
          </motion.div>
        ))}
      </motion.div>

      {/* CTA */}
      <motion.div
        className="cta-banner"
        initial={{ y: 14, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}
      >
        <div>
          <strong>Start Border Analysis</strong>
          <span>Submit a video file or RTSP source to begin YOLO-World + virtual fence detection.</span>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => navigate('/border-monitor')}
          aria-label="Go to Border Monitor to start analysis"
        >
          Start Analysis <ChevronRight size={15} />
        </button>
      </motion.div>

      {/* Chart + Live Feed */}
      <motion.div
        className="grid-2"
        style={{ marginBottom: 24 }}
        initial={{ y: 18, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.25 }}
      >
        {/* Incident trend chart */}
        <div className="card">
          <div className="section-title">
            <h2><TrendingUp size={16} style={{ marginRight: 8, verticalAlign: 'middle' }} />Incident Trend (24h)</h2>
          </div>
          <div className="chart-container">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="ccGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%"   stopColor="#06b6d4" stopOpacity={0.4} />
                      <stop offset="100%" stopColor="#06b6d4" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(148,163,184,0.06)" />
                  <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={{ stroke: 'rgba(148,163,184,0.1)' }} />
                  <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={{ stroke: 'rgba(148,163,184,0.1)' }} allowDecimals={false} />
                  <Tooltip contentStyle={{ background: '#1a2340', border: '1px solid rgba(148,163,184,0.15)', borderRadius: 8, color: '#f1f5f9', fontSize: 12 }} />
                  <Area type="monotone" dataKey="count" stroke="#06b6d4" strokeWidth={2} fill="url(#ccGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState icon={Activity} heading="No data yet" sub="Incidents will appear once analysis runs" />
            )}
          </div>
        </div>

        {/* Live WS event feed */}
        <div className="card">
          <div className="section-title">
            <h2><Activity size={16} style={{ marginRight: 8, verticalAlign: 'middle', color: '#ef4444' }} />Live Event Feed</h2>
            <ConnectionStatus />
          </div>
          <div className="alert-feed">
            {liveAlerts.length === 0 ? (
              <EmptyState icon={Activity} heading="No live events" sub="WebSocket events will stream here in real-time" />
            ) : (
              liveAlerts.map((a, i) => (
                <motion.div
                  key={i}
                  className={`alert-item${i === 0 ? ' new' : ''}${a.event === 'INTRUSION' ? ' alert-intrusion' : ''}`}
                  initial={{ x: -16, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: i * 0.02 }}
                >
                  <span className="alert-time">{a._ts}</span>
                  <span className="alert-msg">
                    {a.event === 'INTRUSION' && (
                      <><IntrusionBadge />{' '}cam <span className="alert-cam">{a.source_cam}</span> — {a.confidence != null ? `${(a.confidence * 100).toFixed(0)}%` : ''}</>
                    )}
                    {a.event === 'new_incident' && (
                      <>New detection on <span className="alert-cam">{a.source_cam}</span> — {a.confidence != null ? `${(a.confidence * 100).toFixed(0)}%` : ''}</>
                    )}
                    {a.event === 'incident_updated' && (
                      <>Incident #{a.incident_id} → <strong>{a.status}</strong></>
                    )}
                    {!a.event && a.message && <>{a.message}</>}
                  </span>
                </motion.div>
              ))
            )}
          </div>
        </div>
      </motion.div>

      {/* Camera sources (derived from real data) */}
      {cameras.length > 0 && (
        <motion.div
          className="card"
          style={{ marginBottom: 24 }}
          initial={{ y: 14, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}
        >
          <div className="section-title">
            <h2><Server size={16} style={{ marginRight: 8, verticalAlign: 'middle' }} />Active Sources (last 24h)</h2>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {cameras.map(cam => (
              <span key={cam} className="cam-chip" role="listitem">{cam}</span>
            ))}
          </div>
        </motion.div>
      )}

      {/* Pipeline cards — explanatory, NOT fake live status */}
      <motion.div
        initial={{ y: 14, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.33 }}
        style={{ marginBottom: 24 }}
      >
        <div className="section-title">
          <h2>Detection Pipeline</h2>
          <span className="text-muted text-sm">System architecture overview</span>
        </div>
        <div className="pipeline-grid">
          {PIPELINE_STAGES.map((stage, i) => (
            <motion.div
              key={i}
              className="pipeline-card"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35 + i * 0.06 }}
            >
              <div className={`pipeline-icon ${stage.color}`} aria-hidden="true">
                <stage.icon size={18} />
              </div>
              <div>
                <div className="pipeline-name">{stage.label}</div>
                <div className="pipeline-desc">{stage.desc}</div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Recent incidents */}
      <motion.div initial={{ y: 14, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.38 }}>
        <div className="section-title">
          <h2>Recent Incidents</h2>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/incidents')}>
            View All <ChevronRight size={13} />
          </button>
        </div>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th><th>Camera</th><th>Time</th><th>Event</th>
                <th>Status</th><th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} aria-hidden="true">
                    {Array.from({ length: 6 }).map((_, j) => (
                      <td key={j}><div className="skeleton" style={{ height: 14, width: '65%' }} /></td>
                    ))}
                  </tr>
                ))
              ) : recent.length === 0 ? (
                <tr><td colSpan={6}>
                  <EmptyState icon={AlertTriangle} heading="No incidents yet" sub="Start border analysis to begin monitoring" />
                </td></tr>
              ) : (
                recent.map((inc, i) => {
                  const isIntrusion = inc.meta?.event_type === 'INTRUSION';
                  return (
                    <motion.tr
                      key={inc.id}
                      className={isIntrusion ? 'intrusion-row' : ''}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.4 + i * 0.03 }}
                    >
                      <td className="mono text-accent">#{inc.id}</td>
                      <td style={{ fontWeight: 600 }}>{inc.source_cam}</td>
                      <td className="text-muted text-sm mono">
                        {new Date(inc.timestamp || inc.created_at).toLocaleString()}
                      </td>
                      <td>{isIntrusion ? <IntrusionBadge /> : <span className="text-muted text-sm">Detection</span>}</td>
                      <td><StatusBadge status={inc.status} /></td>
                      <td>
                        <span className={`confidence ${inc.confidence >= 0.85 ? 'high' : inc.confidence >= 0.6 ? 'medium' : 'low'}`}>
                          {inc.confidence != null ? `${(inc.confidence * 100).toFixed(0)}%` : '—'}
                        </span>
                      </td>
                    </motion.tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </motion.div>
    </motion.div>
  );
}
