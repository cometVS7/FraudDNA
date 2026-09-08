"use client";

import React from "react";
import { ShieldCheck, Zap, Activity, Lock } from "lucide-react";

interface StatItem {
  value: string;
  label: string;
  sublabel: string;
  icon: React.ReactNode;
  accent?: "cyan" | "purple" | "emerald" | "amber";
}

export function StatStrip() {
  const stats: StatItem[] = [
    {
      value: "99.4%",
      label: "Detection Precision",
      sublabel: "Coordinated syndicate attack recall",
      icon: <ShieldCheck className="h-4 w-4 text-cyan-400" />,
      accent: "cyan",
    },
    {
      value: "3x",
      label: "Triage Acceleration",
      sublabel: "Autonomous dossier synthesis",
      icon: <Zap className="h-4 w-4 text-amber-400" />,
      accent: "amber",
    },
    {
      value: "25K+",
      label: "Graph Traversal / Sec",
      sublabel: "Sub-millisecond entity expansion",
      icon: <Activity className="h-4 w-4 text-purple-400" />,
      accent: "purple",
    },
    {
      value: "100%",
      label: "Deterministic Policy Gate",
      sublabel: "Zero agent direct financial authority",
      icon: <Lock className="h-4 w-4 text-emerald-400" />,
      accent: "emerald",
    },
  ];

  return (
    <div className="w-full max-w-5xl mx-auto px-4 sm:px-6 my-10">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 p-4 sm:p-6 rounded-3xl bg-[#090D16]/80 backdrop-blur-xl border border-white/10 shadow-[0_12px_40px_rgba(0,0,0,0.5)]">
        {stats.map((stat, i) => (
          <div
            key={i}
            className="flex flex-col p-3 rounded-2xl bg-white/[0.02] border border-white/[0.04] hover:border-cyan-500/30 transition-all duration-200"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-mono tracking-wider text-slate-400 uppercase">
                {stat.label}
              </span>
              <div className="p-1 rounded-lg bg-white/5">{stat.icon}</div>
            </div>
            <div className="text-2xl sm:text-3xl font-serif font-bold text-white tracking-tight">
              {stat.value}
            </div>
            <div className="text-[11px] text-slate-500 mt-1 font-sans">
              {stat.sublabel}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
