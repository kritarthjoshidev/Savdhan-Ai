import { motion } from 'framer-motion';
import { Eye, CheckCircle2, XCircle } from 'lucide-react';
import { StatusBadge, IntrusionBadge } from './StatusBadge';

/**
 * IncidentTable — reusable table for incident listings.
 * Props:
 *   incidents: Incident[]
 *   loading: boolean
 *   onView: (incident) => void
 *   onVerify: (id) => void
 *   onReject: (id) => void
 */
export default function IncidentTable({ incidents, loading, onView, onVerify, onReject }) {
  return (
    <div className="table-container" role="region" aria-label="Incidents table">
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col">ID</th>
            <th scope="col">Camera</th>
            <th scope="col">Time</th>
            <th scope="col">Event</th>
            <th scope="col">Status</th>
            <th scope="col">Confidence</th>
            <th scope="col">Track ID</th>
            <th scope="col">Actions</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            Array.from({ length: 6 }).map((_, r) => (
              <tr key={r} aria-hidden="true">
                {Array.from({ length: 8 }).map((_, c) => (
                  <td key={c}>
                    <div className="skeleton" style={{ height: 14, width: `${50 + (c * 9) % 40}%` }} />
                  </td>
                ))}
              </tr>
            ))
          ) : incidents.length === 0 ? (
            <tr>
              <td colSpan={8}>
                <div className="empty-state">
                  <h3>No incidents found</h3>
                  <p>Try adjusting filters or time range</p>
                </div>
              </td>
            </tr>
          ) : (
            incidents.map((inc, i) => {
              const isIntrusion = inc.meta?.event_type === 'INTRUSION';
              const pct = inc.confidence != null ? `${(inc.confidence * 100).toFixed(0)}%` : '—';
              const confCls = inc.confidence >= 0.85 ? 'high' : inc.confidence >= 0.6 ? 'medium' : 'low';
              return (
                <motion.tr
                  key={inc.id}
                  initial={{ opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.025 }}
                  className={isIntrusion ? 'intrusion-row' : ''}
                >
                  <td className="mono text-accent">#{inc.id}</td>
                  <td style={{ fontWeight: 600 }}>{inc.source_cam}</td>
                  <td className="text-muted text-sm mono">
                    {new Date(inc.timestamp || inc.created_at).toLocaleString()}
                  </td>
                  <td>
                    {isIntrusion
                      ? <IntrusionBadge />
                      : <span className="text-muted text-sm">Detection</span>}
                  </td>
                  <td><StatusBadge status={inc.status} /></td>
                  <td><span className={`confidence ${confCls}`}>{pct}</span></td>
                  <td className="text-muted mono text-sm">{inc.track_id || '—'}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button
                        className="btn btn-ghost btn-sm"
                        onClick={() => onView && onView(inc)}
                        title="View details"
                        aria-label={`View incident #${inc.id}`}
                      >
                        <Eye size={13} />
                      </button>
                      {inc.status === 'pending' && (
                        <>
                          <button
                            className="btn btn-success btn-sm"
                            onClick={() => onVerify && onVerify(inc.id)}
                            title="Verify"
                            aria-label={`Verify incident #${inc.id}`}
                          >
                            <CheckCircle2 size={13} />
                          </button>
                          <button
                            className="btn btn-danger btn-sm"
                            onClick={() => onReject && onReject(inc.id)}
                            title="Reject"
                            aria-label={`Reject incident #${inc.id}`}
                          >
                            <XCircle size={13} />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </motion.tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
