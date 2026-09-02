import { useEffect, useState } from 'react';
import { Wifi, WifiOff, Radio, Loader } from 'lucide-react';
import alertSocket from '../utils/ws';

const CONFIG = {
  live:         { label: 'Live',         cls: 'conn-live',         Icon: Radio },
  connecting:   { label: 'Connecting',   cls: 'conn-connecting',   Icon: Loader },
  reconnecting: { label: 'Reconnecting', cls: 'conn-reconnecting', Icon: WifiOff },
  offline:      { label: 'Offline',      cls: 'conn-offline',      Icon: WifiOff },
};

/**
 * ConnectionStatus — shows a coloured pill reflecting the WebSocket status.
 * Subscribes to alertSocket.onStatusChange — no props needed.
 */
export default function ConnectionStatus() {
  const [status, setStatus] = useState(alertSocket.getStatus());

  useEffect(() => {
    const unsub = alertSocket.onStatusChange(setStatus);
    return unsub;
  }, []);

  const { label, cls, Icon } = CONFIG[status] || CONFIG.offline;
  const spinning = status === 'connecting' || status === 'reconnecting';

  return (
    <span
      className={`connection-pill ${cls}`}
      role="status"
      aria-live="polite"
      aria-label={`WebSocket: ${label}`}
    >
      <Icon
        size={12}
        style={spinning ? { animation: 'spin 1s linear infinite' } : undefined}
        aria-hidden="true"
      />
      {label}
    </span>
  );
}
