"use client";

import React, { useState } from "react";
import type { RiskFactor } from "@/lib/api";
import { Sparkles, HelpCircle } from "lucide-react";

interface ShapWaterfallProps {
  factors: RiskFactor[];
  loading?: boolean;
}

export function ShapWaterfall({ factors, loading = false }: ShapWaterfallProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  if (loading) {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-[#0A0C10]/95 p-5 space-y-4 shadow-xl">
        <div className="h-4 w-40 bg-[#1C1D22] animate-pulse rounded" />
        <div className="space-y-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-8 bg-[#12141A] animate-pulse rounded border border-white/[0.04]" />
          ))}
        </div>
      </div>
    );
  }

  if (!factors || factors.length === 0) {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-[#0A0C10]/95 p-5 text-center text-xs text-[#777A88]">
        No local Tree SHAP attributions available.
      </div>
    );
  }

  const maxAbsImpact = Math.max(...factors.map((f) => Math.abs(f.impact || 0.01)), 0.01);

  return (
    <div className="rounded-xl border border-white/[0.08] bg-[#0A0C10]/95 p-5 space-y-4 shadow-xl backdrop-blur-xl transition-all">
      {/* Header */}
      <div className="border-b border-white/[0.06] pb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-5 w-5 rounded bg-[#CC9166]/15 flex items-center justify-center text-[#CC9166]">
            <Sparkles className="h-3.5 w-3.5" />
          </div>
          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-[#CC9166] font-semibold">
              EXPLAINABLE AI (XAI)
            </div>
            <h3 className="text-sm font-serif text-white font-normal">
              Tree SHAP Attribution Forces
            </h3>
          </div>
        </div>

        <div className="relative">
          <button
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
            className="text-[#777A88] hover:text-white transition-colors"
          >
            <HelpCircle className="h-3.5 w-3.5" />
          </button>
          {showTooltip && (
            <div className="absolute right-0 top-6 z-30 w-56 p-2 bg-[#14161F] border border-white/[0.1] rounded-lg shadow-xl text-[10px] text-[#9194A1] font-sans">
              Tree SHAP computes exact Shapley values for tree ensembles, decomposing the log-odds margin into additive feature forces.
            </div>
          )}
        </div>
      </div>

      <p className="text-[11px] text-[#9194A1] font-sans leading-relaxed">
        Exact mathematical force decomposition for the LightGBM probability estimate. Red shifts risk upwards, green lowers risk.
      </p>

      {/* Feature Attributions List */}
      <div className="space-y-3">
        {factors.slice(0, 8).map((f, idx) => {
          const isRiskIncreasing = f.impact >= 0 || f.direction === "increases_risk";
          const widthPct = Math.min(100, Math.round((Math.abs(f.impact) / maxAbsImpact) * 100));

          return (
            <div
              key={idx}
              className="space-y-1.5 p-2 rounded-lg bg-[#12141A]/70 hover:bg-[#12141A] border border-white/[0.04] hover:border-white/[0.08] transition-all"
            >
              <div className="flex items-center justify-between text-[11px] font-mono">
                <span className="text-[#E2E3E9] truncate font-medium max-w-[190px]">
                  {f.feature}
                </span>
                <span
                  className={`font-semibold ${
                    isRiskIncreasing ? "text-[#EF4444]" : "text-[#10B981]"
                  }`}
                >
                  {isRiskIncreasing ? "+" : "-"}
                  {Math.abs(f.impact).toFixed(4)}
                </span>
              </div>

              {/* Force Attribution Bar with gradient fill */}
              <div className="h-1.5 w-full bg-[#1C1D24] rounded-full overflow-hidden flex">
                <div
                  style={{ width: `${widthPct}%` }}
                  className={`h-full rounded-full transition-all duration-500 ease-out ${
                    isRiskIncreasing
                      ? "bg-gradient-to-r from-[#F97316] to-[#EF4444] shadow-[0_0_8px_rgba(239,68,68,0.4)]"
                      : "bg-gradient-to-r from-[#059669] to-[#10B981] shadow-[0_0_8px_rgba(16,185,129,0.4)]"
                  }`}
                />
              </div>

              {f.value !== undefined && f.value !== null && (
                <div className="flex items-center justify-between text-[9px] font-mono text-[#777A88]">
                  <span>Observed Value:</span>
                  <span className="text-[#9194A1] font-semibold">{String(f.value)}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
