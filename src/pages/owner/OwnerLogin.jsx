import { useState } from 'react';
import { loginOwner, registerOwner } from '../../api';

export default function OwnerLogin({ onLogin }) {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function switchMode(m) {
    setMode(m);
    setError('');
    setName('');
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'register') {
        if (!name.trim()) { setError('Enter your name'); setLoading(false); return; }
        const data = await registerOwner(name.trim(), email, password);
        onLogin(data);
        return;
      }
      const data = await loginOwner(email, password);
      onLogin(data);
    } catch (err) {
      setError(
        err.message === 'Failed to fetch'
          ? 'Cannot reach server — make sure the backend is running on port 8000.'
          : err.message
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="owner-login-page">
      <div className="owner-login-card">
        <div className="owner-login-header">
          <span className="owner-login-icon">☕</span>
          <h1 className="owner-login-title">CoffeeMeet</h1>
          <p className="owner-login-sub">Owner Portal</p>
        </div>

        <div className="owner-mode-tabs">
          <button
            className={`owner-mode-tab${mode === 'login' ? ' active' : ''}`}
            onClick={() => switchMode('login')}
          >Log In</button>
          <button
            className={`owner-mode-tab${mode === 'register' ? ' active' : ''}`}
            onClick={() => switchMode('register')}
          >Create Account</button>
        </div>

        <form className="owner-login-form" onSubmit={handleSubmit}>
          {mode === 'register' && (
            <div className="form-field">
              <label className="form-label">Your Name</label>
              <input
                className="form-input"
                type="text"
                placeholder="Sarah Mitchell"
                value={name}
                onChange={e => { setName(e.target.value); setError(''); }}
                autoFocus
              />
            </div>
          )}
          <div className="form-field">
            <label className="form-label">Email</label>
            <input
              className="form-input"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={e => { setEmail(e.target.value); setError(''); }}
              autoFocus={mode === 'login'}
            />
          </div>
          <div className="form-field">
            <label className="form-label">Password</label>
            <input
              className="form-input"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={e => { setPassword(e.target.value); setError(''); }}
            />
          </div>
          {error && <div className="owner-form-error">{error}</div>}
          <button className="owner-login-btn" type="submit" disabled={loading}>
            {loading ? 'Please wait…' : mode === 'login' ? 'Log In →' : 'Create Account →'}
          </button>
        </form>
      </div>
    </div>
  );
}
