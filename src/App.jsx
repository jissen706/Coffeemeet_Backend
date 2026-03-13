import { Routes, Route, Navigate } from 'react-router-dom';
import CustomerPage from './pages/CustomerPage';
import BaristaDashboard from './pages/BaristaDashboard';
import './App.css';

function App() {
  return (
    <Routes>
      <Route path="/cafe/:joinCode" element={<CustomerPage />} />
      <Route path="/barista" element={<BaristaDashboard />} />
      <Route path="*" element={<Navigate to="/cafe/demo" replace />} />
    </Routes>
  );
}

export default App;
