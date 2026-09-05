"use client";

import React, { useState, useCallback } from "react";
import { DashboardLayout } from "@/components/layout";
import {
  RiskBadge,
  DecisionBadge,
  LoadingState,
  ErrorState,
  EmptyState,
  DataLabel,
  formatINR,
} from "@/components/ui";
import { useAsync } from "@/hooks/use-async";
import { fetchTransactions } from "@/lib/api";
import type { TransactionsResponse } from "@/lib/api";
import {
  Search,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";

const RISK_LEVELS = [
  { key: "all", label: "All Tiers" },
  { key: "low", label: "Low" },
  { key: "medium", label: "Review" },
  { key: "high", label: "High" },
  { key: "critical", label: "Critical" },
];

export default function TransactionsPage() {
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("all");
  const [suspiciousOnly, setSuspiciousOnly] = useState(false);
  const [page, setPage] = useState(0);
  const [sortBy, setSortBy] = useState("risk_score");
  const [sortOrder, setSortOrder] = useState("desc");
  const limit = 25;

  const fetcher = useCallback(
    () =>
      fetchTransactions({
        limit,
        offset: page * limit,
        sort_by: sortBy,
        sort_order: sortOrder,
        risk_level: riskFilter !== "all" ? riskFilter : undefined,
        suspicious_only: suspiciousOnly || undefined,
        search: search || undefined,
      }),
    [page, sortBy, sortOrder, riskFilter, suspiciousOnly, search]
  );

  const data = useAsync<TransactionsResponse>(fetcher, [
    page,
    sortBy,
    sortOrder,
    riskFilter,
    suspiciousOnly,
    search,
  ]);

  const totalPages =
    data.status === "success" ? Math.ceil(data.data.total / limit) : 0;

  function handleSort(col: string) {
    if (sortBy === col) {
      setSortOrder((o) => (o === "desc" ? "asc" : "desc"));
    } else {
      setSortBy(col);
      setSortOrder("desc");
    }
    setPage(0);
  }

  // Determine policy projection based on score
  const getProjectedDecision = (score: number, isSuspicious: boolean) => {
    if (score >= 0.85 || isSuspicious) return "HOLD";
    if (score >= 0.37) return "REVIEW";
    return "ALLOW";
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Editorial Header */}
        <div className="border-b border-[#1C1D22] pb-5">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div>
              <div className="text-[11px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold">
                Transaction Ledger
              </div>
              <h1 className="text-3xl font-serif tracking-tight text-white font-normal mt-1">
                Transaction Intelligence
              </h1>
              <p className="text-xs text-[#9194A1] font-sans mt-1">
                High-density forensic ledger with risk scores, network clusters, and policy routing.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <DataLabel label="Synthetic Dataset" />
              {data.status === "success" && (
                <div className="text-xs font-mono text-[#777A88]">
                  {data.data.total.toLocaleString()} Records
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Filter Controls Bar */}
        <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-3.5 flex flex-wrap items-center justify-between gap-3">
          {/* Search */}
          <div className="relative flex-1 min-w-[240px] max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#5E616E]" />
            <input
              type="text"
              placeholder="Filter by tx_..., cust_..., dev_..., ip_..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(0);
              }}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-[#121317] border border-[#1C1D22] rounded-md text-[#E2E3E9] placeholder-[#5E616E] font-mono focus:outline-none focus:border-[#CC9166] transition-colors"
            />
          </div>

          {/* Risk Filters & Toggles */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="inline-flex items-center gap-1 bg-[#121317] p-1 rounded-md border border-[#1C1D22]">
              {RISK_LEVELS.map((level) => (
                <button
                  key={level.key}
                  onClick={() => {
                    setRiskFilter(level.key);
                    setPage(0);
                  }}
                  className={`px-2.5 py-1 text-[11px] font-mono rounded transition-colors ${
                    riskFilter === level.key
                      ? "bg-[#1C1D22] text-[#CC9166] font-medium"
                      : "text-[#777A88] hover:text-[#E2E3E9]"
                  }`}
                >
                  {level.label}
                </button>
              ))}
            </div>

            <button
              onClick={() => {
                setSuspiciousOnly((v) => !v);
                setPage(0);
              }}
              className={`px-3 py-1.5 text-xs font-mono rounded-md border transition-all ${
                suspiciousOnly
                  ? "bg-[#CC9166]/10 border-[#CC9166] text-[#CC9166]"
                  : "bg-[#121317] border-[#1C1D22] text-[#777A88] hover:text-[#E2E3E9]"
              }`}
            >
              Suspicious Only
            </button>
          </div>
        </div>

        {/* Ledger Table */}
        {data.status === "loading" && <LoadingState message="Streaming ledger records..." />}
        {data.status === "error" && (
          <ErrorState
            title="FAILED TO LOAD TRANSACTIONS"
            error={data.error}
            onRetry={data.refetch}
          />
        )}
        {data.status === "success" && data.data.transactions.length === 0 && (
          <EmptyState
            title="NO MATCHING TRANSACTIONS"
            description="No transactions matched your search or risk filter criteria."
            action={{
              label: "Reset Ledger Filters",
              onClick: () => {
                setSearch("");
                setRiskFilter("all");
                setSuspiciousOnly(false);
              },
            }}
          />
        )}

        {data.status === "success" && data.data.transactions.length > 0 && (
          <div className="bg-[#040406] border border-[#1C1D22] rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#1C1D22] bg-[#08080A] text-[#5E616E] font-mono text-[10px] uppercase tracking-wider">
                    <th
                      className="py-3 px-4 cursor-pointer hover:text-white transition-colors"
                      onClick={() => handleSort("transaction_id")}
                    >
                      <div className="flex items-center gap-1">
                        <span>TRANSACTION</span>
                        <ArrowUpDown className="h-3 w-3 opacity-60" />
                      </div>
                    </th>
                    <th
                      className="py-3 px-4 text-right cursor-pointer hover:text-white transition-colors"
                      onClick={() => handleSort("amount")}
                    >
                      <div className="flex items-center justify-end gap-1">
                        <span>AMOUNT</span>
                        <ArrowUpDown className="h-3 w-3 opacity-60" />
                      </div>
                    </th>
                    <th className="py-3 px-4">CUSTOMER</th>
                    <th className="py-3 px-4">DEVICE</th>
                    <th
                      className="py-3 px-4 text-center cursor-pointer hover:text-white transition-colors"
                      onClick={() => handleSort("risk_score")}
                    >
                      <div className="flex items-center justify-center gap-1">
                        <span>RISK</span>
                        <ArrowUpDown className="h-3 w-3 opacity-60" />
                      </div>
                    </th>
                    <th className="py-3 px-4">CLUSTER</th>
                    <th className="py-3 px-4 text-center">DECISION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1C1D22]/60">
                  {data.data.transactions.map((tx) => {
                    const projected = getProjectedDecision(tx.risk_score, tx.is_fraud);
                    return (
                      <tr
                        key={tx.transaction_id}
                        className="group hover:bg-[#121317]/50 transition-colors"
                      >
                        <td className="py-2.5 px-4">
                          <Link
                            href={`/investigate?tx=${tx.transaction_id}`}
                            className="font-mono text-xs text-white group-hover:text-[#CC9166] transition-colors flex items-center gap-1.5"
                          >
                            <span>{tx.transaction_id}</span>
                            <ExternalLink className="h-2.5 w-2.5 opacity-0 group-hover:opacity-100 text-[#CC9166] transition-opacity" />
                          </Link>
                          <div className="text-[10px] font-mono text-[#5E616E]">
                            {tx.timestamp
                              ? new Date(tx.timestamp).toLocaleString("en-IN", {
                                  dateStyle: "short",
                                  timeStyle: "short",
                                })
                              : "—"}
                          </div>
                        </td>

                        <td className="py-2.5 px-4 text-right font-mono text-xs text-[#E2E3E9] font-medium">
                          {formatINR(tx.amount)}
                        </td>

                        <td className="py-2.5 px-4 font-mono text-xs text-[#9194A1]">
                          {tx.customer_id}
                        </td>

                        <td className="py-2.5 px-4 font-mono text-xs text-[#777A88]">
                          {tx.device_id.slice(0, 10)}
                        </td>

                        <td className="py-2.5 px-4 text-center">
                          <div className="flex flex-col items-center gap-1">
                            <span className="font-mono text-xs font-semibold text-white">
                              {tx.risk_score.toFixed(4)}
                            </span>
                            <RiskBadge level={tx.risk_level} size="xs" />
                          </div>
                        </td>

                        <td className="py-2.5 px-4 font-mono text-[11px]">
                          {tx.cluster_id ? (
                            <Link
                              href={`/frauddna?cluster=${tx.cluster_id}`}
                              className="text-[#CC9166] hover:underline"
                            >
                              {tx.cluster_id}
                            </Link>
                          ) : (
                            <span className="text-[#464853]">—</span>
                          )}
                        </td>

                        <td className="py-2.5 px-4 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <DecisionBadge action={projected} size="xs" />
                            <Link
                              href={`/investigate?tx=${tx.transaction_id}`}
                              className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#121317] border border-[#1C1D22] text-[#9194A1] hover:text-white hover:border-[#CC9166] transition-colors"
                            >
                              Audit
                            </Link>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="flex items-center justify-between px-4 py-3 border-t border-[#1C1D22] bg-[#08080A]">
              <p className="text-[11px] font-mono text-[#5E616E]">
                Showing {page * limit + 1}–
                {Math.min((page + 1) * limit, data.data.total)} of{" "}
                {data.data.total.toLocaleString()} transactions
              </p>
              <div className="flex items-center gap-2">
                <button
                  disabled={page === 0}
                  onClick={() => setPage((p) => p - 1)}
                  className="p-1.5 rounded bg-[#121317] border border-[#1C1D22] text-[#9194A1] hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  aria-label="Previous Page"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                </button>
                <span className="px-2 text-[11px] font-mono text-[#777A88]">
                  Page {page + 1} of {totalPages || 1}
                </span>
                <button
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage((p) => p + 1)}
                  className="p-1.5 rounded bg-[#121317] border border-[#1C1D22] text-[#9194A1] hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  aria-label="Next Page"
                >
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
