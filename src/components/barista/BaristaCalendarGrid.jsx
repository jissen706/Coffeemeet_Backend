import { useState, useMemo } from 'react';
import DayCell from '../DayCell';
import BaristaTimeRangePicker from './BaristaTimeRangePicker';

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];
const DAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function getMonthDays(year, month) {
  const firstDayOfWeek = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const daysInPrevMonth = new Date(year, month, 0).getDate();
  const cells = [];

  for (let i = firstDayOfWeek - 1; i >= 0; i--) {
    cells.push({ day: daysInPrevMonth - i, inMonth: false });
  }
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    cells.push({ day: d, inMonth: true, dateStr });
  }
  const remaining = 42 - cells.length;
  for (let i = 1; i <= remaining; i++) {
    cells.push({ day: i, inMonth: false });
  }
  return cells;
}

function BaristaCalendarGrid({ slots, startDate, barista, token, selectedDate, onSelectDate, onSlotCreated }) {
  const [pickerDate, setPickerDate] = useState(null);
  const initialMonth = useMemo(() => {
    if (startDate) {
      const d = new Date(startDate);
      return { year: d.getFullYear(), month: d.getMonth() };
    }
    const now = new Date();
    return { year: now.getFullYear(), month: now.getMonth() };
  }, [startDate]);

  const [currentMonth, setCurrentMonth] = useState(initialMonth);

  const slotsByDate = useMemo(() => {
    const map = {};
    for (const slot of slots) {
      const date = new Date(slot.start_time).toLocaleDateString('en-CA');
      if (!map[date]) map[date] = [];
      map[date].push(slot);
    }
    return map;
  }, [slots]);

  const { year, month } = currentMonth;
  const cells = getMonthDays(year, month);
  const today = new Date().toLocaleDateString('en-CA');

  function prevMonth() {
    setCurrentMonth(({ year, month }) =>
      month === 0 ? { year: year - 1, month: 11 } : { year, month: month - 1 }
    );
    onSelectDate(null);
  }

  function nextMonth() {
    setCurrentMonth(({ year, month }) =>
      month === 11 ? { year: year + 1, month: 0 } : { year, month: month + 1 }
    );
    onSelectDate(null);
  }

  function handlePickerConfirm(newSlots) {
    newSlots.forEach((s) => onSlotCreated(s));
    setPickerDate(null);
  }

  return (
    <>
    <div className="calendar-section">
      <div className="calendar-header">
        <div className="month-nav">
          <button className="nav-btn" onClick={prevMonth}>&#8249;</button>
          <span className="month-title">{MONTH_NAMES[month]} {year}</span>
          <button className="nav-btn" onClick={nextMonth}>&#8250;</button>
        </div>
        <div className="calendar-legend">
          <div className="legend-item">
            <span className="legend-dot" style={{ background: '#c8773a' }} />
            Your slots
          </div>
          <div className="legend-item">
            <span className="legend-dot" style={{ background: '#1a7a40' }} />
            Others open
          </div>
          <div className="legend-item">
            <span className="legend-dot" style={{ background: '#c0392b' }} />
            Fully booked
          </div>
        </div>
      </div>

      <div className="calendar-grid">
        <div className="calendar-weekdays">
          {DAY_LABELS.map((d) => (
            <div key={d} className="weekday-label">{d}</div>
          ))}
        </div>
        <div className="calendar-days">
          {cells.map((cell, i) => {
            const daySlots   = cell.dateStr ? (slotsByDate[cell.dateStr] || []) : [];
            const openCount  = daySlots.filter((s) => s.customer === null).length;
            const ownCount   = daySlots.filter((s) => s.barista.id === barista.id).length;
            return (
              <DayCell
                key={i}
                day={cell.day}
                inMonth={cell.inMonth}
                dateStr={cell.dateStr}
                openCount={openCount}
                totalCount={daySlots.length}
                isSelected={selectedDate === cell.dateStr}
                isToday={cell.dateStr === today}
                ownSlotCount={ownCount}
                onClick={cell.inMonth
                  ? () => onSelectDate(selectedDate === cell.dateStr ? null : cell.dateStr)
                  : undefined
                }
                onCreateClick={cell.inMonth
                  ? () => setPickerDate(cell.dateStr)
                  : undefined
                }
              />
            );
          })}
        </div>
      </div>

    </div>

    {pickerDate && (
      <BaristaTimeRangePicker
        date={pickerDate}
        existingSlots={slotsByDate[pickerDate] || []}
        barista={barista}
        token={token}
        onConfirm={handlePickerConfirm}
        onCancel={() => setPickerDate(null)}
      />
    )}
    </>
  );
}

export default BaristaCalendarGrid;
