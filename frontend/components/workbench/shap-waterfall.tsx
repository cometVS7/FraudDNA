"use client";

import type { RiskFactor } from "@/lib/api";

interface ShapWaterfallProps {
  factors: RiskFactor[];
  loading?: boolean;
}

export function ShapWaterfall({ factors, loading = false }: ShapWaterfallProps) {
  if (loading) {
    return (
      <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4">
        <div className="text-center py-6 text-xs text-[#777A88]">Calculating Tree SHAP attributions...</div>
      </div>
    );
  }

  if (!factors || factors.length === 0) {
    return (
      <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4 text-center text-xs text-[#777A88]">
        No local SHAP attributions available.
      </div>
    );
  }

  const maxAbsImpact = Math.max(...factors.map((f) => Math.abs(f.impact || 0.01)), 0.01);

  return (
    <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4 space-y-3.5 shadow-xl">
      <div className="border-b border-[#1C1D22] pb-2 flex items-center justify-between">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-[#CC9166] font-semibold">
            EXPLAINABLE AI (XAI)
          </div>
          <h3 className="text-sm font-serif text-white font-normal mt-0.5">
            Tree SHAP Feature Attributions
          </h3>
        </div>
        <span className="text-[9px] font-mono text-[#5E616E]">Local forces</span>
      </div>

      <p className="text-[11px] text-[#9194A1] font-sans">
        Exact mathematical contribution of top behavioral signals to the LightGBM probability
        estimate.
      </p>

      <div className="space-y-2.5">
        {factors.slice(0, 8).map((f, idx) => {
          const isRiskIncreasing = f.impact >= 0 || f.direction === "increases_risk";
          const widthPct = Math.min(100, Math.round((Math.abs(f.impact) / maxAbsImpact) * 100));

          return (
            <div key={idx} className="space-y-1">
              <div className="flex items-center justify-between text-[11px] font-mono">
                <span className="text-[#E2E3E9] truncate max-w-[180px]">{f.feature}</span>
                <span
                  className={`font-semibold ${
                    isRiskIncreasing ? "text-[#D05B5B]" : "text-[#34D399]"
                  }`}
                >
                  {isRiskIncreasing ? "+" : "-"}
                  {Math.abs(f.impact).toFixed(4)}
                </span>
              </div>

              {/* Force attribution bar */}
              <div className="h-1.5 w-full bg-[#121317] rounded-full overflow-hidden flex">
                <div
                  style={{ width: `${widthPct}%` }}
                  className={`h-full rounded-full transition-all duration-300 ${
                    isRiskIncreasing
                      ? "bg-gradient-to-r from-[#C47A63] to-[#D05B5B]"
                      : "bg-gradient-to-r from-[#10B981] to-[#34D399]"
                  }`}
                />
              </div>

              {f.value !== undefined && f.value !== null && (
                <div className="text-[9px] font-mono text-[#5E616E]">
                  Value: {String(f.value)}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
