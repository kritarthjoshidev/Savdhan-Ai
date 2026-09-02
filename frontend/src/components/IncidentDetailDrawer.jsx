import { AnimatePresence, motion } from 'framer-motion';
import { X, Copy, CheckCircle2, XCircle, ShieldAlert } from 'lucide-react';
import { useState } from 'react';
import { StatusBadge, IntrusionBadge } from './StatusBadge';
import { updateIncident } from '../utils/api';
import { useToast } from './Toast';

/** Returns true if path looks like an HTTP/HTTPS URL */
const isHttpUrl = (path) => /^https?:\/\//i.test(path || '');

function SnapshotDisplay({ path }) {
  const [copied, setCopied] = useState(false);

  if (!path) {
    return <span className="text-muted text-sm">—</span>;
  }

  if (isHttpUrl(path)) {
    return (
      <img
        src={path}
        alt="Snapshot evidence"
        style={{ maxWidth: '100%', borderRadius: 8, border: '1px solid var(--border-color)' }}
      />
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(path).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="snapshot-placeholder">
      <span className="snapshot-stored-label">📦 Evidence stored</span>
      <code className="snapshot-path">{path}</code>
      <button
        className="btn btn-ghost btn-sm"
        onClick={handleCopy}
        title="Copy path to clipboard"
        aria-label="Copy snapshot path to clipboard"
      >
        <Copy size={12} />
        {copied ? 'Copied!' : 'Copy path'}
      </button>
    </div>
  );
}

function MetaRow({ label, value }) {
  if (value == null || value === '') return null;
  return (
    <div className="drawer-meta-row">
      <span className="drawer-meta-label">{label}</span>
      <span className="drawer-meta-value">{String(value)}</span>
    </div>
  );
}

/**
 * IncidentDetailDrawer — right-side drawer with full incident details.
 * onClose: () => void
 * onUpdate: (updatedIncident) => void  — called after confirmed PATCH success
 */
export default function IncidentDetailDrawer({ incident, onClose, onUpdate }) {
  const toast = useToast();
  const [updating, setUpdating] = useState(false);

  if (!incident) return null;
  const meta = incident.meta || {};
  const vf   = meta.virtual_fence || {};
  const det  = meta.detection || {};
  const reid = meta.reid || {};

  // ── Confirmed update: only applies local change after successful PATCH ──────
  const handleStatusUpdate = async (newStatus) => {
    setUpdating(true);
    try {
      const updated = await updateIncident(incident.id, {
        status: newStatus,
        meta: { reviewer_note: 'Reviewed by operator' },
      });
      toast(`Incident ${newStatus}`, newStatus === 'verified' ? 'success' : 'warning');
      onUpdate && onUpdate(updated);
      onClose();
    } catch (e) {
      toast(`Failed to update: ${e.message}`, 'error');
    } finally {
      setUpdating(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        className="drawer-overlay"
        onClick={onClose}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        role="dialog"
        aria-modal="true"
        aria-label={`Incident #${incident.id} details`}
      >
        <motion.div
          className="drawer"
          onClick={(e) => e.stopPropagation()}
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        >
          {/* Header */}
          <div className="drawer-header">
            <div>
              <h2 className="drawer-title">Incident #{incident.id}</h2>
              <div style={{ display: 'flex', gap: 8, marginTop: 6, flexWrap: 'wrap' }}>
                <StatusBadge status={incident.status} />
                {meta.event_type === 'INTRUSION' && <IntrusionBadge />}
              </div>
            </div>
            <button
              className="modal-close"
              onClick={onClose}
              aria-label="Close drawer"
            >
              <X size={20} />
            </button>
          </div>

          {/* Body */}
          <div className="drawer-body">
            {/* Core */}
            <section className="drawer-section">
              <h3 className="drawer-section-title">Detection</h3>
              <MetaRow label="Camera"         value={incident.source_cam} />
              <MetaRow label="Timestamp"      value={new Date(incident.timestamp || incident.created_at).toLocaleString()} />
              <MetaRow label="Confidence"     value={`${(incident.confidence * 100).toFixed(1)}%`} />
              <MetaRow label="Track ID"       value={incident.track_id} />
              <MetaRow label="Bounding Box"   value={JSON.stringify(incident.bbox)} />
              <MetaRow label="Detection Class" value={det.class_name} />
              <MetaRow label="Frame ID"       value={meta.frame_id} />
            </section>

            {/* Virtual Fence */}
            {Object.keys(vf).length > 0 && (
              <section className="drawer-section">
                <h3 className="drawer-section-title">Virtual Fence</h3>
                <MetaRow label="Fence Y"   value={vf.fence_y} />
                <MetaRow label="Centroid"  value={Array.isArray(vf.centroid) ? vf.centroid.join(', ') : vf.centroid} />
                <MetaRow label="Track ID"  value={vf.track_id} />
                <MetaRow label="Intrusion" value={vf.intrusion != null ? String(vf.intrusion) : undefined} />
              </section>
            )}

            {/* Pipeline */}
            <section className="drawer-section">
              <h3 className="drawer-section-title">Pipeline</h3>
              {meta.low_light_enhancement && (
                <div className="drawer-badge-row">
                  <span className="pipeline-badge clahe">
                    ✓ CLAHE Low-Light Enhancement
                  </span>
                </div>
              )}
              {reid.backend && (
                <>
                  <MetaRow label="Re-ID Backend"        value={reid.backend} />
                  <MetaRow label="Matched Incident"     value={reid.matched_incident_id ?? 'None'} />
                  <MetaRow label="Re-ID Similarity"     value={reid.similarity != null ? (reid.similarity * 100).toFixed(1) + '%' : undefined} />
                </>
              )}
            </section>

            {/* Snapshot */}
            <section className="drawer-section">
              <h3 className="drawer-section-title">Evidence / Snapshot</h3>
              <SnapshotDisplay path={incident.snapshot_path} />
            </section>
          </div>

          {/* Footer actions */}
          {incident.status === 'pending' && (
            <div className="drawer-footer">
              <button
                className="btn btn-success"
                onClick={() => handleStatusUpdate('verified')}
                disabled={updating}
                aria-label="Verify this incident"
              >
                <CheckCircle2 size={15} />
                {updating ? 'Saving…' : 'Verify'}
              </button>
              <button
                className="btn btn-danger"
                onClick={() => handleStatusUpdate('rejected')}
                disabled={updating}
                aria-label="Reject this incident"
              >
                <XCircle size={15} />
                {updating ? 'Saving…' : 'Reject'}
              </button>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
