import { useCallback, useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Activity, Camera, CheckCircle2, LoaderCircle, Play, Plus, Radio, RefreshCw, ShieldAlert, Square, Trash2, Video, Wifi, X } from 'lucide-react';
import alertSocket from '../utils/ws';
import { addCamera, cameraStreamUrl, deleteCamera, listCameras, startCamera, stopCamera, testCamera } from '../utils/api';
import { useToast } from '../components/Toast';
import ConnectionStatus from '../components/ConnectionStatus';
import EmptyState from '../components/EmptyState';
import { EventBadge } from '../components/StatusBadge';

const initialForm = { name: '', camera_id: '', stream_url: '' };

const idFromName = (name) => name.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '').slice(0, 70);

function EventRow({ event }) {
  return (
    <div className={`live-event-row ${event.event === 'BORDER_INTRUSION' || event.event === 'INTRUSION' ? 'ev-intrusion' : event.event === 'TRAFFIC_ACCIDENT' ? 'ev-accident' : 'ev-other'}`}>
      <div className="ev-left">
        <span className="ev-time">{event._ts}</span>
        <EventBadge eventType={event.event} />
      </div>
      <div className="ev-right">
        {event.source_cam && <span className="ev-cam">{event.source_cam}</span>}
        {event.confidence != null && <span className="ev-conf">{(event.confidence * 100).toFixed(0)}%</span>}
        {event.incident_id && <span className="text-muted text-sm">#{event.incident_id}</span>}
      </div>
    </div>
  );
}

export default function LiveFeed() {
  const toast = useToast();
  const [cameras, setCameras] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [form, setForm] = useState(initialForm);
  const [analysisMode, setAnalysisMode] = useState('auto');
  const [adding, setAdding] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [busyId, setBusyId] = useState('');
  const [preview, setPreview] = useState({ status: 'idle', image: '', detections: [], error: '' });
  const [events, setEvents] = useState([]);
  const selectedIdRef = useRef('');

  const loadCameras = useCallback(async () => {
    try {
      const data = await listCameras();
      setCameras(Array.isArray(data) ? data : []);
      setSelectedId((current) => current || data?.[0]?.camera_id || '');
    } catch (err) {
      toast(err.message, 'error');
    }
  }, [toast]);

  useEffect(() => { loadCameras(); }, [loadCameras]);
  useEffect(() => {
    const timer = setInterval(loadCameras, 8000);
    return () => clearInterval(timer);
  }, [loadCameras]);
  useEffect(() => { selectedIdRef.current = selectedId; }, [selectedId]);

  useEffect(() => {
    alertSocket.connect();
    return alertSocket.subscribe((message) => {
      setEvents((current) => [{ ...message, _ts: new Date().toLocaleTimeString(), _uid: `${Date.now()}-${Math.random()}` }, ...current].slice(0, 12));
      if (message.event === 'BORDER_INTRUSION' || message.event === 'TRAFFIC_ACCIDENT') loadCameras();
    });
  }, [loadCameras]);

  useEffect(() => {
    if (!selectedId) {
      setPreview({ status: 'idle', image: '', detections: [], error: '' });
      return undefined;
    }
    setPreview({ status: 'connecting', image: '', detections: [], error: '' });
    const socket = new WebSocket(cameraStreamUrl(selectedId));
    socket.onmessage = ({ data }) => {
      try {
        const message = JSON.parse(data);
        if (message.type === 'frame') {
          setPreview({
            status: 'live',
            image: `data:image/jpeg;base64,${message.frame_jpeg}`,
            detections: message.detections || [],
            error: '',
          });
        } else if (message.type === 'error') {
          setPreview((current) => ({ ...current, status: 'error', error: message.error }));
        } else if (message.type === 'stream_end') {
          setPreview((current) => ({ ...current, status: 'ended', error: message.reason || 'Camera disconnected' }));
        }
      } catch {
        setPreview((current) => ({ ...current, status: 'error', error: 'Invalid camera message' }));
      }
    };
    socket.onerror = () => setPreview((current) => ({ ...current, status: 'error', error: 'Could not connect to camera preview' }));
    return () => socket.close();
  }, [selectedId]);

  const handleTest = async () => {
    if (!form.stream_url.trim()) return toast('Paste the phone camera stream URL first.', 'warning');
    setTesting(true);
    setTestResult(null);
    try {
      const result = await testCamera(form.stream_url.trim());
      setTestResult(result);
      toast(result.ok ? 'Camera is reachable' : result.message, result.ok ? 'success' : 'error');
    } catch (err) {
      setTestResult({ ok: false, message: err.message });
      toast(err.message, 'error');
    } finally {
      setTesting(false);
    }
  };

  const handleAdd = async (event) => {
    event.preventDefault();
    const camera_id = form.camera_id.trim() || idFromName(form.name);
    if (!camera_id || !form.stream_url.trim()) return toast('Camera name and stream URL are required.', 'warning');
    setAdding(true);
    try {
      const camera = await addCamera({ camera_id, name: form.name.trim() || camera_id, stream_url: form.stream_url.trim() });
      setForm(initialForm);
      setTestResult(null);
      setSelectedId(camera.camera_id);
      await loadCameras();
      toast('Camera added. Preview is connecting.', 'success');
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      setAdding(false);
    }
  };

  const handleStart = async (cameraId) => {
    setBusyId(cameraId);
    try {
      await startCamera(cameraId, {
        analysis_mode: analysisMode,
        confidence_threshold: 0.35,
        sample_every_n_frames: 8,
        fence_y_ratio: 0.5,
        accident_threshold: 0.52,
      });
      await loadCameras();
      const label = analysisMode === 'traffic' ? 'Traffic accident analysis' : analysisMode === 'border' ? 'Border protection' : 'Auto-profile analysis';
      toast(`${label} started. Named incidents will appear in Incidents.`, 'success');
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      setBusyId('');
    }
  };

  const handleStop = async (cameraId) => {
    setBusyId(cameraId);
    try {
      await stopCamera(cameraId);
      await loadCameras();
      toast('Camera detection is stopping.', 'warning');
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      setBusyId('');
    }
  };

  const handleDelete = async (cameraId) => {
    if (!window.confirm('Remove this saved camera? Its local credentials will be removed.')) return;
    setBusyId(cameraId);
    try {
      await deleteCamera(cameraId);
      if (selectedId === cameraId) setSelectedId('');
      await loadCameras();
      toast('Camera removed.', 'success');
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      setBusyId('');
    }
  };

  const selected = cameras.find((camera) => camera.camera_id === selectedId);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>
      <div className="page-header live-header">
        <div>
          <h1>Live Camera Command</h1>
          <p>Connect a phone or CCTV stream, watch annotated live frames, and choose border-intrusion or traffic-accident analysis.</p>
        </div>
        <ConnectionStatus />
      </div>

      <div className="live-command-grid">
        <section className="card live-preview-card">
          <div className="section-title">
            <h2><Video size={16} /> {selected?.name || 'Live preview'}</h2>
            <span className={`camera-live-status ${preview.status}`}>{preview.status}</span>
          </div>
          <div className="camera-preview">
            {preview.image ? <img src={preview.image} alt="Annotated live camera preview" /> : (
              <EmptyState icon={Camera} heading={selectedId ? 'Connecting to camera…' : 'Add a camera to begin'} sub={preview.error || 'The server processes the phone camera, then streams annotated frames here.'} />
            )}
          </div>
          {preview.detections.length > 0 && <div className="live-detections">{preview.detections.map((item, index) => <span key={`${item.class}-${index}`}>{item.class} {(item.confidence * 100).toFixed(0)}%</span>)}</div>}
          {selected && <p className="form-hint">Source: {selected.stream_url_masked}. Camera credentials stay on the backend and are not sent to the browser.</p>}
        </section>

        <section className="card camera-add-card">
          <div className="section-title"><h2><Plus size={16} /> Add phone / CCTV camera</h2></div>
          <form onSubmit={handleAdd} className="camera-form">
            <label>Camera name<input className="input" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="Gate phone camera" /></label>
            <label>Camera ID <span className="text-muted">(optional)</span><input className="input" value={form.camera_id} onChange={(event) => setForm({ ...form, camera_id: event.target.value })} placeholder="gate-phone" /></label>
            <label>Stream URL<input className="input" value={form.stream_url} onChange={(event) => setForm({ ...form, stream_url: event.target.value })} placeholder="http://192.168.1.23:8080/video or rtsp://…" required /></label>
            <div className="camera-form-actions">
              <button type="button" className="btn btn-ghost" onClick={handleTest} disabled={testing}>{testing ? <LoaderCircle className="spin" size={15} /> : <Wifi size={15} />} Test connection</button>
              <button type="submit" className="btn btn-primary" disabled={adding}>{adding ? 'Adding…' : 'Save camera'}</button>
            </div>
          </form>
          {testResult && <div className={`camera-test-result ${testResult.ok ? 'success' : 'error'}`}>{testResult.ok ? <CheckCircle2 size={15} /> : <X size={15} />}{testResult.message}{testResult.resolution ? ` — ${testResult.resolution}${testResult.fps ? ` @ ${testResult.fps} FPS` : ''}` : ''}</div>}
          <div className="phone-camera-help">
            <strong>Phone setup</strong>
            <p>Install an IP-camera app on the phone, start its server, then copy its video-stream URL. Both laptop and phone must use the same Wi-Fi. Do not enter <code>localhost</code>; use the phone’s LAN IP.</p>
            <p>Common formats: <code>http://PHONE_IP:8080/video</code> for an IP Webcam-style app, or <code>rtsp://PHONE_IP:PORT/STREAM</code> for an RTSP camera app.</p>
          </div>
        </section>
      </div>

      <section className="card camera-list-card">
        <div className="section-title"><h2><Camera size={16} /> Saved cameras</h2><button className="btn btn-ghost btn-sm" onClick={loadCameras}><RefreshCw size={13} /> Refresh</button></div>
        <div className="analysis-profile-control">
          <span>Protection profile</span>
          <select className="select" value={analysisMode} onChange={(event) => setAnalysisMode(event.target.value)} aria-label="Protection profile">
            <option value="auto">Auto — detect traffic or border context</option>
            <option value="border">Border — directional intrusion only</option>
            <option value="traffic">Traffic — accident scene only</option>
          </select>
          <span className="form-hint">Choose before pressing Protect. Auto prevents road footage from being labelled as border intrusion.</span>
        </div>
        {cameras.length === 0 ? <EmptyState icon={Camera} heading="No cameras saved" sub="Use the phone camera form above to add a stream." /> : <div className="camera-list">{cameras.map((camera) => {
          const active = ['starting', 'running', 'stopping'].includes(camera.status);
          const busy = busyId === camera.camera_id;
          return <div key={camera.camera_id} className={`camera-row ${selectedId === camera.camera_id ? 'selected' : ''}`}>
            <button className="camera-row-main" onClick={() => setSelectedId(camera.camera_id)}><span className="camera-name">{camera.name}</span><span className="camera-url">{camera.stream_url_masked}</span></button>
            <span className={`camera-status ${camera.status}`}>{camera.status}</span>
            <div className="camera-actions">{active ? <button className="btn btn-danger btn-sm" disabled={busy} onClick={() => handleStop(camera.camera_id)}><Square size={13} /> Stop</button> : <button className="btn btn-success btn-sm" disabled={busy} onClick={() => handleStart(camera.camera_id)}><Play size={13} /> Protect</button>}<button className="btn btn-ghost btn-sm" disabled={busy} onClick={() => handleDelete(camera.camera_id)} aria-label={`Remove ${camera.name}`}><Trash2 size={13} /></button></div>
          </div>;
        })}</div>}
      </section>

      <section className="card live-events-card">
        <div className="section-title"><h2><Radio size={16} /> Live alerts</h2><span className="text-muted text-sm">{events.length} recent events</span></div>
        <div className="live-event-feed">{events.length ? events.map((event) => <EventRow event={event} key={event._uid} />) : <EmptyState icon={ShieldAlert} heading="No live alerts yet" sub="Choose a profile, then click Protect on a camera." />}</div>
      </section>
    </motion.div>
  );
}
