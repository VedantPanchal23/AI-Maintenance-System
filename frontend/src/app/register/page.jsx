"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authAPI } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import Link from "next/link";
import {
  ShieldCheckIcon,
  ChartBarIcon,
  CpuChipIcon,
  BellAlertIcon,
  BoltIcon,
  ExclamationCircleIcon,
} from "@heroicons/react/24/outline";

const FEATURES = [
  { icon: ChartBarIcon, label: "Real-time Monitoring" },
  { icon: CpuChipIcon, label: "ML Predictions" },
  { icon: BellAlertIcon, label: "Automated Alerts" },
  { icon: BoltIcon, label: "GPU-Accelerated" },
];

export default function RegisterPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    organization_name: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const update = (field) => (e) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authAPI.register(form);
      // Auto-login after registration
      await login(form.email, form.password);
      router.push("/dashboard");
    } catch (err) {
      setError(
        err.response?.data?.error?.message ||
          err.response?.data?.detail ||
          "Registration failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Left — branding panel */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-slate-950 items-center justify-center p-16">
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-brand-600/20 via-brand-800/10 to-transparent" />
        <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-brand-500/10 blur-3xl" />
        <div className="absolute -bottom-32 -left-32 h-64 w-64 rounded-full bg-brand-400/10 blur-3xl" />

        <div className="relative max-w-md text-white z-10">
          <div className="flex items-center gap-3 mb-10">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-500 shadow-glow-blue">
              <ShieldCheckIcon className="h-7 w-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Predictive Maintenance</h1>
              <p className="text-sm text-brand-300">AI-Powered Platform</p>
            </div>
          </div>

          <p className="text-lg text-slate-300 leading-relaxed mb-10">
            Real-time equipment monitoring, ML-driven failure prediction,
            and proactive maintenance scheduling for pharmaceutical manufacturing.
          </p>

          <div className="grid grid-cols-2 gap-3">
            {FEATURES.map(({ icon: Icon, label }) => (
              <div
                key={label}
                className="flex items-center gap-2.5 rounded-xl bg-white/[0.06] border border-white/[0.08] px-3.5 py-2.5 text-sm text-slate-300"
              >
                <Icon className="h-4 w-4 text-brand-400 shrink-0" />
                {label}
              </div>
            ))}
          </div>

          <p className="mt-14 text-2xs text-slate-500 uppercase tracking-wider">
            Enterprise-grade predictive analytics
          </p>
        </div>
      </div>

      {/* Right — registration form */}
      <div className="flex flex-1 items-center justify-center bg-surface-50 p-8">
        <div className="w-full max-w-sm animate-fade-in">
          <div className="lg:hidden flex items-center gap-2.5 mb-10">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-500">
              <ShieldCheckIcon className="h-5 w-5 text-white" />
            </div>
            <h1 className="text-lg font-bold text-slate-900">
              Predictive Maintenance
            </h1>
          </div>

          <h2 className="text-2xl font-bold text-slate-900 tracking-tight mb-1">
            Create Account
          </h2>
          <p className="text-sm text-slate-500 mb-8">
            Register your organization to get started
          </p>

          {error && (
            <div className="mb-5 flex items-start gap-2.5 p-3.5 rounded-xl bg-red-50 border border-red-200/60 text-sm text-red-700">
              <ExclamationCircleIcon className="h-5 w-5 text-red-500 shrink-0 mt-px" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Full Name
              </label>
              <input
                type="text"
                value={form.full_name}
                onChange={update("full_name")}
                className="input-field"
                placeholder="John Doe"
                required
                autoComplete="name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Email
              </label>
              <input
                type="email"
                value={form.email}
                onChange={update("email")}
                className="input-field"
                placeholder="your@email.com"
                required
                autoComplete="email"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Organization Name
              </label>
              <input
                type="text"
                value={form.organization_name}
                onChange={update("organization_name")}
                className="input-field"
                placeholder="Acme Pharmaceuticals"
                required
                autoComplete="organization"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Password
              </label>
              <input
                type="password"
                value={form.password}
                onChange={update("password")}
                className="input-field"
                placeholder="Min. 6 characters"
                required
                minLength={6}
                autoComplete="new-password"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center !mt-6"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                  Creating account...
                </span>
              ) : (
                "Create Account"
              )}
            </button>
          </form>

          <p className="mt-8 text-center text-sm text-slate-500">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-medium text-brand-600 hover:text-brand-700 transition-colors"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
