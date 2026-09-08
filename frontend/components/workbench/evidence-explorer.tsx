"use client";

import React, { useState } from "react";
import type { AgentEvidenceItem } from "@/types/agent";
import { ChevronDown, ChevronRight, Fingerprint, ShieldCheck } from "lucide-react";

interface EvidenceExplorerProps {
  evidenceItems: AgentEvidenceItem[];
  loading?: boolean;
}

export function EvidenceExplorer({ evidenceItems, loading = false }: EvidenceExplorerProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-[#0A0C10]/95 p-5 space-y-3 shadow-xl">
        <div className="h-4 w-36 bg-[#1C1D22] animate-pulse rounded" />
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-12 bg-[#12141A] animate-pulse rounded-lg border border-white/[0.04]" />
          ))}
        </div>
      </div>
    );
  }

  if (!evidenceItems || evidenceItems.length === 0) {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-[#0A0C10]/95 p-5 text-center text-xs text-[#777A88]">
        No grounded evidence items attached.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-white/[0.08] bg-[#0A0C10]/95 p-5 space-y-4 shadow-xl backdrop-blur-xl transition-all">
      {/* Header */}
      <div className="border-b border-white/[0.06] pb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-5 w-5 rounded bg-[#CC9166]/15 flex items-center justify-center text-[#CC9166]">
            <Fingerprint className="h-3.5 w-3.5" />
          </div>
          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-[#CC9166] font-semibold">
              EVIDENCE CORRELATION
            </div>
            <h3 className="text-sm font-serif text-white">
              Grounded Evidence ({evidenceItems.length})
            </h3>
          </div>
        </div>

        <span className="text-[9px] font-mono text-[#10B981] bg-[#10B981]/10 px-2 py-0.5 rounded-md border border-[#10B981]/30 flex items-center gap-1">
          <ShieldCheck className="h-2.5 w-2.5" />
          <span>Grounded</span>
        </span>
      </div>

      <div className="space-y-2">
        {evidenceItems.map((item) => {
          const isExpanded = expandedId === item.id;
          const severityColor =
            item.severity === "critical"
              ? "text-[#EF4444] border-[#EF4444]/40 bg-[#EF4444]/10"
              : item.severity === "high"
              ? "text-[#F97316] border-[#F97316]/40 bg-[#F97316]/10"
              : item.severity === "medium"
              ? "text-[#F59E0B] border-[#F59E0B]/40 bg-[#F59E0B]/10"
              : "text-[#10B981] border-[#10B981]/40 bg-[#10B981]/10";

          return (
            <div
              key={item.id}
              className="bg-[#12141A] border border-white/[0.06] hover:border-white/[0.12] rounded-lg overflow-hidden transition-all text-xs"
            >
              <div
                onClick={() => setExpandedId(isExpanded ? null : item.id)}
                className="p-3 flex items-start justify-between gap-3 cursor-pointer select-none"
              >
                <div className="space-y-1 min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono font-semibold text-[#CC9166] text-[11px]">
                      {item.id}
                    </span>
                    <span
                      className={`text-[9px] font-mono uppercase px-1.5 py-0.5 rounded-md border ${severityColor}`}
                    >
                      {item.severity}
                    </span>
                    <span className="text-[9px] font-mono text-[#777A88]">
                      src: {item.source}
                    </span>
                  </div>
                  <p className="text-[#E2E3E9] text-[11px] leading-relaxed line-clamp-2">
                    {item.snippet}
                  </p>
                </div>
                <div className="flex items-center gap-2 pt-0.5 flex-shrink-0">
                  <span className="font-mono text-[10px] text-[#777A88]">
                    {Math.round(item.confidence * 100)}%
                  </span>
                  {isExpanded ? (
                    <ChevronDown className="h-3.5 w-3.5 text-[#777A88]" />
                  ) : (
                    <ChevronRight className="h-3.5 w-3.5 text-[#777A88]" />
                  )}
                </div>
              </div>

              {isExpanded && item.provenance && (
                <div className="px-3 pb-3 pt-2 border-t border-white/[0.06] bg-[#0A0C10] space-y-1.5">
                  <div className="text-[10px] font-mono text-[#777A88] uppercase">
                    PROVENANCE ATTRIBUTES:
                  </div>
                  <pre className="text-[10px] font-mono bg-[#14161F] p-2 rounded-md text-[#9194A1] overflow-x-auto border border-white/[0.04]">
                    {JSON.stringify(item.provenance, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
