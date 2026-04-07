import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function LandingPage() {
  const navigate = useNavigate();
  const [baristaCode, setBaristaCode] = useState('');
  const [customerCode, setCustomerCode] = useState('');
  const [baristaError, setBaristaError] = useState('');
  const [customerError, setCustomerError] = useState('');

  function handleBaristaGo(e) {
    e.preventDefault();
    const code = baristaCode.trim();
    if (!code) { setBaristaError('Enter a join code'); return; }
    navigate(`/barista?code=${encodeURIComponent(code)}`);
  }

  function handleCustomerGo(e) {
    e.preventDefault();
    const code = customerCode.trim();
    if (!code) { setCustomerError('Enter a join code'); return; }
    navigate(`/cafe/${encodeURIComponent(code)}`);
  }

  return (
    <div className="landing-page">
      <div className="landing-hero">
        <div className="landing-logo">☕</div>
        <h1 className="landing-title">CoffeeMeet</h1>
        <p className="landing-subtitle">
          The easiest way to schedule coffee chats for your club.
        </p>
      </div>

      <div className="landing-cards">
        {/* Owner */}
        <div className="landing-card">
          <div className="landing-card-icon">🏠</div>
          <h2 className="landing-card-title">I'm a Club Leader</h2>
          <p className="landing-card-desc">
            Create a café, set availability, and share links with your baristas and members.
          </p>
          <button
            className="landing-card-btn landing-card-btn-primary"
            onClick={() => navigate('/owner')}
          >
            Go to Owner Portal →
          </button>
        </div>

        {/* Barista */}
        <div className="landing-card">
          <div className="landing-card-icon">👋</div>
          <h2 className="landing-card-title">I'm a Barista</h2>
          <p className="landing-card-desc">
            Got a join code from your club leader? Enter it here to manage your slots.
          </p>
          <form onSubmit={handleBaristaGo} style={{ width: '100%' }}>
            <input
              className={`form-input landing-code-input${baristaError ? ' form-input-error' : ''}`}
              type="text"
              placeholder="Enter join code (e.g. DEMO01)"
              value={baristaCode}
              onChange={(e) => { setBaristaCode(e.target.value.toUpperCase()); setBaristaError(''); }}
            />
            {baristaError && <span className="form-error">{baristaError}</span>}
            <button className="landing-card-btn landing-card-btn-secondary" type="submit">
              Open Barista Dashboard →
            </button>
          </form>
        </div>

        {/* Customer */}
        <div className="landing-card">
          <div className="landing-card-icon">📅</div>
          <h2 className="landing-card-title">I'm booking a Coffee Chat</h2>
          <p className="landing-card-desc">
            Have a link or join code from your club? Enter it here to see available slots.
          </p>
          <form onSubmit={handleCustomerGo} style={{ width: '100%' }}>
            <input
              className={`form-input landing-code-input${customerError ? ' form-input-error' : ''}`}
              type="text"
              placeholder="Enter join code (e.g. DEMO01)"
              value={customerCode}
              onChange={(e) => { setCustomerCode(e.target.value.toUpperCase()); setCustomerError(''); }}
            />
            {customerError && <span className="form-error">{customerError}</span>}
            <button className="landing-card-btn landing-card-btn-secondary" type="submit">
              View Available Slots →
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
