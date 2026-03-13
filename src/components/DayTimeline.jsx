import { useState, useMemo } from 'react';

const HOUR_START = 8, HOUR_END = 22, HOURS = 14, HOUR_H = 80, PX_MIN = HOUR_H / 60;
const COLORS = ['#8b4513','#1a7a40','#2980b9','#7b4f9e','#c8773a','#c0392b','#2c7873'];
const colorOf  = (id) => COLORS[id % COLORS.length];
const fmtTime  = (dt) => new Date(dt).toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' });
const topOf    = (s)  => { const d=new Date(s.start_time); return (d.getHours()*60+d.getMinutes()-HOUR_START*60)*PX_MIN; };
const heightOf = (s)  => Math.max(24,(new Date(s.end_time)-new Date(s.start_time))/60000*PX_MIN);

const MY_SLOT_COLOR = '#d4a017';
const MY_SLOT_BORDER = '#b8860b';

function layoutSlots(slots) {
  const sorted = [...slots].sort((a,b)=>new Date(a.start_time)-new Date(b.start_time));
  const colEnds=[], rows=[];
  for (const slot of sorted) {
    const s=new Date(slot.start_time), e=new Date(slot.end_time);
    let c=colEnds.findIndex(end=>s>=end); if(c<0) c=colEnds.length;
    colEnds[c]=e; rows.push({slot,col:c});
  }
  const n=colEnds.length||1;
  return rows.map(({slot,col})=>({slot,col,n}));
}

export default function DayTimeline({ date, slots, onClose, onBook, myBookedSlotId, onCancelBooking }) {
  const [cancelTarget, setCancelTarget] = useState(null);
  const [alreadyBookedMsg, setAlreadyBookedMsg] = useState(false);

  const formatted = new Date(date+'T12:00:00').toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'});
  const openCount = slots.filter(s=>s.customer===null).length;
  const laid = useMemo(()=>layoutSlots(slots),[slots]);

  function handleSlotClick(slot) {
    if (slot.customer !== null) return; // booked by someone else, not clickable
    if (myBookedSlotId) {
      // already has a booking — flash message instead of opening flow
      setAlreadyBookedMsg(true);
      setTimeout(() => setAlreadyBookedMsg(false), 2500);
      return;
    }
    onBook(slot);
  }

  async function handleCancelConfirm() {
    await onCancelBooking(cancelTarget.id);
    setCancelTarget(null);
  }

  return (
    <>
      <aside className="day-timeline-panel">
        <div className="tl-header">
          <div>
            <div className="tl-date">{formatted}</div>
            <div className="tl-sub">{slots.length===0?'No slots':`${openCount} of ${slots.length} open`}</div>
          </div>
          <button className="tl-close" onClick={onClose}>✕</button>
        </div>

        {alreadyBookedMsg && (
          <div className="tl-already-booked-msg">
            You already have a booking — cancel it first to book another slot.
          </div>
        )}

        {slots.length===0 ? (
          <div className="tl-empty">No slots scheduled for this day.</div>
        ) : (
          <div className="tl-scroll">
            <div className="tl-body" style={{height:HOURS*HOUR_H}}>
              {Array.from({length:HOURS+1},(_,i)=>{
                const h=HOUR_START+i;
                const label=h>12?`${h-12} PM`:h===12?'12 PM':`${h} AM`;
                return <div key={i} className="tl-hour" style={{top:i*HOUR_H}}><span className="tl-hour-label">{label}</span><span className="tl-hour-line"/></div>;
              })}
              {Array.from({length:HOURS},(_,i)=>(
                <div key={`h${i}`} className="tl-half" style={{top:(i+0.5)*HOUR_H}}/>
              ))}
              <div className="tl-slots">
                {laid.map(({slot,col,n})=>{
                  const isOpen = slot.customer === null;
                  const isMySlot = slot.id === myBookedSlotId;
                  const color = colorOf(slot.barista.id);
                  const h = heightOf(slot);

                  let bg, borderColor, textColor, cursor, opacity;
                  if (isMySlot) {
                    bg = MY_SLOT_COLOR;
                    borderColor = MY_SLOT_BORDER;
                    textColor = '#fff';
                    cursor = 'default';
                    opacity = 1;
                  } else if (isOpen) {
                    bg = myBookedSlotId ? `${color}88` : color;
                    borderColor = color;
                    textColor = '#fff';
                    cursor = myBookedSlotId ? 'not-allowed' : 'pointer';
                    opacity = 1;
                  } else {
                    bg = '#e8e8e8';
                    borderColor = '#bbb';
                    textColor = '#888';
                    cursor = 'default';
                    opacity = 0.6;
                  }

                  return (
                    <div key={slot.id}
                      className={`tl-slot${isOpen?' tl-open':' tl-booked'}${isMySlot?' tl-my-slot':''}`}
                      style={{
                        top: topOf(slot), height: h,
                        left: `${(col/n)*100}%`, width: `calc(${(1/n)*100}% - 4px)`,
                        background: bg,
                        borderLeftColor: borderColor,
                        color: textColor,
                        cursor,
                        opacity,
                      }}
                      onClick={() => isMySlot ? null : handleSlotClick(slot)}
                    >
                      <div className="tl-slot-text">
                        <div className="tl-slot-name">
                          {isMySlot ? '★ You' : isOpen ? slot.barista.name.split(' ')[0] : 'Booked'}
                        </div>
                        {h>=38&&(
                          <div className="tl-slot-time" style={{color: isOpen||isMySlot ? 'rgba(255,255,255,0.85)' : '#aaa'}}>
                            {fmtTime(slot.start_time)}–{fmtTime(slot.end_time)}
                          </div>
                        )}
                      </div>
                      {isMySlot && (
                        <button
                          className="tl-slot-cancel-btn"
                          onClick={(e) => { e.stopPropagation(); setCancelTarget(slot); }}
                        >✕ Cancel</button>
                      )}
                      {isOpen && !myBookedSlotId && (
                        <button
                          className="tl-slot-book-btn"
                          onClick={(e) => { e.stopPropagation(); onBook(slot); }}
                        >Book</button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </aside>

      {/* Cancel confirmation */}
      {cancelTarget && (
        <div className="tl-confirm-backdrop">
          <div className="tl-confirm-popup">
            <div className="tl-confirm-title">Cancel your booking?</div>
            <div className="tl-confirm-sub">
              {fmtTime(cancelTarget.start_time)}–{fmtTime(cancelTarget.end_time)} with {cancelTarget.barista.name.split(' ')[0]}
            </div>
            <div className="tl-confirm-actions">
              <button className="tl-confirm-cancel" onClick={() => setCancelTarget(null)}>Keep it</button>
              <button className="tl-confirm-ok tl-confirm-delete" onClick={handleCancelConfirm}>Cancel booking</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
