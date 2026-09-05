import { useContext, createContext, useCallback, useState, useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { X, ShieldAlert, Volume2, VolumeX } from 'lucide-react';

// ─── Existing Toast context (re-exported for backward compat) ─────────────────
const ToastCtx = createContext(null);
export const useToast = () => useContext(ToastCtx);

// ─── Simple toast store ───────────────────────────────────────────────────────
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const idRef = useRef(0);

  const show = useCallback((message, type = 'info', duration = 4000) => {
    const id = ++idRef.current;
    setToasts(p => [...p, { id, message, type }]);
    setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), duration);
  }, []);

  const dismiss = useCallback((id) => {
    setToasts(p => p.filter(t => t.id !== id));
  }, []);

  return (
    <ToastCtx.Provider value={show}>
      {children}
      <div
        className="toast-container"
        role="region"
        aria-label="Notifications"
        aria-live="assertive"
      >
        <AnimatePresence>
          {toasts.map(t => (
            <motion.div
              key={t.id}
              className={`toast-item toast-${t.type}`}
              initial={{ x: 80, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 80, opacity: 0 }}
              transition={{ duration: 0.25 }}
              role="alert"
            >
              <span className="toast-msg">{t.message}</span>
              <button
                className="toast-close"
                onClick={() => dismiss(t.id)}
                aria-label="Dismiss notification"
              >
                <X size={14} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastCtx.Provider>
  );
}

// ─── INTRUSION alert banner (shown at top of page) ────────────────────────────
/**
 * AlertToast — displays a prominent INTRUSION banner.
 * Sound is DISABLED by default; user must click the toggle to enable
 * (browser autoplay policy requires user gesture before audio can play).
 *
 * Props:
 *   alerts: Array of INTRUSION WS messages
 *   onDismiss: (index) => void
 */
export function IntrusionAlertBar({ alerts = [], onDismiss }) {
  // Sound disabled by default (autoplay policy)
  const [soundOn, setSoundOn] = useState(false);
  const audioRef = useRef(null);
  const prevCountRef = useRef(0);

  // Play audio on new INTRUSION if user has enabled sound
  useEffect(() => {
    if (soundOn && alerts.length > prevCountRef.current) {
      try {
        if (!audioRef.current) {
          audioRef.current = new Audio(
            'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAA' +
            'EAAQARAAAARAAAA2AAACABAAAABkYXRhAAAAAA=='
          );
        }
        audioRef.current.currentTime = 0;
        audioRef.current.play().catch(() => {/* ignore autoplay block */});
      } catch { /* ignore */ }
    }
    prevCountRef.current = alerts.length;
  }, [alerts.length, soundOn]);

  if (alerts.length === 0) return null;

  const latest = alerts[0];
  const isTrafficAccident = latest.event === 'TRAFFIC_ACCIDENT';
  const title = isTrafficAccident ? 'TRAFFIC ACCIDENT' : 'BORDER INTRUSION';

  return (
    <motion.div
      className="intrusion-alert-bar"
      initial={{ y: -60, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: -60, opacity: 0 }}
      role="alert"
      aria-live="assertive"
      aria-label={`${title} detected`}
    >
      <ShieldAlert size={18} aria-hidden="true" />
      <span className="intrusion-alert-text">
        <strong>{title}</strong> — camera{' '}
        <code>{latest.source_cam}</code>,&nbsp;
        confidence {latest.confidence != null ? `${(latest.confidence * 100).toFixed(0)}%` : '—'}
        {latest.track_id ? `, track ${latest.track_id}` : ''}
      </span>
      <button
        className="intrusion-sound-btn"
        onClick={() => setSoundOn(v => !v)}
        title={soundOn ? 'Mute alert sound' : 'Enable alert sound (requires click)'}
        aria-label={soundOn ? 'Mute alert sound' : 'Enable alert sound'}
      >
        {soundOn ? <Volume2 size={14} /> : <VolumeX size={14} />}
      </button>
      {onDismiss && (
        <button
          className="intrusion-dismiss-btn"
          onClick={() => onDismiss(0)}
          aria-label="Dismiss intrusion alert"
        >
          <X size={14} />
        </button>
      )}
    </motion.div>
  );
}
