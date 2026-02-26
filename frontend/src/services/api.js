import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_URL}/auth/refresh/`, { refresh: refreshToken });
          localStorage.setItem('access_token', res.data.access);
          originalRequest.headers.Authorization = `Bearer ${res.data.access}`;
          return api(originalRequest);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('username');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// ---- Auth ----
export const login = (username, password) =>
  api.post('/auth/login/', { username, password });

export const getMe = () => api.get('/auth/me/');

// ---- Dashboard ----
export const getDashboardData = (startDate, endDate) =>
  api.get('/dashboard/', { params: { start_date: startDate, end_date: endDate } });

// ---- Recommendations ----
export const getRecommendations = () => api.get('/recommendations/');

// ---- Emission Factors ----
export const getEmissionFactors = () => api.get('/emission_factors/');

// ---- Activity Data ----
export const addActivityData = (data) => api.post('/data/', data);

export const uploadCSV = (records) => api.post('/upload_csv/', { records });

// ---- Human Population ----
export const addHumanData = (data) => api.post('/human_data/', data);

export const getHumanCumulativeStats = () => api.get('/human_cumulative_stats/');

// ---- Admin ----
export const resetData = () => api.delete('/admin/reset/');

// ---- College Profile ----
export const getCollegeProfile = () => api.get('/college_profile/');
export const updateCollegeProfile = (data) => api.patch('/college_profile/update/', data);

export default api;
