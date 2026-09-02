import { NavLink, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  AlertTriangle,
  Box,
  Zap,
  Settings,
  Shield,
  Radio,
  BarChart3,
  Crosshair,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { checkHealth, listIncidents } from '../utils/api';
import alertSocket from '../utils/ws';
import ConnectionStatus from './ConnectionStatus';

const navSections = [
  {
    label: 'Monitoring',
    items: [
      { to: '/',               icon: LayoutDashboard, label: 'Dashboard' },
      { to: '/live',           icon: Radio,           label: 'Live Alerts' },
      { to: '/incidents',      icon: AlertTriangle,   label: 'Incidents', showBadge: true },
      { to: '/border-monitor', icon: Crosshair,       label: 'Border Monitor' },
    ],
  },
  {
    label: 'AI & Training',
    items: [
      { to: '/models',     icon: Box, label: 'Models' },
      { to: '/auto-train', icon: Zap, label: 'Auto-Train' },
    ],
  },
  {
    label: 'System',
    items: [
      { to: '/analytics', icon: BarChart3, label: 'Analytics' },
      { to: '/settings',  icon: Settings,  label: 'Settings' },
    ],
  },
];

export default function Sidebar() {
  const [online, setOnline]           = useState(false);
  const [pendingCount, setPendingCount] = useState(0);

  useEffect(() => {
    let mounted = true;
    const poll = async () => {
      try {
        await checkHealth();
        if (mounted) setOnline(true);
        try {
          const data = await listIncidents({ limit: 20, status: 'pending', hours: 24 });
          const items = Array.isArray(data) ? data : data.incidents || [];
          if (mounted) setPendingCount(items.length);
        } catch { /* ignore */ }
      } catch {
        if (mounted) setOnline(false);
      }
    };
    poll();
    const id = setInterval(poll, 15_000);
    return () => { mounted = false; clearInterval(id); };
  }, []);

  // Connect WS once globally here
  useEffect(() => {
    alertSocket.connect();
    // No unsub — sidebar lives for the app lifetime
  }, []);

  return (
    <aside className="sidebar" role="navigation" aria-label="Main navigation">
      <motion.div
        className="sidebar-brand"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="sidebar-brand-icon" aria-hidden="true">
          <Shield size={20} color="#fff" />
        </div>
        <div>
          <h2>Sawdhan AI</h2>
          <span>Border Surveillance</span>
        </div>
      </motion.div>

      <nav className="sidebar-nav">
        {navSections.map((section, si) => (
          <div key={section.label}>
            <div className="sidebar-section-label">{section.label}</div>
            {section.items.map((item, ii) => (
              <motion.div
                key={item.to}
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: si * 0.1 + ii * 0.05, duration: 0.3 }}
              >
                <NavLink
                  to={item.to}
                  className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
                  end={item.to === '/'}
                  aria-label={item.label}
                >
                  <item.icon size={17} aria-hidden="true" />
                  <span>{item.label}</span>
                  {item.showBadge && pendingCount > 0 && (
                    <span className="nav-badge" aria-label={`${pendingCount} pending incidents`}>
                      {pendingCount > 9 ? '9+' : pendingCount}
                    </span>
                  )}
                </NavLink>
              </motion.div>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        {/* Backend health */}
        <div className="health-indicator">
          <span className={`health-dot${online ? ' online' : ''}`} aria-hidden="true" />
          <span>{online ? 'Backend Online' : 'Backend Offline'}</span>
        </div>
        {/* WebSocket status */}
        <div style={{ marginTop: 8 }}>
          <ConnectionStatus />
        </div>
      </div>
    </aside>
  );
}
