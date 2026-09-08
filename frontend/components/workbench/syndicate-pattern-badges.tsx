"use client";

import React from "react";
import { ShieldAlert, Network, ArrowUpRight } from "lucide-react";
import type { SyndicatePattern } from "@/types/network";

interface SyndicatePatternBadgesProps {
  patterns: SyndicatePattern[] | string[];
}

export function SyndicatePatternBadges({ patterns }: SyndicatePatternBadgesProps) {
  if (!patterns || patterns.length === 0) {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-[#0A0C10]/95 p-4 text-xs text-[#777A88]">
        No coordinated syndicate rings detected.
      </div>
    );
  }

  return (
    <div className="space-y-2.5">
      <div className="text-[10px] font-mono uppercase tracking-widest text-[#EF4444] font-semibold flex items-center gap-1.5">
        <ShieldAlert className="h-3.5 w-3.5" />
        <span>DETECTED SYNDICATE PATTERNS ({patterns.length})</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        {patterns.map((p, idx) => {
          const name = typeof p === "string" ? p : p.pattern_type;
          const desc =
            typeof p === "object"
              ? p.description
              : name === "DEVICE_REUSE_RING"
              ? "Multiplexed identities and payment cards sharing single device fingerprint."
              : name === "CARD_SHARING_RING"
              ? "Distributed accounts executing rapid sequential debits across identical card BIN."
              : "Cross-infrastructure coordination spanning multiple IP subnets and merchants.";

          return (
            <div
              key={idx}
              className="bg-gradient-to-br from-[#1C0D0D]/70 to-[#0A0C10] border border-[#EF4444]/30 hover:border-[#EF4444]/60 rounded-xl p-3.5 space-y-1.5 transition-all shadow-md group"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 min-w-0">
                  <div className="h-5 w-5 rounded-md bg-[#EF4444]/20 flex items-center justify-center text-[#EF4444] flex-shrink-0">
                    <Network className="h-3 w-3" />
                  </div>
                  <span className="font-mono text-[11px] font-bold text-[#EF4444] truncate">
                    {name}
                  </span>
                </div>
                <ArrowUpRight className="h-3 w-3 text-[#EF4444]/60 group-hover:text-[#EF4444] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all flex-shrink-0" />
              </div>
              <p className="text-[10px] text-[#E2E3E9]/80 leading-relaxed">
                {desc}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
