import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import BaristaSidebar from '../../components/BaristaSidebar';
import CalendarGrid from '../../components/CalendarGrid';
import OwnerDayTimeline from '../../components/owner/OwnerDayTimeline';
import OwnerSettings from '../../components/owner/OwnerSettings';
import ShareLinksPopup from '../../components/owner/ShareLinksPopup';
import {
  getOwnerCafe, getOwnerCafeSlots,
  getOwnerCafeBaristas, getCafeCustomers,
  removeBarista, removeCustomer,
} from '../../api';

const EXPERTISE_OPTIONS = [
  'Latte Art', 'Cold Brew Master', 'Espresso Expert',
  'Pour Over', 'Aeropress', 'Siphon Brew',
];
const getExpertise = (id) => EXPERTISE_OPTIONS[id % EXPERTISE_OPTIONS.length];

const initials = (name) =>
  name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();

export default function OwnerCafeView() {
  const { cafeId } = useParams();
  const navigate = useNavigate();

  const auth = useMemo(() => {
    try {
      const stored = localStorage.getItem('owner_auth');
      return stored ? JSON.parse(stored) : null;
    } catch { return null; }
  }, []);

  useEffect(() => {
    if (!auth) navigate('/owner', { replace: true });
  }, [auth, navigate]);

  // ── main data ────────────────────────────────────────────────────────────
  const [cafe, setCafe] = useState(null);
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(true);

  // ── view state ───────────────────────────────────────────────────────────
  const [activeView, setActiveView] = useState('calendar'); // 'calendar'|'baristas'|'customers'
  const [selectedDate, setSelectedDate] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [showShare, setShowShare] = useState(false);

  // ── people state (loaded lazily) ─────────────────────────────────────────
  const [baristas,         setBaristas]         = useState([]);
  const [customers,        setCustomers]        = useState([]);
  const [baristasLoading,  setBaristasLoading]  = useState(false);
  const [customersLoading, setCustomersLoading] = useState(false);
  const [baristasLoaded,   setBaristasLoaded]   = useState(false);
  const [customersLoaded,  setCustomersLoaded]  = useState(false);
  const [removeTarget,     setRemoveTarget]     = useState(null);

  useEffect(() => {
    if (!auth) return;
    Promise.all([
      getOwnerCafe(cafeId, auth.token),
      getOwnerCafeSlots(cafeId, auth.token),
      getOwnerCafeBaristas(cafeId, auth.token),
    ])
      .then(([cafeData, slotsData, baristasData]) => {
        setCafe(cafeData);
        setSlots(slotsData);
        setBaristas(baristasData.map(b => ({ ...b, expertise: getExpertise(b.id) })));
        setBaristasLoaded(true);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [cafeId, auth]);

  useEffect(() => {
    if (!auth) return;
    if (activeView === 'baristas' && !baristasLoaded) {
      setBaristasLoading(true);
      getOwnerCafeBaristas(cafeId, auth.token)
        .then(data => { setBaristas(data); setBaristasLoaded(true); })
        .catch(() => setBaristasLoaded(true))
        .finally(() => setBaristasLoading(false));
    }
    if (activeView === 'customers' && !customersLoaded) {
      setCustomersLoading(true);
      getCafeCustomers(cafeId, auth.token)
        .then(data => { setCustomers(data); setCustomersLoaded(true); })
        .catch(() => setCustomersLoaded(true))
        .finally(() => setCustomersLoading(false));
    }
  }, [activeView]);

  const slotsByDate = useMemo(() => {
    const map = {};
    for (const slot of slots) {
      const date = new Date(slot.start_time).toLocaleDateString('en-CA');
      if (!map[date]) map[date] = [];
      map[date].push(slot);
    }
    return map;
  }, [slots]);


  function handleSlotDeleted(slotId) {
    setSlots(prev => prev.filter(s => s.id !== slotId));
  }

  function handleSlotUnbooked(slotId) {
    setSlots(prev => prev.map(s => s.id === slotId ? { ...s, customer: null } : s));
  }

  async function handleRemoveConfirm() {
    const { type, item } = removeTarget;

    // Optimistic update — remove from UI immediately
    if (type === 'barista') {
      setBaristas(prev => prev.filter(b => b.id !== item.id));
    } else {
      setCustomers(prev => prev.filter(c => c.id !== item.id));
    }
    setRemoveTarget(null);

    // API call in background
    try {
      if (type === 'barista') {
        await removeBarista(item.id, auth.token);
      } else {
        await removeCustomer(item.id, auth.token);
      }
    } catch { /* UI already updated */ }
  }

  if (!auth) return null;

  if (loading) {
    return (
      <div className="loading-screen">
        <span>☕</span>
        Loading cafe…
      </div>
    );
  }

  const peopleList = activeView === 'baristas' ? baristas : customers;
  const peopleLoading = activeView === 'baristas' ? baristasLoading : customersLoading;

  return (
    <>
      <div className="app">
        <div className="owner-cafe-topbar">
          <div className="owner-cafe-topbar-left">
            <button
              className="owner-back-btn"
              onClick={() => activeView !== 'calendar' ? setActiveView('calendar') : navigate('/owner')}
            >← Back</button>
            <span className="owner-cafe-topbar-icon">☕</span>
            <div>
              <div className="owner-cafe-topbar-name">{cafe?.name || 'Cafe'}</div>
              <div className="owner-cafe-topbar-sub">Owner View · Join code: {cafe?.join_code}</div>
            </div>
          </div>
          <div className="owner-cafe-topbar-right">
            <div className="owner-view-tabs">
              {['baristas', 'customers'].map(v => (
                <button
                  key={v}
                  className={`owner-view-tab${activeView === v ? ' active' : ''}`}
                  onClick={() => setActiveView(activeView === v ? 'calendar' : v)}
                >
                  {v.charAt(0).toUpperCase() + v.slice(1)}
                </button>
              ))}
            </div>
            <div className="owner-topbar-divider" />
            {cafe && (
              <button className="owner-share-btn" onClick={() => setShowShare(true)}>
                Share Links
              </button>
            )}
            <button className="owner-settings-btn" onClick={() => setShowSettings(true)}>
              ⚙ Settings
            </button>
          </div>
        </div>

        {activeView === 'calendar' ? (
          <div className="main-layout">
            <BaristaSidebar baristas={baristas} />
            <CalendarGrid
              slots={slots}
              startDate={cafe?.start_date}
              selectedDate={selectedDate}
              onSelectDate={setSelectedDate}
              myBookedDates={new Set()}
            />
            {selectedDate && (
              <OwnerDayTimeline
                date={selectedDate}
                slots={slotsByDate[selectedDate] || []}
                token={auth.token}
                onClose={() => setSelectedDate(null)}
                onSlotDeleted={handleSlotDeleted}
                onSlotUnbooked={handleSlotUnbooked}
              />
            )}
          </div>
        ) : (
          <div className="owner-people-view">
            <div className="owner-people-view-header">
              {activeView === 'baristas' ? 'Baristas' : 'Customers'}
              <span className="owner-people-count">
                {!peopleLoading && `${peopleList.length} total`}
              </span>
            </div>
            {peopleLoading ? (
              <div className="owner-loading">Loading…</div>
            ) : peopleList.length === 0 ? (
              <div className="owner-empty-list">
                No {activeView} registered yet.
              </div>
            ) : (
              <div className="owner-people-grid">
                {peopleList.map(p => (
                  <div key={p.id} className="owner-person-card">
                    <div className="owner-person-card-avatar">{initials(p.name)}</div>
                    <div className="owner-person-card-info">
                      <div className="owner-person-card-name">{p.name}</div>
                      {p.email && <div className="owner-person-card-detail">{p.email}</div>}
                      {p.phone_number && <div className="owner-person-card-detail">{p.phone_number}</div>}
                    </div>
                    <button
                      className="owner-person-remove"
                      onClick={() => setRemoveTarget({ type: activeView === 'baristas' ? 'barista' : 'customer', item: p })}
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {showSettings && cafe && (
        <OwnerSettings
          cafe={cafe}
          token={auth.token}
          onClose={() => setShowSettings(false)}
          onCafeUpdated={setCafe}
        />
      )}

      {showShare && cafe && (
        <ShareLinksPopup cafe={cafe} onClose={() => setShowShare(false)} />
      )}

      {removeTarget && (
        <div className="tl-confirm-backdrop">
          <div className="tl-confirm-popup">
            <div className="tl-confirm-title">Remove {removeTarget.type}?</div>
            <div className="tl-confirm-sub">{removeTarget.item.name}</div>
            <div className="tl-confirm-actions">
              <button className="tl-confirm-cancel" onClick={() => setRemoveTarget(null)}>
                Cancel
              </button>
              <button className="tl-confirm-ok tl-confirm-delete" onClick={handleRemoveConfirm}>
                Remove
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
