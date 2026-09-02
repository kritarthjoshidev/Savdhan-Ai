import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Radio, Activity, ShieldAlert, Trash2,
} from 'lucide-react';
import alertSocket from '../utils/ws';
import ConnectionStatus from '../components/ConnectionStatus';
import EmptyState from '../components/EmptyState';
import { IntrusionBadge } from '../components/StatusBadge';
import { IntrusionAlertBar } from '../components/Toast';

const EVENT_COLOR = {
  INTRUSION:        { cls: 'ev-intrusion', label: 'INTRUSION' },
  new_incident:     { cls: 'ev-new',       label: 'New Detection' },
  incident_updated: { cls: 'ev-updated',   label: 'Updated' },
};

function EventRow({ ev, isFirst }) {
  const cfg = EVENT_COLOR[ev.event] || { cls: 'ev-other', label: ev.event || 'Event' };
  const isIntrusion = ev.event === 'INTRUSION';

  return (
    <motion.div
      className={`live-event-row ${cfg.cls}${isFirst ? ' ev-newest' : ''}`}
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.25 }}
      role="listitem"
    >
      <div className="ev-left">
        <span className="ev-time">{ev._ts}</span>
        <span className={`ev-type-badge ${cfg.cls}`}>{cfg.label}</span>
        {isIntrusion && <IntrusionBadge />}
      </div>
      <div className="ev-right">
        {ev.source_cam && (
          <span className="ev-cam">{ev.source_cam}</span>
        )}
        {ev.confidence != null && (
          <span className="ev-conf">{(ev.confidence * 100).toFixed(0)}%</span>
        )}
        {ev.incident_id && (
          <span className="text-muted text-sm">#{ev.incident_id}</span>
        )}
        {ev.status && (
          <span className="text-muted text-sm">→ {ev.status}</span>
        )}
        {ev.track_id && (
          <span className="mono text-muted text-sm">track: {ev.track_id}</span>
        )}
        {ev.fence_y != null && (
          <span className="mono text-muted text-sm">fence_y: {ev.fence_y}</span>
        )}
      </div>
    </motion.div>
  );
}

export default function LiveFeed() {
  const [events, setEvents] = useState([]);
  const [intrusionAlerts, setIntrusionAlerts] = useState([]);
  const eventsRef = useRef([]);
  const intrusionRef = useRef([]);

  useEffect(() => {
    alertSocket.connect();
    const unsub = alertSocket.subscribe((msg) => {
      const entry = { ...msg, _ts: new Date().toLocaleTimeString(), _uid: Date.now() };

      // All events go to the log
      eventsRef.current = [entry, ...eventsRef.current].slice(0, 50);
      setEvents([...eventsRef.current]);

      // INTRUSION → prominent banner with sound toggle
      if (msg.event === 'INTRUSION') {
        intrusionRef.current = [entry, ...intrusionRef.current].slice(0, 5);
        setIntrusionAlerts([...intrusionRef.current]);
      }
    });
    return () => unsub();
  }, []);

  const clearEvents = () => {
    eventsRef.current = [];
    setEvents([]);
  };

  const dismissIntrusion = (idx) => {
    setIntrusionAlerts(prev => prev.filter((_, i) => i !== idx));
  };

  const intrusionCount = events.filter(e => e.event === 'INTRUSION').length;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>

      {/* INTRUSION banner with sound toggle */}
      <AnimatePresence>
        {intrusionAlerts.length > 0 && (
          <IntrusionAlertBar alerts={intrusionAlerts} onDismiss={dismissIntrusion} />
        )}
      </AnimatePresence>

      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h1>Live Alert Feed</h1>
            <p>Real-time WebSocket events from the border surveillance pipeline</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <ConnectionStatus />
            {events.length > 0 && (
              <button
                className="btn btn-ghost btn-sm"
                onClick={clearEvents}
                aria-label="Clear event log"
                title="Clear event log"
              >
                <Trash2 size={14} /> Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Stat strip */}
      <motion.div
        className="stats-grid"
        initial={{ y: -10, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}
        style={{ marginBottom: 24 }}
      >
        <div className="stat-card">
          <div className="stat-icon red"><ShieldAlert size={20} /></div>
          <div className="stat-info">
            <div className="stat-label">INTRUSION Events</div>
            <div className="stat-value">{intrusionCount}</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon cyan"><Radio size={20} /></div>
          <div className="stat-info">
            <div className="stat-label">Total Events</div>
            <div className="stat-value">{events.length}</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green"><Activity size={20} /></div>
          <div className="stat-info">
            <div className="stat-label">WebSocket</div>
            <div className="stat-value"><ConnectionStatus /></div>
          </div>
        </div>
      </motion.div>

      {/* Event feed */}
      <motion.div
        className="card"
        initial={{ y: 14, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}
      >
        <div className="section-title">
          <h2><Radio size={15} style={{ marginRight: 8, verticalAlign: 'middle', color: '#ef4444' }} />Event Log</h2>
          <span className="text-muted text-sm">{events.length} events — newest first</span>
        </div>

        <div
          className="live-event-feed"
          role="log"
          aria-label="Live event feed"
          aria-live="polite"
        >
          {events.length === 0 ? (
            <EmptyState
              icon={Activity}
              heading="No live events yet"
              sub="Connect to the backend and start border analysis to see real-time events."
            />
          ) : (
            <AnimatePresence initial={false}>
              {events.map((ev, i) => (
                <EventRow key={ev._uid} ev={ev} isFirst={i === 0} />
              ))}
            </AnimatePresence>
          )}
        </div>

        {/* Legend */}
        <div className="ev-legend" aria-label="Event type legend">
          <span className="ev-legend-item ev-intrusion">INTRUSION</span>
          <span className="ev-legend-item ev-new">New Detection</span>
          <span className="ev-legend-item ev-updated">Updated</span>
        </div>
      </motion.div>
    </motion.div>
  );
}
