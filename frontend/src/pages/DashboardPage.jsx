import { useState, useEffect, useCallback } from 'react';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Title, Tooltip, Legend, Filler,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  getDashboardData, getRecommendations,
  getHumanCumulativeStats, getCollegeProfile,
} from '../services/api';
import Loader from '../components/Loader';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Title, Tooltip, Legend, Filler
);

// ── Helpers ────────────────────────────────────────────────
function getDateRange(days) {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - days);
  return {
    start: start.toISOString().split('T')[0],
    end:   end.toISOString().split('T')[0],
  };
}

function fmtLabel(key, raw) {
  if (key === 'date') {
    const d = new Date(raw);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }
  if (key === 'label') return `Week ${raw.split('-W')[1]}`;
  const [y, m] = raw.split('-');
  return new Date(y, m - 1).toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
}

// ── Chart colour scheme ────────────────────────────────────
const COLORS      = ['#00d4aa', '#4da6ff', '#ffaa55', '#ff5577'];
const gridColor   = 'rgba(255,255,255,0.05)';
const tickColor   = '#8899aa';
const legendColor = '#e8f0f7';

const baseScales = {
  x: { ticks: { color: tickColor }, grid: { color: gridColor } },
  y: { ticks: { color: tickColor }, grid: { color: gridColor }, beginAtZero: true },
};

const baseOpts = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { labels: { color: legendColor, font: { family: 'Outfit' } } } },
  scales: baseScales,
};

// ── Sub-components ─────────────────────────────────────────
function KpiCard({ icon, title, value, unit, accent }) {
  return (
    <div className={`kpi-card ${accent ? 'human-kpi-card' : ''}`}>
      <div className="kpi-icon">{icon}</div>
      <div className="kpi-content">
        <h3>{title}</h3>
        <p className="kpi-value">{value ?? '--'}</p>
        <p className="kpi-unit">{unit}</p>
      </div>
    </div>
  );
}

function CollegeBanner({ profile }) {
  if (!profile?.college_name || profile.college_name === 'KIT Campus') return null;
  return (
    <div className="college-banner">
      <div className="college-logo">{profile.logo_emoji || '🏫'}</div>
      <div className="college-info">
        <div className="college-name">
          {profile.college_name}
          {profile.established_year && (
            <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 10, fontWeight: 400 }}>
              Est. {profile.established_year}
            </span>
          )}
        </div>
        <div className="college-tagline">{profile.tagline}</div>
        <div className="college-contacts">
          {profile.address && <span>📍 {profile.address}</span>}
          {profile.contact_email && (
            <a href={`mailto:${profile.contact_email}`}>✉️ {profile.contact_email}</a>
          )}
          {profile.contact_phone && <span>📞 {profile.contact_phone}</span>}
          {profile.website && (
            <a href={profile.website} target="_blank" rel="noopener noreferrer">🌐 Website</a>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Redesigned Recommendation Card ────────────────────────
function RecCard({ rec }) {
  const [open, setOpen] = useState(false);
  const pri = rec.priority?.toLowerCase() || 'low';

  return (
    <div className="rec-card" onClick={() => setOpen(o => !o)}>
      <div className="rec-card-header">
        <div className={`rec-priority-bar priority-bar-${pri}`} />
        <div className="rec-card-body">
          <div className="rec-card-top">
            <span className="rec-card-title">{rec.title}</span>
            <div className="rec-badges">
              <span className={`rec-badge badge-${pri}`}>{rec.priority}</span>
              {rec.impact && (
                <span className="rec-badge badge-impact">{rec.impact}</span>
              )}
              {rec.actionable_steps?.length > 0 && (
                <span style={{ fontSize: 16, color: 'var(--text-muted)' }}>
                  {open ? '▲' : '▼'}
                </span>
              )}
            </div>
          </div>
          <p className="rec-description">{rec.description}</p>
          {!open && rec.actionable_steps?.length > 0 && (
            <p className="rec-toggle-hint">
              <span>⚡</span> Click to see {rec.actionable_steps.length} action steps
            </p>
          )}
        </div>
      </div>

      {open && rec.actionable_steps?.length > 0 && (
        <div className="rec-steps-panel" onClick={e => e.stopPropagation()}>
          <h5>🎯 Actionable Steps</h5>
          <ul className="steps-list">
            {rec.actionable_steps.map((s, i) => (
              <li key={i}>
                <span className="step-num">{i + 1}</span>
                <span>{s}</span>
              </li>
            ))}
          </ul>
          <div className="rec-meta-row">
            {rec.expected_reduction && (
              <span className="rec-meta-pill meta-green">📈 {rec.expected_reduction}</span>
            )}
            {rec.cost && (
              <span className="rec-meta-pill meta-orange">💰 {rec.cost}</span>
            )}
            {rec.timeframe && (
              <span className="rec-meta-pill meta-blue">⏱️ {rec.timeframe}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main Dashboard ─────────────────────────────────────────
export default function DashboardPage() {
  const [days, setDays]               = useState(365);
  const [dashData, setDashData]       = useState(null);
  const [recData, setRecData]         = useState(null);
  const [cumStats, setCumStats]       = useState(null);
  const [college, setCollege]         = useState(null);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState('');

  const fetchAll = useCallback(async (d) => {
    setLoading(true); setError('');
    try {
      const { start, end } = getDateRange(d);
      const [dash, rec, cum, col] = await Promise.all([
        getDashboardData(start, end),
        getRecommendations(),
        getHumanCumulativeStats(),
        getCollegeProfile(),
      ]);
      setDashData(dash.data);
      setRecData(rec.data);
      setCumStats(cum.data);
      setCollege(col.data);
    } catch (e) {
      setError('Cannot connect to the backend. Ensure Django server is running on port 8000.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(days); }, [days, fetchAll]);

  // ── Build trend data ──
  const buildTrend = () => {
    if (!dashData) return { labels: [], values: [] };
    let items, key;
    if      (days <= 7)  { items = dashData.daily_trend   || []; key = 'date'; }
    else if (days <= 90) { items = dashData.weekly_trend  || []; key = 'label'; }
    else                 { items = dashData.monthly_trend || []; key = 'month'; }
    return {
      labels: items.map(d => fmtLabel(key, d[key])),
      values: items.map(d => d.emissions),
    };
  };

  const { labels: tL, values: tV } = buildTrend();

  const trendChart = {
    labels: tL,
    datasets: [{
      label: 'Emissions (Tonnes CO₂e)',
      data: tV,
      borderColor: '#00d4aa',
      backgroundColor: 'rgba(0,212,170,0.08)',
      tension: 0.45, fill: true,
      pointRadius: days <= 7 ? 5 : 2,
      pointBackgroundColor: '#00d4aa',
    }],
  };

  const make = (items, key, label, color) => ({
    labels: items.map(d => d[key]?.toString()),
    datasets: [{ label, data: items.map(d => d.emissions), backgroundColor: color + 'bb', borderColor: color, borderWidth: 1 }],
  });

  const monthlyChart = make(dashData?.monthly_trend || [], 'month',  'Monthly (Tonnes CO₂e)', '#00d4aa');
  const yearlyChart  = make(dashData?.yearly_comparison || [], 'year', 'Yearly (Tonnes CO₂e)', '#4da6ff');
  const weeklyChart  = make(dashData?.weekly_comparison || [], 'label', 'Weekly (Tonnes CO₂e)', '#ffaa55');

  const donutChart = {
    labels: (dashData?.source_breakdown || []).map(d =>
      d.source.replace(/_/g, ' ').replace(/^./, c => c.toUpperCase())
    ),
    datasets: [{
      data: (dashData?.source_breakdown || []).map(d => d.emissions),
      backgroundColor: COLORS, borderColor: '#0d1320', borderWidth: 2,
    }],
  };

  const donutOpts = {
    responsive: true, maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom', labels: { color: legendColor, padding: 14 } },
      tooltip: {
        callbacks: {
          label: ctx => {
            const tot = ctx.dataset.data.reduce((a, b) => a + b, 0);
            return ` ${ctx.label}: ${ctx.parsed.toFixed(2)}t (${((ctx.parsed / tot) * 100).toFixed(1)}%)`;
          },
        },
      },
    },
  };

  const kpis    = dashData?.kpis || {};
  const human   = dashData?.human_emissions || {};
  const recs    = recData?.recommendations || [];
  const summary = recData?.summary || {};

  return (
    <div>
      {/* College Banner */}
      {college && <CollegeBanner profile={college} />}

      {/* Header */}
      <div className="dashboard-header">
        <h2>Carbon Emissions Dashboard</h2>
        <div className="date-selector">
          <label htmlFor="dateRange">Period:</label>
          <select id="dateRange" value={days} onChange={e => setDays(parseInt(e.target.value))}>
            <option value={7}>Last Week</option>
            <option value={30}>Last 30 Days</option>
            <option value={90}>Last 3 Months</option>
            <option value={180}>Last 6 Months</option>
            <option value={365}>Last Year</option>
          </select>
        </div>
      </div>

      {error && <div className="error-message" style={{ marginBottom: 24 }}>{error}</div>}

      {loading ? (
        <Loader label="Analysing" />
      ) : (
        <>
          {/* KPI Cards */}
          <div className="kpi-container">
            <KpiCard icon="📊" title="Total Emissions" value={kpis.total_emissions?.toFixed(2)} unit="Tonnes CO₂e" />
            <KpiCard
              icon="🎯" title="Biggest Source"
              value={(kpis.biggest_source || '—').replace(/_/g, ' ').replace(/^./, c => c.toUpperCase())}
              unit={`${kpis.biggest_source_percent ?? 0}% of total`}
            />
            <KpiCard icon="⚡" title="Energy Consumed" value={kpis.energy_saved?.toLocaleString()} unit="kWh" />
          </div>

          {/* Charts */}
          <div className="charts-container">
            <div className="chart-card chart-large">
              <h3>📈 Emissions Trend</h3>
              <div className="chart-wrapper"><Line data={trendChart} options={baseOpts} /></div>
            </div>
            <div className="chart-card">
              <h3>📅 Monthly Comparison</h3>
              <div className="chart-wrapper"><Bar data={monthlyChart} options={baseOpts} /></div>
            </div>
            <div className="chart-card">
              <h3>📆 Year-over-Year</h3>
              <div className="chart-wrapper"><Bar data={yearlyChart} options={baseOpts} /></div>
            </div>
            <div className="chart-card">
              <h3>📉 Weekly Comparison</h3>
              <div className="chart-wrapper"><Bar data={weeklyChart} options={baseOpts} /></div>
            </div>
            <div className="chart-card">
              <h3>🔘 Source Breakdown</h3>
              <div className="chart-wrapper"><Doughnut data={donutChart} options={donutOpts} /></div>
            </div>
          </div>

          {/* Human Emissions */}
          <div className="human-emissions-section">
            <div className="section-header">
              <span className="icon-large">👥</span>
              <div>
                <h2>Human CO₂ Emissions</h2>
                <p>Campus population direct carbon footprint — Core feature</p>
              </div>
            </div>
            <div className="kpi-container">
              <KpiCard accent icon="👥" title="Avg Total Population" value={human.avg_total_count ?? 0} unit="People/day on campus" />
              <KpiCard accent icon="🎓" title="Avg Students" value={human.avg_student_count ?? 0} unit="Students" />
              <KpiCard accent icon="👨‍🏫" title="Avg Staff" value={human.avg_staff_count ?? 0} unit="Staff members" />
            </div>
            <div className="cumulative-stats">
              <h3>📊 All-Time Cumulative Statistics</h3>
              <div className="stats-grid">
                <div className="stat-item">
                  <div className="stat-label">Total Emissions</div>
                  <div className="stat-value">{cumStats?.total_emissions?.toFixed(2) ?? '--'}</div>
                  <div className="stat-unit">tonnes CO₂</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">Days Recorded</div>
                  <div className="stat-value">{cumStats?.total_records ?? '--'}</div>
                  <div className="stat-unit">records</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">Avg Population</div>
                  <div className="stat-value">{cumStats?.average_population ?? '--'}</div>
                  <div className="stat-unit">people/day</div>
                </div>
              </div>
            </div>
          </div>

          {/* Redesigned Recommendations */}
          <div className="recommendations-section">
            <h3>🌱 Emission Reduction Recommendations</h3>

            {/* Summary stats */}
            <div className="rec-summary-grid">
              <div className="rec-summary-stat">
                <div className="stat-number stat-green">{summary.total_recommendations ?? 0}</div>
                <div className="stat-label">Total Recommendations</div>
              </div>
              <div className="rec-summary-stat">
                <div className="stat-number stat-red">{summary.high_priority ?? 0}</div>
                <div className="stat-label">High Priority</div>
              </div>
              <div className="rec-summary-stat">
                <div className="stat-number stat-blue">50–70%</div>
                <div className="stat-label">Potential Reduction</div>
              </div>
            </div>

            {summary.message && (
              <div className="rec-message-banner">
                <span>💡</span> {summary.message}
              </div>
            )}

            <div className="rec-list">
              {recs.map((rec, i) => <RecCard key={i} rec={rec} />)}
            </div>
          </div>
        </>
      )}

      <footer className="footer">
        <p>© 2025 KIT — Supporting UN SDG 13: Climate Action</p>
      </footer>
    </div>
  );
}
