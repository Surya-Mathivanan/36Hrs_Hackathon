import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { addActivityData, addHumanData, uploadCSV } from '../services/api';

const SOURCE_UNIT_MAP = {
  electricity: 'kWh',
  bus_diesel: 'Liters',
  canteen_lpg: 'kg',
  waste_landfill: 'kg',
};

const EMISSION_FACTORS = [
  { source: 'Electricity', unit: 'kWh', factor: '0.708 kg CO₂e/kWh' },
  { source: 'Bus Diesel', unit: 'Liters', factor: '2.68 kg CO₂e/Liter' },
  { source: 'Canteen LPG', unit: 'kg', factor: '2.93 kg CO₂e/kg' },
  { source: 'Waste (Landfill)', unit: 'kg', factor: '1.25 kg CO₂e/kg' },
];

function today() {
  return new Date().toISOString().split('T')[0];
}

function StatusMessage({ msg }) {
  if (!msg) return null;
  return (
    <div className={msg.type === 'success' ? 'success-message' : 'error-message'}>
      {msg.type === 'success' ? '✅ ' : '❌ '}
      {msg.text}
    </div>
  );
}

// ---- Activity Data Form ----
function ActivityForm() {
  const [form, setForm] = useState({ date: today(), source_type: '', raw_value: '', unit: '' });
  const [msg, setMsg] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSourceChange = (e) => {
    const src = e.target.value;
    setForm(f => ({ ...f, source_type: src, unit: SOURCE_UNIT_MAP[src] || '' }));
  };

  const handleChange = (e) => setForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMsg(null);
    try {
      await addActivityData({
        date: form.date,
        source_type: form.source_type,
        raw_value: parseFloat(form.raw_value),
        unit: form.unit,
      });
      setMsg({ type: 'success', text: 'Data added successfully!' });
      setForm({ date: today(), source_type: '', raw_value: '', unit: '' });
    } catch (err) {
      const errData = err.response?.data?.error;
      const text = typeof errData === 'object' ? JSON.stringify(errData) : (errData || 'Failed to add data.');
      setMsg({ type: 'error', text });
    } finally {
      setLoading(false);
      setTimeout(() => setMsg(null), 4000);
    }
  };

  return (
    <div className="input-card">
      <h3><i className="fas fa-plus-circle" style={{ color: 'var(--accent-green)', marginRight: 8 }} />Add Carbon Footprint Data</h3>
      <p>Enter daily consumption data for carbon footprint analysis</p>
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="date">Date *</label>
            <input id="date" type="date" name="date" value={form.date} onChange={handleChange} required />
          </div>
          <div className="form-group">
            <label htmlFor="source_type">Source Type *</label>
            <select id="source_type" name="source_type" value={form.source_type} onChange={handleSourceChange} required>
              <option value="">Select a source</option>
              <option value="electricity">Electricity</option>
              <option value="bus_diesel">Bus Diesel</option>
              <option value="canteen_lpg">Canteen LPG</option>
              <option value="waste_landfill">Waste (Landfill)</option>
            </select>
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="raw_value">Raw Value *</label>
            <input id="raw_value" type="number" name="raw_value" value={form.raw_value} onChange={handleChange} step="0.01" min="0.01" required placeholder="e.g., 12000" />
          </div>
          <div className="form-group">
            <label htmlFor="unit">Unit</label>
            <input id="unit" type="text" name="unit" value={form.unit} readOnly placeholder="Auto-set by source type" style={{ cursor: 'default', opacity: 0.8 }} />
          </div>
        </div>
        <StatusMessage msg={msg} />
        <button type="submit" className="btn-primary" disabled={loading} style={{ marginTop: 16 }}>
          {loading ? <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2, marginRight: 8 }} />Adding...</> : <><i className="fas fa-plus" /> Add Data</>}
        </button>
      </form>
    </div>
  );
}

// ---- Human Population Form ----
function HumanDataForm() {
  const [form, setForm] = useState({ date: today(), student_count: '', staff_count: '' });
  const [msg, setMsg] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastResult, setLastResult] = useState(null);

  const handleChange = (e) => setForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMsg(null);
    setLastResult(null);
    try {
      const res = await addHumanData({
        date: form.date,
        student_count: parseInt(form.student_count),
        staff_count: parseInt(form.staff_count),
      });
      setMsg({ type: 'success', text: res.data.message });
      setLastResult(res.data);
      setForm({ date: today(), student_count: '', staff_count: '' });
    } catch (err) {
      const errData = err.response?.data?.error;
      const text = typeof errData === 'object' ? JSON.stringify(errData) : (errData || 'Failed to add population data.');
      setMsg({ type: 'error', text });
    } finally {
      setLoading(false);
      setTimeout(() => { setMsg(null); setLastResult(null); }, 6000);
    }
  };

  return (
    <div className="input-card human-input-card">
      <h3><i className="fas fa-users" style={{ marginRight: 8 }} />Campus Population Data (CORE FEATURE)</h3>
      <p style={{ color: '#e4e6eb' }}>Enter daily student and staff count — the main source of campus CO₂ emissions</p>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="human_date">Date *</label>
          <input id="human_date" type="date" name="date" value={form.date} onChange={handleChange} required />
        </div>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="student_count">Student Count *</label>
            <input id="student_count" type="number" name="student_count" value={form.student_count} onChange={handleChange} min="0" required placeholder="e.g., 5000" />
          </div>
          <div className="form-group">
            <label htmlFor="staff_count">Staff Count *</label>
            <input id="staff_count" type="number" name="staff_count" value={form.staff_count} onChange={handleChange} min="0" required placeholder="e.g., 500" />
          </div>
        </div>

        {msg && (
          <div className={msg.type === 'success' ? 'success-message' : 'error-message'}>
            {msg.type === 'success' ? '✅ ' : '❌ '}{msg.text}
            {lastResult && (
              <div style={{ marginTop: 10, padding: 12, background: 'rgba(0,212,170,0.1)', borderRadius: 6 }}>
                <strong>📊 This Day:</strong><br />
                Population: {lastResult.data?.total_count} people |&nbsp;
                CO₂: {lastResult.data?.this_day_emissions_tonnes} tonnes<br />
                <hr style={{ margin: '8px 0', borderColor: 'rgba(0,212,170,0.3)' }} />
                <strong>🌍 Cumulative:</strong> {lastResult.cumulative_stats?.total_emissions_tonnes} tonnes |&nbsp;
                {lastResult.cumulative_stats?.total_records} days recorded
              </div>
            )}
          </div>
        )}

        <button type="submit" className="btn-primary" disabled={loading} style={{ marginTop: 16, background: '#00d4aa', borderColor: '#00d4aa' }}>
          {loading ? <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2, marginRight: 8 }} />Saving...</> : <><i className="fas fa-user-plus" /> Add Population Data</>}
        </button>
      </form>
      <div style={{ marginTop: 16, padding: 12, background: 'rgba(0,212,170,0.1)', borderRadius: 8, fontSize: 13, color: '#e4e6eb' }}>
        <i className="fas fa-info-circle" /> <strong>Human CO₂ Emission Factor:</strong> 1.0 kg CO₂e per person per day<br />
        <small>Accounts for human respiration and metabolic processes during campus presence.</small>
      </div>
    </div>
  );
}

// ---- CSV Upload ----
function CSVUpload() {
  const [msg, setMsg] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const processFile = async (file) => {
    setMsg(null);
    if (!file) return;

    const text = await file.text();
    const lines = text.split(/\r?\n/).filter(l => l.trim());
    if (lines.length < 2) { setMsg({ type: 'error', text: 'CSV must have a header row and at least one data row.' }); return; }

    const header = lines[0].trim().toLowerCase();
    if (header !== 'date,source_type,raw_value,unit') {
      setMsg({ type: 'error', text: 'Invalid CSV header. Expected: date,source_type,raw_value,unit' });
      return;
    }

    const records = [];
    for (let i = 1; i < lines.length; i++) {
      const cols = lines[i].split(',').map(c => c.trim().replace(/"/g, ''));
      if (cols.length !== 4) { setMsg({ type: 'error', text: `Invalid row at line ${i + 1}.` }); return; }
      const [date, source_type, raw_value, unit] = cols;
      const val = parseFloat(raw_value);
      if (!date || !source_type || isNaN(val) || !unit) { setMsg({ type: 'error', text: `Invalid data at line ${i + 1}.` }); return; }
      records.push({ date, source_type, raw_value: val, unit });
    }

    setLoading(true);
    try {
      const res = await uploadCSV(records);
      setMsg({ type: 'success', text: res.data.message || `${records.length} records uploaded.` });
    } catch (err) {
      setMsg({ type: 'error', text: err.response?.data?.error || 'Upload failed.' });
    } finally {
      setLoading(false);
      setTimeout(() => setMsg(null), 5000);
    }
  };

  return (
    <div className="input-card">
      <h3><i className="fas fa-file-csv" style={{ marginRight: 8 }} />CSV Bulk Upload (Admin)</h3>
      <p>Upload a CSV file to insert multiple activity records at once.</p>

      <label
        className={`csv-upload-area ${dragOver ? 'drag-over' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); processFile(e.dataTransfer.files[0]); }}
      >
        <i className="fas fa-cloud-upload-alt" />
        <span>{loading ? 'Uploading...' : 'Drop your CSV file here or click to browse'}</span>
        <input type="file" accept=".csv" onChange={(e) => processFile(e.target.files[0])} disabled={loading} />
      </label>

      <StatusMessage msg={msg} />

      <div style={{ marginTop: 20 }}>
        <h4 style={{ marginBottom: 12 }}><i className="fas fa-info-circle" /> CSV Format Template</h4>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 10 }}>
          Required columns: <code>date,source_type,raw_value,unit</code>
        </p>
        <table className="emission-table">
          <thead>
            <tr><th>Date</th><th>Source Type</th><th>Raw Value</th><th>Unit</th></tr>
          </thead>
          <tbody>
            <tr><td>2025-06-15</td><td>electricity</td><td>130000</td><td>kWh</td></tr>
            <tr><td>2025-06-15</td><td>bus_diesel</td><td>5500</td><td>Liters</td></tr>
            <tr><td>2025-06-15</td><td>canteen_lpg</td><td>850</td><td>kg</td></tr>
            <tr><td>2025-06-15</td><td>waste_landfill</td><td>2300</td><td>kg</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---- Main Page ----
export default function DataInputPage() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) navigate('/login');
  }, [isAuthenticated, navigate]);

  if (!isAuthenticated) return null;

  return (
    <div className="data-input-page">
      <div className="page-header">
        <h2>Add Carbon Footprint Data</h2>
        <p className="page-subtitle">Enter daily consumption data for carbon footprint analysis</p>
      </div>

      <ActivityForm />
      <HumanDataForm />

      {/* Emission Factors Reference */}
      <div className="info-card">
        <h3>Emission Factors Reference</h3>
        <table className="emission-table">
          <thead>
            <tr><th>Source Type</th><th>Unit</th><th>Emission Factor</th></tr>
          </thead>
          <tbody>
            {EMISSION_FACTORS.map(ef => (
              <tr key={ef.source}>
                <td>{ef.source}</td>
                <td>{ef.unit}</td>
                <td>{ef.factor}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <CSVUpload />

      <footer className="footer">
        <p>© 2025 KIT - Supporting UN SDG 13: Climate Action</p>
      </footer>
    </div>
  );
}
