"use client";

import { ShieldAlert, Network } from "lucide-react";
import type { SyndicatePattern } from "@/types/network";

interface SyndicatePatternBadgesProps {
  patterns: SyndicatePattern[] | string[];
}

export function SyndicatePatternBadges({ patterns }: SyndicatePatternBadgesProps) {
  if (!patterns || patterns.length === 0) {
    return (
      <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-3 text-xs text-[#777A88]">
        No coordinated syndicate rings detected.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-[#D05B5B] font-semibold flex items-center gap-1.5">
        <ShieldAlert className="h-3.5 w-3.5" />
        <span>Detected Syndicate Patterns ({patterns.length})</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        {patterns.map((p, idx) => {
          const name = typeof p === "string" ? p : p.pattern_type;
          const desc =
            typeof p === "object"
              ? p.description
              : name === "DEVICE_REUSE_RING"
              ? "Multiple distinct identities and cards multiplexed across a single device fingerprint."
              : name === "CARD_SHARING_RING"
              ? "Rapid sequential debits on a single payment instrument across distributed accounts."
              : "Cross-infrastructure coordination spanning multiple IPs, merchants, and hardware nodes.";

          return (
            <div
              key={idx}
              className="bg-[#D05B5B]/10 border border-[#D05B5B]/30 rounded-lg p-3 space-y-1 hover:border-[#D05B5B]/60 transition-colors shadow-sm"
            >
              <div className="flex items-center gap-1.5">
                <Network className="h-3.5 w-3.5 text-[#D05B5B] flex-shrink-0" />
                <span className="font-mono text-[11px] font-bold text-[#D05B5B] truncate">
                  {name}
                </span>
              </div>
              <p className="text-[10px] text-[#E2E3E9] leading-snug line-clamp-2">{desc}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
