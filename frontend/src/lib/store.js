/**
 * Zustand Store — Global state for auth, equipment, alerts
 */

import { create } from "zustand";
import { authAPI, equipmentAPI, alertAPI, analyticsAPI } from "./api";

// ─── Auth Store ───
export const useAuthStore = create((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  initialize: async () => {
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (!token) {
      set({ isLoading: false, isAuthenticated: false });
      return;
    }
    try {
      const { data } = await authAPI.me();
      set({ user: data, isAuthenticated: true, isLoading: false });
    } catch {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  login: async (email, password) => {
    const { data } = await authAPI.login(email, password);
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    const me = await authAPI.me();
    set({ user: me.data, isAuthenticated: true });
    return me.data;
  },

  logout: () => {
    authAPI.logout();
    set({ user: null, isAuthenticated: false });
  },
}));

// ─── Dashboard Store ───
export const useDashboardStore = create((set) => ({
  summary: null,
  riskTrends: [],
  loading: false,
  error: null,

  fetchDashboard: async () => {
    set({ loading: true, error: null });
    try {
      const { data } = await analyticsAPI.dashboard();
      set({ summary: data, loading: false });
    } catch (err) {
      set({ error: err.message, loading: false });
    }
  },

  fetchRiskTrends: async (days = 7) => {
    try {
      const { data } = await analyticsAPI.riskTrends({ hours: days * 24 });
      set({ riskTrends: data });
    } catch (err) {
      console.error("Failed to fetch risk trends:", err);
    }
  },
}));

// ─── Equipment Store ───
export const useEquipmentStore = create((set) => ({
  equipment: [],
  total: 0,
  loading: false,
  error: null,

  fetchEquipment: async (params = {}) => {
    set({ loading: true, error: null });
    try {
      const { data } = await equipmentAPI.list({ page_size: 100, ...params });
      set({ equipment: data.items || data, total: data.total || 0, loading: false });
    } catch (err) {
      set({ error: err.message, loading: false });
    }
  },
}));

// ─── Alert Store ───
export const useAlertStore = create((set) => ({
  alerts: [],
  activeAlerts: [],
  loading: false,

  fetchAlerts: async (params = {}) => {
    set({ loading: true });
    try {
      const { data } = await alertAPI.list({ page_size: 100, ...params });
      set({ alerts: data.items || data, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  fetchActiveAlerts: async () => {
    try {
      const { data } = await alertAPI.active();
      set({ activeAlerts: data });
    } catch {
      // ignore
    }
  },

  acknowledgeAlert: async (id) => {
    try {
      await alertAPI.acknowledge(id);
      set((state) => ({
        alerts: state.alerts.map((a) =>
          a.id === id ? { ...a, status: "acknowledged" } : a
        ),
        activeAlerts: state.activeAlerts.map((a) =>
          a.id === id ? { ...a, status: "acknowledged" } : a
        ),
      }));
    } catch (err) {
      console.error("Failed to acknowledge alert:", err);
      throw err;
    }
  },

  resolveAlert: async (id, notes) => {
    try {
      await alertAPI.resolve(id, notes);
      set((state) => ({
        alerts: state.alerts.map((a) =>
          a.id === id ? { ...a, status: "resolved" } : a
        ),
        activeAlerts: state.activeAlerts.filter((a) => a.id !== id),
      }));
    } catch (err) {
      console.error("Failed to resolve alert:", err);
      throw err;
    }
  },
}));
