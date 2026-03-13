import { useEffect, useMemo } from 'react';

const COLORS = ['#f7c948', '#1a7a40', '#c0392b', '#3498db', '#9b59b6', '#e67e22', '#e8a050', '#f39c12'];

function CelebrationOverlay({ slot, onDone }) {
  useEffect(() => {
    const t = setTimeout(onDone, 3800);
    return () => clearTimeout(t);
  }, [onDone]);

  const pieces = useMemo(() =>
    Array.from({ length: 90 }, (_, i) => ({
      id: i,
      color: COLORS[i % COLORS.length],
      left: ((i * 13.7 + 3) % 100),
      delay: (i * 0.038) % 2.2,
      duration: 2.2 + (i % 6) * 0.3,
      size: 7 + (i % 5) * 2.5,
      isCircle: i % 4 === 0,
      isLong: i % 5 === 2,
    })),
  []);

  const { barista, location } = slot;

  return (
    <div className="celebration-overlay">
      <div className="confetti-container" aria-hidden="true">
        {pieces.map((p) => (
          <div
            key={p.id}
            className="confetti-piece"
            style={{
              left: `${p.left}%`,
              backgroundColor: p.color,
              width: p.isLong ? p.size * 0.5 : p.size,
              height: p.isLong ? p.size * 2.5 : p.size,
              borderRadius: p.isCircle ? '50%' : '2px',
              animationDelay: `${p.delay}s`,
              animationDuration: `${p.duration}s`,
            }}
          />
        ))}
      </div>

      <div className="celebration-content">
        <div className="celebration-icon">🎉</div>
        <h1 className="celebration-title">You're Booked!</h1>
        <p className="celebration-sub">
          See you at <strong>{location}</strong> with <strong>{barista.name}</strong>
        </p>
        <button className="celebration-done-btn" onClick={onDone}>
          Back to Calendar
        </button>
      </div>
    </div>
  );
}

export default CelebrationOverlay;
