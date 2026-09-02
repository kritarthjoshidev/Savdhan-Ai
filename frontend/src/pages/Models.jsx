import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Box, Rocket, Crown, RefreshCw, FileText, X, Cpu, AlertTriangle } from 'lucide-react';
import { listModels, getProductionModel, deployModel, listTrainJobs, getTrainLogs, triggerTraining } from '../utils/api';
import { useToast } from '../components/Toast';
import { StatusBadge } from '../components/StatusBadge';
import EmptyState from '../components/EmptyState';
import LoadingSkeleton from '../components/LoadingSkeleton';

export default function Models() {
  const toast = useToast();
  const [models, setModels]         = useState([]);
  const [prodModel, setProdModel]   = useState(undefined); // undefined=loading, null=none
  const [jobs, setJobs]             = useState([]);
  const [loadingModels, setLoadingModels] = useState(true);
  const [loadingJobs, setLoadingJobs]     = useState(true);
  const [logsModal, setLogsModal]   = useState(null);
  const [logs, setLogs]             = useState('');
  const [deployModal, setDeployModal] = useState(null); // model to deploy
  const [deploying, setDeploying]   = useState(false);

  // Manual training form
  const [trainForm, setTrainForm] = useState({
    model_name: '', base_model: 'yolov8n', epochs: 50, batch_size: 16, data_yaml_path: '',
  });
  const [training, setTraining] = useState(false);

  const loadModels = async () => {
    setLoadingModels(true);
    try {
      const d = await listModels();
      setModels(Array.isArray(d) ? d : []);
    } catch (e) { toast(e.message, 'error'); }
    finally { setLoadingModels(false); }
  };

  const loadProdModel = async () => {
    try {
      const d = await getProductionModel();
      setProdModel(d || null);
    } catch (e) {
      // 404 = no production model yet — valid empty state, not an error
      if (e.status === 404) { setProdModel(null); }
      else { toast('Could not fetch production model: ' + e.message, 'warning'); setProdModel(null); }
    }
  };

  const loadJobs = async () => {
    setLoadingJobs(true);
    try {
      const d = await listTrainJobs({ limit: 50 });
      setJobs(Array.isArray(d) ? d : []);
    } catch (e) { toast(e.message, 'error'); }
    finally { setLoadingJobs(false); }
  };

  useEffect(() => { loadModels(); loadProdModel(); loadJobs(); }, []);

  const handleDeploy = async () => {
    if (!deployModal) return;
    setDeploying(true);
    try {
      await deployModel(deployModal.id);
      toast('Model deployed to production!', 'success');
      setDeployModal(null);
      loadModels();
      loadProdModel();
    } catch (e) { toast(e.message, 'error'); }
    finally { setDeploying(false); }
  };

  const viewLogs = async (id) => {
    setLogsModal(id);
    setLogs('Loading…');
    try {
      const d = await getTrainLogs(id);
      setLogs(d.logs || 'No logs available.');
    } catch (e) { setLogs('Error: ' + e.message); }
  };

  const handleTrain = async (e) => {
    e.preventDefault();
    if (!trainForm.model_name.trim()) { toast('Model name is required', 'warning'); return; }
    if (!trainForm.data_yaml_path.trim()) { toast('Dataset YAML path is required', 'warning'); return; }
    setTraining(true);
    try {
      await triggerTraining({
        model_name:     trainForm.model_name.trim(),
        base_model:     trainForm.base_model,
        epochs:         Number(trainForm.epochs),
        batch_size:     Number(trainForm.batch_size),
        data_yaml_path: trainForm.data_yaml_path.trim(),
      });
      toast('Training job queued!', 'success');
      loadJobs();
    } catch (e) { toast(e.message, 'error'); }
    finally { setTraining(false); }
  };

  const setTrain = (k, v) => setTrainForm(f => ({ ...f, [k]: v }));

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>
      <div className="page-header">
        <h1>Models</h1>
        <p>Manage YOLO models, training jobs, and deployments</p>
      </div>

      {/* Production model card */}
      {prodModel === undefined ? (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="skeleton" style={{ height: 20, width: '40%', marginBottom: 12 }} />
          <div className="skeleton" style={{ height: 14, width: '70%' }} />
        </div>
      ) : prodModel === null ? (
        <motion.div
          className="card"
          style={{ marginBottom: 24, border: '1px solid var(--border-color)' }}
          initial={{ y: 8, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
        >
          <EmptyState icon={Crown} heading="No production model deployed yet" sub="Deploy a candidate model below to activate it." />
        </motion.div>
      ) : (
        <motion.div
          className="card"
          style={{ marginBottom: 24, border: '1px solid rgba(6,182,212,0.25)', background: 'linear-gradient(135deg,rgba(6,182,212,0.06),rgba(59,130,246,0.04))' }}
          initial={{ y: 8, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}
        >
          <div className="flex items-center gap-2" style={{ marginBottom: 12 }}>
            <Crown size={18} style={{ color: '#fbbf24' }} />
            <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>Production Model</span>
            <StatusBadge status="production" />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(140px,1fr))', gap: 16, fontSize: '0.85rem' }}>
            <div><span className="text-muted text-sm">Name</span><p style={{ fontWeight: 600 }}>{prodModel.model_name}</p></div>
            <div><span className="text-muted text-sm">Version</span><p className="mono">{prodModel.version || '—'}</p></div>
            <div><span className="text-muted text-sm">Base</span><p className="mono">{prodModel.base_model || '—'}</p></div>
            <div><span className="text-muted text-sm">mAP</span><p className="mono text-accent">{prodModel.metrics?.mAP ? (prodModel.metrics.mAP * 100).toFixed(1) + '%' : '—'}</p></div>
          </div>
        </motion.div>
      )}

      {/* Model registry */}
      <div className="section-title">
        <h2><Box size={15} style={{ marginRight: 8, verticalAlign: 'middle' }} />Model Registry</h2>
        <button className="btn btn-ghost btn-sm" onClick={loadModels} aria-label="Refresh models">
          <RefreshCw size={13} /> Refresh
        </button>
      </div>
      <motion.div className="table-container mb-2" initial={{ y: 14, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th><th>Name</th><th>Version</th><th>Base</th>
              <th>Status</th><th>mAP</th><th>Created</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loadingModels
              ? <LoadingSkeleton rows={4} cols={8} />
              : models.length === 0
                ? <tr><td colSpan={8}><EmptyState icon={Box} heading="No models" sub="Train a model to get started" /></td></tr>
                : models.map((m, i) => (
                  <motion.tr key={m.id} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }}>
                    <td className="mono text-accent">#{m.id}</td>
                    <td style={{ fontWeight: 600 }}>{m.model_name}</td>
                    <td className="mono text-muted">{m.version || '—'}</td>
                    <td className="mono text-sm">{m.base_model || '—'}</td>
                    <td><StatusBadge status={m.status} /></td>
                    <td className="mono">{m.metrics?.mAP ? (m.metrics.mAP * 100).toFixed(1) + '%' : '—'}</td>
                    <td className="text-muted text-sm mono">{m.created_at ? new Date(m.created_at).toLocaleDateString() : '—'}</td>
                    <td>
                      {m.status === 'candidate' && (
                        <button className="btn btn-primary btn-sm" onClick={() => setDeployModal(m)}>
                          <Rocket size={13} /> Deploy
                        </button>
                      )}
                      {m.status === 'production' && <span className="text-muted text-sm">Active</span>}
                    </td>
                  </motion.tr>
                ))
            }
          </tbody>
        </table>
      </motion.div>

      {/* Manual training form */}
      <div className="section-title mt-3">
        <h2><Cpu size={15} style={{ marginRight: 8, verticalAlign: 'middle' }} />Trigger Training Job</h2>
      </div>
      <motion.div className="card" style={{ marginBottom: 24 }} initial={{ y: 14, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.25 }}>
        <form onSubmit={handleTrain} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))', gap: 16 }}>
          <div className="form-group">
            <label className="form-label">Model Name</label>
            <input className="input" placeholder="border_detector_v1" value={trainForm.model_name} onChange={e => setTrain('model_name', e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Base Model</label>
            <select className="select" value={trainForm.base_model} onChange={e => setTrain('base_model', e.target.value)}>
              <option>yolov8n</option><option>yolov8s</option><option>yolov8m</option><option>yolov8l</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Epochs</label>
            <input type="number" className="input" value={trainForm.epochs} min={1} max={500} onChange={e => setTrain('epochs', e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Batch Size</label>
            <input type="number" className="input" value={trainForm.batch_size} min={1} max={128} onChange={e => setTrain('batch_size', e.target.value)} />
          </div>
          <div className="form-group" style={{ gridColumn: '1/-1' }}>
            <label className="form-label">Dataset YAML Path (server-side)</label>
            <input className="input" placeholder="/path/to/dataset/data.yaml" value={trainForm.data_yaml_path} onChange={e => setTrain('data_yaml_path', e.target.value)} />
          </div>
          <div style={{ gridColumn: '1/-1' }}>
            <button type="submit" className="btn btn-primary" disabled={training}>
              {training ? <><RefreshCw size={14} style={{ animation: 'spin 1s linear infinite' }} /> Submitting…</> : <><Cpu size={14} /> Queue Training Job</>}
            </button>
          </div>
        </form>
      </motion.div>

      {/* Training jobs */}
      <div className="section-title mt-3">
        <h2><Cpu size={15} style={{ marginRight: 8, verticalAlign: 'middle' }} />Training Jobs</h2>
        <button className="btn btn-ghost btn-sm" onClick={loadJobs} aria-label="Refresh jobs"><RefreshCw size={13} /> Refresh</button>
      </div>
      <motion.div className="table-container" initial={{ y: 14, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}>
        <table className="data-table">
          <thead><tr><th>ID</th><th>Status</th><th>Config</th><th>Created</th><th>Started</th><th>Completed</th><th>Actions</th></tr></thead>
          <tbody>
            {loadingJobs
              ? <LoadingSkeleton rows={3} cols={7} />
              : jobs.length === 0
                ? <tr><td colSpan={7}><EmptyState icon={Cpu} heading="No training jobs" sub="Queue a training job above" /></td></tr>
                : jobs.map((j, i) => (
                  <motion.tr key={j.id} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }}>
                    <td className="mono text-accent">#{j.id}</td>
                    <td><StatusBadge status={j.status} /></td>
                    <td className="text-sm text-muted" style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {j.config ? `${j.config.model_name || ''} · ${j.config.epochs || '—'} ep` : '—'}
                    </td>
                    <td className="mono text-sm text-muted">{j.created_at ? new Date(j.created_at).toLocaleString() : '—'}</td>
                    <td className="mono text-sm text-muted">{j.started_at ? new Date(j.started_at).toLocaleTimeString() : '—'}</td>
                    <td className="mono text-sm text-muted">{j.completed_at ? new Date(j.completed_at).toLocaleTimeString() : '—'}</td>
                    <td>
                      <button className="btn btn-ghost btn-sm" onClick={() => viewLogs(j.id)} aria-label={`View logs for job #${j.id}`}>
                        <FileText size={13} /> Logs
                      </button>
                    </td>
                  </motion.tr>
                ))
            }
          </tbody>
        </table>
      </motion.div>

      {/* Deploy confirmation modal */}
      <AnimatePresence>
        {deployModal && (
          <motion.div className="modal-overlay" onClick={() => setDeployModal(null)} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <motion.div className="modal" onClick={e => e.stopPropagation()} initial={{ scale: 0.92 }} animate={{ scale: 1 }} exit={{ scale: 0.92 }}
              role="dialog" aria-modal="true" aria-label="Deploy model confirmation">
              <div className="modal-header">
                <h2>Deploy Model to Production</h2>
                <button className="modal-close" onClick={() => setDeployModal(null)} aria-label="Cancel"><X size={20} /></button>
              </div>
              <p style={{ marginBottom: 16, color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
                Deploy <strong>{deployModal.model_name}</strong> (v{deployModal.version || '?'}) as the production model?
                The current production model will be replaced.
              </p>
              <div className="flex gap-2">
                <button className="btn btn-primary" onClick={handleDeploy} disabled={deploying}>
                  {deploying ? 'Deploying…' : <><Rocket size={14} /> Confirm Deploy</>}
                </button>
                <button className="btn btn-ghost" onClick={() => setDeployModal(null)}>Cancel</button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Logs modal */}
      <AnimatePresence>
        {logsModal !== null && (
          <motion.div className="modal-overlay" onClick={() => setLogsModal(null)} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <motion.div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 720 }}
              initial={{ scale: 0.92 }} animate={{ scale: 1 }} exit={{ scale: 0.92 }}
              role="dialog" aria-modal="true" aria-label={`Training logs for job #${logsModal}`}>
              <div className="modal-header">
                <h2>Training Logs — Job #{logsModal}</h2>
                <button className="modal-close" onClick={() => setLogsModal(null)} aria-label="Close"><X size={20} /></button>
              </div>
              <pre style={{ background: 'var(--bg-input)', padding: 16, borderRadius: 10, fontSize: '0.78rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', maxHeight: 420, overflow: 'auto', whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                {logs}
              </pre>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
