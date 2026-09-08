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
  FileCheck2,
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
      <div className="rounded-xl border border-white/[0.08] bg-[#0A0C10]/95 p-5 space-y-3.5 shadow-xl backdrop-blur-xl">
        <div className="flex items-center justify-between border-b border-white/[0.06] pb-2.5">
          <div className="flex items-center gap-2">
            <div className="h-5 w-5 rounded bg-[#CC9166]/15 flex items-center justify-center text-[#CC9166]">
              <Briefcase className="h-3.5 w-3.5" />
            </div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-[#CC9166] font-semibold">
              CASE WORKFLOW
            </div>
          </div>
        </div>
        <p className="text-xs text-[#9194A1]">
          This transaction is not currently bound to an active operational case.
        </p>
        {onRequestCreateCase && (
          <button
            onClick={onRequestCreateCase}
            className="w-full flex items-center justify-center gap-2 px-3.5 py-2 text-xs font-mono rounded-lg bg-[#CC9166] text-[#08080A] font-bold hover:bg-[#CC9166]/90 transition-all shadow-[0_0_15px_rgba(204,145,102,0.25)]"
          >
            <Briefcase className="h-3.5 w-3.5" />
            <span>Open / Bind Case</span>
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
    <div className="rounded-xl border border-white/[0.08] bg-[#0A0C10]/95 p-5 space-y-4 shadow-xl backdrop-blur-xl transition-all">
      <div className="border-b border-white/[0.06] pb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-5 w-5 rounded bg-[#CC9166]/15 flex items-center justify-center text-[#CC9166]">
            <Briefcase className="h-3.5 w-3.5" />
          </div>
          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-[#CC9166] font-semibold">
              CASE WORKFLOW
            </div>
            <h3 className="text-sm font-serif text-white">
              Lifecycle Transition
            </h3>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-[#777A88]">{caseData.id}</span>
          <CaseStatusBadge status={caseData.status} />
        </div>
      </div>

      {msg && (
        <div
          className={`p-2.5 rounded-lg text-xs flex items-center gap-2 ${
            msg.isError
              ? "bg-[#EF4444]/10 border border-[#EF4444]/30 text-[#EF4444]"
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
              className="w-full bg-[#12141A] border border-white/[0.08] rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-[#CC9166] transition-colors"
            >
              <option value="NEW">NEW</option>
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
              className="w-full bg-[#12141A] border border-white/[0.08] rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-[#CC9166] transition-colors"
            />
          </div>
        </div>

        <div>
          <label className="block text-[10px] font-mono text-[#777A88] uppercase mb-1">
            Analyst Investigation Notes
          </label>
          <textarea
            rows={2}
            value={analystNotes}
            onChange={(e) => setAnalystNotes(e.target.value)}
            placeholder="Document rationale, verified syndicate rings, or escalation instructions..."
            className="w-full bg-[#12141A] border border-white/[0.08] rounded-lg p-2.5 text-xs text-white placeholder-[#5E616E] focus:outline-none focus:border-[#CC9166] transition-colors"
          />
        </div>

        <div className="flex items-center justify-between pt-1">
          <span className="text-[10px] font-mono text-[#5E616E] flex items-center gap-1">
            <FileCheck2 className="h-3 w-3 text-[#10B981]" />
            <span>Immutable audit logged</span>
          </span>
          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-[#CC9166] text-[#08080A] font-bold text-xs hover:bg-[#CC9166]/90 disabled:opacity-40 transition-all shadow-md"
          >
            <Send className="h-3 w-3" />
            <span>{loading ? "Recording..." : "Record Action"}</span>
          </button>
        </div>
      </form>
    </div>
  );
}
