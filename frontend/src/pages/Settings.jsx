import { useState } from 'react';
import { motion } from 'framer-motion';
import { Server, Info, Palette, ExternalLink } from 'lucide-react';

export default function Settings() {
  const [apiUrl, setApiUrl] = useState('http://localhost:8000');

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
      <div className="page-header"><h1>Settings</h1><p>Configure your Sawdhan AI dashboard</p></div>

      <div style={{ maxWidth: 640 }}>
        <motion.div className="card" style={{ marginBottom: 20 }} initial={{ y: 15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}>
          <div className="flex items-center gap-2" style={{ marginBottom: 16 }}><Server size={18} style={{ color: 'var(--accent)' }} /><span style={{ fontWeight: 700, fontSize: '0.95rem' }}>API Connection</span></div>
          <div className="form-group"><label className="form-label">Backend URL</label><input type="text" className="input" value={apiUrl} onChange={(e) => setApiUrl(e.target.value)} placeholder="http://localhost:8000" /><span className="text-muted" style={{ fontSize: '0.72rem', marginTop: 4, display: 'block' }}>FastAPI backend running address</span></div>
          <div className="flex gap-2 mt-2">
            <a href={`${apiUrl}/docs`} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm"><ExternalLink size={14} /> Swagger UI</a>
            <a href={`${apiUrl}/redoc`} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm"><ExternalLink size={14} /> ReDoc</a>
          </div>
        </motion.div>

        <motion.div className="card" style={{ marginBottom: 20 }} initial={{ y: 15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}>
          <div className="flex items-center gap-2" style={{ marginBottom: 16 }}><Palette size={18} style={{ color: 'var(--accent)' }} /><span style={{ fontWeight: 700, fontSize: '0.95rem' }}>Appearance</span></div>
          <div style={{ display: 'flex', gap: 12 }}>
            <motion.div whileHover={{ scale: 1.03 }} style={{ flex: 1, padding: '14px 16px', borderRadius: 10, border: '2px solid var(--accent)', background: 'rgba(6,182,212,0.06)', cursor: 'pointer', textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', marginBottom: 4 }}>🌙</div><span style={{ fontWeight: 600, fontSize: '0.82rem' }}>Dark Mode</span><div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 2 }}>Active</div>
            </motion.div>
            <div style={{ flex: 1, padding: '14px 16px', borderRadius: 10, border: '1px solid var(--border-color)', background: 'var(--bg-card)', cursor: 'not-allowed', textAlign: 'center', opacity: 0.5 }}>
              <div style={{ fontSize: '1.5rem', marginBottom: 4 }}>☀️</div><span style={{ fontWeight: 600, fontSize: '0.82rem' }}>Light Mode</span><div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 2 }}>Coming soon</div>
            </div>
          </div>
        </motion.div>

        <motion.div className="card" initial={{ y: 15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}>
          <div className="flex items-center gap-2" style={{ marginBottom: 16 }}><Info size={18} style={{ color: 'var(--accent)' }} /><span style={{ fontWeight: 700, fontSize: '0.95rem' }}>About</span></div>
          <div style={{ fontSize: '0.85rem', lineHeight: 1.8 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '8px 0' }}>
              <span className="text-muted">Application</span><span style={{ fontWeight: 600 }}>Sawdhan AI Surveillance</span>
              <span className="text-muted">Version</span><span className="mono">1.0.0</span>
              <span className="text-muted">Backend</span><span className="mono">FastAPI v0.1.0</span>
              <span className="text-muted">ML Engine</span><span>YOLOv8 + YOLO-World</span>
              <span className="text-muted">Tracking</span><span>Multi-Object + Re-ID (OSNet)</span>
              <span className="text-muted">Storage</span><span>MinIO (S3) + PostgreSQL</span>
              <span className="text-muted">ML Tracking</span><span>MLflow</span>
              <span className="text-muted">Queue</span><span>Celery + Redis</span>
              <span className="text-muted">License</span><span>MIT</span>
            </div>
          </div>
          <div style={{ marginTop: 20, padding: 14, borderRadius: 10, background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.1)', fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            <strong style={{ color: 'var(--accent)' }}>Sawdhan AI</strong> is a complete AI surveillance system with real-time YOLO detection, person Re-ID matching across cameras, automated model training from video, and a human-in-the-loop incident verification pipeline. Infrastructure includes PostgreSQL, Redis, MinIO, MLflow, and Celery workers.
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
