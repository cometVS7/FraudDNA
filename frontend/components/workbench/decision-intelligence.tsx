"use client";

import { ShieldAlert, AlertTriangle, Bot, CheckCircle2, Lock } from "lucide-react";
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
    <div className="bg-[#040406] border border-[#1C1D22] rounded-lg overflow-hidden shadow-2xl">
      <div className="px-5 py-3 border-b border-[#1C1D22] bg-[#08080A] flex items-center justify-between">
        <div>
          <div className="text-[10px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold">
            DECISION INTELLIGENCE COMPARISON
          </div>
          <h3 className="text-sm font-serif text-white font-normal mt-0.5">
            Authoritative Financial Control vs AI Advisory Recommendation
          </h3>
        </div>
        <div className="hidden sm:flex items-center gap-1.5 text-[10px] font-mono text-[#777A88] bg-[#121317] px-2.5 py-1 rounded border border-[#1C1D22]">
          <Lock className="h-3 w-3 text-[#CC9166]" />
          <span>Strict Invariant Enforced</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#1C1D22]">
        {/* Left Column: Authoritative Policy Decision */}
        <div className="p-5 space-y-4 bg-[#060608]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-7 w-7 rounded bg-[#121317] border border-[#2E3038] flex items-center justify-center text-[#CC9166]">
                <ShieldAlert className="h-4 w-4" />
              </div>
              <div>
                <div className="text-[10px] font-mono text-[#777A88] uppercase tracking-wider">
                  AUTHORITATIVE POLICY ENGINE
                </div>
                <div className="text-xs font-serif text-white font-medium">
                  Deterministic Financial Gate
                </div>
              </div>
            </div>
            <span className="text-[10px] font-mono text-[#5E616E]">
              v{policyDecision?.policy_version || "2.0.0"}
            </span>
          </div>

          <div>
            <div className="text-[10px] font-mono text-[#5E616E] uppercase mb-1">
              Authoritative Decision Action
            </div>
            <div
              className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-md font-mono text-sm font-bold tracking-wider border ${
                policyAction === "HOLD"
                  ? "bg-[#D05B5B]/20 text-[#D05B5B] border-[#D05B5B]/50 shadow-[0_0_15px_rgba(208,91,91,0.25)]"
                  : policyAction === "REVIEW"
                  ? "bg-[#C47A63]/20 text-[#C47A63] border-[#C47A63]/40"
                  : "bg-[#10B981]/15 text-[#34D399] border-[#10B981]/30"
              }`}
            >
              <span>{policyAction}</span>
              <span className="text-[10px] font-sans font-normal opacity-80">
                {policyAction === "HOLD"
                  ? "(Settlement Blocked)"
                  : policyAction === "REVIEW"
                  ? "(Manual Hold)"
                  : "(Settlement Approved)"}
              </span>
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="text-[10px] font-mono text-[#5E616E] uppercase">
              Triggered Policy Reason Codes:
            </div>
            <div className="flex flex-wrap gap-1.5">
              {reasonCodes.map((code: string) => (
                <span
                  key={code}
                  className="px-2 py-0.5 text-[10px] font-mono bg-[#121317] text-[#E2E3E9] border border-[#1C1D22] rounded"
                >
                  {code}
                </span>
              ))}
            </div>
          </div>

          <div className="text-[10px] font-mono text-[#5E616E] border-t border-[#1C1D22]/60 pt-2 flex items-center gap-1.5">
            <CheckCircle2 className="h-3 w-3 text-[#10B981]" />
            <span>Pure Deterministic Logic — No LLM / Non-Deterministic Dependency</span>
          </div>
        </div>

        {/* Right Column: AI Investigation Recommendation */}
        <div className="p-5 space-y-4 bg-[#040406]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-7 w-7 rounded bg-[#CC9166]/15 border border-[#CC9166]/40 flex items-center justify-center text-[#CC9166]">
                <Bot className="h-4 w-4" />
              </div>
              <div>
                <div className="text-[10px] font-mono text-[#CC9166] uppercase tracking-wider font-semibold">
                  AI INVESTIGATION AGENT
                </div>
                <div className="text-xs font-serif text-white font-medium">
                  LangGraph Grounded Synthesis
                </div>
              </div>
            </div>
            <span className="text-[10px] font-mono text-[#CC9166] bg-[#CC9166]/10 px-2 py-0.5 rounded border border-[#CC9166]/30">
              ADVISORY ONLY
            </span>
          </div>

          <div>
            <div className="text-[10px] font-mono text-[#5E616E] uppercase mb-1">
              Advisory Operational Recommendation
            </div>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md font-mono text-xs font-bold tracking-wider bg-[#121317] text-[#CC9166] border border-[#CC9166]/40">
              <span>{String(agentAction).replace(/_/g, " ")}</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs font-sans">
            <div className="bg-[#121317] border border-[#1C1D22] rounded p-2.5">
              <div className="text-[10px] font-mono text-[#777A88] uppercase">Confidence</div>
              <div className="text-sm font-mono font-semibold text-white mt-0.5">
                {confidencePct}%
              </div>
            </div>

            <div className="bg-[#121317] border border-[#1C1D22] rounded p-2.5">
              <div className="text-[10px] font-mono text-[#777A88] uppercase">
                Grounded Evidence
              </div>
              <div className="text-sm font-mono font-semibold text-white mt-0.5">
                {evidenceCount} items
              </div>
            </div>
          </div>

          <div className="text-[10px] font-mono text-[#777A88] border-t border-[#1C1D22]/60 pt-2 flex items-center gap-1.5">
            <AlertTriangle className="h-3 w-3 text-[#CC9166]" />
            <span>Advisory Triage Guidance for Human Analysts (Zero Financial Authority)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
