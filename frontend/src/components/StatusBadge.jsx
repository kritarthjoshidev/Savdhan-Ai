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

export function EventBadge({ eventType }) {
  const normalizedEventType = String(eventType || '').toUpperCase();
  if (normalizedEventType === 'BORDER_INTRUSION' || normalizedEventType === 'INTRUSION') {
    return <IntrusionBadge />;
  }
  if (normalizedEventType === 'TRAFFIC_ACCIDENT') {
    return (
      <span className="event-badge accident" role="status" aria-label="Traffic accident suspected">
        ⚠ TRAFFIC ACCIDENT
      </span>
    );
  }
  const fallbackLabel = normalizedEventType
    ? normalizedEventType.replaceAll('_', ' ')
    : 'Unclassified event';
  return <span className="event-badge" role="status" aria-label={fallbackLabel}>{fallbackLabel}</span>;
}
