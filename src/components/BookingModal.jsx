import { useEffect } from 'react';

function BookingModal({ slot, onConfirm, onCancel }) {
  const { barista, start_time, end_time, location } = slot;

  const fmt = (dt) =>
    new Date(dt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const formatted = new Date(start_time).toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric',
  });

  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onCancel(); }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onCancel]);

  const rows = [
    { label: 'Barista',  value: barista.name },
    { label: 'Date',     value: formatted },
    { label: 'Time',     value: `${fmt(start_time)} – ${fmt(end_time)}` },
    { label: 'Location', value: location },
  ];

  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <div className="booking-modal" onClick={(e) => e.stopPropagation()}>
        <div className="booking-modal-header">
          <span className="booking-modal-icon">☕</span>
          <h2 className="booking-modal-title">Book This Spot?</h2>
          <p className="booking-modal-sub">Confirm your coffee chat details</p>
        </div>

        <div className="booking-modal-details">
          {rows.map(({ label, value }) => (
            <div key={label} className="booking-detail-row">
              <span className="booking-detail-label">{label}</span>
              <span className="booking-detail-value">{value}</span>
            </div>
          ))}
        </div>

        <div className="booking-modal-actions">
          <button className="bm-btn-cancel" onClick={onCancel}>Cancel</button>
          <button className="bm-btn-confirm" onClick={onConfirm}>Yes, Book It!</button>
        </div>
      </div>
    </div>
  );
}

export default BookingModal;
