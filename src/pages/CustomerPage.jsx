import { useState, useEffect, useMemo } from 'react';
import Header from '../components/Header';
import BaristaSidebar from '../components/BaristaSidebar';
import CalendarGrid from '../components/CalendarGrid';
import DayTimeline from '../components/DayTimeline';
import BookingModal from '../components/BookingModal';
import BookingPage from '../components/BookingPage';
import CelebrationOverlay from '../components/CelebrationOverlay';
import { getCafe, getSlots, bookSlot, cancelBooking } from '../api';

const CAFE_ID = 1;
const OWNER_NAME = 'Sarah Mitchell';
const CAFE_DESCRIPTION = 'Where great conversations brew over better coffee.';

const EXPERTISE_OPTIONS = [
  'Latte Art', 'Cold Brew Master', 'Espresso Expert',
  'Pour Over', 'Aeropress', 'Siphon Brew',
];

function getExpertise(id) {
  return EXPERTISE_OPTIONS[id % EXPERTISE_OPTIONS.length];
}

function CustomerPage() {
  const [cafe, setCafe] = useState(null);
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDate, setSelectedDate] = useState(null);

  const [modalSlot, setModalSlot] = useState(null);
  const [view, setView] = useState('main');
  const [activeSlot, setActiveSlot] = useState(null);
  const [myBookedDates, setMyBookedDates] = useState(new Set());
  const [myBookedSlotId, setMyBookedSlotId] = useState(null);

  useEffect(() => {
    Promise.all([getCafe(CAFE_ID), getSlots(CAFE_ID)])
      .then(([cafeData, slotsData]) => {
        setCafe(cafeData);
        setSlots(slotsData);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const slotsByDate = useMemo(() => {
    const map = {};
    for (const slot of slots) {
      const date = new Date(slot.start_time).toLocaleDateString('en-CA');
      if (!map[date]) map[date] = [];
      map[date].push(slot);
    }
    return map;
  }, [slots]);

  const baristas = useMemo(() => Object.values(
    slots.reduce((acc, slot) => {
      if (slot.barista && !acc[slot.barista.id]) {
        acc[slot.barista.id] = { ...slot.barista, expertise: getExpertise(slot.barista.id) };
      }
      return acc;
    }, {})
  ), [slots]);

  function handleBookSlot(slot) { setModalSlot(slot); }

  function handleModalConfirm() {
    setActiveSlot(modalSlot);
    setModalSlot(null);
    setView('booking');
  }

  function handleModalCancel() { setModalSlot(null); }

  async function handleBookingConfirm(customerData) {
    try {
      await bookSlot(CAFE_ID, activeSlot.id, customerData);
    } catch {
      // Backend not connected yet — proceed with local state
    }
    setSlots((prev) =>
      prev.map((s) =>
        s.id === activeSlot.id
          ? { ...s, customer: { id: 999, name: `${customerData.first_name} ${customerData.last_name}` } }
          : s
      )
    );
    const date = new Date(activeSlot.start_time).toLocaleDateString('en-CA');
    setMyBookedDates((prev) => new Set([...prev, date]));
    setMyBookedSlotId(activeSlot.id);
    setSelectedDate(null);
    setView('celebration');
  }

  async function handleCancelBooking(slotId) {
    try {
      await cancelBooking(CAFE_ID, slotId);
    } catch {
      // Backend not connected yet — proceed with local state
    }
    const cancelledSlot = slots.find((s) => s.id === slotId);
    setSlots((prev) => prev.map((s) => s.id === slotId ? { ...s, customer: null } : s));
    if (cancelledSlot) {
      const date = new Date(cancelledSlot.start_time).toLocaleDateString('en-CA');
      setMyBookedDates((prev) => { const next = new Set(prev); next.delete(date); return next; });
    }
    setMyBookedSlotId(null);
  }

  function handleBookingBack() { setActiveSlot(null); setView('main'); }
  function handleCelebrationDone() { setActiveSlot(null); setView('main'); }

  if (loading) {
    return (
      <div className="loading-screen">
        <span>☕</span>
        Brewing your experience...
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-screen">
        <span>Could not connect to the server</span>
        <small>{error}</small>
      </div>
    );
  }

  return (
    <>
      <div className="app">
        <Header
          cafeName={cafe?.name || 'CoffeeMeet'}
          description={CAFE_DESCRIPTION}
          ownerName={OWNER_NAME}
        />
        <div className="main-layout">
          <BaristaSidebar baristas={baristas} />
          <CalendarGrid
            slots={slots}
            startDate={cafe?.start_date}
            selectedDate={selectedDate}
            onSelectDate={setSelectedDate}
            myBookedDates={myBookedDates}
          />
          {selectedDate && (
            <DayTimeline
              date={selectedDate}
              slots={slotsByDate[selectedDate] || []}
              onClose={() => setSelectedDate(null)}
              onBook={handleBookSlot}
              myBookedSlotId={myBookedSlotId}
              onCancelBooking={handleCancelBooking}
            />
          )}
        </div>
      </div>

      {modalSlot && (
        <BookingModal slot={modalSlot} onConfirm={handleModalConfirm} onCancel={handleModalCancel} />
      )}
      {view === 'booking' && activeSlot && (
        <BookingPage slot={activeSlot} onConfirm={handleBookingConfirm} onBack={handleBookingBack} />
      )}
      {view === 'celebration' && activeSlot && (
        <CelebrationOverlay slot={activeSlot} onDone={handleCelebrationDone} />
      )}
    </>
  );
}

export default CustomerPage;
