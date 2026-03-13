import { useState } from 'react';
import BaristaSlotCard from './BaristaSlotCard';
import BaristaTimeRangePicker from './BaristaTimeRangePicker';

function BaristaSlotPopup({ date, slots, barista, onClose, onSlotCreated }) {
  const [showPicker, setShowPicker] = useState(false);

  const ownSlots   = slots.filter((s) => s.barista.id === barista.id);
  const otherSlots = slots.filter((s) => s.barista.id !== barista.id);
  const totalOpen  = slots.filter((s) => s.customer === null).length;

  const formatted = new Date(date + 'T12:00:00').toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric',
  });

  function handlePickerConfirm(newSlots) {
    newSlots.forEach((s) => onSlotCreated(s));
    setShowPicker(false);
  }

  return (
    <>
      <div className="slot-popup">
        <div className="popup-header">
          <div>
            <div className="popup-date-title">{formatted}</div>
            <div className="popup-date-sub">
              {ownSlots.length} your slot{ownSlots.length !== 1 ? 's' : ''} &middot; {totalOpen} open total
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <button className="barista-create-day-btn" onClick={() => setShowPicker(true)}>
              + Create Slots
            </button>
            <button className="popup-close-btn" onClick={onClose}>&#x2715; Close</button>
          </div>
        </div>

        {slots.length === 0 ? (
          <div className="popup-empty">
            <span className="popup-empty-icon">&#9749;</span>
            No slots yet — click Create Slots to add some.
          </div>
        ) : (
          <div className="slot-cards-grid">
            {ownSlots.map((s) => <BaristaSlotCard key={s.id} slot={s} isOwn />)}
            {otherSlots.map((s) => <BaristaSlotCard key={s.id} slot={s} isOwn={false} />)}
          </div>
        )}
      </div>

      {showPicker && (
        <BaristaTimeRangePicker
          date={date}
          existingSlots={slots}
          barista={barista}
          onConfirm={handlePickerConfirm}
          onCancel={() => setShowPicker(false)}
        />
      )}
    </>
  );
}

export default BaristaSlotPopup;
