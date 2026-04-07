import { useState } from 'react';
import { registerBarista } from '../../api';

function BaristaLogin({ joinCode, onLogin }) {
  const [name,     setName]     = useState('');
  const [email,    setEmail]    = useState('');
  const [phone,    setPhone]    = useState('');
  const [error,    setError]    = useState('');
  const [loading,  setLoading]  = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');

    if (!name.trim()) { setError('Enter your name'); return; }
    if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Enter a valid email address');
      return;
    }
    if (!joinCode) {
      setError('No join code — use the barista link from your café owner');
      return;
    }

    setLoading(true);
    try {
      const barista = await registerBarista(joinCode, {
        name: name.trim(),
        email: email.trim(),
        phone: phone.trim() || null,
      });
      onLogin(barista);
    } catch (err) {
      setError(err.message || 'Could not sign in. Check your join code and try again.');
    } finally {
      setLoading(false);
    }
  }

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

        <form className="barista-login-form" onSubmit={handleSubmit}>
          <p className="barista-login-hint">
            Enter your name and email to sign in or register as a barista for this café.
          </p>

          <div className="form-field">
            <label className="form-label">Your Name</label>
            <input
              className={`form-input${error && !name.trim() ? ' form-input-error' : ''}`}
              type="text"
              placeholder="Alice Kim"
              value={name}
              onChange={(e) => { setName(e.target.value); setError(''); }}
              autoFocus
            />
          </div>

          <div className="form-field">
            <label className="form-label">Email</label>
            <input
              className={`form-input${error && name.trim() ? ' form-input-error' : ''}`}
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setError(''); }}
            />
          </div>

          <div className="form-field">
            <label className="form-label">
              Phone <span className="form-label-optional">(optional)</span>
            </label>
            <input
              className="form-input"
              type="tel"
              placeholder="555-1234"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </div>

          {error && <span className="form-error">{error}</span>}

          <button className="barista-login-btn" type="submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Enter Dashboard →'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default BaristaLogin;
