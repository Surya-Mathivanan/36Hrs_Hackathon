import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import DataInputPage from './pages/DataInputPage';
import AdminPage from './pages/AdminPage';
import './index.css';

function AppLayout({ children }) {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content" id="mainContent">
        {children}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Login has its own full-page layout (no sidebar) */}
          <Route path="/login" element={<LoginPage />} />

          {/* All other routes use sidebar layout */}
          <Route path="/" element={<AppLayout><DashboardPage /></AppLayout>} />
          <Route path="/data-input" element={<AppLayout><DataInputPage /></AppLayout>} />
          <Route path="/admin" element={<AppLayout><AdminPage /></AppLayout>} />

          {/* 404 fallback */}
          <Route path="*" element={
            <AppLayout>
              <div style={{ textAlign: 'center', padding: '80px 20px' }}>
                <div style={{ fontSize: 64, marginBottom: 16 }}>🍃</div>
                <h2>Page Not Found</h2>
                <p style={{ color: 'var(--text-secondary)', marginTop: 8 }}>The page you're looking for doesn't exist.</p>
                <a href="/" style={{ color: 'var(--accent-green)', marginTop: 20, display: 'inline-block' }}>← Go to Dashboard</a>
              </div>
            </AppLayout>
          } />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
