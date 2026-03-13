function DayCell({ day, inMonth, dateStr, openCount, totalCount, isSelected, isToday, isMyBooking, ownSlotCount = 0, onClick, onCreateClick }) {
  if (!inMonth) {
    return (
      <div className="day-cell other-month">
        <span className="day-number">{day}</span>
      </div>
    );
  }

  let badgeClass = null;
  let badgeLabel = null;
  if (totalCount > 0 && !isMyBooking) {
    badgeClass = openCount === 0 ? 'zero-slots' : 'has-slots';
    badgeLabel = openCount === 0 ? '0 open' : `${openCount} open`;
  }

  return (
    <div
      className={[
        'day-cell',
        isSelected  ? 'selected'   : '',
        isToday     ? 'today'      : '',
        isMyBooking ? 'my-booking' : '',
        onCreateClick ? 'has-create' : '',
      ].filter(Boolean).join(' ')}
      onClick={onClick}
    >
      <span className="day-number">{day}</span>

      {isMyBooking && (
        <span className="my-booking-badge">★ Your spot</span>
      )}
      {ownSlotCount > 0 && (
        <span className="slot-count-badge own-slots">{ownSlotCount} yours</span>
      )}
      {badgeLabel && (
        <span className={`slot-count-badge ${badgeClass}`}>{badgeLabel}</span>
      )}
      {onCreateClick && (
        <button
          className="barista-cell-create-btn"
          onClick={(e) => { e.stopPropagation(); onCreateClick(); }}
        >
          + Create Slots
        </button>
      )}
    </div>
  );
}

export default DayCell;
