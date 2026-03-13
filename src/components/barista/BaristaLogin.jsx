import { useState } from 'react';
import { findBaristaByEmail, registerBarista } from '../../api';

function BaristaLogin({ joinCode, onLogin }) {
  const [step, setStep] = useState('email'); // 'email' | 'found' | 'register'
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [foundBarista, setFoundBarista] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleEmailSubmit(e) {
    e.preventDefault();
    if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Enter a valid email address');
      return;
    }
    setError('');
    setLoading(true);
    const barista = await findBaristaByEmail(1, email.trim());
    setLoading(false);
    if (barista) {
      setFoundBarista(barista);
      setStep('found');
    } else {
      setStep('register');
    }
  }

  async function handleRegister(e) {
    e.preventDefault();
    if (!name.trim()) { setError('Enter your name'); return; }
    setLoading(true);
    let barista;
    try {
      barista = await registerBarista(joinCode, { name: name.trim(), email: email.trim() });
    } catch {
      // No backend — create local barista for frontend dev
      barista = { id: Date.now(), name: name.trim(), email: email.trim(), phone_number: null };
    }
    setLoading(false);
    onLogin(barista);
  }

  const avatarInitials = (n) =>
    n.split(' ').map((w) => w[0]).join('').slice(0, 2).toUpperCase();

  return (
    <div className="barista-login-page">
      <div className="barista-login-card">
        <div className="barista-login-header">
          <span className="barista-login-icon">☕</span>
          <h1 className="barista-login-title">Barista Dashboard</h1>
          {joinCode && (
            <div className="barista-login-code">
              Join code: <strong>{joinCode}</strong>
            </div>
          )}
        </div>

        {step === 'email' && (
          <form className="barista-login-form" onSubmit={handleEmailSubmit}>
            <p className="barista-login-hint">
              Already a barista here? Enter your email to log back in.<br />
              New to this café? We'll get you set up.
            </p>
            <div className="form-field">
              <label className="form-label">Email</label>
              <input
                className={`form-input${error ? ' form-input-error' : ''}`}
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setError(''); }}
                autoFocus
              />
              {error && <span className="form-error">{error}</span>}
            </div>
            <button className="barista-login-btn" type="submit" disabled={loading}>
              {loading ? 'Checking…' : 'Continue →'}
            </button>
          </form>
        )}

        {step === 'found' && foundBarista && (
          <div className="barista-login-form">
            <div className="barista-welcome-back">
              <div className="barista-welcome-avatar">
                {avatarInitials(foundBarista.name)}
              </div>
              <div className="barista-welcome-name">
                Welcome back, {foundBarista.name.split(' ')[0]}!
              </div>
              <div className="barista-welcome-email">{foundBarista.email}</div>
            </div>
            <button className="barista-login-btn" onClick={() => onLogin(foundBarista)}>
              Enter Dashboard
            </button>
            <button
              className="barista-login-back"
              onClick={() => { setStep('email'); setFoundBarista(null); setEmail(''); }}
            >
              ← Use a different email
            </button>
          </div>
        )}

        {step === 'register' && (
          <form className="barista-login-form" onSubmit={handleRegister}>
            <p className="barista-login-hint">
              No account found for <strong>{email}</strong>.<br />
              Enter your name to join this café as a barista.
            </p>
            <div className="form-field">
              <label className="form-label">Your Name</label>
              <input
                className={`form-input${error ? ' form-input-error' : ''}`}
                type="text"
                placeholder="Alice Kim"
                value={name}
                onChange={(e) => { setName(e.target.value); setError(''); }}
                autoFocus
              />
              {error && <span className="form-error">{error}</span>}
            </div>
            <button className="barista-login-btn" type="submit" disabled={loading}>
              {loading ? 'Registering…' : 'Join as Barista'}
            </button>
            <button
              className="barista-login-back"
              type="button"
              onClick={() => { setStep('email'); setError(''); }}
            >
              ← Back
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

export default BaristaLogin;
