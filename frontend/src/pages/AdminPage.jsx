import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { resetData, getCollegeProfile, updateCollegeProfile } from '../services/api';

// ── Confirm Modal ──────────────────────────────────────────
function ConfirmModal({ onConfirm, onCancel }) {
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-icon">⚠️</div>
        <h3>Reset All Data?</h3>
        <p>
          This will permanently delete <strong>ALL activity records</strong> and{' '}
          <strong>ALL human population records</strong> from the database.
        </p>
        <p className="modal-warning">This action cannot be undone.</p>
        <div className="modal-actions">
          <button className="btn-modal-cancel" onClick={onCancel}>Cancel</button>
          <button className="btn-modal-confirm" onClick={onConfirm}>
            Yes, Reset Everything
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Status Banner ──────────────────────────────────────────
function StatusBanner({ msg, onClose }) {
  if (!msg) return null;
  return (
    <div className={`status-banner ${msg.type}`}>
      <span>{msg.type === 'success' ? '✅' : '❌'} {msg.text}</span>
      <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', fontSize: 18 }}>×</button>
    </div>
  );
}

// ── Main Admin Page ────────────────────────────────────────
export default function AdminPage() {
  const { isAuthenticated, user } = useAuth();
  const navigate = useNavigate();

  const [showModal, setShowModal] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const [profileLoading, setProfileLoading] = useState(false);
  const [msg, setMsg] = useState(null);

  const [profile, setProfile] = useState({
    college_name: '',
    tagline: '',
    address: '',
    contact_email: '',
    contact_phone: '',
    website: '',
    logo_emoji: '🏫',
    established_year: '',
  });

  useEffect(() => {
    if (!isAuthenticated) { navigate('/login'); return; }
    loadProfile();
  }, [isAuthenticated]);

  const loadProfile = async () => {
    try {
      const res = await getCollegeProfile();
      setProfile(res.data);
    } catch (e) {
      console.error('Failed to load college profile', e);
    }
  };

  const showMsg = (type, text) => {
    setMsg({ type, text });
    setTimeout(() => setMsg(null), 5000);
  };

  // ── Reset Handler ──
  const handleReset = async () => {
    setShowModal(false);
    setResetLoading(true);
    try {
      const res = await resetData();
      showMsg('success', res.data.message);
    } catch (e) {
      showMsg('error', e.response?.data?.error || 'Failed to reset data.');
    } finally {
      setResetLoading(false);
    }
  };

  // ── Profile Save ──
  const handleProfileChange = (e) => {
    setProfile(p => ({ ...p, [e.target.name]: e.target.value }));
  };

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setProfileLoading(true);
    try {
      const res = await updateCollegeProfile(profile);
      setProfile(res.data.data);
      showMsg('success', 'College details updated successfully! Dashboard will show the new info.');
    } catch (e) {
      const errData = e.response?.data?.error;
      showMsg('error', typeof errData === 'object' ? JSON.stringify(errData) : (errData || 'Failed to save.'));
    } finally {
      setProfileLoading(false);
    }
  };

  if (!isAuthenticated) return null;

  return (
    <div className="admin-page">
      {showModal && (
        <ConfirmModal
          onConfirm={handleReset}
          onCancel={() => setShowModal(false)}
        />
      )}

      <div className="page-header">
        <h2>⚙️ Admin Panel</h2>
        <p className="page-subtitle">Logged in as <strong>{user?.username}</strong></p>
      </div>

      <StatusBanner msg={msg} onClose={() => setMsg(null)} />

      {/* ── Section 1: College Identity ── */}
      <div className="admin-card">
        <div className="admin-card-header">
          <div className="admin-card-icon">🏫</div>
          <div>
            <h3>College Identity</h3>
            <p>These details are publicly displayed on the main dashboard header.</p>
          </div>
        </div>

        <form onSubmit={handleProfileSave}>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="logo_emoji">Logo Emoji</label>
              <input id="logo_emoji" name="logo_emoji" type="text" value={profile.logo_emoji} onChange={handleProfileChange} placeholder="🏫" maxLength={4} />
            </div>
            <div className="form-group">
              <label htmlFor="established_year">Established Year</label>
              <input id="established_year" name="established_year" type="text" value={profile.established_year} onChange={handleProfileChange} placeholder="e.g. 2001" />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="college_name">College Name *</label>
            <input id="college_name" name="college_name" type="text" value={profile.college_name} onChange={handleProfileChange} placeholder="e.g. Kalaignar Karunanidhi Institute of Technology" required />
          </div>

          <div className="form-group">
            <label htmlFor="tagline">Tagline / Mission</label>
            <input id="tagline" name="tagline" type="text" value={profile.tagline} onChange={handleProfileChange} placeholder="e.g. Supporting UN SDG 13: Climate Action" />
          </div>

          <div className="form-group">
            <label htmlFor="address">Address</label>
            <textarea
              id="address" name="address" value={profile.address} onChange={handleProfileChange}
              placeholder="Full address of the institution..."
              rows={3}
              style={{
                width: '100%', background: 'var(--bg-primary)', color: 'var(--text-primary)',
                border: '1px solid var(--border-color)', padding: '12px 16px', borderRadius: '10px',
                fontFamily: 'inherit', fontSize: '15px', resize: 'vertical',
              }}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="contact_email">Contact Email</label>
              <input id="contact_email" name="contact_email" type="email" value={profile.contact_email} onChange={handleProfileChange} placeholder="admin@college.edu" />
            </div>
            <div className="form-group">
              <label htmlFor="contact_phone">Contact Phone</label>
              <input id="contact_phone" name="contact_phone" type="text" value={profile.contact_phone} onChange={handleProfileChange} placeholder="+91 9XXXXXXXXX" />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="website">Website URL</label>
            <input id="website" name="website" type="url" value={profile.website} onChange={handleProfileChange} placeholder="https://www.college.edu" />
          </div>

          {/* Live Preview */}
          {profile.college_name && (
            <div className="profile-preview">
              <div className="preview-label">📱 Dashboard Preview</div>
              <div className="college-banner-preview">
                <span className="preview-emoji">{profile.logo_emoji || '🏫'}</span>
                <div>
                  <div className="preview-name">{profile.college_name}</div>
                  <div className="preview-tagline">{profile.tagline}</div>
                  {(profile.contact_email || profile.contact_phone) && (
                    <div className="preview-contacts">
                      {profile.contact_email && <span>✉️ {profile.contact_email}</span>}
                      {profile.contact_phone && <span>📞 {profile.contact_phone}</span>}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          <button type="submit" className="btn-primary" disabled={profileLoading} style={{ marginTop: 20 }}>
            {profileLoading ? (
              <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Saving...</>
            ) : (
              <><i className="fas fa-save" /> Save College Details</>
            )}
          </button>
        </form>
      </div>

      {/* ── Section 2: Danger Zone – Reset Data ── */}
      <div className="admin-card danger-zone">
        <div className="admin-card-header">
          <div className="admin-card-icon danger-icon">🗑️</div>
          <div>
            <h3>Danger Zone</h3>
            <p>Irreversible actions that affect all recorded data.</p>
          </div>
        </div>

        <div className="danger-action-row">
          <div>
            <h4>Reset All Emission Data</h4>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 4 }}>
              Permanently deletes all activity records and human population records from the database.
              The emission factors and your college profile will <strong>not</strong> be affected.
            </p>
          </div>
          <button
            className="btn-danger"
            onClick={() => setShowModal(true)}
            disabled={resetLoading}
          >
            {resetLoading ? (
              <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Resetting...</>
            ) : (
              <><i className="fas fa-trash-alt" /> Reset All Data</>
            )}
          </button>
        </div>
      </div>

      <footer className="footer">
        <p>© 2025 KIT — Supporting UN SDG 13: Climate Action</p>
      </footer>
    </div>
  );
}
