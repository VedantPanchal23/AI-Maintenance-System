/**
 * Utility functions for the frontend
 */

import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind + clsx classes */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

/** Format date for display */
export function formatDate(dateStr) {
  if (!dateStr) return "N/A";
  return new Date(dateStr).toLocaleDateString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Format relative time */
export function timeAgo(dateStr) {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

/** Risk level → colour map */
export const riskColors = {
  critical: { bg: "bg-red-100", text: "text-red-800", ring: "ring-red-600/20" },
  high: { bg: "bg-orange-100", text: "text-orange-800", ring: "ring-orange-600/20" },
  medium: { bg: "bg-yellow-100", text: "text-yellow-800", ring: "ring-yellow-600/20" },
  low: { bg: "bg-green-100", text: "text-green-800", ring: "ring-green-600/20" },
};

/** Status → colour map */
export const statusColors = {
  operational: { bg: "bg-green-100", text: "text-green-800" },
  warning: { bg: "bg-yellow-100", text: "text-yellow-800" },
  critical: { bg: "bg-red-100", text: "text-red-800" },
  maintenance: { bg: "bg-blue-100", text: "text-blue-800" },
  offline: { bg: "bg-gray-100", text: "text-gray-800" },
};

/** Clamp a value between min and max */
export function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

/** Round to N decimal places */
export function round(value, decimals = 2) {
  return Number(Math.round(value + "e" + decimals) + "e-" + decimals);
}
