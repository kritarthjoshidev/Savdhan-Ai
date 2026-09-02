/**
 * StatusBadge — pending=amber, verified=green, rejected=muted, INTRUSION=red
 * Pass `intrusion={true}` for the INTRUSION override badge.
 */
export function StatusBadge({ status }) {
  return (
    <span className={`badge ${status}`} role="status" aria-label={status}>
      <span className="badge-dot" aria-hidden="true" />
      {status}
    </span>
  );
}

export function IntrusionBadge() {
  return (
    <span
      className="intrusion-badge"
      role="status"
      aria-label="INTRUSION detected"
    >
      ⚠ INTRUSION
    </span>
  );
}
