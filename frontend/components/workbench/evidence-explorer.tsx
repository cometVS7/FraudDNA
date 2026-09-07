"use client";

import React, { useState } from "react";
import type { AgentEvidenceItem } from "@/types/agent";
import { ChevronDown, ChevronRight } from "lucide-react";

interface EvidenceExplorerProps {
  evidenceItems: AgentEvidenceItem[];
  loading?: boolean;
}

export function EvidenceExplorer({ evidenceItems, loading = false }: EvidenceExplorerProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4">
        <div className="text-center py-6 text-xs text-[#777A88]">Loading grounded evidence items...</div>
      </div>
    );
  }

  if (!evidenceItems || evidenceItems.length === 0) {
    return (
      <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4 text-center text-xs text-[#777A88]">
        No grounded evidence items attached.
      </div>
    );
  }

  return (
    <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4 space-y-3.5 shadow-xl">
      <div className="border-b border-[#1C1D22] pb-2.5 flex items-center justify-between">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-[#CC9166] font-semibold">
            VERIFIABLE PROVENANCE
          </div>
          <h3 className="text-sm font-serif text-white font-normal mt-0.5">
            Grounded Evidence Dossier ({evidenceItems.length})
          </h3>
        </div>
        <span className="text-[9px] font-mono text-[#10B981] bg-[#10B981]/10 px-2 py-0.5 rounded border border-[#10B981]/30">
          100% Grounded
        </span>
      </div>

      <div className="space-y-2">
        {evidenceItems.map((item) => {
          const isExpanded = expandedId === item.id;
          const severityColor =
            item.severity === "critical"
              ? "text-[#D05B5B] border-[#D05B5B]/30 bg-[#D05B5B]/10"
              : item.severity === "high"
              ? "text-[#C47A63] border-[#C47A63]/30 bg-[#C47A63]/10"
              : item.severity === "medium"
              ? "text-[#EAB308] border-[#EAB308]/30 bg-[#EAB308]/10"
              : "text-[#34D399] border-[#10B981]/30 bg-[#10B981]/10";

          return (
            <div
              key={item.id}
              className="bg-[#0D0E12] border border-[#1C1D22] rounded-md overflow-hidden hover:border-[#2E3038] transition-colors text-xs"
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
                      className={`text-[9px] font-mono uppercase px-1.5 py-0.5 rounded border ${severityColor}`}
                    >
                      {item.severity}
                    </span>
                    <span className="text-[9px] font-mono text-[#777A88]">
                      src: {item.source}
                    </span>
                  </div>
                  <p className="text-[#E2E3E9] text-[11px] leading-snug line-clamp-2">
                    {item.snippet}
                  </p>
                </div>
                <div className="flex items-center gap-2 pt-0.5">
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
                <div className="px-3 pb-3 pt-1 border-t border-[#1C1D22] bg-[#08080A]/60 space-y-1.5">
                  <div className="text-[10px] font-mono text-[#5E616E] uppercase">
                    Provenance Attributes:
                  </div>
                  <pre className="text-[10px] font-mono bg-[#121317] p-2 rounded text-[#9194A1] overflow-x-auto">
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
