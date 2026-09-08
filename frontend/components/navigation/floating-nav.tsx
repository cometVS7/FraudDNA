"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Shield,
  Sun,
  Moon,
  ArrowRight,
  Menu,
  X,
  Sparkles,
  Layers,
  Search,
  Share2,
  Briefcase,
  FileCheck,
} from "lucide-react";
import { useTheme } from "../design-system/theme-provider";
import { MagneticButton } from "../design-system/magnetic-button";

interface FloatingNavProps {
  currentSection?: string;
}

export function FloatingNav({ currentSection }: FloatingNavProps) {
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { href: "/#overview", label: "Product", activePath: "/" },
    { href: "/cases", label: "Case Queue", activePath: "/cases" },
    { href: "/investigate?tx=tx_0001991", label: "Workbench", activePath: "/investigate" },
    { href: "/frauddna", label: "Networks", activePath: "/frauddna" },
    { href: "/audit", label: "Trust & Audit", activePath: "/audit" },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 flex justify-center px-4 sm:px-6 pt-4 pointer-events-none">
      <nav
        className={`pointer-events-auto w-full max-w-5xl rounded-full transition-all duration-300 flex items-center justify-between px-4 sm:px-6 py-2.5 ${
          scrolled
            ? "bg-[#06080E]/80 backdrop-blur-xl border border-white/10 shadow-[0_10px_40px_rgba(0,0,0,0.6)]"
            : "bg-[#0A0D14]/60 backdrop-blur-lg border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.4)]"
        }`}
      >
        {/* Logo with Glowing DNA wave */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="relative h-8 w-8 rounded-full bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 p-[1.5px] shadow-[0_0_15px_rgba(0,229,255,0.4)] group-hover:shadow-[0_0_25px_rgba(0,229,255,0.7)] transition-shadow">
            <div className="h-full w-full rounded-full bg-[#080B11] flex items-center justify-center">
              <Shield className="h-4 w-4 text-cyan-400 group-hover:scale-110 transition-transform" />
            </div>
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold tracking-tight text-white flex items-center gap-1.5">
              Fraud<span className="bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">DNA</span>
            </span>
            <span className="text-[9px] font-mono tracking-widest text-cyan-400/70 uppercase">
              Spatial Intelligence
            </span>
          </div>
        </Link>

        {/* Center Nav Links */}
        <div className="hidden md:flex items-center gap-1 lg:gap-2 px-3 py-1 rounded-full bg-white/[0.03] border border-white/[0.06]">
          {navLinks.map((link) => {
            const isActive =
              link.activePath === "/"
                ? pathname === "/"
                : pathname.startsWith(link.activePath);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`px-3 py-1 text-xs font-medium rounded-full transition-all duration-150 ${
                  isActive
                    ? "text-white bg-white/10 shadow-xs border border-white/10"
                    : "text-slate-400 hover:text-white hover:bg-white/5"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </div>

        {/* Right Action & Theme Switch */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-full text-slate-400 hover:text-white hover:bg-white/10 transition-colors border border-white/5"
            aria-label="Toggle light/dark theme"
            title={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
          >
            {theme === "dark" ? (
              <Moon className="h-4 w-4 text-cyan-400" />
            ) : (
              <Sun className="h-4 w-4 text-amber-400" />
            )}
          </button>

          {/* Launch App Button */}
          <MagneticButton
            href="/investigate?tx=tx_0001991"
            variant="primary"
            size="sm"
            icon={<ArrowRight className="h-3.5 w-3.5" />}
          >
            Launch App
          </MagneticButton>

          {/* Mobile Menu Toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-full text-slate-400 hover:text-white hover:bg-white/10"
            aria-label="Toggle mobile menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </nav>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="pointer-events-auto absolute top-18 inset-x-4 max-w-lg mx-auto bg-[#0A0D14]/95 backdrop-blur-2xl rounded-2xl border border-white/15 p-4 shadow-2xl space-y-2 md:hidden">
          <div className="flex flex-col space-y-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className="px-4 py-2.5 rounded-xl text-sm font-medium text-slate-300 hover:text-white hover:bg-white/10 transition-colors flex items-center justify-between"
              >
                <span>{link.label}</span>
                <ArrowRight className="h-4 w-4 text-slate-500" />
              </Link>
            ))}
          </div>
          <div className="pt-2 border-t border-white/10 flex items-center justify-between">
            <span className="text-xs font-mono text-slate-500">Seed #42 • Razorpay 2026</span>
            <Link
              href="/cases"
              onClick={() => setMobileMenuOpen(false)}
              className="text-xs font-mono text-cyan-400 hover:underline"
            >
              Case Queue →
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
