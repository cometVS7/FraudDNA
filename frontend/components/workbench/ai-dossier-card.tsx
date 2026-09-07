"use client";

import React, { useState } from "react";
import type { AgentFindings } from "@/types/agent";
import {
  Bot,
  Terminal,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

interface AIDossierCardProps {
  findings: AgentFindings | null;
  loading?: boolean;
}

export function AIDossierCard({ findings, loading = false }: AIDossierCardProps) {
  const [showTrace, setShowTrace] = useState(false);

  if (loading) {
    return (
      <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4">
        <div className="text-center py-8 text-xs text-[#777A88]">
          Executing bounded LangGraph investigation...
        </div>
      </div>
    );
  }

  if (!findings) {
    return (
      <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4 text-center text-xs text-[#777A88]">
        No AI findings generated for this transaction.
      </div>
    );
  }

  return (
    <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-5 space-y-4 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#1C1D22] pb-3">
        <div className="flex items-center gap-2.5">
          <div className="h-7 w-7 rounded bg-[#CC9166]/15 border border-[#CC9166]/40 flex items-center justify-center text-[#CC9166]">
            <Bot className="h-4 w-4" />
          </div>
          <div>
            <div className="text-[10px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold">
              LANGGRAPH INVESTIGATION DOSSIER
            </div>
            <h3 className="text-sm font-serif text-white mt-0.5">Autonomous Agent Synthesis</h3>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {findings.is_persisted ? (
            <span className="text-[9px] font-mono text-[#10B981] bg-[#10B981]/10 px-2 py-0.5 rounded border border-[#10B981]/30">
              PostgreSQL Persisted
            </span>
          ) : (
            <span className="text-[9px] font-mono text-[#777A88] bg-[#121317] px-2 py-0.5 rounded border border-[#1C1D22]">
              In-Memory Session
            </span>
          )}
        </div>
      </div>

      {/* Investigation Summary & Hypothesis */}
      <div className="space-y-3 text-xs font-sans">
        <div className="bg-[#0D0E12] border border-[#1C1D22] rounded-lg p-3 space-y-1.5">
          <div className="text-[10px] font-mono uppercase text-[#777A88]">Executive Summary</div>
          <p className="text-[#E2E3E9] leading-relaxed">{findings.summary}</p>
        </div>

        <div className="bg-[#0D0E12] border border-[#1C1D22] rounded-lg p-3 space-y-1.5">
          <div className="text-[10px] font-mono uppercase text-[#CC9166]">
            Grounded Fraud Hypothesis
          </div>
          <p className="text-[#E2E3E9] leading-relaxed font-medium">
            {findings.fraud_hypothesis}
          </p>
        </div>

        {/* Suggested Next Steps */}
        {findings.recommended_actions && findings.recommended_actions.length > 0 && (
          <div className="bg-[#0D0E12] border border-[#1C1D22] rounded-lg p-3 space-y-2">
            <div className="text-[10px] font-mono uppercase text-[#5E616E]">
              Suggested Investigative Actions:
            </div>
            <ul className="space-y-1 text-[11px] text-[#9194A1] list-disc list-inside">
              {findings.recommended_actions.map((act, idx) => (
                <li key={idx} className="text-[#E2E3E9]">
                  {act}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Tool Execution Trace Trigger */}
        <div className="pt-2 border-t border-[#1C1D22]/60">
          <button
            onClick={() => setShowTrace(!showTrace)}
            className="w-full flex items-center justify-between p-2 rounded bg-[#121317] hover:bg-[#1C1D22] border border-[#1C1D22] transition-colors text-[11px] font-mono text-[#9194A1] hover:text-white"
          >
            <span className="flex items-center gap-1.5">
              <Terminal className="h-3.5 w-3.5 text-[#CC9166]" />
              <span>
                Inspect Tool Execution Trace ({findings.tool_trace?.length || 0} calls,{" "}
                {findings.agent_steps || 0} steps)
              </span>
            </span>
            {showTrace ? (
              <ChevronDown className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            )}
          </button>

          {showTrace && findings.tool_trace && (
            <div className="mt-2 space-y-1.5 bg-[#08080A] p-3 rounded border border-[#1C1D22]">
              {findings.tool_trace.map((rec, idx) => (
                <div
                  key={idx}
                  className="p-2 rounded bg-[#121317] border border-[#1C1D22] text-[10px] font-mono space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[#CC9166] font-semibold">{rec.tool_name}</span>
                    <span className="text-[#777A88]">{rec.duration_ms.toFixed(2)}ms</span>
                  </div>
                  <div className="text-[#5E616E] truncate">
                    args: {JSON.stringify(rec.tool_args)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
