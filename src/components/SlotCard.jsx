function SlotCard({ slot, onBook }) {
  const { barista, customer, start_time, end_time, location } = slot;
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
    <div className={`slot-card${isBooked ? ' booked' : ''}`}>
      <div className="slot-avatar">{initials}</div>
      <div className="slot-info">
        <div className="slot-barista-name">{barista.name}</div>
        <div className="slot-meta">
          <div className="slot-meta-row">
            <span className="slot-meta-icon">&#8987;</span>
            <span>{fmt(start_time)} &ndash; {fmt(end_time)}</span>
          </div>
          <div className="slot-meta-row">
            <span className="slot-meta-icon">&#128205;</span>
            <span>{location}</span>
          </div>
        </div>
      </div>

      {isBooked ? (
        <div className="slot-status-badge booked">Booked</div>
      ) : (
        <button className="slot-book-btn" onClick={() => onBook(slot)}>
          Book
        </button>
      )}
    </div>
  );
}

export default SlotCard;
