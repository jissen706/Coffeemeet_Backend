function BaristaSlotCard({ slot, isOwn }) {
  const { barista, customer, start_time, end_time, location, meet_link } = slot;
  const isBooked = customer !== null;

  const initials = barista.name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  const fmt = (dt) =>
    new Date(dt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <div className={`slot-card${isBooked ? ' booked' : ''}${isOwn ? ' own-slot' : ''}`}>
      <div className={`slot-avatar${isOwn ? ' own-avatar' : ''}`}>{initials}</div>

      <div className="slot-info">
        <div className="slot-barista-name">
          {isOwn ? 'Your Slot' : barista.name}
          {isOwn && isBooked && (
            <span className="own-booked-tag">Booked by {customer.name}</span>
          )}
        </div>
        <div className="slot-meta">
          <div className="slot-meta-row">
            <span className="slot-meta-icon">&#8987;</span>
            <span>{fmt(start_time)} &ndash; {fmt(end_time)}</span>
          </div>
          <div className="slot-meta-row">
            <span className="slot-meta-icon">&#128205;</span>
            <span>{location}</span>
          </div>
          {meet_link && (
            <div className="slot-meta-row">
              <span className="slot-meta-icon">🎥</span>
              <a href={meet_link} target="_blank" rel="noreferrer" className="zoom-link">
                Meet Link
              </a>
            </div>
          )}
        </div>
      </div>

      <div className={`slot-status-badge ${isBooked ? 'booked' : isOwn ? 'own-open' : 'open'}`}>
        {isBooked ? 'Booked' : 'Open'}
      </div>
    </div>
  );
}

export default BaristaSlotCard;
