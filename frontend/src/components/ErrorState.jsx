import { AlertTriangle } from 'lucide-react';

/** ErrorState — red-tinted card with error message */
export default function ErrorState({ message, onRetry }) {
  return (
    <div
      className="error-state"
      role="alert"
      aria-live="assertive"
    >
      <AlertTriangle size={20} aria-hidden="true" />
      <span>{message || 'An unexpected error occurred.'}</span>
      {onRetry && (
        <button className="btn btn-ghost btn-sm" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
