import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, Play, Loader, CheckCircle2, XCircle, Film, Tag, RotateCw, Layers, RefreshCw } from 'lucide-react';
import { startAutoTrain, getAutoTrainStatus, downloadAutoTrainResults } from '../utils/api';
import { useToast } from '../components/Toast';

const DEFAULT_CLASSES = ['person', 'vehicle', 'weapon', 'backpack'];

function statusIcon(status) {
  switch (status) {
    case 'completed': return <CheckCircle2 size={16} style={{ color: 'var(--color-success)' }} />;
    case 'failed':    return <XCircle      size={16} style={{ color: 'var(--color-danger)' }} />;
    case 'running':   return <Loader       size={16} style={{ color: 'var(--color-info)', animation: 'spin 1s linear infinite' }} />;
    default:          return <RotateCw     size={16} style={{ color: 'var(--color-warning)' }} />;
  }
}

export default function AutoTrain() {
  const toast = useToast();
  const [videoPath,      setVideoPath]      = useState('');
  const [classes,        setClasses]        = useState(DEFAULT_CLASSES.join(', '));
  const [epochs,         setEpochs]         = useState(15);
  const [frameInterval,  setFrameInterval]  = useState(4);
  const [submitting,     setSubmitting]      = useState(false);

  // Active job
  const [activeJob,   setActiveJob]   = useState(null);
  const [jobStatus,   setJobStatus]   = useState(null);
  const [results,     setResults]     = useState(null);
  const [history,     setHistory]     = useState([]);

  const pollRef = useRef(null);

  const stopPolling = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  };

  const startPolling = (jobId) => {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const s = await getAutoTrainStatus(jobId);
        setJobStatus(s);
        setHistory(prev => prev.map(h => h.job_id === jobId ? { ...h, status: s.status } : h));

        if (s.status === 'completed') {
          stopPolling();
          toast('Training complete! 🎉', 'success');
          try {
            const r = await downloadAutoTrainResults(jobId);
            setResults(r);
          } catch { /* results may not be ready */ }
        } else if (s.status === 'failed') {
          stopPolling();
          toast('Training failed: ' + (s.error || 'Unknown error'), 'error');
        }
      } catch { /* silent */ }
    }, 5_000);
  };

  useEffect(() => () => stopPolling(), []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!videoPath.trim()) { toast('Server-side video path is required', 'warning'); return; }

    setSubmitting(true);
    setResults(null);
    setJobStatus(null);

    try {
      const res = await startAutoTrain({
        video_path:     videoPath.trim(),
        classes:        classes.split(',').map(c => c.trim()).filter(Boolean),
        epochs:         Number(epochs),
        frame_interval: Number(frameInterval),
      });
      setActiveJob(res.job_id);
      setJobStatus({ status: 'queued', progress: 0, message: 'Job submitted…' });
      setHistory(prev => [{ job_id: res.job_id, status: 'queued', created_at: res.created_at }, ...prev]);
      toast('Auto-train job submitted!', 'success');
      startPolling(res.job_id);
    } catch (e) {
      toast(e.message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>
      <div className="page-header">
        <h1>Auto-Train Pipeline</h1>
        <p>1-click automated YOLO training from a server-side video — extract frames, auto-label, train, infer</p>
      </div>

      <div className="grid-2">
        {/* Form */}
        <motion.div className="card" initial={{ x: -18, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.1 }}>
          <div className="flex items-center gap-2" style={{ marginBottom: 20 }}>
            <Zap size={18} style={{ color: 'var(--accent)' }} />
            <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>New Auto-Train Job</span>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">
                <Film size={13} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                Server-Side Video Path
              </label>
              <input
                type="text"
                className="input"
                placeholder="C:\path\to\video.mp4 or /data/border.mp4"
                value={videoPath}
                onChange={e => setVideoPath(e.target.value)}
                aria-label="Server-side video file path"
              />
              <span className="form-hint">Absolute path on the machine running the backend</span>
            </div>

            <div className="form-group">
              <label className="form-label">
                <Tag size={13} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                Detection Classes
              </label>
              <input
                type="text"
                className="input"
                placeholder="person, vehicle, weapon, backpack"
                value={classes}
                onChange={e => setClasses(e.target.value)}
              />
              <span className="form-hint">Comma-separated — YOLO-World zero-shot detection</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div className="form-group">
                <label className="form-label">
                  <Layers size={13} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                  Epochs
                </label>
                <input
                  type="number" className="input"
                  value={epochs} min={1} max={300}
                  onChange={e => setEpochs(e.target.value)}
                  aria-label="Training epochs"
                />
              </div>
              <div className="form-group">
                <label className="form-label">
                  <Film size={13} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                  Frame Interval
                </label>
                <input
                  type="number" className="input"
                  value={frameInterval} min={1} max={30}
                  onChange={e => setFrameInterval(e.target.value)}
                  aria-label="Frame extraction interval"
                />
                <span className="form-hint">Extract 1 frame every N frames</span>
              </div>
            </div>

            <motion.button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
              style={{ width: '100%', justifyContent: 'center', marginTop: 8 }}
              whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            >
              {submitting
                ? <><Loader size={15} style={{ animation: 'spin 1s linear infinite' }} /> Submitting…</>
                : <><Play size={15} /> Start Auto-Train</>}
            </motion.button>
          </form>
        </motion.div>

        {/* Progress */}
        <motion.div className="card" initial={{ x: 18, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.15 }}>
          <div className="flex items-center gap-2" style={{ marginBottom: 20 }}>
            <RefreshCw size={18} style={{ color: 'var(--accent)' }} />
            <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>Job Progress</span>
          </div>

          {!activeJob ? (
            <div className="empty-state">
              <Zap size={40} />
              <h3>No active job</h3>
              <p>Submit a training job to see progress</p>
            </div>
          ) : (
            <div>
              <div className="flex items-center gap-2" style={{ marginBottom: 12 }}>
                {statusIcon(jobStatus?.status)}
                <code className="mono text-sm text-accent">{activeJob}</code>
                <span className={`badge ${jobStatus?.status || 'pending'}`}>
                  <span className="badge-dot" />{jobStatus?.status || 'pending'}
                </span>
              </div>

              {/* Progress bar — only shown when backend returns a real progress value */}
              {jobStatus?.progress != null && (
                <div style={{ marginBottom: 16 }}>
                  <div className="flex justify-between mb-2">
                    <span className="text-muted text-sm">{jobStatus.message || 'Processing…'}</span>
                    <span className="mono text-accent text-sm">{jobStatus.progress}%</span>
                  </div>
                  <div className="progress-bar" role="progressbar"
                    aria-valuenow={jobStatus.progress} aria-valuemin={0} aria-valuemax={100}>
                    <div className="progress-fill" style={{ width: `${jobStatus.progress}%` }} />
                  </div>
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, fontSize: '0.78rem', marginBottom: 16 }}>
                <div><span className="text-muted">Created</span><p className="mono">{jobStatus?.created_at ? new Date(jobStatus.created_at).toLocaleTimeString() : '—'}</p></div>
                <div><span className="text-muted">Started</span><p className="mono">{jobStatus?.started_at ? new Date(jobStatus.started_at).toLocaleTimeString() : '—'}</p></div>
                <div><span className="text-muted">Done</span><p className="mono">{jobStatus?.completed_at ? new Date(jobStatus.completed_at).toLocaleTimeString() : '—'}</p></div>
              </div>

              {jobStatus?.error && (
                <div className="error-state" style={{ marginBottom: 12 }}>
                  <strong>Error:</strong> {jobStatus.error}
                </div>
              )}

              <AnimatePresence>
                {results && (
                  <motion.div
                    initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
                    style={{ background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 10, padding: 16 }}
                  >
                    <div className="flex items-center gap-2" style={{ marginBottom: 12 }}>
                      <CheckCircle2 size={16} style={{ color: 'var(--color-success)' }} />
                      <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--color-success)' }}>Training Complete</span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, fontSize: '0.8rem' }}>
                      <div><span className="text-muted">Frames Extracted</span><p className="mono" style={{ fontWeight: 600 }}>{results.frames_extracted ?? '—'}</p></div>
                      <div><span className="text-muted">Detections</span><p className="mono" style={{ fontWeight: 600 }}>{results.detections_count ?? '—'}</p></div>
                      <div style={{ gridColumn: '1/-1' }}><span className="text-muted">Model Path</span><p className="mono text-sm" style={{ wordBreak: 'break-all' }}>{results.model_path || '—'}</p></div>
                      <div style={{ gridColumn: '1/-1' }}><span className="text-muted">Output Video</span><p className="mono text-sm" style={{ wordBreak: 'break-all' }}>{results.output_video || '—'}</p></div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}
        </motion.div>
      </div>

      {/* Job history */}
      {history.length > 0 && (
        <motion.div className="mt-3" initial={{ y: 18, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}>
          <div className="section-title"><h2>Session Job History</h2></div>
          <div className="table-container">
            <table className="data-table">
              <thead><tr><th>Job ID</th><th>Status</th><th>Created</th></tr></thead>
              <tbody>
                {history.map(h => (
                  <tr key={h.job_id}>
                    <td className="mono text-accent">{h.job_id}</td>
                    <td><span className={`badge ${h.status}`}><span className="badge-dot" />{h.status}</span></td>
                    <td className="mono text-muted text-sm">{h.created_at ? new Date(h.created_at).toLocaleString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
