import { useState, useEffect, useMemo } from 'react';
import { createSlot } from '../../api';

const START_HOUR    = 7;   // 7 AM
const END_HOUR      = 21;  // 9 PM
const BLOCK_MIN     = 15;  // minutes per grid row
const TOTAL_BLOCKS  = ((END_HOUR - START_HOUR) * 60) / BLOCK_MIN; // 56
const BLOCK_H       = 18;  // px per row

const DURATION_OPTIONS = [15, 20, 25, 30, 45, 60, 90];

function blockToMins(i)    { return START_HOUR * 60 + i * BLOCK_MIN; }
function minsToISO(m, d)   {
  const h = Math.floor(m / 60), min = m % 60;
  return `${d}T${String(h).padStart(2,'0')}:${String(min).padStart(2,'0')}:00`;
}
function minsFmt(m) {
  const h = Math.floor(m / 60), min = m % 60;
  const ampm = h >= 12 ? 'PM' : 'AM';
  const h12  = h > 12 ? h - 12 : h === 0 ? 12 : h;
  return `${h12}:${String(min).padStart(2,'0')} ${ampm}`;
}
function slotToBlockRange(slot) {
  const s   = new Date(slot.start_time);
  const e   = new Date(slot.end_time);
  const sM  = s.getHours() * 60 + s.getMinutes();
  const eM  = e.getHours() * 60 + e.getMinutes();
  return {
    start: (sM - START_HOUR * 60) / BLOCK_MIN,
    end:   (eM - START_HOUR * 60) / BLOCK_MIN,
  };
}

export default function BaristaTimeRangePicker({ date, existingSlots, barista, token, onConfirm, onCancel }) {
  const [dragStart,   setDragStart]   = useState(null);
  const [dragCurrent, setDragCurrent] = useState(null);
  const [isDragging,  setIsDragging]  = useState(false);
  const [duration,    setDuration]    = useState(20);
  const [location,    setLocation]    = useState('');
  const [zoomLink,    setZoomLink]    = useState('');
  const [locErr,      setLocErr]      = useState('');
  const [submitting,  setSubmitting]  = useState(false);

  const selStart = dragStart !== null && dragCurrent !== null ? Math.min(dragStart, dragCurrent) : null;
  const selEnd   = dragStart !== null && dragCurrent !== null ? Math.max(dragStart, dragCurrent) : null;

  const selectedMins = selStart !== null ? (selEnd - selStart + 1) * BLOCK_MIN : 0;
  const slotCount    = Math.floor(selectedMins / duration);
  const remainder    = selStart !== null ? selectedMins % duration : 0;

  const previewSlots = useMemo(() => {
    if (selStart === null || slotCount === 0) return [];
    const base = blockToMins(selStart);
    return Array.from({ length: slotCount }, (_, i) => ({
      startMins: base + i * duration,
      endMins:   base + (i + 1) * duration,
    }));
  }, [selStart, selEnd, duration]); // eslint-disable-line react-hooks/exhaustive-deps

  // End drag on mouse up anywhere
  useEffect(() => {
    const up = () => setIsDragging(false);
    document.addEventListener('mouseup', up);
    return () => document.removeEventListener('mouseup', up);
  }, []);

  // Escape to close
  useEffect(() => {
    const key = (e) => { if (e.key === 'Escape') onCancel(); };
    document.addEventListener('keydown', key);
    return () => document.removeEventListener('keydown', key);
  }, [onCancel]);

  async function handleConfirm() {
    if (!location.trim()) { setLocErr('Location is required'); return; }
    if (selStart === null || slotCount === 0) return;

    setSubmitting(true);
    const results = [];
    for (const { startMins, endMins } of previewSlots) {
      const slotData = {
        barista_id: barista.id,
        start_time: minsToISO(startMins, date),
        end_time:   minsToISO(endMins,   date),
        location:   location.trim(),
        meet_link:  zoomLink.trim() || null,
      };
      const created = await createSlot(barista.cafe_id, slotData, token);
      results.push(created);
    }
    setSubmitting(false);
    onConfirm(results);
  }

  const formatted = new Date(date + 'T12:00:00').toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric',
  });

  const existingRanges = existingSlots.map(slotToBlockRange);

  return (
    <div className="tpicker-backdrop" onClick={onCancel}>
      <div className="tpicker-modal" onClick={(e) => e.stopPropagation()}>

        {/* Header */}
        <div className="tpicker-header">
          <div>
            <div className="tpicker-title">Create Slots</div>
            <div className="tpicker-sub">{formatted}</div>
          </div>
          <button className="time-picker-close" onClick={onCancel}>✕</button>
        </div>

        <div className="tpicker-body">

          {/* ── Left: draggable time grid ── */}
          <div className="tpicker-grid-col">
            <div className="tpicker-grid-hint">Click and drag to select a time range</div>
            <div className="tpicker-grid-scroll">
              <div
                className="tpicker-grid"
                style={{ height: TOTAL_BLOCKS * BLOCK_H }}
                onMouseLeave={() => {/* allow drag to continue outside */}}
              >
                {/* Existing slots (decorative, pointer-events: none) */}
                {existingRanges.map(({ start, end }, i) => {
                  if (end <= 0 || start >= TOTAL_BLOCKS) return null;
                  const cStart = Math.max(0, start);
                  const cEnd   = Math.min(TOTAL_BLOCKS, end);
                  return (
                    <div
                      key={i}
                      className="tpicker-existing"
                      style={{ top: cStart * BLOCK_H, height: (cEnd - cStart) * BLOCK_H }}
                    />
                  );
                })}

                {/* Drag selection highlight */}
                {selStart !== null && (
                  <div
                    className="tpicker-selection"
                    style={{
                      top:    selStart * BLOCK_H,
                      height: (selEnd - selStart + 1) * BLOCK_H,
                    }}
                  >
                    {(selEnd - selStart + 1) >= 2 && (
                      <div className="tpicker-sel-label">
                        <span className="tpicker-sel-time">
                          {minsFmt(blockToMins(selStart))} – {minsFmt(blockToMins(selEnd + 1))}
                        </span>
                        {slotCount > 0 && (
                          <span className="tpicker-sel-count">{slotCount} × {duration} min</span>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Grid rows (interactive) */}
                {Array.from({ length: TOTAL_BLOCKS }, (_, i) => {
                  const isHour = i % 4 === 0;
                  const isHalf = i % 2 === 0 && !isHour;
                  return (
                    <div
                      key={i}
                      className={['tpicker-row', isHour ? 'is-hour' : isHalf ? 'is-half' : ''].filter(Boolean).join(' ')}
                      style={{ height: BLOCK_H }}
                      onMouseDown={(e) => {
                        e.preventDefault();
                        setDragStart(i);
                        setDragCurrent(i);
                        setIsDragging(true);
                      }}
                      onMouseEnter={() => { if (isDragging) setDragCurrent(i); }}
                    >
                      {isHour && (
                        <span className="tpicker-row-label">{minsFmt(blockToMins(i))}</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* ── Right: controls + preview ── */}
          <div className="tpicker-controls-col">

            {/* Preview panel */}
            {selStart === null ? (
              <div className="tpicker-empty">
                <div className="tpicker-empty-arrow">←</div>
                <div>Drag on the time grid to select an availability window</div>
              </div>
            ) : slotCount === 0 ? (
              <div className="tpicker-empty tpicker-empty-warn">
                Selected range ({selectedMins} min) is shorter than one slot ({duration} min). Drag further or reduce duration.
              </div>
            ) : (
              <div className="tpicker-preview">
                <div className="tpicker-preview-headline">
                  {slotCount} slot{slotCount !== 1 ? 's' : ''} &times; {duration} min
                </div>
                <div className="tpicker-preview-range">
                  {minsFmt(blockToMins(selStart))} – {minsFmt(blockToMins(selEnd + 1))}
                </div>
                <div className="tpicker-preview-list">
                  {previewSlots.map(({ startMins, endMins }, i) => (
                    <div key={i} className="tpicker-preview-row">
                      <span className="tpicker-preview-dot" />
                      {minsFmt(startMins)} – {minsFmt(endMins)}
                    </div>
                  ))}
                </div>
                {remainder > 0 && (
                  <div className="tpicker-preview-rem">+{remainder} min gap at end (not enough for another slot)</div>
                )}
              </div>
            )}

            {/* Form fields */}
            <div className="tpicker-fields">
              <div className="form-field">
                <label className="form-label">Slot Duration</label>
                <select
                  className="form-input"
                  value={duration}
                  onChange={(e) => setDuration(Number(e.target.value))}
                >
                  {DURATION_OPTIONS.map((d) => (
                    <option key={d} value={d}>{d} min</option>
                  ))}
                </select>
              </div>

              <div className="form-field">
                <label className="form-label">Location</label>
                <input
                  className={`form-input${locErr ? ' form-input-error' : ''}`}
                  type="text"
                  placeholder="e.g. Table 3, Corner Booth"
                  value={location}
                  onChange={(e) => { setLocation(e.target.value); setLocErr(''); }}
                />
                {locErr && <span className="form-error">{locErr}</span>}
              </div>

              <div className="form-field">
                <label className="form-label">
                  Zoom Link <span className="form-label-optional">(optional)</span>
                </label>
                <input
                  className="form-input"
                  type="url"
                  placeholder="https://zoom.us/j/..."
                  value={zoomLink}
                  onChange={(e) => setZoomLink(e.target.value)}
                />
              </div>
            </div>

            <button
              className="tpicker-confirm-btn"
              onClick={handleConfirm}
              disabled={submitting || selStart === null || slotCount === 0}
            >
              {submitting
                ? 'Creating…'
                : slotCount > 0
                  ? `Create ${slotCount} Slot${slotCount !== 1 ? 's' : ''}`
                  : 'Select a time range first'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
