import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import Sidebar from './components/Sidebar';
import { ToastProvider } from './components/Toast';
import Dashboard    from './pages/Dashboard';
import LiveFeed     from './pages/LiveFeed';
import Incidents    from './pages/Incidents';
import Models       from './pages/Models';
import AutoTrain    from './pages/AutoTrain';
import Analytics    from './pages/Analytics';
import Settings     from './pages/Settings';
import BorderMonitor from './pages/BorderMonitor';

function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/"               element={<Dashboard />} />
        <Route path="/live"           element={<LiveFeed />} />
        <Route path="/incidents"      element={<Incidents />} />
        <Route path="/border-monitor" element={<BorderMonitor />} />
        <Route path="/models"         element={<Models />} />
        <Route path="/auto-train"     element={<AutoTrain />} />
        <Route path="/analytics"      element={<Analytics />} />
        <Route path="/settings"       element={<Settings />} />
      </Routes>
    </AnimatePresence>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <div className="app-layout">
          <Sidebar />
          <main className="main-content" role="main">
            <AnimatedRoutes />
          </main>
        </div>
      </ToastProvider>
    </BrowserRouter>
  );
}
