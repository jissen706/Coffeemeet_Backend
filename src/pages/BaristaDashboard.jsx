import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import Header from '../components/Header';
import BaristaSidebar from '../components/BaristaSidebar';
import BaristaLogin from '../components/barista/BaristaLogin';
import BaristaCalendarGrid from '../components/barista/BaristaCalendarGrid';
import BaristaDayTimeline from '../components/barista/BaristaDayTimeline';
import { getCafe, getSlots } from '../api';

const CAFE_ID = 1;

const EXPERTISE_OPTIONS = [
  'Latte Art', 'Cold Brew Master', 'Espresso Expert',
  'Pour Over', 'Aeropress', 'Siphon Brew',
];
function getExpertise(id) {
  return EXPERTISE_OPTIONS[id % EXPERTISE_OPTIONS.length];
}

function BaristaDashboard() {
  const [searchParams] = useSearchParams();
  const joinCode = searchParams.get('code') || '';

  const [barista, setBarista] = useState(null);
  const [cafe, setCafe] = useState(null);
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(null);

  useEffect(() => {
    Promise.all([getCafe(CAFE_ID), getSlots(CAFE_ID)])
      .then(([cafeData, slotsData]) => {
        setCafe(cafeData);
        setSlots(slotsData);
        setLoading(false);
      })
      .catch(() => setLoading(false));
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

  function handleSlotCreated(newSlot) {
    setSlots((prev) => [...prev, newSlot]);
  }

  function handleSlotDeleted(slotId) {
    setSlots((prev) => prev.filter((s) => s.id !== slotId));
  }

  // Show login screen regardless of loading state — it doesn't depend on cafe data
  if (!barista) {
    return <BaristaLogin joinCode={joinCode} onLogin={setBarista} />;
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <span>☕</span>
        Brewing your experience...
      </div>
    );
  }

  const allBaristas = Object.values(
    slots.reduce((acc, slot) => {
      if (slot.barista && !acc[slot.barista.id]) {
        acc[slot.barista.id] = { ...slot.barista, expertise: getExpertise(slot.barista.id) };
      }
      return acc;
    }, {})
  );

  // If the logged-in barista isn't in any slots yet, add them to the sidebar
  if (!allBaristas.find((b) => b.id === barista.id)) {
    allBaristas.unshift({ ...barista, expertise: getExpertise(barista.id) });
  }

  return (
    <div className="app">
      <Header
        cafeName={cafe?.name || 'Brew & Chat'}
        description="Manage your slots and availability"
        ownerName={`Barista: ${barista.name}`}
      />
      <div className="main-layout">
        <BaristaSidebar baristas={allBaristas} />
        <BaristaCalendarGrid
          slots={slots}
          startDate={cafe?.start_date}
          barista={barista}
          selectedDate={selectedDate}
          onSelectDate={setSelectedDate}
          onSlotCreated={handleSlotCreated}
        />
        {selectedDate && (
          <BaristaDayTimeline
            date={selectedDate}
            slots={slotsByDate[selectedDate] || []}
            barista={barista}
            onClose={() => setSelectedDate(null)}
            onSlotCreated={handleSlotCreated}
            onSlotDeleted={handleSlotDeleted}
          />
        )}
      </div>
    </div>
  );
}

export default BaristaDashboard;
