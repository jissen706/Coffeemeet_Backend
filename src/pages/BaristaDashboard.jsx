import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import Header from '../components/Header';
import BaristaSidebar from '../components/BaristaSidebar';
import BaristaLogin from '../components/barista/BaristaLogin';
import BaristaCalendarGrid from '../components/barista/BaristaCalendarGrid';
import BaristaDayTimeline from '../components/barista/BaristaDayTimeline';
import { getCafe, getSlots, getCafeBaristas } from '../api';

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
  const [allBaristas, setAllBaristas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedDate, setSelectedDate] = useState(null);

  // Fetch cafe data after barista logs in
  useEffect(() => {
    if (!barista) return;
    setLoading(true);
    Promise.all([
      getCafe(barista.cafe_id),
      getSlots(barista.cafe_id),
      getCafeBaristas(barista.cafe_id),
    ])
      .then(([cafeData, slotsData, baristasData]) => {
        setCafe(cafeData);
        setSlots(slotsData);
        setAllBaristas(baristasData.map((b) => ({ ...b, expertise: getExpertise(b.id) })));
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [barista]);

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

  return (
    <div className="app">
      <Header
        cafeName={cafe?.name || 'CoffeeMeet'}
        description="Manage your slots and availability"
        ownerName={`Barista: ${barista.name}`}
      />
      <div className="main-layout">
        <BaristaSidebar baristas={allBaristas} />
        <BaristaCalendarGrid
          slots={slots}
          startDate={cafe?.start_date}
          barista={barista}
          token={barista.token}
          selectedDate={selectedDate}
          onSelectDate={setSelectedDate}
          onSlotCreated={handleSlotCreated}
        />
        {selectedDate && (
          <BaristaDayTimeline
            date={selectedDate}
            slots={slotsByDate[selectedDate] || []}
            barista={barista}
            token={barista.token}
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
