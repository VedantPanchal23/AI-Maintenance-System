"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore, useThemeStore } from "@/lib/store";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import ErrorBoundary from "@/components/ErrorBoundary";
import { Toaster } from "sonner";
import { CommandPalette } from "@/components/CommandPalette";
import { motion, AnimatePresence } from "framer-motion";

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
  const { initTheme } = useThemeStore();
  const [mobileOpen, setMobileOpen] = useState(false);

  // Close mobile sidebar on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  useEffect(() => {
    initialize();
    initTheme();
  }, [initialize, initTheme]);

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
      <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-[#020617]">
        <div className="flex flex-col items-center gap-4 animate-fade-in">
          <div className="animate-spin h-9 w-9 border-[3px] border-brand-600 border-t-transparent rounded-full" />
          <p className="text-sm text-slate-400 font-medium">Loading…</p>
        </div>
      </div>
    );
  }

  // Authenticated layout — Top navigation + main
  return (
    <ErrorBoundary>
      <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-[#020617] transition-colors duration-500 selection:bg-brand-500/30">
        {/* Skip to main content link for keyboard users */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:z-[100] focus:top-2 focus:left-2 focus:bg-brand-600 focus:text-white focus:px-4 focus:py-2 focus:rounded-lg text-sm font-medium"
        >
          Skip to main content
        </a>
        <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
        <div className="flex flex-1 flex-col overflow-hidden">
          <Header onMenuToggle={() => setMobileOpen((v) => !v)} />
          <main id="main-content" className="flex-1 overflow-y-auto px-6 lg:px-10 2xl:px-16 py-8 w-full">
            <AnimatePresence mode="wait">
              <motion.div
                key={pathname}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2, ease: "easeOut" }}
                className="mx-auto max-w-[1920px] w-full"
              >
                {children}
              </motion.div>
            </AnimatePresence>
          </main>
        </div>
        <Toaster 
          position="bottom-right" 
          theme="system"
          toastOptions={{
            style: {
              background: 'rgba(2, 6, 23, 0.8)',
              backdropFilter: 'blur(16px)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              color: 'white',
            },
            className: 'font-semibold tracking-wide'
          }}
        />
        <CommandPalette />
      </div>
    </ErrorBoundary>
  );
}
