import axios from 'axios';

// Determine and normalize API Base URL
let rawBase = (import.meta.env.VITE_API_URL || '').trim();

if (!rawBase) {
  rawBase = typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000/api'
    : '/api';
}

// Remove trailing slashes
rawBase = rawBase.replace(/\/+$/, '');

// Ensure /api suffix is present
if (!rawBase.endsWith('/api') && !rawBase.includes('/api/')) {
  rawBase = `${rawBase}/api`;
}

const API_BASE = rawBase;

// Origin without the trailing /api, used for building URLs to static assets (uploads)
export const API_ORIGIN = API_BASE.replace(/\/api\/?$/, '');

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;