import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Crosshair, Play, Loader, CheckCircle2, AlertTriangle,
  ToggleLeft, ToggleRight, RefreshCw,
} from 'lucide-react';
import { processBorderSource, listIncidents } from '../utils/api';
import { useToast } from '../components/Toast';
import BorderFencePreview from '../components/BorderFencePreview';
import { IntrusionBadge, StatusBadge } from '../components/StatusBadge';

const INITIAL_FORM = {
  sourceType: 'file',
  source: '',
  camera_id: 'border-cam-01',
  confidence_threshold: 0.35,
  sample_every_n_frames: 30,
  fence_y_ratio: 0.5,
};

function FormRow({ label, hint, children }) {
  return (
    <div className="form-group">
      <label className="form-label">{label}</label>
      {children}
      {hint && <span className="form-hint">{hint}</span>}
    </div>
  );
}

export default function BorderMonitor() {
  const toast = useToast();
  const [form, setForm]           = useState(INITIAL_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [accepted, setAccepted]   = useState(null);   // 202 response payload
  const [error, setError]         = useState(null);
  const [newIncidents, setNewIncidents] = useState([]);
  const pollRef = useRef(null);
  const knownIdsRef = useRef(new Set());

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }));

  // Poll incidents by camera_id after 202 accepted
  const startPolling = useCallback((cameraId) => {
    if (pollRef.current) clearInterval(pollRef.current);
    knownIdsRef.current = new Set();

    pollRef.current = setInterval(async () => {
      try {
        const data = await listIncidents({ source_cam: cameraId, hours: 1, limit: 50 });
        const items = Array.isArray(data) ? data : data.incidents || [];
        const fresh = items.filter(i => !knownIdsRef.current.has(i.id));
        if (fresh.length > 0) {
          fresh.forEach(i => knownIdsRef.current.add(i.id));
          setNewIncidents(prev => [...fresh, ...prev].slice(0, 20));
        }
      } catch { /* silent poll */ }
    }, 10_000);
  }, []);

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const validate = () => {
    if (!form.source.trim()) return 'Source path or RTSP URL is required.';
    if (form.sourceType === 'rtsp' && !form.source.trim().startsWith('rtsp://'))
      return 'RTSP source must begin with rtsp://';
    if (!form.camera_id.trim()) return 'Camera ID is required.';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const err = validate();
    if (err) { toast(err, 'warning'); return; }

    setSubmitting(true);
    setError(null);
    setAccepted(null);
    setNewIncidents([]);

    const payload = {
      source:                 form.source.trim(),
      source_type:            form.sourceType,
      camera_id:              form.camera_id.trim(),
      confidence_threshold:   Number(form.confidence_threshold),
      sample_every_n_frames:  Number(form.sample_every_n_frames),
      fence_y_ratio:          Number(form.fence_y_ratio),
    };

    try {
      const res = await processBorderSource(payload);
      setAccepted(res);
      toast('Analysis accepted by backend!', 'success');
      startPolling(payload.camera_id);
    } catch (e) {
      const msg = e.status === 404
        ? 'Video file not found on server. Check the server-side path.'
        : e.status === 422
          ? 'Validation error: ' + e.message
          : e.message;
      setError(msg);
      toast(msg, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>
      <div className="page-header">
        <h1>Border Monitor</h1>
        <p>Submit a video file or RTSP stream for YOLO-World + virtual fence analysis</p>
      </div>

      <div className="grid-2" style={{ alignItems: 'start' }}>

        {/* ── Form ─────────────────────────────────────────────────────────── */}
        <motion.div className="card" initial={{ x: -18, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
            <Crosshair size={18} style={{ color: 'var(--accent)' }} />
            <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>Analysis Configuration</span>
          </div>

          <form onSubmit={handleSubmit} noValidate>
            {/* Source type toggle */}
            <FormRow label="Source Type">
              <div className="toggle-row" role="group" aria-label="Source type">
                <button
                  type="button"
                  className={`toggle-btn${form.sourceType === 'file' ? ' active' : ''}`}
                  onClick={() => set('sourceType', 'file')}
                  aria-pressed={form.sourceType === 'file'}
                >
                  {form.sourceType === 'file' ? <ToggleLeft size={14} /> : <ToggleLeft size={14} />}
                  Local Video File Path
                </button>
                <button
                  type="button"
                  className={`toggle-btn${form.sourceType === 'rtsp' ? ' active' : ''}`}
                  onClick={() => set('sourceType', 'rtsp')}
                  aria-pressed={form.sourceType === 'rtsp'}
                >
                  <ToggleRight size={14} />
                  RTSP Stream
                </button>
              </div>
            </FormRow>

            {/* Source input — server-side path, NOT a browser file picker */}
            <FormRow
              label={form.sourceType === 'file' ? 'Server-Side Video Path' : 'RTSP URL'}
              hint={
                form.sourceType === 'file'
                  ? 'Enter the absolute path on the server where the backend is running, e.g. C:\\videos\\border.mp4'
                  : 'Enter the full RTSP URL, e.g. rtsp://192.168.1.101/stream1'
              }
            >
              <input
                type="text"
                className="input"
                placeholder={form.sourceType === 'file' ? 'C:\\path\\to\\video.mp4' : 'rtsp://...'}
                value={form.source}
                onChange={e => set('source', e.target.value)}
                required
                aria-label={form.sourceType === 'file' ? 'Server-side video file path' : 'RTSP URL'}
              />
            </FormRow>

            <FormRow label="Camera ID" hint="Unique identifier for this analysis session">
              <input
                type="text"
                className="input"
                placeholder="border-cam-01"
                value={form.camera_id}
                onChange={e => set('camera_id', e.target.value)}
                required
                aria-label="Camera ID"
              />
            </FormRow>

            {/* Confidence slider */}
            <FormRow
              label={`Confidence Threshold: ${Number(form.confidence_threshold).toFixed(2)}`}
              hint="Detections below this score are ignored. Lower = more sensitive."
            >
              <input
                type="range" min={0.05} max={0.95} step={0.01}
                className="slider"
                value={form.confidence_threshold}
                onChange={e => set('confidence_threshold', e.target.value)}
                aria-label="Confidence threshold"
                aria-valuemin={0.05} aria-valuemax={0.95}
                aria-valuenow={form.confidence_threshold}
              />
              <div className="slider-labels">
                <span>0.05 (sensitive)</span><span>0.95 (strict)</span>
              </div>
            </FormRow>

            {/* Sample interval */}
            <FormRow
              label={`Sample Every N Frames: ${form.sample_every_n_frames}`}
              hint="Run inference every N frames. 30 ≈ 1 frame/sec at 30 FPS."
            >
              <input
                type="range" min={1} max={300} step={1}
                className="slider"
                value={form.sample_every_n_frames}
                onChange={e => set('sample_every_n_frames', e.target.value)}
                aria-label="Sample every N frames"
                aria-valuemin={1} aria-valuemax={300}
                aria-valuenow={form.sample_every_n_frames}
              />
              <div className="slider-labels"><span>1 (every frame)</span><span>300</span></div>
            </FormRow>

            {/* Fence Y ratio */}
            <FormRow
              label={`Virtual Fence Position: ${Number(form.fence_y_ratio).toFixed(2)}`}
              hint={`0.50 = midway down the frame. ${Number(form.fence_y_ratio).toFixed(2)} = ${Math.round(form.fence_y_ratio * 100)}% from top.`}
            >
              <input
                type="range" min={0.05} max={0.95} step={0.01}
                className="slider"
                value={form.fence_y_ratio}
                onChange={e => set('fence_y_ratio', e.target.value)}
                aria-label="Virtual fence vertical position"
                aria-valuemin={0.05} aria-valuemax={0.95}
                aria-valuenow={form.fence_y_ratio}
              />
              <div className="slider-labels"><span>0.05 (top)</span><span>0.95 (bottom)</span></div>
            </FormRow>

            {/* Error */}
            <AnimatePresence>
              {error && (
                <motion.div
                  className="error-state"
                  style={{ marginBottom: 16 }}
                  initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  role="alert"
                >
                  <AlertTriangle size={16} aria-hidden="true" />
                  <span>{error}</span>
                </motion.div>
              )}
            </AnimatePresence>

            <motion.button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
              style={{ width: '100%', justifyContent: 'center', marginTop: 8 }}
              whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            >
              {submitting
                ? <><Loader size={15} style={{ animation: 'spin 1s linear infinite' }} /> Submitting…</>
                : <><Play size={15} /> Start Analysis</>}
            </motion.button>
          </form>

          {/* 202 accepted */}
          <AnimatePresence>
            {accepted && (
              <motion.div
                className="accepted-panel"
                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                  <CheckCircle2 size={18} style={{ color: 'var(--color-success)' }} />
                  <strong style={{ color: 'var(--color-success)' }}>Analysis accepted by backend</strong>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: '0.82rem' }}>
                  <div><span className="text-muted">Camera ID</span><p className="mono">{accepted.camera_id}</p></div>
                  <div><span className="text-muted">Event Type</span><p className="mono" style={{ color: '#ef4444' }}>{accepted.event_on_crossing}</p></div>
                  <div><span className="text-muted">Fence Y Ratio</span><p className="mono">{accepted.fence_y_ratio}</p></div>
                  <div><span className="text-muted">Sample Interval</span><p className="mono">{accepted.sample_every_n_frames} frames</p></div>
                </div>
                <p className="text-muted" style={{ fontSize: '0.75rem', marginTop: 10 }}>
                  Polling for new incidents from camera <code>{accepted.camera_id}</code>…
                  <RefreshCw size={11} style={{ marginLeft: 4, verticalAlign: 'middle', animation: 'spin 2s linear infinite' }} />
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* ── Right panel: fence preview + new incidents ────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <motion.div className="card" initial={{ x: 18, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.15 }}>
            <BorderFencePreview fenceRatio={Number(form.fence_y_ratio)} />
          </motion.div>

          <AnimatePresence>
            {newIncidents.length > 0 && (
              <motion.div
                className="card"
                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              >
                <div className="section-title" style={{ marginBottom: 12 }}>
                  <h2>New Incidents from {accepted?.camera_id}</h2>
                  <span className="badge running"><span className="badge-dot" />Polling</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {newIncidents.map(inc => {
                    const isIntrusion = inc.meta?.event_type === 'INTRUSION';
                    return (
                      <motion.div
                        key={inc.id}
                        className={`new-incident-row${isIntrusion ? ' intrusion-row' : ''}`}
                        initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
                      >
                        <span className="mono text-accent text-sm">#{inc.id}</span>
                        {isIntrusion && <IntrusionBadge />}
                        <StatusBadge status={inc.status} />
                        <span className="text-muted text-sm">
                          {(inc.confidence * 100).toFixed(0)}%
                        </span>
                        <span className="text-muted text-sm mono">
                          {new Date(inc.timestamp || inc.created_at).toLocaleTimeString()}
                        </span>
                      </motion.div>
                    );
                  })}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}
