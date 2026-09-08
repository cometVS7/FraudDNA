"use client";

import React from "react";
import { ShieldCheck, Zap, Network, Lock } from "lucide-react";

interface StatItem {
  value: string;
  label: string;
  sublabel: string;
  context: string;
  icon: React.ReactNode;
}

export function StatStrip() {
  const stats: StatItem[] = [
    {
      value: "99.0%",
      label: "Fraud Recall",
      sublabel: "Coordinated attack detection",
      context: "Validated on benchmark test split",
      icon: <ShieldCheck className="h-4 w-4 text-cyan-400" />,
    },
    {
      value: "3x",
      label: "Triage Velocity",
      sublabel: "Forensic dossier synthesis",
      context: "Multi-tool autonomous reasoning",
      icon: <Zap className="h-4 w-4 text-amber-400" />,
    },
    {
      value: "250",
      label: "Max Graph Nodes",
      sublabel: "Bounded investigation surface",
      context: "Multi-hop topology expansion (depth ≤ 3)",
      icon: <Network className="h-4 w-4 text-purple-400" />,
    },
    {
      value: "100%",
      label: "Deterministic Policy Gate",
      sublabel: "Strict financial safety invariant",
      context: "Zero agent direct money movement authority",
      icon: <Lock className="h-4 w-4 text-emerald-400" />,
    },
  ];

  return (
    <div className="w-full max-w-5xl mx-auto px-4 sm:px-6 my-12">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-5 sm:p-6 rounded-3xl bg-[#080C16]/75 backdrop-blur-xl border border-white/[0.08] shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
        {stats.map((stat, i) => (
          <div
            key={i}
            className="flex flex-col justify-between p-4 rounded-2xl bg-white/[0.02] border border-white/[0.04] hover:border-cyan-500/20 hover:bg-white/[0.03] transition-all duration-300"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-mono tracking-widest text-slate-400 uppercase">
                  {stat.label}
                </span>
                <div className="p-1.5 rounded-lg bg-white/[0.04] border border-white/[0.06]">
                  {stat.icon}
                </div>
              </div>
              <div className="text-2xl sm:text-3xl font-serif font-bold text-white tracking-tight">
                {stat.value}
              </div>
              <div className="text-xs text-slate-300 font-medium mt-1">
                {stat.sublabel}
              </div>
            </div>
            <div className="text-[10px] font-mono text-slate-500 mt-3 pt-2.5 border-t border-white/[0.04]">
              {stat.context}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
