"use client";

import React from "react";
import Link from "next/link";
import { RiskBadge, DecisionBadge } from "@/components/ui";
import type { PolicyDecision } from "@/types/decision";
import { Zap, Briefcase } from "lucide-react";

interface HeroHeaderProps {
  transactionId: string;
  riskScore: number;
  riskLevel: string;
  policyDecision: PolicyDecision | null;
  caseId?: string | null;
  onSelectTx: (txId: string) => void;
  onRequestCreateCase?: () => void;
}

export function HeroHeader({
  transactionId,
  riskScore,
  riskLevel,
  policyDecision,
  caseId,
  onSelectTx,
  onRequestCreateCase,
}: HeroHeaderProps) {
  const policyAction =
    policyDecision?.action ??
    (riskScore >= 0.85 ? "HOLD" : riskScore >= 0.37 ? "REVIEW" : "ALLOW");

  return (
    <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-6 relative overflow-hidden shadow-2xl">
      {/* Top Banner & Quick Shortcuts */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1C1D22]/80 pb-4 mb-5">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[10px] font-mono text-[#5E616E] uppercase tracking-wider">
            Quick Load Golden Tests:
          </span>
          <button
            onClick={() => onSelectTx("tx_0001991")}
            className={`px-2.5 py-1 text-[11px] font-mono rounded border transition-all ${
              transactionId === "tx_0001991"
                ? "bg-[#CC9166]/20 border-[#CC9166] text-[#CC9166] font-semibold"
                : "bg-[#121317] border-[#1C1D22] text-[#9194A1] hover:text-white hover:border-[#CC9166]/40"
            }`}
          >
            <span className="inline-flex items-center gap-1">
              <Zap className="h-3 w-3 text-[#CC9166]" />
              Golden Case: tx_0001991 (CRITICAL Syndicate)
            </span>
          </button>
          <button
            onClick={() => onSelectTx("tx_0000000")}
            className={`px-2.5 py-1 text-[11px] font-mono rounded border transition-all ${
              transactionId === "tx_0000000"
                ? "bg-[#10B981]/20 border-[#10B981] text-[#34D399] font-semibold"
                : "bg-[#121317] border-[#1C1D22] text-[#9194A1] hover:text-white hover:border-[#10B981]/40"
            }`}
          >
            Baseline Legit: tx_0000000
          </button>
        </div>

        {caseId ? (
          <div className="flex items-center gap-1.5 text-xs font-mono text-[#CC9166]">
            <Briefcase className="h-3.5 w-3.5" />
            <span>Bound to Case:</span>
            <Link
              href={`/cases`}
              className="underline font-semibold hover:text-white transition-colors"
            >
              {caseId}
            </Link>
          </div>
        ) : (
          onRequestCreateCase && (
            <button
              onClick={onRequestCreateCase}
              className="inline-flex items-center gap-1 px-3 py-1 text-xs font-mono text-[#9194A1] hover:text-white bg-[#121317] border border-[#1C1D22] hover:border-[#CC9166]/40 rounded transition-colors"
            >
              <Briefcase className="h-3 w-3 text-[#CC9166]" />
              <span>Bind / Create Case</span>
            </button>
          )
        )}
      </div>

      {/* Main Hero Header Metrics */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className="text-xs font-mono text-[#5E616E] uppercase">TRANSACTION /</span>
            <span className="text-base sm:text-lg font-mono font-semibold text-white tracking-wider">
              {transactionId}
            </span>
            <RiskBadge level={riskLevel} size="sm" />
          </div>
          <div className="text-xs text-[#9194A1] font-sans max-w-xl">
            Multi-layer forensic investigation correlating LightGBM risk probabilities, Tree SHAP XAI
            forces, FraudDNA ego-subgraphs, syndicate topologies, and deterministic policy rules.
          </div>
        </div>

        <div className="flex items-center gap-8 self-start md:self-auto border-t md:border-t-0 border-[#1C1D22] pt-4 md:pt-0">
          {/* Editorial Serif Score */}
          <div>
            <div className="text-[10px] font-mono text-[#777A88] uppercase tracking-wider">
              COMPOSITE RISK SCORE
            </div>
            <div className="text-4xl sm:text-5xl font-serif tracking-tight text-white leading-none mt-1">
              {riskScore.toFixed(4)}
            </div>
          </div>

          <div className="h-12 w-[1px] bg-[#1C1D22]" />

          {/* Authoritative Policy State */}
          <div>
            <div className="text-[10px] font-mono text-[#777A88] uppercase tracking-wider">
              DETERMINISTIC DECISION
            </div>
            <div className="mt-1">
              <DecisionBadge action={policyAction} size="md" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
