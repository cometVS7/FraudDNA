"use client";

import React, { useState } from "react";
import { CaseStatusBadge } from "@/components/cases/case-status-badge";
import { updateCaseStatus } from "@/lib/api";
import type { CaseResponse, CaseStatus } from "@/types/case";
import {
  Briefcase,
  CheckCircle2,
  Send,
  AlertTriangle,
} from "lucide-react";

interface CaseActionToolbarProps {
  caseData: CaseResponse | null;
  onCaseUpdated: (updatedCase: CaseResponse) => void;
  onRequestCreateCase?: () => void;
}

export function CaseActionToolbar({
  caseData,
  onCaseUpdated,
  onRequestCreateCase,
}: CaseActionToolbarProps) {
  const [targetStatus, setTargetStatus] = useState<CaseStatus>(
    caseData?.status || "IN_REVIEW"
  );
  const [analystNotes, setAnalystNotes] = useState("");
  const [owner, setOwner] = useState(caseData?.owner || "analyst_01");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<{ text: string; isError: boolean } | null>(null);

  if (!caseData) {
    return (
      <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-5 space-y-3 shadow-xl">
        <div className="flex items-center justify-between border-b border-[#1C1D22] pb-2.5">
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-[#CC9166] font-semibold">
            ANALYST TRIAGE WORKFLOW
          </div>
        </div>
        <p className="text-xs text-[#777A88]">
          This transaction is not currently bound to an active operational case.
        </p>
        {onRequestCreateCase && (
          <button
            onClick={onRequestCreateCase}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono rounded bg-[#CC9166] text-[#08080A] font-semibold hover:bg-[#CC9166]/90 transition-opacity"
          >
            <Briefcase className="h-3.5 w-3.5" />
            <span>Open New Case for Transaction</span>
          </button>
        )}
      </div>
    );
  }

  async function handleStatusTransition(e: React.FormEvent) {
    e.preventDefault();
    if (!caseData) return;

    setLoading(true);
    setMsg(null);
    try {
      const resp = await updateCaseStatus(caseData.id, {
        status: targetStatus,
        notes: analystNotes.trim() || undefined,
        owner: owner.trim() || undefined,
      });
      onCaseUpdated(resp);
      setMsg({ text: `Case transitioned to ${targetStatus} successfully.`, isError: false });
      setAnalystNotes("");
    } catch (err: unknown) {
      setMsg({
        text: err instanceof Error ? err.message : "Failed to update case status",
        isError: true,
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-5 space-y-4 shadow-xl">
      <div className="border-b border-[#1C1D22] pb-2.5 flex items-center justify-between">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-[#CC9166] font-semibold">
            ANALYST TRIAGE WORKFLOW
          </div>
          <h3 className="text-sm font-serif text-white font-normal mt-0.5">
            Case Lifecycle Actions
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-[#5E616E]">{caseData.id}</span>
          <CaseStatusBadge status={caseData.status} />
        </div>
      </div>

      {msg && (
        <div
          className={`p-2.5 rounded text-xs flex items-center gap-2 ${
            msg.isError
              ? "bg-[#D05B5B]/10 border border-[#D05B5B]/30 text-[#D05B5B]"
              : "bg-[#10B981]/10 border border-[#10B981]/30 text-[#34D399]"
          }`}
        >
          {msg.isError ? (
            <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0" />
          ) : (
            <CheckCircle2 className="h-3.5 w-3.5 flex-shrink-0" />
          )}
          <span>{msg.text}</span>
        </div>
      )}

      <form onSubmit={handleStatusTransition} className="space-y-3 text-xs font-sans">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-[10px] font-mono text-[#777A88] uppercase mb-1">
              Transition Status
            </label>
            <select
              value={targetStatus}
              onChange={(e) => setTargetStatus(e.target.value as CaseStatus)}
              className="w-full bg-[#121317] border border-[#1C1D22] rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-[#CC9166]"
            >
              <option value="IN_REVIEW">IN_REVIEW</option>
              <option value="ESCALATED">ESCALATED</option>
              <option value="RESOLVED">RESOLVED</option>
              <option value="CLOSED">CLOSED</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-mono text-[#777A88] uppercase mb-1">
              Assignee
            </label>
            <input
              type="text"
              value={owner}
              onChange={(e) => setOwner(e.target.value)}
              className="w-full bg-[#121317] border border-[#1C1D22] rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-[#CC9166]"
            />
          </div>
        </div>

        <div>
          <label className="block text-[10px] font-mono text-[#777A88] uppercase mb-1">
            Analyst Case Notes / Triage Findings
          </label>
          <textarea
            rows={2}
            value={analystNotes}
            onChange={(e) => setAnalystNotes(e.target.value)}
            placeholder="Document rationale, verified syndicate rings, or escalation instructions..."
            className="w-full bg-[#121317] border border-[#1C1D22] rounded p-2.5 text-xs text-white placeholder-[#5E616E] focus:outline-none focus:border-[#CC9166]"
          />
        </div>

        <div className="flex items-center justify-between pt-1">
          <span className="text-[10px] font-mono text-[#5E616E]">
            Mutations recorded to immutable audit log
          </span>
          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded bg-[#CC9166] text-[#08080A] font-medium font-sans hover:bg-[#CC9166]/90 disabled:opacity-40 transition-opacity"
          >
            <Send className="h-3 w-3" />
            <span>{loading ? "Recording..." : "Record Action"}</span>
          </button>
        </div>
      </form>
    </div>
  );
}
