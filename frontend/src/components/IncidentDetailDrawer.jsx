import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle2, Film, ImageOff, RefreshCw, ShieldAlert, X, XCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { EventBadge, StatusBadge } from './StatusBadge';
import { getIncidentEvidence, updateIncident } from '../utils/api';
import { useToast } from './Toast';

function MetaRow({ label, value }) {
  if (value == null || value === '') return null;
  return (
    <div className="drawer-meta-row">
      <span className="drawer-meta-label">{label}</span>
      <span className="drawer-meta-value">{String(value)}</span>
    </div>
  );
}

function EvidenceImage({ item, className = '' }) {
  if (!item?.url) {
    return <div className="evidence-unavailable"><ImageOff size={17} /> Evidence not available yet</div>;
  }
  return <img className={className} src={item.url} alt={item.label || 'Incident evidence'} />;
}

function EvidencePanel({ incidentId }) {
  const [evidence, setEvidence] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadEvidence = async (quiet = false) => {
    if (!quiet) setLoading(true);
    try {
      setEvidence(await getIncidentEvidence(incidentId));
      setError('');
    } catch (err) {
      setError(err.message || 'Could not load incident evidence');
    } finally {
      if (!quiet) setLoading(false);
    }
  };

  useEffect(() => {
    loadEvidence();
  }, [incidentId]);

  useEffect(() => {
    if (evidence?.status !== 'recording') return undefined;
    const timer = setInterval(() => loadEvidence(true), 2000);
    return () => clearInterval(timer);
  }, [evidence?.status, incidentId]);

  if (loading) return <div className="evidence-loading">Loading evidence…</div>;
  if (error) return <div className="evidence-unavailable"><ImageOff size={17} /> {error}</div>;

  const isRecording = evidence?.status === 'recording';
  const images = evidence?.frames || [];
  return (
    <div className="evidence-panel">
      <div className="evidence-toolbar">
        <span className={`evidence-state ${isRecording ? 'recording' : 'ready'}`}>
          {isRecording ? 'Recording post-event context…' : 'Review evidence ready'}
        </span>
        <button className="btn btn-ghost btn-sm" onClick={() => loadEvidence()} aria-label="Refresh evidence">
          <RefreshCw size={13} /> Refresh
        </button>
      </div>

      {evidence?.detected_frame && (
        <figure className="evidence-primary">
          <EvidenceImage item={evidence.detected_frame} />
          <figcaption>{evidence.detected_frame.label} — annotated with tripwire and detection box</figcaption>
        </figure>
      )}

      {evidence?.clip?.url && (
        <div className="evidence-clip">
          <div className="evidence-media-label"><Film size={14} /> Context clip {evidence.clip_duration_seconds ? `(${evidence.clip_duration_seconds}s)` : ''}</div>
          <video controls preload="metadata" src={evidence.clip.url}>
            Your browser cannot play this evidence clip.
          </video>
        </div>
      )}

      {images.length > 0 && (
        <div className="evidence-nearby">
          <div className="evidence-media-label">Nearby frames</div>
          <div className="evidence-frame-grid">
            {images.map((item) => (
              <figure key={item.key}>
                <EvidenceImage item={item} />
                <figcaption>{item.label}</figcaption>
              </figure>
            ))}
          </div>
        </div>
      )}

      {!evidence?.detected_frame && evidence?.snapshot && (
        <figure className="evidence-primary">
          <EvidenceImage item={evidence.snapshot} />
          <figcaption>Stored detection crop</figcaption>
        </figure>
      )}
    </div>
  );
}

/** Right-side operator review drawer with directly playable incident evidence. */
export default function IncidentDetailDrawer({ incident, onClose, onUpdate }) {
  const toast = useToast();
  const [updating, setUpdating] = useState(false);

  if (!incident) return null;
  const meta = incident.meta || {};
  const vf = meta.virtual_fence || {};
  const det = meta.detection || {};
  const reid = meta.reid || {};

  const handleStatusUpdate = async (newStatus) => {
    setUpdating(true);
    try {
      const updated = await updateIncident(incident.id, {
        status: newStatus,
        meta: { reviewer_note: 'Reviewed by operator' },
      });
      toast(`Incident ${newStatus}`, newStatus === 'verified' ? 'success' : 'warning');
      onUpdate?.(updated);
      onClose();
    } catch (err) {
      toast(`Failed to update: ${err.message}`, 'error');
    } finally {
      setUpdating(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div className="drawer-overlay" onClick={onClose} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} role="dialog" aria-modal="true" aria-label={`Incident #${incident.id} details`}>
        <motion.div className="drawer" onClick={(event) => event.stopPropagation()} initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }} transition={{ type: 'spring', stiffness: 300, damping: 30 }}>
          <div className="drawer-header">
            <div>
              <h2 className="drawer-title">Incident #{incident.id}</h2>
              <div style={{ display: 'flex', gap: 8, marginTop: 6, flexWrap: 'wrap' }}>
                <StatusBadge status={incident.status} />
                <EventBadge eventType={meta.event_type} />
              </div>
            </div>
            <button className="modal-close" onClick={onClose} aria-label="Close drawer"><X size={20} /></button>
          </div>

          <div className="drawer-body">
            <section className="drawer-section">
              <h3 className="drawer-section-title">Review evidence</h3>
              <p className="form-hint">Watch the annotated trigger frame and nearby context before approving or denying this alert.</p>
              <EvidencePanel incidentId={incident.id} />
            </section>

            <section className="drawer-section">
              <h3 className="drawer-section-title">Detection</h3>
              <MetaRow label="Camera" value={incident.source_cam} />
              <MetaRow label="Timestamp" value={new Date(incident.timestamp || incident.created_at).toLocaleString()} />
              <MetaRow label="Confidence" value={`${(incident.confidence * 100).toFixed(1)}%`} />
              <MetaRow label="Track ID" value={incident.track_id} />
              <MetaRow label="Detection Class" value={det.class_name} />
              <MetaRow label="Frame ID" value={meta.frame_id} />
              <MetaRow label="AI finding" value={meta.ai_finding?.summary} />
            </section>

            {Object.keys(vf).length > 0 && (
              <section className="drawer-section">
                <h3 className="drawer-section-title">Virtual Fence</h3>
                <MetaRow label="Fence Y" value={vf.fence_y} />
                <MetaRow label="Centroid" value={Array.isArray(vf.centroid) ? vf.centroid.join(', ') : vf.centroid} />
                <MetaRow label="Track ID" value={vf.track_id} />
                <MetaRow label="Intrusion" value={vf.intrusion != null ? String(vf.intrusion) : undefined} />
              </section>
            )}

            <section className="drawer-section">
              <h3 className="drawer-section-title">Pipeline</h3>
              {meta.low_light_enhancement && <div className="drawer-badge-row"><span className="pipeline-badge clahe">CLAHE Low-Light Enhancement</span></div>}
              {reid.backend && <><MetaRow label="Re-ID Backend" value={reid.backend} /><MetaRow label="Matched Incident" value={reid.matched_incident_id ?? 'None'} /><MetaRow label="Re-ID Similarity" value={reid.similarity != null ? `${(reid.similarity * 100).toFixed(1)}%` : undefined} /></>}
            </section>
          </div>

          {incident.status === 'pending' && (
            <div className="drawer-footer">
              <button className="btn btn-success" onClick={() => handleStatusUpdate('verified')} disabled={updating} aria-label="Verify this incident"><CheckCircle2 size={15} />{updating ? 'Saving…' : 'Verify'}</button>
              <button className="btn btn-danger" onClick={() => handleStatusUpdate('rejected')} disabled={updating} aria-label="Reject this incident"><XCircle size={15} />{updating ? 'Saving…' : 'Reject'}</button>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
