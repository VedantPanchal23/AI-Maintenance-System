"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import ErrorBoundary from "@/components/ErrorBoundary";

/**
 * Client-side application shell.
 *
 * Handles auth gating, mobile sidebar state, and the
 * sidebar + header chrome for authenticated pages.
 * Rendered inside the single server <html>/<body> tree
 * from layout.jsx so Next.js never sees conditional roots.
 */
export default function AppShell({ children }) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, isLoading, initialize } = useAuthStore();
  const [mobileOpen, setMobileOpen] = useState(false);

  // Close mobile sidebar on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  useEffect(() => {
    initialize();
  }, [initialize]);

  const isPublicPage = pathname === "/login" || pathname === "/register";

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated && !isPublicPage) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, isPublicPage, router]);

  // Public pages (login, register) — no sidebar / header shell
  if (isPublicPage) {
    return <ErrorBoundary>{children}</ErrorBoundary>;
  }

  // Not authenticated — block rendering while redirecting
  if (!isLoading && !isAuthenticated) {
    return null;
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-surface-50">
        <div className="flex flex-col items-center gap-4 animate-fade-in">
          <div className="animate-spin h-9 w-9 border-[3px] border-brand-600 border-t-transparent rounded-full" />
          <p className="text-sm text-slate-400 font-medium">Loading…</p>
        </div>
      </div>
    );
  }

  // Authenticated layout — sidebar + header + main
  return (
    <ErrorBoundary>
      <div className="flex h-screen overflow-hidden bg-surface-50">
        <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
        <div className="flex flex-1 flex-col overflow-hidden">
          <Header onMenuToggle={() => setMobileOpen((v) => !v)} />
          <main className="flex-1 overflow-y-auto p-5 lg:p-6">
            <div className="mx-auto max-w-[1440px] animate-fade-in">
              {children}
            </div>
          </main>
        </div>
      </div>
    </ErrorBoundary>
  );
}
