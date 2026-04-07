import { useState, useMemo } from 'react';
import BaristaTimeRangePicker from './BaristaTimeRangePicker';
import { deleteSlot } from '../../api';

const HOUR_START=8,HOUR_END=22,HOURS=14,HOUR_H=80,PX_MIN=HOUR_H/60;
const COLORS=['#8b4513','#1a7a40','#2980b9','#7b4f9e','#c8773a','#c0392b','#2c7873'];
const colorOf=(id)=>COLORS[id%COLORS.length];
const fmtTime=(dt)=>new Date(dt).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
const topOf=(s)=>{const d=new Date(s.start_time);return(d.getHours()*60+d.getMinutes()-HOUR_START*60)*PX_MIN;};
const heightOf=(s)=>Math.max(24,(new Date(s.end_time)-new Date(s.start_time))/60000*PX_MIN);

function layoutSlots(slots){
  const sorted=[...slots].sort((a,b)=>new Date(a.start_time)-new Date(b.start_time));
  const colEnds=[],rows=[];
  for(const slot of sorted){const s=new Date(slot.start_time),e=new Date(slot.end_time);let c=colEnds.findIndex(end=>s>=end);if(c<0)c=colEnds.length;colEnds[c]=e;rows.push({slot,col:c});}
  const n=colEnds.length||1;
  return rows.map(({slot,col})=>({slot,col,n}));
}

export default function BaristaDayTimeline({ date, slots, barista, token, onClose, onSlotCreated, onSlotDeleted }) {
  const [showPicker, setShowPicker]     = useState(false);
  const [detailSlot, setDetailSlot]     = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const formatted = new Date(date+'T12:00:00').toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'});
  const ownSlots  = slots.filter(s=>s.barista.id===barista.id);
  const openCount = slots.filter(s=>s.customer===null).length;
  const laid      = useMemo(()=>layoutSlots(slots),[slots]);

  function handlePickerConfirm(newSlots){ newSlots.forEach(s=>onSlotCreated(s)); setShowPicker(false); }

  async function handleDeleteConfirm() {
    // Optimistic update
    onSlotDeleted(deleteTarget.id);
    if (detailSlot?.id === deleteTarget.id) setDetailSlot(null);
    setDeleteTarget(null);
    try { await deleteSlot(deleteTarget.id, token); } catch { /* already removed from UI */ }
  }

  return (
    <>
      <aside className="day-timeline-panel">
        <div className="tl-header">
          <div>
            <div className="tl-date">{formatted}</div>
            <div className="tl-sub">{ownSlots.length} yours · {openCount} open total</div>
          </div>
          <div style={{display:'flex',gap:6,alignItems:'center'}}>
            <button className="tl-create-btn" onClick={()=>setShowPicker(true)}>+ Create</button>
            <button className="tl-close" onClick={onClose}>✕</button>
          </div>
        </div>

        {/* Slot detail card */}
        {detailSlot&&(
          <div className="tl-detail-card">
            <div className="tl-detail-row"><span className="tl-detail-label">Barista</span><span className="tl-detail-val">{detailSlot.barista.name}</span></div>
            <div className="tl-detail-row"><span className="tl-detail-label">Time</span><span className="tl-detail-val">{fmtTime(detailSlot.start_time)} – {fmtTime(detailSlot.end_time)}</span></div>
            <div className="tl-detail-row"><span className="tl-detail-label">Location</span><span className="tl-detail-val">{detailSlot.location||'—'}</span></div>
            <div className="tl-detail-row"><span className="tl-detail-label">Status</span><span className="tl-detail-val">{detailSlot.customer?`Booked — ${detailSlot.customer.name}`:'Open'}</span></div>
            <button className="tl-detail-dismiss" onClick={()=>setDetailSlot(null)}>✕ Dismiss</button>
          </div>
        )}

        <div className="tl-scroll">
          <div className="tl-body" style={{height:HOURS*HOUR_H}}>
            {Array.from({length:HOURS+1},(_,i)=>{const h=HOUR_START+i;const label=h>12?`${h-12} PM`:h===12?'12 PM':`${h} AM`;return<div key={i} className="tl-hour" style={{top:i*HOUR_H}}><span className="tl-hour-label">{label}</span><span className="tl-hour-line"/></div>;})}
            {Array.from({length:HOURS},(_,i)=><div key={`h${i}`} className="tl-half" style={{top:(i+0.5)*HOUR_H}}/>)}
            <div className="tl-slots">
              {laid.map(({slot,col,n})=>{
                const isOwn=slot.barista.id===barista.id;
                const isOpen=slot.customer===null;
                const color=isOwn?'#c8773a':colorOf(slot.barista.id);
                const h=heightOf(slot);
                return(
                  <div key={slot.id}
                    className={`tl-slot${isOpen?' tl-open':' tl-booked'}${isOwn?' tl-own':''}`}
                    style={{
                      top:topOf(slot),height:h,
                      left:`${(col/n)*100}%`,width:`calc(${(1/n)*100}% - 4px)`,
                      background:isOwn?(isOpen?'rgba(200,119,58,0.22)':'rgba(200,119,58,0.12)'):(isOpen?color:`${color}99`),
                      color:isOwn?'#6b3410':'#fff',
                      borderLeftColor:color,
                      cursor:'pointer',
                    }}
                    onClick={()=>setDetailSlot(slot)}
                  >
                    <div className="tl-slot-name">{isOwn?'You':slot.barista.name.split(' ')[0]}</div>
                    {h>=38&&<div className="tl-slot-time">{fmtTime(slot.start_time)}–{fmtTime(slot.end_time)}</div>}
                    {isOwn&&(
                      <button
                        className="tl-slot-delete-btn"
                        title="Delete slot"
                        onClick={(e)=>{e.stopPropagation();setDeleteTarget(slot);}}
                      >✕</button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </aside>

      {/* Delete confirmation */}
      {deleteTarget&&(
        <div className="tl-confirm-backdrop">
          <div className="tl-confirm-popup">
            <div className="tl-confirm-title">Delete this slot?</div>
            <div className="tl-confirm-sub">
              {fmtTime(deleteTarget.start_time)}–{fmtTime(deleteTarget.end_time)}
              {deleteTarget.customer&&<span className="tl-confirm-warn"> · Has a booking!</span>}
            </div>
            <div className="tl-confirm-actions">
              <button className="tl-confirm-cancel" onClick={()=>setDeleteTarget(null)}>Cancel</button>
              <button className="tl-confirm-ok tl-confirm-delete" onClick={handleDeleteConfirm}>Delete</button>
            </div>
          </div>
        </div>
      )}

      {showPicker&&(
        <BaristaTimeRangePicker date={date} existingSlots={slots} barista={barista} token={token} onConfirm={handlePickerConfirm} onCancel={()=>setShowPicker(false)}/>
      )}
    </>
  );
}
