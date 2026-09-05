"use client";

import React, { useState, useCallback } from "react";
import { DashboardLayout } from "@/components/layout";
import {
  RiskBadge,
  DecisionBadge,
  LoadingState,
  ErrorState,
  EmptyState,
  formatINR,
  formatNumber,
  formatPct,
} from "@/components/ui";
import { useAsync } from "@/hooks/use-async";
import { fetchTransactions, fetchOverview } from "@/lib/api";
import type { TransactionsResponse, OverviewData } from "@/lib/api";
import {
  Search,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  ExternalLink,
  ShieldAlert,
  BarChart3,
  TrendingUp,
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

  const overview = useAsync<OverviewData>(() => fetchOverview(), []);

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
        {/* Forensic Financial Ledger Header */}
        <div className="border-b border-[#1C1D22] pb-5">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div>
              <div className="text-[11px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-[#CC9166]" />
                Forensic Financial Ledger
              </div>
              <h1 className="text-3xl font-serif tracking-tight text-white font-normal mt-1">
                Transaction Intelligence
              </h1>
              <p className="text-xs text-[#9194A1] font-sans mt-1">
                Review transaction-level risk signals and decision context.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#121317] border border-[#1C1D22] text-[11px] font-mono text-[#8FAF9B]">
                <span className="h-1.5 w-1.5 rounded-full bg-[#8FAF9B]" />
                <span>Live Audit Stream</span>
              </div>
              {data.status === "success" && (
                <div className="text-xs font-mono text-[#777A88]">
                  {data.data.total.toLocaleString()} Records
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Compact Visual Analytics Bar */}
        {overview.status === "success" && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Metric 1: Risk Distribution */}
            <div className="p-3.5 rounded-lg bg-[#040406] border border-[#1C1D22] flex flex-col justify-between">
              <div className="flex items-center justify-between text-[11px] font-mono text-[#777A88] mb-2">
                <span className="flex items-center gap-1.5 uppercase">
                  <BarChart3 className="h-3.5 w-3.5 text-[#CC9166]" />
                  Risk Distribution
                </span>
                <span className="text-white font-semibold">
                  {formatNumber(overview.data.total_transactions)}
                </span>
              </div>
              <div className="h-2 w-full bg-[#121317] rounded-full overflow-hidden flex border border-[#1C1D22]">
                <div
                  style={{
                    width: `${(overview.data.risk_distribution.low / overview.data.total_transactions) * 100}%`,
                  }}
                  className="bg-[#8FAF9B]"
                  title="Low Risk"
                />
                <div
                  style={{
                    width: `${(overview.data.risk_distribution.medium / overview.data.total_transactions) * 100}%`,
                  }}
                  className="bg-[#C7A66B]"
                  title="Review Risk"
                />
                <div
                  style={{
                    width: `${(overview.data.risk_distribution.high / overview.data.total_transactions) * 100}%`,
                  }}
                  className="bg-[#C47A63]"
                  title="High Risk"
                />
                <div
                  style={{
                    width: `${(overview.data.risk_distribution.critical / overview.data.total_transactions) * 100}%`,
                  }}
                  className="bg-[#D05B5B]"
                  title="Critical Risk"
                />
              </div>
              <div className="flex items-center justify-between text-[10px] font-mono pt-2 text-[#5E616E]">
                <span className="text-[#8FAF9B]">Low: {formatNumber(overview.data.risk_distribution.low)}</span>
                <span className="text-[#C7A66B]">Med: {formatNumber(overview.data.risk_distribution.medium)}</span>
                <span className="text-[#C47A63]">High: {formatNumber(overview.data.risk_distribution.high)}</span>
                <span className="text-[#D05B5B]">Crit: {formatNumber(overview.data.risk_distribution.critical)}</span>
              </div>
            </div>

            {/* Metric 2: Exposure Concentration */}
            <div className="p-3.5 rounded-lg bg-[#040406] border border-[#1C1D22] flex flex-col justify-between">
              <div className="flex items-center justify-between text-[11px] font-mono text-[#777A88] mb-1">
                <span className="flex items-center gap-1.5 uppercase">
                  <ShieldAlert className="h-3.5 w-3.5 text-[#D05B5B]" />
                  Exposure Concentration
                </span>
                <span className="text-[#D05B5B] font-semibold">
                  {formatPct(overview.data.fraud_rate)}
                </span>
              </div>
              <div className="text-xl font-serif text-white tracking-tight">
                {formatINR(overview.data.fraud_exposure)}
              </div>
              <div className="text-[10px] font-mono text-[#777A88] mt-1 flex items-center justify-between">
                <span>Concentrated in {overview.data.suspicious_clusters} risk networks</span>
                <span className="text-[#CC9166]">{overview.data.suspicious_transactions} flagged</span>
              </div>
            </div>

            {/* Metric 3: Amount / Risk Relationship */}
            <div className="p-3.5 rounded-lg bg-[#040406] border border-[#1C1D22] flex flex-col justify-between">
              <div className="flex items-center justify-between text-[11px] font-mono text-[#777A88] mb-1">
                <span className="flex items-center gap-1.5 uppercase">
                  <TrendingUp className="h-3.5 w-3.5 text-[#AE9357]" />
                  Amount / Risk Correlation
                </span>
                <span className="text-[#AE9357] font-semibold">Hold ≥ 0.85</span>
              </div>
              <div className="text-xl font-serif text-white tracking-tight">
                {formatNumber(overview.data.critical_risk_count)} Priority Holds
              </div>
              <div className="text-[10px] font-mono text-[#777A88] mt-1 flex items-center justify-between">
                <span>Escalation threshold: 0.3700</span>
                <span className="text-[#8FAF9B]">Auto-clear: &lt;0.3000</span>
              </div>
            </div>
          </div>
        )}

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
                    <th className="py-3 px-4">MERCHANT</th>
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

                        <td className="py-2.5 px-4 font-mono text-xs text-[#9194A1]">
                          {tx.merchant_id || "—"}
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
