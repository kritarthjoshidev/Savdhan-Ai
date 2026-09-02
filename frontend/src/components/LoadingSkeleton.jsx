/** LoadingSkeleton — animated shimmer rows */
export default function LoadingSkeleton({ rows = 5, cols = 6 }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, r) => (
        <tr key={r} aria-hidden="true">
          {Array.from({ length: cols }).map((_, c) => (
            <td key={c}>
              <div
                className="skeleton"
                style={{ height: 16, width: `${55 + (c * 7) % 35}%` }}
              />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

/** Inline skeleton for non-table use */
export function SkeletonBlock({ height = 16, width = '70%', style }) {
  return <div className="skeleton" style={{ height, width, ...style }} aria-hidden="true" />;
}
