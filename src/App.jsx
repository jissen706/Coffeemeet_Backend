import { Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import CustomerPage from './pages/CustomerPage';
import BaristaDashboard from './pages/BaristaDashboard';
import OwnerPage from './pages/OwnerPage';
import OwnerCafeView from './pages/owner/OwnerCafeView';
import './App.css';

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/cafe/:joinCode" element={<CustomerPage />} />
      <Route path="/barista" element={<BaristaDashboard />} />
      <Route path="/owner" element={<OwnerPage />} />
      <Route path="/owner/cafe/:cafeId" element={<OwnerCafeView />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
