/**
 * BorderFencePreview — SVG schematic of the directional virtual fence.
 * fenceRatio: 0.05–0.95, where 0.5 means midway down the frame.
 * Labeled clearly as "Fence Configuration Preview" — not a live video overlay.
 */
export default function BorderFencePreview({ fenceRatio = 0.5 }) {
  const W = 320;
  const H = 200;
  const fenceY = Math.round(H * fenceRatio);
  const arrowX = W / 2;

  return (
    <figure className="fence-preview" aria-label="Fence Configuration Preview diagram">
      <figcaption className="fence-preview-caption">Fence Configuration Preview</figcaption>

      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`Virtual fence at ${Math.round(fenceRatio * 100)}% of frame height`}
        style={{ width: '100%', maxWidth: W, display: 'block' }}
      >
        {/* Safe zone (above fence) */}
        <rect x={0} y={0} width={W} height={fenceY}
          fill="rgba(16,185,129,0.08)" />
        <text x={12} y={Math.max(18, fenceY / 2)} fill="#10b981"
          fontSize={11} fontFamily="var(--font-mono)" fontWeight={600}>
          SAFE ZONE
        </text>

        {/* Restricted zone (below fence) */}
        <rect x={0} y={fenceY} width={W} height={H - fenceY}
          fill="rgba(239,68,68,0.10)" />
        <text x={12} y={Math.min(H - 8, fenceY + (H - fenceY) / 2 + 5)} fill="#ef4444"
          fontSize={11} fontFamily="var(--font-mono)" fontWeight={600}>
          RESTRICTED ZONE
        </text>

        {/* Fence line */}
        <line x1={0} y1={fenceY} x2={W} y2={fenceY}
          stroke="#f59e0b" strokeWidth={2} strokeDasharray="8 4" />

        {/* Fence label */}
        <rect x={W / 2 - 42} y={fenceY - 10} width={84} height={20} rx={4}
          fill="#0f172a" stroke="#f59e0b" strokeWidth={1} />
        <text x={W / 2} y={fenceY + 5} fill="#f59e0b"
          fontSize={10} fontFamily="var(--font-mono)" textAnchor="middle" fontWeight={700}>
          VIRTUAL FENCE
        </text>

        {/* Downward direction arrow */}
        <g aria-label="Crossing direction: above to below triggers INTRUSION">
          <line
            x1={arrowX} y1={fenceY - 30}
            x2={arrowX} y2={fenceY + 30}
            stroke="#ef4444" strokeWidth={2.5}
          />
          <polygon
            points={`${arrowX - 7},${fenceY + 18} ${arrowX + 7},${fenceY + 18} ${arrowX},${fenceY + 32}`}
            fill="#ef4444"
          />
        </g>

        {/* Frame border */}
        <rect x={1} y={1} width={W - 2} height={H - 2}
          fill="none" stroke="rgba(148,163,184,0.15)" strokeWidth={1} rx={4} />
      </svg>

      <p className="fence-preview-hint">
        Crossing <strong>above → below</strong> the fence line triggers an{' '}
        <strong style={{ color: '#ef4444' }}>INTRUSION</strong> event.{' '}
        Fence at <strong>{Math.round(fenceRatio * 100)}%</strong> of frame height.
      </p>
    </figure>
  );
}
