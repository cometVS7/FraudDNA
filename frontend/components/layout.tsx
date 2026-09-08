"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Shield,
  LayoutDashboard,
  ListOrdered,
  Share2,
  Search,
  Briefcase,
  SlidersHorizontal,
  BarChart3,
  ClipboardList,
  Menu,
  X,
  Cpu,
  Database,
} from "lucide-react";
import { fetchHealth } from "@/lib/api";

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const OVERVIEW_NAV: NavItem[] = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/cases", label: "Case Queue", icon: Briefcase },
  { href: "/investigate", label: "Workbench", icon: Search },
  { href: "/transactions", label: "Transactions", icon: ListOrdered },
  { href: "/frauddna", label: "FraudDNA Network", icon: Share2 },
  { href: "/simulation", label: "Simulation", icon: SlidersHorizontal },
  { href: "/evaluation", label: "Evaluation", icon: BarChart3 },
];

const SYSTEM_NAV: NavItem[] = [
  { href: "/audit", label: "Audit", icon: ClipboardList },
];

export function Sidebar({
  mobileOpen,
  onClose,
}: {
  mobileOpen?: boolean;
  onClose?: () => void;
}) {
  const pathname = usePathname();

  const renderNavGroup = (title: string, items: NavItem[]) => (
    <div className="mb-6">
      <div className="px-3 mb-2 text-[10px] font-mono tracking-[0.18em] text-slate-500 uppercase">
        {title}
      </div>
      <div className="space-y-0.5">
        {items.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onClose}
              className={`group relative flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition-all duration-150 ${
                isActive
                  ? "bg-white/[0.08] text-white shadow-xs border border-white/10"
                  : "text-slate-400 hover:text-white hover:bg-white/[0.04]"
              }`}
            >
              {/* Cyan active indicator line */}
              {isActive && (
                <span className="absolute left-0 top-1.5 bottom-1.5 w-[3px] bg-cyan-400 rounded-r shadow-[0_0_8px_rgba(0,229,255,0.8)]" />
              )}
              <Icon
                className={`h-3.5 w-3.5 flex-shrink-0 transition-colors ${
                  isActive
                    ? "text-cyan-400"
                    : "text-slate-500 group-hover:text-slate-300"
                }`}
              />
              <span className="tracking-tight">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 w-60 bg-[#06080E]/95 backdrop-blur-2xl border-r border-white/10 flex flex-col transition-transform duration-200 ease-in-out md:translate-x-0 ${
        mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      }`}
    >
      {/* Brand Header */}
      <div className="h-14 px-5 flex items-center justify-between border-b border-white/10">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="h-7 w-7 rounded-full bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-400 group-hover:shadow-[0_0_12px_rgba(0,229,255,0.6)] transition-all">
            <Shield className="h-3.5 w-3.5" />
          </div>
          <div>
            <div className="text-sm font-semibold tracking-tight text-white flex items-center gap-1">
              <span>Fraud</span>
              <span className="text-cyan-400">DNA</span>
            </div>
            <div className="text-[9px] font-mono tracking-[0.14em] text-slate-500 leading-none uppercase">
              Spatial Intelligence
            </div>
          </div>
        </Link>
        {onClose && (
          <button
            onClick={onClose}
            className="md:hidden text-slate-400 hover:text-white p-1"
            aria-label="Close navigation"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Navigation Sections */}
      <nav className="flex-1 py-4 px-3 overflow-y-auto custom-scrollbar">
        {renderNavGroup("Overview", OVERVIEW_NAV)}
        {renderNavGroup("System", SYSTEM_NAV)}
      </nav>

      {/* Footer System Provenance */}
      <div className="px-4 py-3.5 border-t border-white/10 bg-black/40">
        <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
          <span>RAZORPAY 2026</span>
          <span className="text-emerald-400 font-bold">DEFENSE ONLY</span>
        </div>
        <div className="mt-1 text-[9px] font-mono text-slate-500 truncate">
          AI Risk Manager • Track 02
        </div>
      </div>
    </aside>
  );
}

export function TopUtilityBar({ onMenuClick }: { onMenuClick?: () => void }) {
  const [apiHealth, setApiHealth] = useState<"healthy" | "checking" | "degraded">("checking");
  const [apiVersion, setApiVersion] = useState<string>("v1");

  useEffect(() => {
    let mounted = true;
    fetchHealth()
      .then((res) => {
        if (!mounted) return;
        if (res.status === "healthy") {
          setApiHealth("healthy");
          if (res.version) setApiVersion(res.version);
        } else {
          setApiHealth("degraded");
        }
      })
      .catch(() => {
        if (mounted) setApiHealth("degraded");
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <header className="h-12 border-b border-white/10 bg-[#06080E]/80 backdrop-blur-xl sticky top-0 z-20 flex items-center justify-between px-4 md:px-8">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="md:hidden text-slate-400 hover:text-white p-1 rounded"
          aria-label="Open navigation"
        >
          <Menu className="h-4 w-4" />
        </button>
        <span className="hidden sm:inline-flex items-center gap-1.5 text-[11px] font-mono text-slate-400">
          <Database className="h-3 w-3 text-cyan-400" />
          <span>Synthetic Dataset</span>
        </span>
        <span className="hidden sm:inline text-slate-700">•</span>
        <span className="hidden md:inline-flex items-center gap-1.5 text-[11px] font-mono text-slate-400">
          <Cpu className="h-3 w-3 text-purple-400" />
          <span>Model {apiVersion}</span>
        </span>
        <span className="hidden md:inline text-slate-700">•</span>
        <span className="hidden lg:inline-flex items-center gap-1.5 text-[11px] font-mono text-slate-400">
          <span>Agent: Bounded Read-Only</span>
        </span>
      </div>

      <div className="flex items-center gap-3">
        <Link
          href="/"
          className="hidden sm:inline-flex text-[11px] font-mono text-cyan-400 hover:text-cyan-300 px-2.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-400/20"
        >
          Spatial View →
        </Link>
        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/10 text-[11px] font-mono text-slate-300">
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              apiHealth === "healthy"
                ? "bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.6)]"
                : apiHealth === "checking"
                ? "bg-amber-400 animate-pulse"
                : "bg-rose-500"
            }`}
          />
          <span className="capitalize">
            {apiHealth === "healthy"
              ? "API Healthy"
              : apiHealth === "checking"
              ? "API Checking"
              : "API Degraded"}
          </span>
        </div>
      </div>
    </header>
  );
}

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#06080E] text-[#E2E3E9] selection:bg-cyan-500/30 selection:text-white">
      <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />

      {/* Backdrop for mobile */}
      {mobileOpen && (
        <div
          onClick={() => setMobileOpen(false)}
          className="fixed inset-0 z-30 bg-black/60 backdrop-blur-xs md:hidden"
        />
      )}

      <div className="md:pl-60 flex flex-col min-h-screen">
        <TopUtilityBar onMenuClick={() => setMobileOpen(true)} />
        <main className="flex-1 px-4 sm:px-6 lg:px-8 py-6 max-w-[1520px] w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
