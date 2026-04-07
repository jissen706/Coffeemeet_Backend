const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ── Cafe API ──────────────────────────────────────────────────────────────────

export async function getCafe(cafeId) {
  const res = await fetch(`${BASE_URL}/cafes/${cafeId}`);
  if (!res.ok) throw new Error(`Failed to load cafe (${res.status})`);
  return res.json();
}

export async function getSlots(cafeId) {
  const res = await fetch(`${BASE_URL}/cafes/${cafeId}/slots`);
  if (!res.ok) throw new Error(`Failed to load slots (${res.status})`);
  return res.json();
}

export async function getCafeByCode(joinCode) {
  const res = await fetch(`${BASE_URL}/cafes/join/${encodeURIComponent(joinCode)}`);
  if (!res.ok) throw new Error(`Cafe not found (${res.status})`);
  return res.json();
}

export async function getCafeBaristas(cafeId) {
  const res = await fetch(`${BASE_URL}/cafes/${cafeId}/baristas`);
  if (!res.ok) throw new Error(`Failed to load baristas (${res.status})`);
  return res.json();
}

// ── Barista API ───────────────────────────────────────────────────────────────

// POST /baristas — handles both register and login (if email already exists in cafe)
export async function registerBarista(joinCode, { name, email, phone }) {
  const res = await fetch(`${BASE_URL}/baristas`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, phone_number: phone || null, join_code: joinCode }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Failed to sign in (${res.status})`);
  }
  const data = await res.json();
  // Normalize to { id, name, cafe_id, token, email }
  return {
    id: data.user.id,
    name: data.user.name,
    cafe_id: data.user.cafe_id,
    token: data.access_token,
    email,
  };
}

export async function createSlot(cafeId, slotData, token) {
  const res = await fetch(`${BASE_URL}/slots`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ ...slotData, cafe_id: cafeId }),
  });
  if (!res.ok) throw new Error(`Failed to create slot (${res.status})`);
  return res.json();
}

export async function deleteSlot(slotId, token) {
  const res = await fetch(`${BASE_URL}/slots/${slotId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Failed to delete slot (${res.status})`);
}

// ── Customer API ──────────────────────────────────────────────────────────────

export async function loginCustomer(email) {
  const res = await fetch(
    `${BASE_URL}/customers/login?email=${encodeURIComponent(email)}`,
    { method: 'POST' }
  );
  const err = Object.assign(new Error(`Customer not found (${res.status})`), { status: res.status });
  if (!res.ok) throw err;
  return res.json();
}

export async function createCustomer(cafeId, { name, email }) {
  const res = await fetch(`${BASE_URL}/customers/${cafeId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email }),
  });
  if (!res.ok) throw new Error(`Failed to create customer (${res.status})`);
  return res.json();
}

export async function bookSlot(slotId, customerId) {
  const res = await fetch(`${BASE_URL}/slots/${slotId}/book`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ customer_id: customerId }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Failed to book slot (${res.status})`);
  }
  return res.json();
}

export async function cancelBooking(slotId, token) {
  const res = await fetch(`${BASE_URL}/slots/${slotId}/unbook`, {
    method: 'PATCH',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Failed to cancel booking (${res.status})`);
  return res.json();
}

// ── Owner API ─────────────────────────────────────────────────────────────────

function ownerHeaders(token) {
  return { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
}

// Returns normalized { token, owner_id, name }
export async function loginOwner(email, password) {
  const res = await fetch(`${BASE_URL}/owners/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Login failed (${res.status})`);
  }
  const data = await res.json();
  return { token: data.access_token, owner_id: data.user.id, name: data.user.name };
}

// Returns normalized { token, owner_id, name }
export async function registerOwner(name, email, password) {
  const res = await fetch(`${BASE_URL}/owners`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Registration failed (${res.status})`);
  }
  const data = await res.json();
  return { token: data.access_token, owner_id: data.user.id, name: data.user.name };
}

export async function getOwnerCafes(ownerId, token) {
  const res = await fetch(`${BASE_URL}/owners/${ownerId}/cafes`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Failed to load cafes (${res.status})`);
  return res.json();
}

export async function getOwnerCafe(cafeId, token) {
  const res = await fetch(`${BASE_URL}/cafes/${cafeId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Failed to load cafe (${res.status})`);
  return res.json();
}

export async function getOwnerCafeSlots(cafeId, token) {
  const res = await fetch(`${BASE_URL}/cafes/${cafeId}/slots`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Failed to load slots (${res.status})`);
  return res.json();
}

export async function createCafeApi(cafeData, token) {
  const res = await fetch(`${BASE_URL}/cafes`, {
    method: 'POST',
    headers: ownerHeaders(token),
    body: JSON.stringify(cafeData),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Failed to create cafe (${res.status})`);
  }
  return res.json();
}

export async function updateCafe(cafeId, data, token) {
  const res = await fetch(`${BASE_URL}/cafes/${cafeId}`, {
    method: 'PUT',
    headers: ownerHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to update cafe (${res.status})`);
  return res.json();
}

export async function getOwnerCafeBaristas(cafeId, token) {
  const res = await fetch(`${BASE_URL}/cafes/${cafeId}/baristas`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Failed to load baristas (${res.status})`);
  return res.json();
}

export async function getCafeCustomers(cafeId, token) {
  const res = await fetch(`${BASE_URL}/cafes/${cafeId}/customers`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Failed to load customers (${res.status})`);
  return res.json();
}

export async function removeBarista(baristaId, token) {
  const res = await fetch(`${BASE_URL}/baristas/${baristaId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Failed to remove barista (${res.status})`);
}

export async function removeCustomer(customerId, token) {
  const res = await fetch(`${BASE_URL}/customers/${customerId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Failed to remove customer (${res.status})`);
}

export async function ownerDeleteSlot(slotId, token) {
  const res = await fetch(`${BASE_URL}/slots/${slotId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Failed to delete slot (${res.status})`);
}

export async function ownerUnbookSlot(slotId, token) {
  const res = await fetch(`${BASE_URL}/slots/${slotId}/unbook`, {
    method: 'PATCH',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Failed to unbook slot (${res.status})`);
  return res.json();
}
