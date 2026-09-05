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
  { href: "/transactions", label: "Transactions", icon: ListOrdered },
];

const SYSTEM_NAV: NavItem[] = [
  { href: "/frauddna", label: "Risk Networks", icon: Share2 },
  { href: "/investigate", label: "Investigations", icon: Search },
  { href: "/simulation", label: "Simulation", icon: SlidersHorizontal },
  { href: "/evaluation", label: "Detection Performance", icon: BarChart3 },
  { href: "/audit", label: "Decision Audit", icon: ClipboardList },
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
      <div className="px-3 mb-2 text-[10px] font-mono tracking-[0.18em] text-[#5E616E] uppercase">
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
              className={`group relative flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-all duration-150 ${
                isActive
                  ? "bg-[#121317] text-white shadow-sm"
                  : "text-[#9194A1] hover:text-[#E2E3E9] hover:bg-[#121317]/60"
              }`}
            >
              {/* Copper active indicator line */}
              {isActive && (
                <span className="absolute left-0 top-1.5 bottom-1.5 w-[2.5px] bg-[#CC9166] rounded-r" />
              )}
              <Icon
                className={`h-3.5 w-3.5 flex-shrink-0 transition-colors ${
                  isActive
                    ? "text-[#CC9166]"
                    : "text-[#5E616E] group-hover:text-[#9194A1]"
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
      className={`fixed inset-y-0 left-0 z-40 w-60 bg-[#040406] border-r border-[#1C1D22] flex flex-col transition-transform duration-200 ease-in-out md:translate-x-0 ${
        mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      }`}
    >
      {/* Brand Header */}
      <div className="h-14 px-5 flex items-center justify-between border-b border-[#1C1D22]">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="h-7 w-7 rounded-md bg-[#121317] border border-[#2E3038] flex items-center justify-center text-[#CC9166] group-hover:border-[#CC9166]/60 transition-colors">
            <Shield className="h-3.5 w-3.5" />
          </div>
          <div>
            <div className="text-sm font-semibold tracking-tight text-[#E2E3E9] flex items-center gap-1.5">
              <span>FraudDNA</span>
            </div>
            <div className="text-[9px] font-mono tracking-[0.14em] text-[#5E616E] leading-none uppercase">
              Risk Intelligence
            </div>
          </div>
        </Link>
        {onClose && (
          <button
            onClick={onClose}
            className="md:hidden text-[#5E616E] hover:text-[#E2E3E9] p-1"
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
      <div className="px-4 py-3.5 border-t border-[#1C1D22] bg-[#08080A]/60">
        <div className="flex items-center justify-between text-[10px] font-mono text-[#5E616E]">
          <span>FRAUDDNA ENTERPRISE</span>
          <span className="text-[#AE9357]/80">ACTIVE</span>
        </div>
        <div className="mt-1 text-[9px] font-mono text-[#464853] truncate">
          Institutional Risk Operations
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
    <header className="h-12 border-b border-[#1C1D22] bg-[#08080A]/90 backdrop-blur sticky top-0 z-20 flex items-center justify-between px-4 md:px-8">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="md:hidden text-[#777A88] hover:text-white p-1 rounded"
          aria-label="Open navigation"
        >
          <Menu className="h-4 w-4" />
        </button>
        <span className="hidden sm:inline-flex items-center gap-1.5 text-[11px] font-mono text-[#777A88]">
          <Database className="h-3 w-3 text-[#5E616E]" />
          <span>Transaction Ledger</span>
        </span>
        <span className="hidden sm:inline text-[#2E3038]">•</span>
        <span className="hidden md:inline-flex items-center gap-1.5 text-[11px] font-mono text-[#777A88]">
          <Cpu className="h-3 w-3 text-[#5E616E]" />
          <span>Engine {apiVersion}</span>
        </span>
        <span className="hidden md:inline text-[#2E3038]">•</span>
        <span className="hidden lg:inline-flex items-center gap-1.5 text-[11px] font-mono text-[#777A88]">
          <span>Policy Controls: Active</span>
        </span>
      </div>

      <div className="flex items-center gap-2">
        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#121317] border border-[#1C1D22] text-[10px] font-mono tracking-wider text-[#9194A1]">
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              apiHealth === "healthy"
                ? "bg-[#8FAF9B] shadow-[0_0_6px_rgba(143,175,155,0.4)]"
                : apiHealth === "checking"
                ? "bg-[#C7A66B] animate-pulse"
                : "bg-[#D05B5B]"
            }`}
          />
          <span className="uppercase">
            {apiHealth === "healthy"
              ? "System Operational"
              : apiHealth === "checking"
              ? "System Connecting"
              : "System Degraded"}
          </span>
        </div>
      </div>
    </header>
  );
}

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#08080A] text-[#E2E3E9] selection:bg-[#CC9166]/30 selection:text-white">
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
