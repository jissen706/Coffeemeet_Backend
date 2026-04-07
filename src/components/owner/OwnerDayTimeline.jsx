import { useState, useMemo } from 'react';
import { ownerDeleteSlot, ownerUnbookSlot } from '../../api';

const HOUR_START = 8, HOURS = 14, HOUR_H = 80, PX_MIN = HOUR_H / 60;
const COLORS = ['#8b4513','#1a7a40','#2980b9','#7b4f9e','#c8773a','#c0392b','#2c7873'];
const colorOf  = (id) => COLORS[id % COLORS.length];
const fmtTime  = (dt) => new Date(dt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
const topOf    = (s)  => { const d = new Date(s.start_time); return (d.getHours()*60+d.getMinutes()-HOUR_START*60)*PX_MIN; };
const heightOf = (s)  => Math.max(24, (new Date(s.end_time)-new Date(s.start_time))/60000*PX_MIN);

function layoutSlots(slots) {
  const sorted = [...slots].sort((a,b) => new Date(a.start_time)-new Date(b.start_time));
  const colEnds = [], rows = [];
  for (const slot of sorted) {
    const s = new Date(slot.start_time), e = new Date(slot.end_time);
    let c = colEnds.findIndex(end => s >= end);
    if (c < 0) c = colEnds.length;
    colEnds[c] = e; rows.push({ slot, col: c });
  }
  const n = colEnds.length || 1;
  return rows.map(({ slot, col }) => ({ slot, col, n }));
}

export default function OwnerDayTimeline({ date, slots, token, onClose, onSlotDeleted, onSlotUnbooked }) {
  const [detailSlot, setDetailSlot] = useState(null);
  const [confirm, setConfirm] = useState(null); // { type: 'delete'|'unbook', slot }
  const [processing, setProcessing] = useState(false);

  const formatted = new Date(date+'T12:00:00').toLocaleDateString('en-US', { weekday:'long', month:'long', day:'numeric' });
  const openCount  = slots.filter(s => s.customer === null).length;
  const laid       = useMemo(() => layoutSlots(slots), [slots]);

  async function handleConfirm() {
    const slotId = confirm.slot.id;
    const type = confirm.type;

    // Optimistic update — remove from UI immediately
    if (type === 'delete') {
      onSlotDeleted(slotId);
      if (detailSlot?.id === slotId) setDetailSlot(null);
    } else {
      onSlotUnbooked(slotId);
      if (detailSlot?.id === slotId) {
        setDetailSlot(prev => ({ ...prev, customer: null }));
      }
    }
    setConfirm(null);

    // API call in background
    try {
      if (type === 'delete') {
        await ownerDeleteSlot(slotId, token);
      } else {
        await ownerUnbookSlot(slotId, token);
      }
    } catch { /* UI already updated; backend may be out of sync */ }
  }

  return (
    <>
      <aside className="day-timeline-panel">
        <div className="tl-header">
          <div>
            <div className="tl-date">{formatted}</div>
            <div className="tl-sub">
              {slots.length === 0 ? 'No slots' : `${openCount} of ${slots.length} open`}
            </div>
          </div>
          <button className="tl-close" onClick={onClose}>✕</button>
        </div>

        {detailSlot && (
          <div className="tl-detail-card">
            <div className="tl-detail-row">
              <span className="tl-detail-label">Barista</span>
              <span className="tl-detail-val">{detailSlot.barista.name}</span>
            </div>
            <div className="tl-detail-row">
              <span className="tl-detail-label">Time</span>
              <span className="tl-detail-val">{fmtTime(detailSlot.start_time)} – {fmtTime(detailSlot.end_time)}</span>
            </div>
            <div className="tl-detail-row">
              <span className="tl-detail-label">Location</span>
              <span className="tl-detail-val">{detailSlot.location || '—'}</span>
            </div>
            <div className="tl-detail-row">
              <span className="tl-detail-label">Customer</span>
              <span className="tl-detail-val">{detailSlot.customer ? detailSlot.customer.name : <em>Open</em>}</span>
            </div>
            <div className="tl-detail-owner-actions">
              {detailSlot.customer && (
                <button
                  className="tl-detail-action-btn unbook"
                  onClick={() => setConfirm({ type: 'unbook', slot: detailSlot })}
                >Unbook</button>
              )}
              <button
                className="tl-detail-action-btn delete"
                onClick={() => setConfirm({ type: 'delete', slot: detailSlot })}
              >Delete Slot</button>
            </div>
            <button className="tl-detail-dismiss" onClick={() => setDetailSlot(null)}>✕ Dismiss</button>
          </div>
        )}

        {slots.length === 0 ? (
          <div className="tl-empty">No slots scheduled for this day.</div>
        ) : (
          <div className="tl-scroll">
            <div className="tl-body" style={{ height: HOURS * HOUR_H }}>
              {Array.from({ length: HOURS+1 }, (_, i) => {
                const h = HOUR_START + i;
                const label = h > 12 ? `${h-12} PM` : h === 12 ? '12 PM' : `${h} AM`;
                return (
                  <div key={i} className="tl-hour" style={{ top: i*HOUR_H }}>
                    <span className="tl-hour-label">{label}</span>
                    <span className="tl-hour-line" />
                  </div>
                );
              })}
              {Array.from({ length: HOURS }, (_, i) => (
                <div key={`h${i}`} className="tl-half" style={{ top: (i+0.5)*HOUR_H }} />
              ))}
              <div className="tl-slots">
                {laid.map(({ slot, col, n }) => {
                  const isOpen = slot.customer === null;
                  const color  = colorOf(slot.barista.id);
                  const h      = heightOf(slot);
                  return (
                    <div
                      key={slot.id}
                      className={`tl-slot${isOpen ? ' tl-open' : ' tl-booked'}`}
                      style={{
                        top: topOf(slot), height: h,
                        left: `${(col/n)*100}%`, width: `calc(${(1/n)*100}% - 4px)`,
                        background: isOpen ? color : `${color}88`,
                        borderLeftColor: color,
                        color: '#fff',
                        cursor: 'pointer',
                      }}
                      onClick={() => setDetailSlot(slot)}
                    >
                      <div className="tl-slot-text">
                        <div className="tl-slot-name">{slot.barista.name.split(' ')[0]}</div>
                        {!isOpen && (
                          <div className="tl-slot-name" style={{ fontSize: '0.62rem', opacity: 0.85 }}>
                            {slot.customer.name.split(' ')[0]}
                          </div>
                        )}
                        {h >= 38 && (
                          <div className="tl-slot-time" style={{ color: 'rgba(255,255,255,0.8)' }}>
                            {fmtTime(slot.start_time)}–{fmtTime(slot.end_time)}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </aside>

      {confirm && (
        <div className="tl-confirm-backdrop">
          <div className="tl-confirm-popup">
            <div className="tl-confirm-title">
              {confirm.type === 'delete' ? 'Delete this slot?' : 'Cancel this booking?'}
            </div>
            <div className="tl-confirm-sub">
              {fmtTime(confirm.slot.start_time)}–{fmtTime(confirm.slot.end_time)} · {confirm.slot.barista.name.split(' ')[0]}
              {confirm.type === 'unbook' && confirm.slot.customer && ` · ${confirm.slot.customer.name}`}
            </div>
            <div className="tl-confirm-actions">
              <button className="tl-confirm-cancel" onClick={() => setConfirm(null)} disabled={processing}>
                Keep it
              </button>
              <button className="tl-confirm-ok tl-confirm-delete" onClick={handleConfirm} disabled={processing}>
                {processing ? 'Working…' : confirm.type === 'delete' ? 'Delete' : 'Cancel Booking'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
