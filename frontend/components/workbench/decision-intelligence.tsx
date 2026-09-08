"use client";

import React from "react";
import { ShieldAlert, Bot, CheckCircle2, Lock, ArrowRight, Sparkles, Scale } from "lucide-react";
import type { PolicyDecision } from "@/types/decision";
import type { AgentFindings } from "@/types/agent";

interface DecisionIntelligenceProps {
  policyDecision: PolicyDecision | null;
  agentFindings: AgentFindings | null;
  riskScore: number;
}

export function DecisionIntelligenceCard({
  policyDecision,
  agentFindings,
  riskScore,
}: DecisionIntelligenceProps) {
  const policyAction =
    policyDecision?.action ??
    (riskScore >= 0.85 ? "HOLD" : riskScore >= 0.37 ? "REVIEW" : "ALLOW");

  const reasonCodes = policyDecision?.reason_codes || [
    riskScore >= 0.85 ? "CRITICAL_RISK_SCORE" : "STANDARD_BASELINE_EVALUATION",
  ];

  const agentAction = agentFindings?.recommended_action || "MANUAL_REVIEW_ESCALATION";
  const confidencePct = Math.round((agentFindings?.confidence ?? 0.95) * 100);
  const evidenceCount = agentFindings?.evidence_items?.length ?? 10;

  return (
    <div className="relative rounded-xl border border-white/[0.08] bg-[#0A0C10]/95 backdrop-blur-xl overflow-hidden shadow-2xl transition-all">
      {/* Header Bar */}
      <div className="px-5 py-3.5 border-b border-white/[0.06] bg-[#0E1017]/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="h-6 w-6 rounded-md bg-[#CC9166]/15 border border-[#CC9166]/40 flex items-center justify-center text-[#CC9166]">
            <Scale className="h-3.5 w-3.5" />
          </div>
          <div>
            <div className="text-[10px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold">
              DECISION DEMARCATION
            </div>
            <h3 className="text-xs sm:text-sm font-serif text-white font-normal">
              Authoritative Policy Engine vs Advisory AI Investigator
            </h3>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-[10px] font-mono text-[#777A88] bg-[#12141A] px-2.5 py-1 rounded-md border border-white/[0.06] self-start sm:self-auto">
          <Lock className="h-3 w-3 text-[#CC9166]" />
          <span>Zero AI Financial Authority Invariant</span>
        </div>
      </div>

      {/* Side-by-side Demarcation Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-white/[0.06]">
        {/* Left: Authoritative Policy Engine */}
        <div className="p-5 space-y-4 bg-gradient-to-b from-[#120D0D]/60 to-[#0A0C10]/90 relative">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="h-8 w-8 rounded-lg bg-[#D05B5B]/15 border border-[#D05B5B]/40 flex items-center justify-center text-[#D05B5B] shadow-[0_0_12px_rgba(208,91,91,0.2)]">
                <ShieldAlert className="h-4 w-4" />
              </div>
              <div>
                <div className="text-[10px] font-mono text-[#D05B5B] uppercase tracking-widest font-semibold flex items-center gap-1">
                  <span>POLICY ENGINE</span>
                  <span className="px-1.5 py-0.2 bg-[#D05B5B]/20 rounded text-[9px]">AUTHORITATIVE</span>
                </div>
                <div className="text-xs font-serif text-white">
                  Deterministic Financial Execution Gate
                </div>
              </div>
            </div>
            <span className="text-[10px] font-mono text-[#5E616E]">
              v{policyDecision?.policy_version || "2.0.0"}
            </span>
          </div>

          <div>
            <div className="text-[10px] font-mono text-[#777A88] uppercase mb-1.5">
              Authoritative Execution Action:
            </div>
            <div
              className={`inline-flex items-center gap-2.5 px-3.5 py-2 rounded-lg font-mono text-sm font-bold tracking-wider border ${
                policyAction === "HOLD"
                  ? "bg-[#D05B5B]/20 text-[#D05B5B] border-[#D05B5B]/60 shadow-[0_0_20px_rgba(208,91,91,0.3)]"
                  : policyAction === "REVIEW"
                  ? "bg-[#C47A63]/20 text-[#C47A63] border-[#C47A63]/50"
                  : "bg-[#10B981]/15 text-[#34D399] border-[#10B981]/40"
              }`}
            >
              <span>{policyAction}</span>
              <span className="text-[10px] font-sans font-normal opacity-85">
                {policyAction === "HOLD"
                  ? "— Immediate Settlement Block"
                  : policyAction === "REVIEW"
                  ? "— Manual Triage Gate"
                  : "— Authorized Settlement"}
              </span>
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="text-[10px] font-mono text-[#777A88] uppercase">
              Deterministic Policy Reason Codes:
            </div>
            <div className="flex flex-wrap gap-1.5">
              {reasonCodes.map((code: string) => (
                <span
                  key={code}
                  className="px-2 py-0.5 text-[10px] font-mono bg-[#14161F] text-[#E2E3E9] border border-white/[0.08] rounded-md"
                >
                  {code}
                </span>
              ))}
            </div>
          </div>

          <div className="text-[10px] font-mono text-[#5E616E] border-t border-white/[0.06] pt-3 flex items-center gap-1.5">
            <CheckCircle2 className="h-3 w-3 text-[#10B981] flex-shrink-0" />
            <span>Pure Deterministic Logic — No Non-Deterministic LLM Dependency</span>
          </div>
        </div>

        {/* Right: AI Investigator (Advisory Only) */}
        <div className="p-5 space-y-4 bg-gradient-to-b from-[#14120D]/60 to-[#0A0C10]/90 relative">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="h-8 w-8 rounded-lg bg-[#CC9166]/15 border border-[#CC9166]/40 flex items-center justify-center text-[#CC9166]">
                <Bot className="h-4 w-4" />
              </div>
              <div>
                <div className="text-[10px] font-mono text-[#CC9166] uppercase tracking-widest font-semibold flex items-center gap-1">
                  <span>AI INVESTIGATOR</span>
                  <span className="px-1.5 py-0.2 bg-[#CC9166]/20 text-[#CC9166] rounded text-[9px]">ADVISORY ONLY</span>
                </div>
                <div className="text-xs font-serif text-white">
                  LangGraph Autonomous Grounded Synthesis
                </div>
              </div>
            </div>
            <span className="text-[10px] font-mono text-[#CC9166] bg-[#CC9166]/10 px-2 py-0.5 rounded border border-[#CC9166]/30">
              ZERO FINANCIAL AUTHORITY
            </span>
          </div>

          <div>
            <div className="text-[10px] font-mono text-[#777A88] uppercase mb-1.5">
              Advisory Operational Recommendation:
            </div>
            <div className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg font-mono text-xs font-bold tracking-wider bg-[#14161F] text-[#CC9166] border border-[#CC9166]/40">
              <Sparkles className="h-3 w-3 text-[#CC9166]" />
              <span>{String(agentAction).replace(/_/g, " ")}</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs font-sans">
            <div className="bg-[#12141A] border border-white/[0.06] rounded-lg p-2.5">
              <div className="text-[10px] font-mono text-[#777A88] uppercase">Confidence</div>
              <div className="text-sm font-mono font-semibold text-white mt-0.5">
                {confidencePct}%
              </div>
            </div>

            <div className="bg-[#12141A] border border-white/[0.06] rounded-lg p-2.5">
              <div className="text-[10px] font-mono text-[#777A88] uppercase">
                Grounded Evidence
              </div>
              <div className="text-sm font-mono font-semibold text-white mt-0.5">
                {evidenceCount} items
              </div>
            </div>
          </div>

          <div className="text-[10px] font-mono text-[#777A88] border-t border-white/[0.06] pt-3 flex items-center gap-1.5">
            <ArrowRight className="h-3 w-3 text-[#CC9166] flex-shrink-0" />
            <span>Advisory Triage Guidance for Human Analysts (Does not mutate financial ledger)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
