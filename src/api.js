const MOCK_CAFE = {
  id: 1,
  name: 'Brew & Chat',
  start_date: '2026-03-01',
  end_date: '2026-03-31',
};

const MOCK_BARISTAS = [
  { id: 1, name: 'Alice Kim',    email: 'alice@brewtchat.com',  phone_number: '555-1001' },
  { id: 2, name: 'Marco Reyes',  email: 'marco@brewtchat.com',  phone_number: '555-1002' },
  { id: 3, name: 'Priya Nair',   email: 'priya@brewtchat.com',  phone_number: null       },
];

// Helper to build a slot object
function slot(id, baristaId, date, startHour, endHour, location, customer = null) {
  const b = MOCK_BARISTAS.find((b) => b.id === baristaId);
  return {
    id,
    barista: b,
    customer,
    start_time: `${date}T${String(startHour).padStart(2, '0')}:00:00`,
    end_time:   `${date}T${String(endHour).padStart(2, '0')}:00:00`,
    location,
  };
}

const MOCK_SLOTS = [
  // March 12
  slot(1,  1, '2026-03-12', 9,  10, 'Table 1'),
  slot(2,  2, '2026-03-12', 10, 11, 'Table 2', { id: 99, name: 'Jordan Lee' }),
  slot(3,  3, '2026-03-12', 11, 12, 'Table 3'),

  // March 14
  slot(4,  1, '2026-03-14', 13, 14, 'Table 1', { id: 100, name: 'Sam Park' }),
  slot(5,  2, '2026-03-14', 14, 15, 'Table 2'),

  // March 17
  slot(6,  3, '2026-03-17', 9,  10, 'Table 3'),
  slot(7,  1, '2026-03-17', 10, 11, 'Table 1', { id: 101, name: 'Maya Chen' }),
  slot(8,  2, '2026-03-17', 11, 12, 'Table 2', { id: 102, name: 'Ravi Das' }),
  slot(9,  3, '2026-03-17', 14, 15, 'Table 3'),

  // March 20 — fully booked
  slot(10, 1, '2026-03-20', 9,  10, 'Table 1', { id: 103, name: 'Nina Torres' }),
  slot(11, 2, '2026-03-20', 10, 11, 'Table 2', { id: 104, name: 'Leo Wang' }),

  // March 25
  slot(12, 3, '2026-03-25', 15, 16, 'Table 3'),
  slot(13, 1, '2026-03-25', 16, 17, 'Table 1'),
];

export async function getCafe(_cafeId) {
  return MOCK_CAFE;
}

export async function getSlots(_cafeId) {
  return MOCK_SLOTS;
}

// ---- Barista API ----

// Simulate login — real app: GET /cafes/:cafeId/baristas?email=...
export async function findBaristaByEmail(_cafeId, email) {
  const barista = MOCK_BARISTAS.find(
    (b) => b.email.toLowerCase() === email.trim().toLowerCase()
  );
  return barista || null;
}

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// POST /baristas — register a new barista with a join code
// body: { name, email, join_code }
export async function registerBarista(joinCode, { name, email }) {
  const res = await fetch(`${BASE_URL}/baristas`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, join_code: joinCode }),
  });
  if (!res.ok) throw new Error(`Failed to register barista (${res.status})`);
  return res.json();
}

// POST /cafes/:cafeId/slots — create a new slot
// body: { barista_id, start_time, end_time, location, zoom_link }
export async function createSlot(cafeId, slotData) {
  const res = await fetch(`${BASE_URL}/cafes/${cafeId}/slots`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(slotData),
  });
  if (!res.ok) throw new Error(`Failed to create slot (${res.status})`);
  return res.json();
}

// DELETE /slots/:slotId — barista deletes their own slot
export async function deleteSlot(slotId) {
  const res = await fetch(`${BASE_URL}/slots/${slotId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`Failed to delete slot (${res.status})`);
}

// ---- Customer API ----

// POST /cafes/:cafeId/slots/:slotId/book
// body: { first_name, last_name, email }
export async function bookSlot(cafeId, slotId, customerData) {
  const res = await fetch(`${BASE_URL}/cafes/${cafeId}/slots/${slotId}/book`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(customerData),
  });
  if (!res.ok) throw new Error(`Failed to book slot (${res.status})`);
  return res.json();
}

// DELETE /cafes/:cafeId/slots/:slotId/book — customer cancels their booking
export async function cancelBooking(cafeId, slotId) {
  const res = await fetch(`${BASE_URL}/cafes/${cafeId}/slots/${slotId}/book`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`Failed to cancel booking (${res.status})`);
}
