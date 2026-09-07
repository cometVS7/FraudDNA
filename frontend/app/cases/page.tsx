"use client";

import React, { useState } from "react";
import { DashboardLayout } from "@/components/layout";
import { CaseTable } from "@/components/cases/case-table";
import { CaseCreateModal } from "@/components/cases/case-create-modal";
import { useAsync } from "@/hooks/use-async";
import { fetchCases } from "@/lib/api";
import type { CaseListResponse, CaseResponse } from "@/types/case";
import {
  Briefcase,
  Plus,
  Search,
  Filter,
  RefreshCw,
  ShieldAlert,
  Clock,
  CheckCircle2,
} from "lucide-react";

export default function CasesPage() {
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [priorityFilter, setPriorityFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  const casesData = useAsync<CaseListResponse>(
    () =>
      fetchCases({
        limit: 100,
        offset: 0,
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
      }),
    [statusFilter, priorityFilter, reloadKey]
  );

  const allCases: CaseResponse[] =
    casesData.status === "success" ? casesData.data.items : [];
  const filteredCases = allCases.filter((c: CaseResponse) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.id.toLowerCase().includes(q) ||
      c.title.toLowerCase().includes(q) ||
      (c.owner ? c.owner.toLowerCase().includes(q) : false) ||
      c.investigation_ids.some((inv: string) => inv.toLowerCase().includes(q))
    );
  });

  const totalCases = allCases.length;
  const newCases = allCases.filter((c) => c.status === "NEW").length;
  const escalatedCases = allCases.filter((c) => c.status === "ESCALATED").length;
  const inReviewCases = allCases.filter((c) => c.status === "IN_REVIEW").length;
  const resolvedCases = allCases.filter((c) => c.status === "RESOLVED").length;

  function handleCaseCreated() {
    setReloadKey((k) => k + 1);
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="border-b border-[#1C1D22] pb-5 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <div className="text-[10px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold">
              OPERATIONAL WORKFLOWS
            </div>
            <h1 className="text-3xl font-serif tracking-tight text-white font-normal mt-1">
              Case Management Queue
            </h1>
            <p className="text-xs text-[#9194A1] font-sans mt-1">
              Triage, assign, and manage multi-entity fraud investigations and syndicate attacks.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setReloadKey((k) => k + 1)}
              className="p-2 text-[#777A88] hover:text-white bg-[#121317] border border-[#1C1D22] rounded hover:border-[#CC9166]/40 transition-colors"
              title="Refresh queue"
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={() => setIsCreateOpen(true)}
              className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium rounded bg-[#CC9166] text-[#08080A] hover:bg-[#CC9166]/90 transition-opacity"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Create Case</span>
            </button>
          </div>
        </div>

        {/* Metrics Overview Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase text-[#777A88]">Total Active</span>
              <Briefcase className="h-4 w-4 text-[#CC9166]" />
            </div>
            <div className="text-2xl font-serif text-white mt-1.5">{totalCases}</div>
          </div>

          <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase text-[#60A5FA]">New / In Review</span>
              <Clock className="h-4 w-4 text-[#60A5FA]" />
            </div>
            <div className="text-2xl font-serif text-white mt-1.5">
              {newCases + inReviewCases}
            </div>
          </div>

          <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase text-[#D05B5B]">Escalated</span>
              <ShieldAlert className="h-4 w-4 text-[#D05B5B]" />
            </div>
            <div className="text-2xl font-serif text-[#D05B5B] mt-1.5">{escalatedCases}</div>
          </div>

          <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase text-[#34D399]">Resolved</span>
              <CheckCircle2 className="h-4 w-4 text-[#34D399]" />
            </div>
            <div className="text-2xl font-serif text-white mt-1.5">{resolvedCases}</div>
          </div>
        </div>

        {/* Search & Filter Utility Bar */}
        <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-3 flex flex-wrap items-center justify-between gap-3">
          <div className="relative flex-1 min-w-[240px] max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#5E616E]" />
            <input
              type="text"
              placeholder="Search cases by ID, title, owner, or transaction..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-[#121317] border border-[#1C1D22] rounded font-mono text-[#E2E3E9] placeholder-[#5E616E] focus:outline-none focus:border-[#CC9166]"
            />
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs text-[#777A88]">
              <Filter className="h-3 w-3" />
              <span>Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-[#121317] border border-[#1C1D22] rounded px-2 py-1 text-xs text-[#E2E3E9] focus:outline-none focus:border-[#CC9166]"
              >
                <option value="">All Statuses</option>
                <option value="NEW">NEW</option>
                <option value="IN_REVIEW">IN_REVIEW</option>
                <option value="ESCALATED">ESCALATED</option>
                <option value="RESOLVED">RESOLVED</option>
                <option value="CLOSED">CLOSED</option>
              </select>
            </div>

            <div className="flex items-center gap-1.5 text-xs text-[#777A88]">
              <span>Priority:</span>
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="bg-[#121317] border border-[#1C1D22] rounded px-2 py-1 text-xs text-[#E2E3E9] focus:outline-none focus:border-[#CC9166]"
              >
                <option value="">All Priorities</option>
                <option value="CRITICAL">CRITICAL</option>
                <option value="HIGH">HIGH</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="LOW">LOW</option>
              </select>
            </div>
          </div>
        </div>

        {/* Case Queue Table */}
        <CaseTable cases={filteredCases} loading={casesData.status === "loading"} />
      </div>

      <CaseCreateModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onCreated={handleCaseCreated}
      />
    </DashboardLayout>
  );
}
