import { useState } from 'react';

function BookingPage({ slot, onConfirm, onBack }) {
  const { barista, start_time, end_time, location } = slot;

  const [form, setForm] = useState({ firstName: '', lastName: '', email: '' });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState(null);

  const fmt = (dt) =>
    new Date(dt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const formatted = new Date(start_time).toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric',
  });

  const initials = barista.name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  const rows = [
    { label: 'Date',     value: formatted },
    { label: 'Time',     value: `${fmt(start_time)} – ${fmt(end_time)}` },
    { label: 'Location', value: location },
  ];

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
    if (errors[field]) setErrors((e) => ({ ...e, [field]: null }));
  }

  async function handleSubmit() {
    const errs = {};
    if (!form.firstName.trim()) errs.firstName = 'Required';
    if (!form.lastName.trim())  errs.lastName  = 'Required';
    if (!form.email.trim())     errs.email     = 'Required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errs.email = 'Enter a valid email';

    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }

    setSubmitting(true);
    setApiError(null);
    try {
      await onConfirm({
        first_name: form.firstName.trim(),
        last_name:  form.lastName.trim(),
        email:      form.email.trim(),
      });
    } catch (err) {
      setApiError(err.message || 'Booking failed. Please try again.');
      setSubmitting(false);
    }
  }

  return (
    <div className="booking-page-overlay">
      <div className="booking-page-inner">
        <button className="booking-back-btn" onClick={onBack}>← Back</button>

        <div className="booking-page-card">
          <div className="booking-page-top">
            <div className="booking-page-avatar">{initials}</div>
            <div className="booking-page-barista-name">{barista.name}</div>
            <div className="booking-page-title">Confirm Your Booking</div>
          </div>

          <div className="booking-page-details">
            {rows.map(({ label, value }) => (
              <div key={label} className="booking-detail-row">
                <span className="booking-detail-label">{label}</span>
                <span className="booking-detail-value">{value}</span>
              </div>
            ))}
          </div>

          <div className="booking-form">
            <div className="booking-form-divider">Your details</div>

            <div className="booking-form-row">
              <div className="form-field">
                <label className="form-label">First Name</label>
                <input
                  className={`form-input${errors.firstName ? ' form-input-error' : ''}`}
                  type="text"
                  placeholder="Jordan"
                  value={form.firstName}
                  onChange={(e) => set('firstName', e.target.value)}
                />
                {errors.firstName && <span className="form-error">{errors.firstName}</span>}
              </div>
              <div className="form-field">
                <label className="form-label">Last Name</label>
                <input
                  className={`form-input${errors.lastName ? ' form-input-error' : ''}`}
                  type="text"
                  placeholder="Lee"
                  value={form.lastName}
                  onChange={(e) => set('lastName', e.target.value)}
                />
                {errors.lastName && <span className="form-error">{errors.lastName}</span>}
              </div>
            </div>

            <div className="form-field">
              <label className="form-label">Email</label>
              <input
                className={`form-input${errors.email ? ' form-input-error' : ''}`}
                type="email"
                placeholder="jordan@example.com"
                value={form.email}
                onChange={(e) => set('email', e.target.value)}
              />
              {errors.email && <span className="form-error">{errors.email}</span>}
            </div>
          </div>

          {apiError && <div className="form-error" style={{ marginBottom: 12 }}>{apiError}</div>}
          <button className="btn-confirm-big" onClick={handleSubmit} disabled={submitting}>
            {submitting ? 'Booking…' : '☕ Confirm Booking'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default BookingPage;
