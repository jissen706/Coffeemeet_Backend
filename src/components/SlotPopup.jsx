import SlotCard from './SlotCard';

function SlotPopup({ date, slots, onClose, onBook }) {
  const openCount = slots.filter((s) => s.customer === null).length;

  const formatted = new Date(date + 'T12:00:00').toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  });

  const subtext =
    slots.length === 0
      ? 'No slots scheduled'
      : `${openCount} of ${slots.length} slot${slots.length !== 1 ? 's' : ''} available`;

  return (
    <div className="slot-popup">
      <div className="popup-header">
        <div>
          <div className="popup-date-title">{formatted}</div>
          <div className="popup-date-sub">{subtext}</div>
        </div>
        <button className="popup-close-btn" onClick={onClose}>
          &#x2715; Close
        </button>
      </div>

      {slots.length === 0 ? (
        <div className="popup-empty">
          <span className="popup-empty-icon">&#9749;</span>
          No coffee chats scheduled for this day.
        </div>
      ) : (
        <div className="slot-cards-grid">
          {slots.map((slot) => (
            <SlotCard key={slot.id} slot={slot} onBook={onBook} />
          ))}
        </div>
      )}
    </div>
  );
}

export default SlotPopup;
