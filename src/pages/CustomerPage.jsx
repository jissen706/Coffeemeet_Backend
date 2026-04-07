import { useState, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import Header from '../components/Header';
import BaristaSidebar from '../components/BaristaSidebar';
import CalendarGrid from '../components/CalendarGrid';
import DayTimeline from '../components/DayTimeline';
import BookingModal from '../components/BookingModal';
import BookingPage from '../components/BookingPage';
import CelebrationOverlay from '../components/CelebrationOverlay';
import { getCafeByCode, getSlots, getCafeBaristas, loginCustomer, createCustomer, bookSlot, cancelBooking } from '../api';

const EXPERTISE_OPTIONS = [
  'Latte Art', 'Cold Brew Master', 'Espresso Expert',
  'Pour Over', 'Aeropress', 'Siphon Brew',
];
function getExpertise(id) {
  return EXPERTISE_OPTIONS[id % EXPERTISE_OPTIONS.length];
}

function CustomerPage() {
  const { joinCode } = useParams();

  const [cafe, setCafe] = useState(null);
  const [slots, setSlots] = useState([]);
  const [baristas, setBaristas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDate, setSelectedDate] = useState(null);

  const [modalSlot, setModalSlot] = useState(null);
  const [view, setView] = useState('main');
  const [activeSlot, setActiveSlot] = useState(null);
  const [myBookedDates, setMyBookedDates] = useState(new Set());
  const [myBookedSlotId, setMyBookedSlotId] = useState(null);
  const [customerToken, setCustomerToken] = useState(null);

  useEffect(() => {
    if (!joinCode) { setError('No join code in URL'); setLoading(false); return; }
    getCafeByCode(joinCode)
      .then((cafeData) => {
        setCafe(cafeData);
        return Promise.all([
          getSlots(cafeData.id),
          getCafeBaristas(cafeData.id),
        ]);
      })
      .then(([slotsData, baristasData]) => {
        setSlots(slotsData);
        setBaristas(baristasData.map((b) => ({ ...b, expertise: getExpertise(b.id) })));
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [joinCode]);

  const slotsByDate = useMemo(() => {
    const map = {};
    for (const slot of slots) {
      const date = new Date(slot.start_time).toLocaleDateString('en-CA');
      if (!map[date]) map[date] = [];
      map[date].push(slot);
    }
    return map;
  }, [slots]);

  function handleBookSlot(slot) { setModalSlot(slot); }

  function handleModalConfirm() {
    setActiveSlot(modalSlot);
    setModalSlot(null);
    setView('booking');
  }

  function handleModalCancel() { setModalSlot(null); }

  async function handleBookingConfirm(customerData) {
    const name = `${customerData.first_name} ${customerData.last_name}`.trim();
    const email = customerData.email.trim();
    // Try to login existing customer, otherwise create them
    let customer;
    try {
      customer = await loginCustomer(email);
    } catch (e) {
      if (e.status === 404) {
        await createCustomer(cafe.id, { name, email });
        customer = await loginCustomer(email);
      } else {
        throw e;
      }
    }

    // Book the slot
    const updatedSlot = await bookSlot(activeSlot.id, customer.customer_id);

    // Store token for cancellation
    setCustomerToken(customer.access_token);

    // Update slots state with the booked slot
    setSlots((prev) => prev.map((s) => s.id === activeSlot.id ? updatedSlot : s));

    const date = new Date(activeSlot.start_time).toLocaleDateString('en-CA');
    setMyBookedDates((prev) => new Set([...prev, date]));
    setMyBookedSlotId(activeSlot.id);
    setSelectedDate(null);
    setView('celebration');
  }

  async function handleCancelBooking(slotId) {
    if (!customerToken) return;
    try {
      const updatedSlot = await cancelBooking(slotId, customerToken);
      setSlots((prev) => prev.map((s) => s.id === slotId ? updatedSlot : s));
    } catch {
      // Optimistic fallback
      setSlots((prev) => prev.map((s) => s.id === slotId ? { ...s, customer: null } : s));
    }
    const cancelledSlot = slots.find((s) => s.id === slotId);
    if (cancelledSlot) {
      const date = new Date(cancelledSlot.start_time).toLocaleDateString('en-CA');
      setMyBookedDates((prev) => { const next = new Set(prev); next.delete(date); return next; });
    }
    setMyBookedSlotId(null);
    setCustomerToken(null);
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
          description="Where great conversations brew over better coffee."
          ownerName=""
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
        <BookingPage
          slot={activeSlot}
          onConfirm={handleBookingConfirm}
          onBack={handleBookingBack}
        />
      )}
      {view === 'celebration' && activeSlot && (
        <CelebrationOverlay slot={activeSlot} onDone={handleCelebrationDone} />
      )}
    </>
  );
}

export default CustomerPage;
