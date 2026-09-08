"use client";

import React, { useState } from "react";
import Link from "next/link";
import { RiskBadge, DecisionBadge } from "@/components/ui";
import type { PolicyDecision } from "@/types/decision";
import {
  Zap,
  Briefcase,
  ShieldCheck,
  Copy,
  Check,
  ShieldAlert,
} from "lucide-react";

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
  const [copied, setCopied] = useState(false);

  const policyAction =
    policyDecision?.action ??
    (riskScore >= 0.85 ? "HOLD" : riskScore >= 0.37 ? "REVIEW" : "ALLOW");

  function copyTxId() {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(transactionId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  return (
    <div className="relative rounded-xl border border-white/[0.08] bg-[#0A0C10]/90 backdrop-blur-xl p-5 sm:p-6 shadow-2xl overflow-hidden transition-all">
      {/* Ambient Radial Lighting Glow */}
      <div
        className="pointer-events-none absolute -top-24 -right-24 h-64 w-64 rounded-full blur-3xl opacity-20"
        style={{
          background:
            riskScore >= 0.7
              ? "radial-gradient(circle, #EF4444 0%, transparent 70%)"
              : "radial-gradient(circle, #38BDF8 0%, transparent 70%)",
        }}
      />

      {/* Top Bar: Golden Shortcuts & Audit Cryptographic Status */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-white/[0.06] pb-4 mb-4">
        {/* Quick Golden Selectors */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[10px] font-mono text-[#777A88] uppercase tracking-wider">
            Quick Load:
          </span>
          <button
            onClick={() => onSelectTx("tx_0001991")}
            className={`px-2.5 py-1 text-[11px] font-mono rounded-md border transition-all flex items-center gap-1.5 ${
              transactionId === "tx_0001991"
                ? "bg-[#CC9166]/20 border-[#CC9166] text-[#CC9166] font-semibold shadow-[0_0_12px_rgba(204,145,102,0.2)]"
                : "bg-[#121317] border-[#1C1D22] text-[#9194A1] hover:text-white hover:border-[#CC9166]/40"
            }`}
          >
            <Zap className="h-3 w-3 text-[#CC9166]" />
            <span>Golden Case: tx_0001991 (CRITICAL)</span>
          </button>
          <button
            onClick={() => onSelectTx("tx_0000001")}
            className={`px-2.5 py-1 text-[11px] font-mono rounded-md border transition-all flex items-center gap-1.5 ${
              transactionId === "tx_0000001"
                ? "bg-[#10B981]/20 border-[#10B981] text-[#34D399] font-semibold shadow-[0_0_12px_rgba(16,185,129,0.2)]"
                : "bg-[#121317] border-[#1C1D22] text-[#9194A1] hover:text-white hover:border-[#10B981]/40"
            }`}
          >
            <span>Baseline Legit: tx_0000001</span>
          </button>
        </div>

        {/* Right Status Badges: Case & Cryptographic Audit State */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1.5 text-[10px] font-mono text-[#34D399] bg-[#10B981]/10 px-2.5 py-1 rounded-md border border-[#10B981]/30">
            <ShieldCheck className="h-3 w-3 text-[#10B981]" />
            <span>SHA-256 Audit Chain Verified</span>
          </div>

          {caseId ? (
            <div className="flex items-center gap-1.5 text-xs font-mono text-[#CC9166] bg-[#CC9166]/10 px-2.5 py-1 rounded-md border border-[#CC9166]/30">
              <Briefcase className="h-3 w-3" />
              <span>Case:</span>
              <Link
                href={`/cases/${caseId}`}
                className="underline font-semibold hover:text-white transition-colors"
              >
                {caseId}
              </Link>
            </div>
          ) : (
            onRequestCreateCase && (
              <button
                onClick={onRequestCreateCase}
                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-mono text-[#9194A1] hover:text-white bg-[#121317] border border-[#1C1D22] hover:border-[#CC9166]/40 rounded-md transition-colors"
              >
                <Briefcase className="h-3 w-3 text-[#CC9166]" />
                <span>Bind Case</span>
              </button>
            )
          )}
        </div>
      </div>

      {/* Main Forensic Hero Banner */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        {/* Left: Transaction Identity & Context */}
        <div className="space-y-2">
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-[10px] font-mono uppercase tracking-widest text-[#777A88]">
              TRANSACTION IDENTITY /
            </span>
            <div className="flex items-center gap-1.5 bg-[#12141A] px-2.5 py-1 rounded-md border border-white/[0.08]">
              <span className="text-base font-mono font-bold text-white tracking-wider">
                {transactionId}
              </span>
              <button
                onClick={copyTxId}
                title="Copy Transaction ID"
                className="text-[#777A88] hover:text-white transition-colors p-0.5"
              >
                {copied ? (
                  <Check className="h-3 w-3 text-[#34D399]" />
                ) : (
                  <Copy className="h-3 w-3" />
                )}
              </button>
            </div>
            <RiskBadge level={riskLevel} size="sm" />
          </div>

          <p className="text-xs text-[#9194A1] font-sans max-w-2xl leading-relaxed">
            Forensic multi-signal intelligence correlating LightGBM probability forces, Tree SHAP attributions,
            multi-hop FraudDNA ego-subgraphs, and deterministic policy gates.
          </p>
        </div>

        {/* Right: Key Performance / Score Callouts */}
        <div className="flex items-center gap-6 sm:gap-8 self-start lg:self-auto border-t lg:border-t-0 border-white/[0.06] pt-4 lg:pt-0">
          {/* Composite Score */}
          <div>
            <div className="text-[10px] font-mono text-[#777A88] uppercase tracking-wider">
              COMPOSITE RISK SCORE
            </div>
            <div className="text-3xl sm:text-4xl font-serif tracking-tight text-white leading-none mt-1">
              {riskScore.toFixed(4)}
            </div>
          </div>

          <div className="h-10 w-[1px] bg-white/[0.08]" />

          {/* Authoritative Policy State */}
          <div>
            <div className="text-[10px] font-mono text-[#777A88] uppercase tracking-wider flex items-center gap-1">
              <ShieldAlert className="h-3 w-3 text-[#D05B5B]" />
              <span>DETERMINISTIC GATE</span>
            </div>
            <div className="mt-1 flex items-center gap-2">
              <DecisionBadge action={policyAction} size="md" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
