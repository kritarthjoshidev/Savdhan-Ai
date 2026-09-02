/**
 * MetricCard — icon + label + value stat card
 * Props: icon (Lucide component), color (css class suffix), label, value, loading
 */
export default function MetricCard({ icon: Icon, color = 'cyan', label, value, loading = false }) {
  return (
    <div className="stat-card" role="region" aria-label={label}>
      <div className={`stat-icon ${color}`} aria-hidden="true">
        {Icon && <Icon size={20} />}
      </div>
      <div className="stat-info">
        <div className="stat-label">{label}</div>
        <div className="stat-value">
          {loading ? <div className="skeleton" style={{ height: 24, width: 48 }} /> : value}
        </div>
      </div>
    </div>
  );
}
