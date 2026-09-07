"use client";

import React, { use } from "react";
import Link from "next/link";
import { DashboardLayout } from "@/components/layout";
import { CaseStatusBadge, CasePriorityBadge } from "@/components/cases/case-status-badge";
import { CaseActionToolbar } from "@/components/workbench/case-action-toolbar";
import { useAsync } from "@/hooks/use-async";
import { fetchCase } from "@/lib/api";
import type { CaseResponse } from "@/types/case";
import { ArrowLeft, ArrowUpRight } from "lucide-react";

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
      <div className="space-y-6">
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
            <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-6 shadow-2xl">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-[#5E616E]">CASE /</span>
                    <span className="font-mono text-sm font-semibold text-[#CC9166]">
                      {c.id}
                    </span>
                    <CaseStatusBadge status={c.status} size="sm" />
                    <CasePriorityBadge priority={c.priority} size="sm" />
                  </div>
                  <h1 className="text-2xl font-serif text-white font-normal">{c.title}</h1>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <div className="text-[10px] font-mono text-[#5E616E] uppercase">Assigned</div>
                    <div className="font-mono text-xs text-white mt-0.5">
                      {c.owner || "Unassigned"}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Details & Investigations (8 Cols) */}
              <div className="lg:col-span-8 space-y-6">
                {/* Notes & Summary */}
                <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-5 space-y-2">
                  <div className="text-[10px] font-mono uppercase text-[#777A88] tracking-wider font-semibold">
                    Case Summary & Notes
                  </div>
                  <p className="text-xs text-[#E2E3E9] leading-relaxed">
                    {c.notes || "No initial notes provided."}
                  </p>
                </div>

                {/* Linked Investigations */}
                <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-5 space-y-3">
                  <div className="text-[10px] font-mono uppercase text-[#CC9166] tracking-wider font-semibold">
                    Linked Investigations ({c.investigation_ids?.length || 0})
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
                            className="p-3 bg-[#0D0E12] border border-[#1C1D22] rounded flex items-center justify-between text-xs"
                          >
                            <div>
                              <div className="font-mono text-[#E2E3E9] font-semibold">{invId}</div>
                              <div className="text-[10px] font-mono text-[#5E616E]">
                                Target Transaction: {txId}
                              </div>
                            </div>
                            <Link
                              href={`/investigate?tx=${txId}&case_id=${c.id}`}
                              className="inline-flex items-center gap-1 px-3 py-1 text-xs font-mono text-[#CC9166] hover:text-white bg-[#121317] border border-[#1C1D22] hover:border-[#CC9166]/40 rounded transition-colors"
                            >
                              <span>Open in Workbench</span>
                              <ArrowUpRight className="h-3 w-3" />
                            </Link>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>

              {/* Right Column: Workflow Actions (4 Cols) */}
              <div className="lg:col-span-4 space-y-6">
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
