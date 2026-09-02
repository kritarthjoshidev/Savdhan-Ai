import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart3, PieChart as PieChartIcon, TrendingUp, Clock,
  Camera, ShieldCheck, AlertTriangle, Activity,
  Database, Server, HardDrive, Cpu, Radio, Layers,
} from 'lucide-react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  AreaChart, Area, Legend,
} from 'recharts';
import { listIncidents, listModels, checkHealth } from '../utils/api';

const COLORS = ['#a78bfa', '#10b981', '#ef4444', '#f59e0b', '#3b82f6', '#06b6d4'];

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

// Infrastructure services from docker-compose
const INFRA_SERVICES = [
  { name: 'FastAPI', port: '8000', icon: '⚡', color: '#06b6d4' },
  { name: 'PostgreSQL', port: '5432', icon: '🐘', color: '#3b82f6' },
  { name: 'Redis', port: '6379', icon: '🔴', color: '#ef4444' },
  { name: 'MinIO', port: '9000', icon: '📦', color: '#f59e0b' },
  { name: 'MLflow', port: '5000', icon: '🧪', color: '#a78bfa' },
  { name: 'Celery', port: '—', icon: '🌿', color: '#10b981' },
];

export default function Analytics() {
  const [incidents, setIncidents] = useState([]);
  const [models, setModels] = useState([]);
  const [backendOk, setBackendOk] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        await checkHealth();
        setBackendOk(true);
        const incData = await listIncidents({ limit: 200, hours: 168 });
        setIncidents(Array.isArray(incData) ? incData : incData.incidents || []);
        const modData = await listModels();
        setModels(Array.isArray(modData) ? modData : []);
      } catch {
        setBackendOk(false);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // Status distribution (Pie chart)
  const statusCounts = {};
  incidents.forEach((i) => {
    statusCounts[i.status] = (statusCounts[i.status] || 0) + 1;
  });
  const statusPieData = Object.entries(statusCounts).map(([name, value]) => ({ name, value }));

  // Camera distribution (Bar chart)
  const camCounts = {};
  incidents.forEach((i) => {
    camCounts[i.source_cam] = (camCounts[i.source_cam] || 0) + 1;
  });
  const camBarData = Object.entries(camCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([cam, count]) => ({ cam, count }));

  // Daily trend (Area chart)
  const dailyCounts = {};
  incidents.forEach((inc) => {
    const d = new Date(inc.timestamp || inc.created_at);
    const key = `${d.getMonth() + 1}/${d.getDate()}`;
    dailyCounts[key] = (dailyCounts[key] || 0) + 1;
  });
  const dailyData = Object.entries(dailyCounts).map(([day, count]) => ({ day, count }));

  // Confidence distribution
  const confBuckets = { '90-100%': 0, '80-90%': 0, '70-80%': 0, '60-70%': 0, '<60%': 0 };
  incidents.forEach((i) => {
    const c = i.confidence * 100;
    if (c >= 90) confBuckets['90-100%']++;
    else if (c >= 80) confBuckets['80-90%']++;
    else if (c >= 70) confBuckets['70-80%']++;
    else if (c >= 60) confBuckets['60-70%']++;
    else confBuckets['<60%']++;
  });
  const confData = Object.entries(confBuckets).map(([range, count]) => ({ range, count }));

  // Model stats
  const prodModels = models.filter((m) => m.status === 'production').length;
  const candidateModels = models.filter((m) => m.status === 'candidate').length;

  const totalIncidents = incidents.length;
  const avgConfidence = incidents.length > 0
    ? (incidents.reduce((s, i) => s + i.confidence, 0) / incidents.length * 100).toFixed(1)
    : '0';

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div style={{
        background: '#1a2340',
        border: '1px solid rgba(148,163,184,0.15)',
        borderRadius: 8,
        padding: '8px 12px',
        fontSize: '0.78rem',
        color: '#f1f5f9',
      }}>
        <p style={{ fontWeight: 600 }}>{label || payload[0].name}</p>
        <p style={{ color: '#06b6d4' }}>{payload[0].value}</p>
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
    >
      <div className="page-header">
        <h1>Analytics & Infrastructure</h1>
        <p>Deep insights into surveillance data and system health</p>
      </div>

      {/* Summary stats */}
      <motion.div
        className="stats-grid"
        variants={containerVariants}
        initial="hidden"
        animate="show"
      >
        {[
          { icon: AlertTriangle, color: 'cyan', label: 'Total Incidents (7d)', value: totalIncidents },
          { icon: ShieldCheck, color: 'green', label: 'Avg Confidence', value: `${avgConfidence}%` },
          { icon: Camera, color: 'purple', label: 'Active Cameras', value: Object.keys(camCounts).length },
          { icon: Layers, color: 'blue', label: 'Models', value: `${prodModels} prod / ${candidateModels} candidate` },
        ].map((s, i) => (
          <motion.div className="stat-card" key={i} variants={itemVariants}>
            <div className={`stat-icon ${s.color}`}><s.icon size={20} /></div>
            <div className="stat-info">
              <div className="stat-label">{s.label}</div>
              <div className="stat-value">{loading ? '—' : s.value}</div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Charts Row 1 */}
      <motion.div
        className="analytics-grid mb-2"
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        {/* Daily trend */}
        <div className="card">
          <div className="section-title">
            <h2><TrendingUp size={16} style={{ marginRight: 8, verticalAlign: 'middle' }} />Daily Incident Trend</h2>
          </div>
          <div className="chart-container">
            {dailyData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={dailyData}>
                  <defs>
                    <linearGradient id="grad1" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.4} />
                      <stop offset="100%" stopColor="#06b6d4" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(148,163,184,0.06)" />
                  <XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={{ stroke: 'rgba(148,163,184,0.1)' }} />
                  <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={{ stroke: 'rgba(148,163,184,0.1)' }} allowDecimals={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="count" stroke="#06b6d4" strokeWidth={2} fill="url(#grad1)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state"><Activity size={36} /><h3>No data yet</h3></div>
            )}
          </div>
        </div>

        {/* Status Pie */}
        <div className="card">
          <div className="section-title">
            <h2><PieChartIcon size={16} style={{ marginRight: 8, verticalAlign: 'middle' }} />Status Distribution</h2>
          </div>
          <div className="chart-container" style={{ height: 260 }}>
            {statusPieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statusPieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    dataKey="value"
                    paddingAngle={3}
                    stroke="none"
                  >
                    {statusPieData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend
                    formatter={(value) => <span style={{ color: '#94a3b8', fontSize: '0.75rem', textTransform: 'capitalize' }}>{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state"><PieChartIcon size={36} /><h3>No data</h3></div>
            )}
          </div>
        </div>
      </motion.div>

      {/* Charts Row 2 */}
      <motion.div
        className="grid-2 mb-2"
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.35 }}
      >
        {/* Camera Bar Chart */}
        <div className="card">
          <div className="section-title">
            <h2><Camera size={16} style={{ marginRight: 8, verticalAlign: 'middle' }} />Incidents by Camera</h2>
          </div>
          <div className="chart-container">
            {camBarData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={camBarData} layout="vertical">
                  <CartesianGrid stroke="rgba(148,163,184,0.06)" horizontal={false} />
                  <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={{ stroke: 'rgba(148,163,184,0.1)' }} />
                  <YAxis type="category" dataKey="cam" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={{ stroke: 'rgba(148,163,184,0.1)' }} width={80} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={18} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state"><BarChart3 size={36} /><h3>No data</h3></div>
            )}
          </div>
        </div>

        {/* Confidence Distribution */}
        <div className="card">
          <div className="section-title">
            <h2><ShieldCheck size={16} style={{ marginRight: 8, verticalAlign: 'middle' }} />Confidence Distribution</h2>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={confData}>
                <CartesianGrid stroke="rgba(148,163,184,0.06)" />
                <XAxis dataKey="range" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={{ stroke: 'rgba(148,163,184,0.1)' }} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={{ stroke: 'rgba(148,163,184,0.1)' }} allowDecimals={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]} barSize={30}>
                  {confData.map((_, i) => (
                    <Cell key={i} fill={['#10b981', '#22d3ee', '#3b82f6', '#f59e0b', '#ef4444'][i]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </motion.div>

      {/* Infrastructure Status */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <div className="section-title">
          <h2><Server size={16} style={{ marginRight: 8, verticalAlign: 'middle' }} />Infrastructure Services</h2>
          <span className={`badge ${backendOk ? 'online' : 'offline'}`}>
            <span className="badge-dot" />
            {backendOk ? 'Healthy' : 'Unreachable'}
          </span>
        </div>

        <div className="infra-grid">
          {INFRA_SERVICES.map((svc, i) => (
            <motion.div
              className="infra-card"
              key={svc.name}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.55 + i * 0.05 }}
              whileHover={{ scale: 1.04, y: -3 }}
            >
              <div
                className="infra-card-icon"
                style={{ background: `${svc.color}18`, fontSize: '1.3rem' }}
              >
                {svc.icon}
              </div>
              <div className="infra-card-name">{svc.name}</div>
              <div className="infra-card-port">:{svc.port}</div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}
