import { AlertTriangle } from 'lucide-react';

/** EmptyState — centered icon + heading + optional sub-text */
export default function EmptyState({ icon: Icon = AlertTriangle, heading, sub, children }) {
  return (
    <div className="empty-state" role="status" aria-live="polite">
      <Icon size={40} aria-hidden="true" />
      {heading && <h3>{heading}</h3>}
      {sub     && <p>{sub}</p>}
      {children}
    </div>
  );
}
