// Derive WebSocket URL from VITE_API_BASE_URL (http→ws, https→wss)
const HTTP_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const WS_URL = HTTP_BASE.replace(/^http/, 'ws') + '/ws/alerts';

const PING_INTERVAL_MS   = 20_000; // backend needs incoming text to stay alive
const INITIAL_BACKOFF_MS = 2_000;
const MAX_BACKOFF_MS     = 30_000;

/** @typedef {'connecting'|'live'|'reconnecting'|'offline'} WsStatus */

class AlertSocket {
  constructor() {
    this.ws              = null;
    this.listeners       = new Set();
    this.statusListeners = new Set();
    this.reconnectTimer  = null;
    this.pingTimer       = null;
    this.backoffDelay    = INITIAL_BACKOFF_MS;
    /** @type {WsStatus} */
    this._status         = 'offline';
    this._intentionalClose = false;
  }

  // ── Status ─────────────────────────────────────────────────────────────────
  getStatus() { return this._status; }

  /** @param {(status: WsStatus) => void} fn */
  onStatusChange(fn) {
    this.statusListeners.add(fn);
    return () => this.statusListeners.delete(fn);
  }

  _setStatus(s) {
    if (this._status === s) return;
    this._status = s;
    this.statusListeners.forEach(fn => fn(s));
  }

  // ── Connection ─────────────────────────────────────────────────────────────
  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) return;
    this._intentionalClose = false;
    this._setStatus('connecting');

    try {
      this.ws = new WebSocket(WS_URL);

      this.ws.onopen = () => {
        console.log('[WS] Connected:', WS_URL);
        this.backoffDelay = INITIAL_BACKOFF_MS;
        this._setStatus('live');
        this._startPing();
      };

      this.ws.onmessage = (event) => {
        if (event.data === 'pong') return; // heartbeat echo
        try {
          const data = JSON.parse(event.data);
          this.listeners.forEach(fn => fn(data));
        } catch (e) {
          console.warn('[WS] Parse error:', e);
        }
      };

      this.ws.onclose = () => {
        this._stopPing();
        if (this._intentionalClose) {
          this._setStatus('offline');
          return;
        }
        console.log('[WS] Disconnected — will reconnect in', this.backoffDelay, 'ms');
        this._setStatus('reconnecting');
        this._scheduleReconnect();
      };

      this.ws.onerror = () => {
        // onclose fires after onerror — handled there
      };
    } catch {
      this._setStatus('reconnecting');
      this._scheduleReconnect();
    }
  }

  _startPing() {
    this._stopPing();
    this.pingTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, PING_INTERVAL_MS);
  }

  _stopPing() {
    if (this.pingTimer) { clearInterval(this.pingTimer); this.pingTimer = null; }
  }

  _scheduleReconnect() {
    clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => {
      this.backoffDelay = Math.min(this.backoffDelay * 2, MAX_BACKOFF_MS);
      this.connect();
    }, this.backoffDelay);
  }

  // ── Subscribe ──────────────────────────────────────────────────────────────
  /** @param {(data: object) => void} fn  @returns {() => void} unsubscribe */
  subscribe(fn) {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  // ── Disconnect ─────────────────────────────────────────────────────────────
  disconnect() {
    this._intentionalClose = true;
    this._stopPing();
    clearTimeout(this.reconnectTimer);
    if (this.ws) { this.ws.close(); this.ws = null; }
    this._setStatus('offline');
  }
}

const alertSocket = new AlertSocket();
export default alertSocket;
