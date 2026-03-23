/**
 * API Client for Predictive Maintenance Platform
 *
 * Axios-based client with JWT auth, token refresh, and interceptors.
 */

import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// ─── Token helpers ───
function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

function getRefreshToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("refresh_token");
}

function setTokens(access, refresh) {
  localStorage.setItem("access_token", access);
  if (refresh) localStorage.setItem("refresh_token", refresh);
}

function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
}

// ─── Request interceptor: attach JWT ───
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response interceptor: refresh on 401 ───
let isRefreshing = false;
let failedQueue = [];

function processQueue(error, token) {
  failedQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token)));
  failedQueue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refresh = getRefreshToken();
        if (!refresh) throw new Error("No refresh token");

        const { data } = await axios.post(`${API_BASE}/api/v1/auth/refresh`, {
          refresh_token: refresh,
        });

        setTokens(data.access_token, data.refresh_token);
        processQueue(null, data.access_token);
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return api(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        clearTokens();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ═════════════════════════════════════════
// Auth
// ═════════════════════════════════════════
export const authAPI = {
  login: (email, password) =>
    api.post("/auth/login", { email, password }),

  register: (data) =>
    api.post("/auth/register", data),

  me: () => api.get("/auth/me"),

  refresh: (refreshToken) =>
    api.post("/auth/refresh", { refresh_token: refreshToken }),

  logout: () => {
    // Best-effort server-side token revocation before clearing local tokens
    api.post("/auth/logout").catch(() => {});
    clearTokens();
  },
};

// ═════════════════════════════════════════
// Equipment
// ═════════════════════════════════════════
export const equipmentAPI = {
  list: (params = {}) =>
    api.get("/equipment", { params }),

  get: (id) =>
    api.get(`/equipment/${id}`),

  create: (data) =>
    api.post("/equipment", data),

  update: (id, data) =>
    api.put(`/equipment/${id}`, data),

  delete: (id) =>
    api.delete(`/equipment/${id}`),
};

// ═════════════════════════════════════════
// Sensors
// ═════════════════════════════════════════
export const sensorAPI = {
  ingest: (data) =>
    api.post("/sensors/readings", data),

  ingestBatch: (readings) =>
    api.post("/sensors/readings/batch", { readings }),

  query: (equipmentId, params = {}) =>
    api.get("/sensors/readings", { params: { equipment_id: equipmentId, ...params } }),

  latest: (equipmentId) =>
    api.get(`/sensors/latest/${equipmentId}`),
};

// ═════════════════════════════════════════
// Predictions
// ═════════════════════════════════════════
export const predictionAPI = {
  predict: (equipmentId, sensorData = {}) =>
    api.post("/predictions/predict", { equipment_id: equipmentId, ...sensorData }),

  history: (equipmentId, params = {}) =>
    api.get(`/predictions/history/${equipmentId}`, { params }),

  latest: (equipmentId) =>
    api.get(`/predictions/latest/${equipmentId}`),
};

// ═════════════════════════════════════════
// Alerts
// ═════════════════════════════════════════
export const alertAPI = {
  list: (params = {}) =>
    api.get("/alerts", { params }),

  active: () =>
    api.get("/alerts/active"),

  get: (id) =>
    api.get(`/alerts/${id}`),

  acknowledge: (id) =>
    api.put(`/alerts/${id}`, { status: "acknowledged" }),

  resolve: (id, notes) =>
    api.put(`/alerts/${id}`, { status: "resolved", resolution_notes: notes }),
};

// ═════════════════════════════════════════
// Analytics
// ═════════════════════════════════════════
export const analyticsAPI = {
  dashboard: () =>
    api.get("/analytics/dashboard"),

  equipmentHealth: () =>
    api.get("/analytics/equipment-health"),

  riskTrends: (params = {}) =>
    api.get("/analytics/trends", { params }),

  systemHealth: () =>
    axios.get(`${API_BASE}/health`, { timeout: 10000 }),
};

// ═════════════════════════════════════════
// ML Admin
// ═════════════════════════════════════════
export const mlAdminAPI = {
  train: (algorithm) =>
    api.post("/ml/train", { algorithm }),

  trainAll: () =>
    api.post("/ml/train-all"),

  listModels: () =>
    api.get("/ml/models"),

  loadModel: (modelPath) =>
    api.post("/ml/models/load", { model_path: modelPath }),

  activeModel: () =>
    api.get("/ml/models/active"),

  backtest: (modelId) =>
    api.post(`/ml/models/${modelId}/backtest`),
};

// ═════════════════════════════════════════
// Maintenance
// ═════════════════════════════════════════
export const maintenanceAPI = {
  list: (params = {}) => api.get("/maintenance", { params }),
  get: (id) => api.get(`/maintenance/${id}`),
  create: (data) => api.post("/maintenance", data),
  update: (id, data) => api.put(`/maintenance/${id}`, data),
  delete: (id) => api.delete(`/maintenance/${id}`),
};

// ═════════════════════════════════════════
// User Management (Admin)
// ═════════════════════════════════════════
export const userAPI = {
  list: () =>
    api.get("/users"),

  get: (id) =>
    api.get(`/users/${id}`),

  updateRole: (id, role) =>
    api.put(`/users/${id}/role`, { role }),

  updateStatus: (id, isActive) =>
    api.put(`/users/${id}/status`, { is_active: isActive }),
};

// ═════════════════════════════════════════
// WebSocket for real-time sensor data
// ═════════════════════════════════════════
export function createSensorWebSocket(onMessage, onError) {
  const wsBase = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  let ws = null;
  let reconnectTimer = null;
  let reconnectDelay = 1000; // start at 1s, exponential backoff up to 30s
  let disposed = false;

  function connect() {
    if (disposed) return;
    // Re-read token on each connect attempt so reconnects use a refreshed token
    const currentToken = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    const url = currentToken
      ? `${wsBase}/ws/sensors?token=${encodeURIComponent(currentToken)}`
      : `${wsBase}/ws/sensors`;
    ws = new WebSocket(url);

    ws.onopen = () => {
      console.log("[WS] Connected to sensor stream");
      reconnectDelay = 1000; // reset on success
    };
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.error("[WS] Parse error:", e);
      }
    };
    ws.onerror = (err) => {
      console.error("[WS] Error:", err);
      if (onError) onError(err);
    };
    ws.onclose = () => {
      console.log("[WS] Disconnected");
      if (!disposed) {
        reconnectTimer = setTimeout(() => {
          console.log(`[WS] Reconnecting in ${reconnectDelay}ms…`);
          reconnectDelay = Math.min(reconnectDelay * 2, 30000);
          connect();
        }, reconnectDelay);
      }
    };
  }

  connect();

  // Return an object with a .close() that also stops reconnection
  return {
    close() {
      disposed = true;
      clearTimeout(reconnectTimer);
      if (ws) {
        if (ws.readyState === WebSocket.CONNECTING) {
          // Delay closure until it opens to prevent "WebSocket is closed before the connection is established" error in React Strict Mode.
          ws.onopen = () => ws.close();
        } else if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      }
    },
  };
}

export default api;
