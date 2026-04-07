import { useState } from 'react';
import { updateCafe } from '../../api';

export default function OwnerSettings({ cafe, token, onClose, onCafeUpdated }) {
  const [cafeName,  setCafeName]  = useState(cafe.name);
  const [startDate, setStartDate] = useState(cafe.start_date);
  const [endDate,   setEndDate]   = useState(cafe.end_date);
  const [oneSlot,   setOneSlot]   = useState(cafe.one_slot);
  const [saving,    setSaving]    = useState(false);
  const [saveMsg,   setSaveMsg]   = useState('');

  async function handleSave(e) {
    e.preventDefault();
    setSaving(true);
    setSaveMsg('');
    try {
      const updated = await updateCafe(cafe.id, {
        name: cafeName, start_date: startDate, end_date: endDate, one_slot: oneSlot,
      }, token);
      onCafeUpdated(updated);
      setSaveMsg('Saved!');
      setTimeout(() => setSaveMsg(''), 2500);
    } catch {
      setSaveMsg('Failed to save');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="owner-settings-backdrop" onClick={onClose}>
      <div className="owner-settings-panel" onClick={e => e.stopPropagation()}>
        <div className="owner-settings-header">
          <div className="owner-settings-title">⚙ Cafe Settings</div>
          <button className="owner-settings-close" onClick={onClose}>✕</button>
        </div>

        <div className="owner-settings-body">
          <form onSubmit={handleSave}>
            <div className="form-field">
              <label className="form-label">Cafe Name</label>
              <input
                className="form-input"
                value={cafeName}
                onChange={e => setCafeName(e.target.value)}
              />
            </div>
            <div className="owner-form-row">
              <div className="form-field">
                <label className="form-label">Start Date</label>
                <input className="form-input" type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
              </div>
              <div className="form-field">
                <label className="form-label">End Date</label>
                <input className="form-input" type="date" value={endDate} onChange={e => setEndDate(e.target.value)} />
              </div>
            </div>
            <label className="owner-toggle-label">
              <input
                type="checkbox"
                checked={oneSlot}
                onChange={e => setOneSlot(e.target.checked)}
              />
              One slot per customer
            </label>
            <div className="owner-settings-save-row">
              <button type="submit" className="owner-modal-submit" disabled={saving}>
                {saving ? 'Saving…' : 'Save Changes'}
              </button>
              {saveMsg && (
                <span className={`owner-save-msg${saveMsg === 'Saved!' ? ' ok' : ' err'}`}>
                  {saveMsg}
                </span>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
