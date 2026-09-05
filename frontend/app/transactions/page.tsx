"use client";

import { useState, useCallback } from "react";
import { DashboardLayout } from "@/components/layout";
import {
  RiskBadge,
  LoadingState,
  ErrorState,
  EmptyState,
  DataLabel,
  formatINR,
} from "@/components/ui";
import { useAsync } from "@/hooks/use-async";
import { fetchTransactions } from "@/lib/api";
import type { TransactionsResponse } from "@/lib/api";
import { Search, ChevronLeft, ChevronRight, Filter } from "lucide-react";
import Link from "next/link";

const RISK_LEVELS = ["all", "low", "medium", "high", "critical"];

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

  return (
    <DashboardLayout>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight">Transactions</h2>
            <p className="text-sm text-muted-foreground">
              Transaction investigation table with risk scoring
            </p>
          </div>
          <DataLabel label="Synthetic Dataset" />
        </div>

        {/* Filters Row */}
        <div className="bg-card border border-border rounded-xl p-4 flex flex-wrap items-center gap-3">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search by ID, customer, merchant..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(0);
              }}
              className="w-full pl-9 pr-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
            />
          </div>

          {/* Risk Level Filter */}
          <div className="flex items-center gap-1.5">
            <Filter className="h-4 w-4 text-muted-foreground" />
            {RISK_LEVELS.map((level) => (
              <button
                key={level}
                onClick={() => {
                  setRiskFilter(level);
                  setPage(0);
                }}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
                  riskFilter === level
                    ? "bg-primary/10 text-primary border-primary/30"
                    : "bg-background text-muted-foreground border-border hover:bg-muted/50"
                }`}
              >
                {level === "all" ? "All" : level.charAt(0).toUpperCase() + level.slice(1)}
              </button>
            ))}
          </div>

          {/* Suspicious Only Toggle */}
          <label className="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer">
            <input
              type="checkbox"
              checked={suspiciousOnly}
              onChange={(e) => {
                setSuspiciousOnly(e.target.checked);
                setPage(0);
              }}
              className="rounded border-border"
            />
            Suspicious Only
          </label>
        </div>

        {/* Table */}
        {data.status === "loading" && <LoadingState message="Loading transactions..." />}
        {data.status === "error" && (
          <ErrorState error={data.error} onRetry={data.refetch} />
        )}
        {data.status === "success" && data.data.transactions.length === 0 && (
          <EmptyState
            title="No transactions found"
            description="Adjust your search or filters"
          />
        )}
        {data.status === "success" && data.data.transactions.length > 0 && (
          <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-muted-foreground uppercase tracking-wider border-b border-border bg-muted/30">
                    <th
                      className="text-left py-3 px-4 font-medium cursor-pointer hover:text-foreground"
                      onClick={() => handleSort("transaction_id")}
                    >
                      Transaction ID
                    </th>
                    <th className="text-left py-3 px-4 font-medium">Timestamp</th>
                    <th
                      className="text-right py-3 px-4 font-medium cursor-pointer hover:text-foreground"
                      onClick={() => handleSort("amount")}
                    >
                      Amount
                    </th>
                    <th className="text-left py-3 px-4 font-medium">Customer</th>
                    <th
                      className="text-center py-3 px-4 font-medium cursor-pointer hover:text-foreground"
                      onClick={() => handleSort("risk_score")}
                    >
                      Risk Score
                    </th>
                    <th className="text-center py-3 px-4 font-medium">Risk Level</th>
                    <th className="text-center py-3 px-4 font-medium">Fraud</th>
                    <th className="text-left py-3 px-4 font-medium">Cluster</th>
                    <th className="text-center py-3 px-4 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {data.data.transactions.map((tx) => (
                    <tr
                      key={tx.transaction_id}
                      className="border-b border-border/50 hover:bg-muted/20 transition-colors"
                    >
                      <td className="py-2.5 px-4 font-mono text-xs">
                        {tx.transaction_id}
                      </td>
                      <td className="py-2.5 px-4 text-xs text-muted-foreground">
                        {tx.timestamp ? new Date(tx.timestamp).toLocaleString("en-IN", { dateStyle: "short", timeStyle: "short" }) : "—"}
                      </td>
                      <td className="py-2.5 px-4 text-right font-mono text-xs">
                        {formatINR(tx.amount)}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-xs text-muted-foreground">
                        {tx.customer_id}
                      </td>
                      <td className="py-2.5 px-4 text-center font-mono text-xs font-semibold">
                        {tx.risk_score.toFixed(4)}
                      </td>
                      <td className="py-2.5 px-4 text-center">
                        <RiskBadge level={tx.risk_level} size="xs" />
                      </td>
                      <td className="py-2.5 px-4 text-center">
                        {tx.is_fraud ? (
                          <span className="text-red-600 text-xs font-medium">●</span>
                        ) : (
                          <span className="text-emerald-500 text-xs">○</span>
                        )}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-[10px] text-muted-foreground">
                        {tx.cluster_id || "—"}
                      </td>
                      <td className="py-2.5 px-4 text-center">
                        <Link
                          href={`/investigate?tx=${tx.transaction_id}`}
                          className="px-2.5 py-1 text-xs font-medium text-primary border border-primary/30 rounded-lg hover:bg-primary/5 transition-colors"
                        >
                          Investigate
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between px-4 py-3 border-t border-border bg-muted/20">
              <p className="text-xs text-muted-foreground">
                Showing {page * limit + 1}–{Math.min((page + 1) * limit, data.data.total)}{" "}
                of {data.data.total.toLocaleString()}
              </p>
              <div className="flex items-center gap-1">
                <button
                  disabled={page === 0}
                  onClick={() => setPage((p) => p - 1)}
                  className="p-1.5 rounded-lg border border-border text-muted-foreground hover:bg-muted/50 disabled:opacity-30 transition-colors"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <span className="px-3 py-1 text-xs font-mono text-muted-foreground">
                  {page + 1} / {totalPages}
                </span>
                <button
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage((p) => p + 1)}
                  className="p-1.5 rounded-lg border border-border text-muted-foreground hover:bg-muted/50 disabled:opacity-30 transition-colors"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
