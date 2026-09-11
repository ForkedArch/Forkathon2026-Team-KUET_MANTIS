import axios from 'axios';

// Determine and normalize API Base URL
let rawBase = (import.meta.env.VITE_API_URL || '').trim();

const isCapacitor = typeof window !== 'undefined' && (
  Boolean(window.Capacitor) ||
  window.location.protocol === 'capacitor:' ||
  window.location.protocol === 'ionic:'
);

if (isCapacitor && (!rawBase || rawBase.includes('localhost') || rawBase.includes('127.0.0.1'))) {
  rawBase = 'https://forkathon2026-team-kuet-mantis-2.onrender.com/api';
} else if (!rawBase) {
  rawBase = typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000/api'
    : 'https://forkathon2026-team-kuet-mantis-2.onrender.com/api';
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
  timeout: 30000,
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

// Helper: sleep
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

api.interceptors.response.use(
  (response) => {
    // If a static host (like Vercel) rewrites an API route to index.html, it returns HTML with status 200
    if (
      typeof response.data === 'string' &&
      (response.data.trim().startsWith('<!DOCTYPE') || response.data.includes('<html'))
    ) {
      const errorMsg =
        'Backend API unreachable: The server returned index.html. Please ensure VITE_API_URL is configured in your deployment settings.';
      console.error(errorMsg);
      return Promise.reject(new Error(errorMsg));
    }
    return response;
  },
  async (error) => {
    const config = error.config;
    // Retry on 404 or 503 (Render cold-start) up to 3 times with 3s delay
    const status = error.response?.status;
    const isRetryable = status === 404 || status === 503 || !error.response;
    config._retryCount = config._retryCount || 0;

    if (isRetryable && config._retryCount < 3) {
      config._retryCount += 1;
      console.warn(
        `Backend may be waking up (attempt ${config._retryCount}/3). Retrying in 3s...`
      );
      await sleep(3000);
      return api(config);
    }

    // Friendly error for persistent 404 (wrong URL or backend down)
    if (status === 404) {
      return Promise.reject(
        new Error(
          'Backend server not reachable. It may still be starting up — please wait a moment and try again.'
        )
      );
    }
    return Promise.reject(error);
  }
);

export default api;