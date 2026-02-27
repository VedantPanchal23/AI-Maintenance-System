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

  const isLoginPage = pathname === "/login";

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated && !isLoginPage) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, isLoginPage, router]);

  // Login page — no sidebar / header shell
  if (isLoginPage) {
    return <ErrorBoundary>{children}</ErrorBoundary>;
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin h-10 w-10 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  // Authenticated layout — sidebar + header + main
  return (
    <ErrorBoundary>
      <div className="flex h-screen overflow-hidden">
        <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
        <div className="flex flex-1 flex-col overflow-hidden">
          <Header onMenuToggle={() => setMobileOpen((v) => !v)} />
          <main className="flex-1 overflow-y-auto bg-slate-50 p-6">
            {children}
          </main>
        </div>
      </div>
    </ErrorBoundary>
  );
}
