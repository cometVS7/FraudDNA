"use client";

import React, { use } from "react";
import Link from "next/link";
import { DashboardLayout } from "@/components/layout";
import { CaseStatusBadge, CasePriorityBadge } from "@/components/cases/case-status-badge";
import { CaseActionToolbar } from "@/components/workbench/case-action-toolbar";
import { useAsync } from "@/hooks/use-async";
import { fetchCase } from "@/lib/api";
import type { CaseResponse } from "@/types/case";
import {
  ArrowLeft,
  ArrowUpRight,
  FileText,
  Calendar,
  User,
  Zap,
} from "lucide-react";

export default function CaseDetailPage({
  params,
}: {
  params: Promise<{ case_id: string }>;
}) {
  const resolvedParams = use(params);
  const caseId = resolvedParams.case_id;

  const caseData = useAsync<CaseResponse | null>(
    () => (caseId ? fetchCase(caseId).catch(() => null) : Promise.resolve(null)),
    [caseId]
  );

  const c = caseData.status === "success" ? caseData.data : null;

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-[1400px] mx-auto pb-12">
        {/* Back Link */}
        <div>
          <Link
            href="/cases"
            className="inline-flex items-center gap-1.5 text-xs font-mono text-[#777A88] hover:text-[#CC9166] transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Case Queue</span>
          </Link>
        </div>

        {caseData.status === "loading" && (
          <div className="p-12 text-center text-xs text-[#777A88]">Loading case details...</div>
        )}

        {c && (
          <div className="space-y-6">
            {/* Header Card */}
            <div className="bg-[#0A0C10]/95 border border-white/[0.08] rounded-xl p-6 shadow-2xl backdrop-blur-xl">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span className="font-mono text-xs text-[#777A88]">CASE /</span>
                    <span className="font-mono text-sm font-bold text-[#CC9166]">
                      {c.id}
                    </span>
                    <CaseStatusBadge status={c.status} size="sm" />
                    <CasePriorityBadge priority={c.priority} size="sm" />
                  </div>
                  <h1 className="text-2xl font-serif text-white font-normal">{c.title}</h1>
                </div>

                <div className="flex items-center gap-4 text-xs font-mono">
                  <div className="bg-[#12141A] p-2.5 rounded-lg border border-white/[0.06]">
                    <div className="text-[10px] text-[#777A88] uppercase">Assigned Analyst</div>
                    <div className="text-white mt-0.5 font-semibold flex items-center gap-1">
                      <User className="h-3 w-3 text-[#CC9166]" />
                      <span>{c.owner || "Unassigned"}</span>
                    </div>
                  </div>
                  <div className="bg-[#12141A] p-2.5 rounded-lg border border-white/[0.06]">
                    <div className="text-[10px] text-[#777A88] uppercase">Created Date</div>
                    <div className="text-white mt-0.5 flex items-center gap-1">
                      <Calendar className="h-3 w-3 text-[#777A88]" />
                      <span>{c.created_at ? new Date(c.created_at).toLocaleDateString("en-IN") : "—"}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Left Column: Details & Linked Investigations (8 Cols) */}
              <div className="lg:col-span-7 space-y-6">
                {/* Notes & Summary */}
                <div className="bg-[#0A0C10]/95 border border-white/[0.08] rounded-xl p-5 space-y-2 shadow-xl backdrop-blur-xl">
                  <div className="text-[10px] font-mono uppercase text-[#CC9166] tracking-widest font-semibold flex items-center gap-1.5">
                    <FileText className="h-3.5 w-3.5" />
                    <span>CASE SUMMARY & TRIAGE NOTES</span>
                  </div>
                  <p className="text-xs text-[#E2E3E9] leading-relaxed bg-[#12141A] p-3 rounded-lg border border-white/[0.04]">
                    {c.notes || "No initial notes recorded for this case."}
                  </p>
                </div>

                {/* Linked Investigations */}
                <div className="bg-[#0A0C10]/95 border border-white/[0.08] rounded-xl p-5 space-y-3.5 shadow-xl backdrop-blur-xl">
                  <div className="text-[10px] font-mono uppercase text-[#CC9166] tracking-widest font-semibold flex items-center gap-1.5">
                    <Zap className="h-3.5 w-3.5" />
                    <span>LINKED INVESTIGATIONS ({c.investigation_ids?.length || 0})</span>
                  </div>

                  {c.investigation_ids?.length === 0 ? (
                    <div className="text-xs text-[#777A88]">No investigations linked yet.</div>
                  ) : (
                    <div className="space-y-2">
                      {c.investigation_ids?.map((invId) => {
                        const txId = invId.replace(/^inv_/, "");
                        return (
                          <div
                            key={invId}
                            className="p-3.5 bg-[#12141A] border border-white/[0.06] hover:border-white/[0.12] rounded-lg flex items-center justify-between text-xs transition-all"
                          >
                            <div className="space-y-0.5">
                              <div className="font-mono text-[#CC9166] font-semibold">{invId}</div>
                              <div className="text-[10px] font-mono text-[#777A88]">
                                Target Transaction: <span className="text-[#E2E3E9]">{txId}</span>
                              </div>
                            </div>
                            <Link
                              href={`/investigate?tx=${txId}&case_id=${c.id}`}
                              className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-mono text-[#CC9166] hover:text-white bg-[#181A22] border border-[#CC9166]/40 hover:border-[#CC9166] rounded-lg transition-all"
                            >
                              <span>Open Workbench</span>
                              <ArrowUpRight className="h-3 w-3" />
                            </Link>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>

              {/* Right Column: Workflow Actions (5 Cols) */}
              <div className="lg:col-span-5 space-y-6">
                <CaseActionToolbar
                  caseData={c}
                  onCaseUpdated={() => caseData.refetch()}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
