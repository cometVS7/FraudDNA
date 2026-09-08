"use client";

import React, { useState } from "react";
import type { AgentFindings } from "@/types/agent";
import {
  Bot,
  Terminal,
  ChevronDown,
  ChevronRight,
  Database,
  ShieldAlert,
  CheckCircle2,
  FileText,
} from "lucide-react";

interface AIDossierCardProps {
  findings: AgentFindings | null;
  loading?: boolean;
}

export function AIDossierCard({ findings, loading = false }: AIDossierCardProps) {
  const [showTrace, setShowTrace] = useState(false);

  if (loading) {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-[#0A0C10]/95 p-5 space-y-4 shadow-xl">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-[#CC9166] animate-pulse" />
          <span className="text-xs font-mono text-[#CC9166]">Executing bounded LangGraph investigation...</span>
        </div>
        <div className="space-y-2">
          <div className="h-16 bg-[#12141A] animate-pulse rounded-lg border border-white/[0.04]" />
          <div className="h-12 bg-[#12141A] animate-pulse rounded-lg border border-white/[0.04]" />
        </div>
      </div>
    );
  }

  if (!findings) {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-[#0A0C10]/95 p-5 text-center text-xs text-[#777A88]">
        No AI findings available for this transaction.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-white/[0.08] bg-[#0A0C10]/95 p-5 space-y-4 shadow-xl backdrop-blur-xl transition-all">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
        <div className="flex items-center gap-2.5">
          <div className="h-7 w-7 rounded-lg bg-[#CC9166]/15 border border-[#CC9166]/40 flex items-center justify-center text-[#CC9166]">
            <Bot className="h-4 w-4" />
          </div>
          <div>
            <div className="text-[10px] font-mono tracking-widest text-[#CC9166] uppercase font-semibold">
              LANGGRAPH DOSSIER
            </div>
            <h3 className="text-sm font-serif text-white">Autonomous Agent Synthesis</h3>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          {findings.is_persisted ? (
            <span className="text-[9px] font-mono text-[#10B981] bg-[#10B981]/10 px-2 py-0.5 rounded-md border border-[#10B981]/30 flex items-center gap-1">
              <Database className="h-2.5 w-2.5" />
              <span>Postgres Persisted</span>
            </span>
          ) : (
            <span className="text-[9px] font-mono text-[#777A88] bg-[#12141A] px-2 py-0.5 rounded-md border border-white/[0.06]">
              In-Memory Session
            </span>
          )}
        </div>
      </div>

      {/* Investigation Summary & Grounded Hypothesis */}
      <div className="space-y-3 text-xs font-sans">
        <div className="bg-[#12141A] border border-white/[0.06] rounded-lg p-3 space-y-1">
          <div className="text-[10px] font-mono uppercase text-[#777A88] flex items-center gap-1">
            <FileText className="h-3 w-3 text-[#CC9166]" />
            <span>EXECUTIVE SUMMARY</span>
          </div>
          <p className="text-[#E2E3E9] leading-relaxed text-[11px]">{findings.summary}</p>
        </div>

        <div className="bg-[#12141A] border border-white/[0.06] rounded-lg p-3 space-y-1">
          <div className="text-[10px] font-mono uppercase text-[#CC9166] flex items-center gap-1 font-semibold">
            <ShieldAlert className="h-3 w-3 text-[#CC9166]" />
            <span>GROUNDED FRAUD HYPOTHESIS</span>
          </div>
          <p className="text-[#E2E3E9] leading-relaxed text-[11px]">
            {findings.fraud_hypothesis}
          </p>
        </div>

        {/* Suggested Next Steps */}
        {findings.recommended_actions && findings.recommended_actions.length > 0 && (
          <div className="bg-[#12141A] border border-white/[0.06] rounded-lg p-3 space-y-1.5">
            <div className="text-[10px] font-mono uppercase text-[#777A88]">
              Recommended Triage Steps:
            </div>
            <ul className="space-y-1 text-[11px] text-[#9194A1]">
              {findings.recommended_actions.map((act, idx) => (
                <li key={idx} className="flex items-start gap-1.5 text-[#E2E3E9]">
                  <CheckCircle2 className="h-3 w-3 text-[#CC9166] mt-0.5 flex-shrink-0" />
                  <span>{act}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Tool Execution Trace Trigger */}
        <div className="pt-2 border-t border-white/[0.06]">
          <button
            onClick={() => setShowTrace(!showTrace)}
            className="w-full flex items-center justify-between p-2 rounded-lg bg-[#12141A] hover:bg-[#181A22] border border-white/[0.06] transition-colors text-[11px] font-mono text-[#9194A1] hover:text-white"
          >
            <span className="flex items-center gap-1.5">
              <Terminal className="h-3.5 w-3.5 text-[#CC9166]" />
              <span>
                Tool Trace ({findings.tool_trace?.length || 0} calls, {findings.agent_steps || 0} steps)
              </span>
            </span>
            {showTrace ? (
              <ChevronDown className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            )}
          </button>

          {showTrace && findings.tool_trace && (
            <div className="mt-2 space-y-1.5 bg-[#08080A] p-3 rounded-lg border border-white/[0.06] max-h-48 overflow-y-auto">
              {findings.tool_trace.map((rec, idx) => (
                <div
                  key={idx}
                  className="p-2 rounded bg-[#12141A] border border-white/[0.04] text-[10px] font-mono space-y-0.5"
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
