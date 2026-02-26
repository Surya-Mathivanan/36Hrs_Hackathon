import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useState, useEffect } from 'react';

export default function Sidebar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('sidebarCollapsed') === 'true');
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');

  useEffect(() => {
    document.body.classList.toggle('light-mode', theme === 'light');
  }, [theme]);

  const toggleSidebar = () => {
    const next = !collapsed;
    setCollapsed(next);
    localStorage.setItem('sidebarCollapsed', next);
    // Trigger chart resize
    setTimeout(() => window.dispatchEvent(new Event('resize')), 320);
  };

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('theme', next);
    setTimeout(() => window.dispatchEvent(new Event('resize')), 100);
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-brand">
        <i className="fas fa-leaf fa-2x" />
        <span className="brand-text">Carbon Footprint</span>
      </div>

      <button className="sidebar-toggle" onClick={toggleSidebar} title="Toggle sidebar">
        <i className={`fas ${collapsed ? 'fa-bars' : 'fa-bars'}`} />
      </button>

      <nav className="nav-menu">
        <Link to="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>
          <i className="fas fa-chart-line" />
          <span className="nav-text">Dashboard</span>
        </Link>

        {user ? (
          <>
            <Link to="/data-input" className={`nav-link ${isActive('/data-input') ? 'active' : ''}`}>
              <i className="fas fa-edit" />
              <span className="nav-text">Data Input</span>
            </Link>
            <Link to="/admin" className={`nav-link ${isActive('/admin') ? 'active' : ''}`}>
              <i className="fas fa-cog" />
              <span className="nav-text">Admin Panel</span>
            </Link>
            <button
              className="nav-link"
              style={{ background: 'none', border: 'none', cursor: 'pointer', width: '100%', textAlign: 'left' }}
              onClick={handleLogout}
            >
              <i className="fas fa-sign-out-alt" />
              <span className="nav-text">Logout ({user.username})</span>
            </button>
          </>
        ) : (
          <Link to="/login" className={`nav-link ${isActive('/login') ? 'active' : ''}`}>
            <i className="fas fa-user" />
            <span className="nav-text">Admin Login</span>
          </Link>
        )}
      </nav>

      <div className="toggle-container">
        <button className="theme-toggle-btn" onClick={toggleTheme}>
          <i className={`fas ${theme === 'dark' ? 'fa-sun' : 'fa-moon'}`} />
          <span className="nav-text">{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
        </button>
      </div>
    </aside>
  );
}
