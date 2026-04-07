import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getOwnerCafes, createCafeApi } from '../../api';
import ShareLinksPopup from '../../components/owner/ShareLinksPopup';

function fmtDate(d) {
  return new Date(d + 'T12:00:00').toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  });
}

export default function OwnerDashboard({ token, owner, onLogout }) {
  const navigate = useNavigate();
  const [cafes, setCafes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: '', start_date: '', end_date: '', one_slot: true });
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');
  const [shareLinks, setShareLinks] = useState(null);

  useEffect(() => {
    getOwnerCafes(owner.owner_id, token)
      .then(setCafes)
      .catch(() => setCafes([]))
      .finally(() => setLoading(false));
  }, []);

  async function handleCreateCafe(e) {
    e.preventDefault();
    if (!form.name.trim() || !form.start_date || !form.end_date) {
      setCreateError('All fields are required');
      return;
    }
    setCreating(true);
    setCreateError('');
    try {
      const cafe = await createCafeApi(
        { name: form.name, start_date: form.start_date, end_date: form.end_date, one_slot: form.one_slot },
        token
      );
      setCafes(prev => [...prev, cafe]);
      setShowCreate(false);
      setForm({ name: '', start_date: '', end_date: '', one_slot: true });
      setShareLinks(cafe);
    } catch (err) {
      setCreateError(err.message);
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="owner-dashboard">
      <div className="owner-dash-header">
        <div className="owner-dash-left">
          <span className="owner-dash-icon">☕</span>
          <div>
            <div className="owner-dash-welcome">Welcome back, {owner.name.split(' ')[0]}!</div>
            <div className="owner-dash-sub">CoffeeMeet Owner Portal</div>
          </div>
        </div>
        <div className="owner-dash-actions">
          <button className="owner-create-btn" onClick={() => setShowCreate(true)}>+ Create Cafe</button>
          <button className="owner-logout-btn" onClick={onLogout}>Log Out</button>
        </div>
      </div>

      <div className="owner-dash-body">
        <div className="owner-section-title">Your Cafes</div>
        {loading ? (
          <div className="owner-loading">Loading cafes…</div>
        ) : cafes.length === 0 ? (
          <div className="owner-empty-state">
            <div className="owner-empty-icon">☕</div>
            <div className="owner-empty-title">No cafes yet</div>
            <div className="owner-empty-sub">Create your first cafe to get started.</div>
            <button className="owner-create-btn" onClick={() => setShowCreate(true)}>+ Create Cafe</button>
          </div>
        ) : (
          <div className="owner-cafe-grid">
            {cafes.map(cafe => (
              <div key={cafe.id} className="owner-cafe-card" onClick={() => navigate(`/owner/cafe/${cafe.id}`)}>
                <div className="owner-cafe-card-name">{cafe.name}</div>
                <div className="owner-cafe-card-dates">{fmtDate(cafe.start_date)} – {fmtDate(cafe.end_date)}</div>
                <div className="owner-cafe-card-code">Join code: <strong>{cafe.join_code}</strong></div>
                <div className="owner-cafe-card-arrow">→</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showCreate && (
        <div className="owner-modal-backdrop" onClick={() => setShowCreate(false)}>
          <div className="owner-modal" onClick={e => e.stopPropagation()}>
            <div className="owner-modal-title">Create a Cafe</div>
            <form onSubmit={handleCreateCafe}>
              <div className="form-field">
                <label className="form-label">Cafe Name</label>
                <input
                  className="form-input"
                  type="text"
                  placeholder="Brew & Chat"
                  value={form.name}
                  onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
                  autoFocus
                />
              </div>
              <div className="owner-form-row">
                <div className="form-field">
                  <label className="form-label">Start Date</label>
                  <input
                    className="form-input"
                    type="date"
                    value={form.start_date}
                    onChange={e => setForm(p => ({ ...p, start_date: e.target.value }))}
                  />
                </div>
                <div className="form-field">
                  <label className="form-label">End Date</label>
                  <input
                    className="form-input"
                    type="date"
                    value={form.end_date}
                    onChange={e => setForm(p => ({ ...p, end_date: e.target.value }))}
                  />
                </div>
              </div>
              <label className="owner-toggle-label">
                <input
                  type="checkbox"
                  checked={form.one_slot}
                  onChange={e => setForm(p => ({ ...p, one_slot: e.target.checked }))}
                />
                One slot per customer
              </label>
              {createError && <div className="owner-form-error">{createError}</div>}
              <div className="owner-modal-actions">
                <button type="button" className="owner-modal-cancel" onClick={() => setShowCreate(false)}>Cancel</button>
                <button type="submit" className="owner-modal-submit" disabled={creating}>
                  {creating ? 'Creating…' : 'Create Cafe'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {shareLinks && (
        <ShareLinksPopup cafe={shareLinks} onClose={() => setShareLinks(null)} />
      )}
    </div>
  );
}
