import { useState } from 'react';
import OwnerLogin from './owner/OwnerLogin';
import OwnerDashboard from './owner/OwnerDashboard';

export default function OwnerPage() {
  const [auth, setAuth] = useState(() => {
    try {
      const stored = localStorage.getItem('owner_auth');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  function handleLogin(authData) {
    localStorage.setItem('owner_auth', JSON.stringify(authData));
    setAuth(authData);
  }

  function handleLogout() {
    localStorage.removeItem('owner_auth');
    setAuth(null);
  }

  if (!auth) return <OwnerLogin onLogin={handleLogin} />;
  return <OwnerDashboard token={auth.token} owner={auth} onLogout={handleLogout} />;
}
