"use client";

import React from "react";
import Link from "next/link";
import { CasePriorityBadge, CaseStatusBadge } from "./case-status-badge";
import type { CaseResponse } from "@/types/case";
import { ArrowUpRight, Calendar, User, FileText } from "lucide-react";

interface CaseTableProps {
  cases: CaseResponse[];
  loading?: boolean;
  onSelectCase?: (c: CaseResponse) => void;
}

export function CaseTable({ cases, loading = false, onSelectCase }: CaseTableProps) {
  if (loading) {
    return (
      <div className="border border-white/[0.08] rounded-xl overflow-hidden bg-[#0A0C10]/95 p-8 text-center text-xs text-[#777A88]">
        Loading case queue...
      </div>
    );
  }

  if (cases.length === 0) {
    return (
      <div className="border border-white/[0.08] rounded-xl overflow-hidden bg-[#0A0C10]/95 p-12 text-center shadow-xl">
        <FileText className="h-8 w-8 text-[#5E616E] mx-auto mb-3" />
        <h3 className="text-sm font-serif text-white">No Cases Found</h3>
        <p className="text-xs text-[#777A88] mt-1">
          No operational cases match the selected filter criteria.
        </p>
      </div>
    );
  }

  return (
    <div className="border border-white/[0.08] rounded-xl overflow-hidden bg-[#0A0C10]/95 shadow-xl backdrop-blur-xl">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-sans">
          <thead className="bg-[#0E1017]/80 text-[#777A88] uppercase text-[10px] font-mono tracking-wider border-b border-white/[0.06]">
            <tr>
              <th className="py-3 px-4">Case ID</th>
              <th className="py-3 px-4">Title</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Priority</th>
              <th className="py-3 px-4">Owner</th>
              <th className="py-3 px-4">Investigations</th>
              <th className="py-3 px-4">Created</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {cases.map((c) => {
              const primaryTx = c.investigation_ids?.[0]?.replace(/^inv_/, "") || "";
              const workbenchHref = primaryTx
                ? `/investigate?tx=${primaryTx}&case_id=${c.id}`
                : `/cases/${c.id}`;

              return (
                <tr
                  key={c.id}
                  onClick={() => onSelectCase && onSelectCase(c)}
                  className="hover:bg-[#12141A]/80 transition-colors group cursor-pointer"
                >
                  <td className="py-3 px-4 font-mono text-[#CC9166] font-semibold text-[11px]">
                    <Link
                      href={`/cases/${c.id}`}
                      className="hover:underline"
                    >
                      {c.id}
                    </Link>
                  </td>
                  <td className="py-3 px-4 text-[#E2E3E9] font-medium max-w-xs truncate">
                    <Link
                      href={`/cases/${c.id}`}
                      className="hover:text-white"
                    >
                      {c.title}
                    </Link>
                  </td>
                  <td className="py-3 px-4">
                    <CaseStatusBadge status={c.status} />
                  </td>
                  <td className="py-3 px-4">
                    <CasePriorityBadge priority={c.priority} />
                  </td>
                  <td className="py-3 px-4 font-mono text-[11px] text-[#9194A1]">
                    <span className="inline-flex items-center gap-1">
                      <User className="h-3 w-3 text-[#5E616E]" />
                      {c.owner || "Unassigned"}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-[11px] text-[#9194A1]">
                    {c.investigation_ids?.length || 0} linked
                  </td>
                  <td className="py-3 px-4 font-mono text-[11px] text-[#5E616E]">
                    <span className="inline-flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {c.created_at ? new Date(c.created_at).toLocaleDateString("en-IN") : "—"}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <Link
                      href={workbenchHref}
                      onClick={(e) => e.stopPropagation()}
                      className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-mono text-[#CC9166] hover:text-white bg-[#14161F] hover:bg-[#CC9166]/20 border border-white/[0.08] hover:border-[#CC9166]/50 rounded-lg transition-all"
                    >
                      <span>Workbench</span>
                      <ArrowUpRight className="h-3 w-3" />
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
