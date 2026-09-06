"use client";

import React from "react";
import Link from "next/link";
import { DashboardLayout } from "@/components/layout";
import {
  MetricCard,
  RiskBadge,
  SectionCard,
  LoadingState,
  ErrorState,
  DataLabel,
  formatINR,
  formatPct,
  formatNumber,
} from "@/components/ui";
import { useAsync } from "@/hooks/use-async";
import { fetchOverview, fetchClusters, fetchTransactions } from "@/lib/api";
import type { OverviewData, ClustersResponse, TransactionsResponse } from "@/lib/api";
import {
  TrendingUp,
  Eye,
  Share2,
  ArrowRight,
  ShieldAlert,
  Search,
  CheckCircle2,
} from "lucide-react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
} from "recharts";

export default function OverviewPage() {
  const overview = useAsync<OverviewData>(() => fetchOverview(), []);
  const clusters = useAsync<ClustersResponse>(
    () => fetchClusters({ suspicious_only: true, limit: 5 }),
    []
  );
  const recentRiskTx = useAsync<TransactionsResponse>(
    () =>
      fetchTransactions({
        limit: 5,
        sort_by: "risk_score",
        sort_order: "desc",
        suspicious_only: true,
      }),
    []
  );

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Executive Header */}
        <div className="border-b border-[#1C1D22] pb-6">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div className="space-y-2">
              <div className="text-[11px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold">
                Risk Intelligence
              </div>
              <h1 className="text-3xl md:text-4xl lg:text-5xl font-serif tracking-tight text-white font-normal">
                See the risk before it becomes a loss.
              </h1>
              <p className="text-sm md:text-base text-[#9194A1] max-w-3xl font-sans leading-relaxed">
                A live view of transaction risk, coordinated fraud networks,
                investigation activity, and financial exposure across the payment ecosystem.
              </p>
            </div>
            <div className="flex items-center gap-3 self-start md:self-auto">
              <DataLabel label="Synthetic Dataset" />
              <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#121317] border border-[#1C1D22] text-xs font-mono text-[#777A88]">
                <span>Seed #42</span>
              </div>
            </div>
          </div>
        </div>

        {overview.status === "loading" && (
          <LoadingState message="Connecting to fraud intelligence kernel..." />
        )}
        {overview.status === "error" && (
          <ErrorState
            title="RISK INTELLIGENCE UNAVAILABLE"
            error={overview.error}
            onRetry={overview.refetch}
          />
        )}

        {overview.status === "success" && (
          <>
            {/* Primary KPI Grid: 4 Core Cards as Specified */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard
                label="Transactions"
                value={formatNumber(overview.data.total_transactions)}
                sublabel="Total processed volume"
                icon={<TrendingUp className="h-4 w-4" />}
              />
              <MetricCard
                label="Fraud Exposure"
                value={formatINR(overview.data.fraud_exposure)}
                sublabel={`${formatPct(overview.data.fraud_rate)} overall attack rate`}
                variant="danger"
                icon={<ShieldAlert className="h-4 w-4" />}
              />
              <MetricCard
                label="Suspicious Transactions"
                value={formatNumber(overview.data.suspicious_transactions)}
                sublabel={`${overview.data.critical_risk_count} critical • score ≥ 0.37`}
                variant="warning"
                icon={<Eye className="h-4 w-4" />}
              />
              <MetricCard
                label="Suspicious Clusters"
                value={overview.data.suspicious_clusters}
                sublabel={`of ${overview.data.total_clusters} isolated network clusters`}
                variant="warning"
                icon={<Share2 className="h-4 w-4" />}
              />
            </div>

            {/* Analytical Visualizations Row */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Risk Distribution Card */}
              <div className="lg:col-span-7">
                <SectionCard
                  title="Risk Distribution"
                  subtitle="Volume partition by ML score severity tiers"
                >
                  <div className="space-y-6 pt-2">
                    {/* Header metrics row */}
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-[10px] font-mono tracking-wider text-[#5E616E] uppercase">
                          Total Evaluated Volume
                        </div>
                        <div className="text-2xl font-serif text-white mt-0.5">
                          {formatNumber(overview.data.total_transactions)}{" "}
                          <span className="text-xs font-sans text-[#777A88] font-normal">transactions</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-[10px] font-mono tracking-wider text-[#5E616E] uppercase">
                          Elevated / Critical Risk
                        </div>
                        <div className="text-2xl font-mono text-[#D05B5B] mt-0.5">
                          {formatPct(
                            (overview.data.risk_distribution.critical + overview.data.risk_distribution.high) /
                              overview.data.total_transactions
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Compact Horizontal Stacked Distribution Bar */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs text-[#777A88] font-mono">
                        <span>Risk Spectrum Partition</span>
                        <span className="text-[11px] text-[#5E616E]">Threshold Spectrum [0.00 — 1.00]</span>
                      </div>

                      {/* Stacked Bar Container */}
                      <div
                        className="relative w-full h-8 bg-[#121317] rounded-md p-1 border border-[#1C1D22] flex gap-1 items-center overflow-hidden"
                        role="progressbar"
                        aria-label="Risk score distribution across transactions"
                      >
                        {/* Low Segment */}
                        <div
                          style={{
                            flex: `${Math.max(overview.data.risk_distribution.low, 1)} 1 0%`,
                            minWidth: "24px",
                          }}
                          className="h-full rounded-sm bg-[#8FAF9B]/85 hover:bg-[#8FAF9B] transition-colors group relative cursor-pointer"
                          title={`Low (<0.37): ${formatNumber(overview.data.risk_distribution.low)} txns (${formatPct(
                            overview.data.risk_distribution.low / overview.data.total_transactions
                          )})`}
                        />
                        {/* Review Segment */}
                        <div
                          style={{
                            flex: `${Math.max(overview.data.risk_distribution.medium, 1)} 1 0%`,
                            minWidth: "16px",
                          }}
                          className="h-full rounded-sm bg-[#C7A66B]/85 hover:bg-[#C7A66B] transition-colors group relative cursor-pointer"
                          title={`Review (0.37–0.70): ${formatNumber(overview.data.risk_distribution.medium)} txns (${formatPct(
                            overview.data.risk_distribution.medium / overview.data.total_transactions
                          )})`}
                        />
                        {/* High Segment */}
                        <div
                          style={{
                            flex: `${Math.max(overview.data.risk_distribution.high, 1)} 1 0%`,
                            minWidth: "16px",
                          }}
                          className="h-full rounded-sm bg-[#C47A63]/85 hover:bg-[#C47A63] transition-colors group relative cursor-pointer"
                          title={`High (0.70–0.90): ${formatNumber(overview.data.risk_distribution.high)} txns (${formatPct(
                            overview.data.risk_distribution.high / overview.data.total_transactions
                          )})`}
                        />
                        {/* Critical Segment */}
                        <div
                          style={{
                            flex: `${Math.max(overview.data.risk_distribution.critical, 1)} 1 0%`,
                            minWidth: "24px",
                          }}
                          className="h-full rounded-sm bg-[#D05B5B]/85 hover:bg-[#D05B5B] transition-colors group relative cursor-pointer"
                          title={`Critical (≥0.90): ${formatNumber(overview.data.risk_distribution.critical)} txns (${formatPct(
                            overview.data.risk_distribution.critical / overview.data.total_transactions
                          )})`}
                        />
                      </div>

                      {/* Threshold Markers */}
                      <div className="flex justify-between text-[10px] font-mono text-[#5E616E] px-0.5">
                        <span>0.00 (Low)</span>
                        <span>0.37 (Review)</span>
                        <span>0.70 (High)</span>
                        <span>0.90 (Critical)</span>
                        <span>1.00</span>
                      </div>
                    </div>

                    {/* Numerical Tiers Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-[#1C1D22]">
                      <div className="p-3 rounded-md bg-[#121317]/60 border border-[#1C1D22]/80">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono text-[#5E616E] uppercase">LOW</span>
                          <span className="h-1.5 w-1.5 rounded-full bg-[#8FAF9B]" />
                        </div>
                        <div className="text-base font-mono font-medium text-[#8FAF9B] mt-1.5">
                          {formatNumber(overview.data.risk_distribution.low)}
                        </div>
                        <div className="text-[10px] font-mono text-[#777A88] mt-0.5">
                          {formatPct(overview.data.risk_distribution.low / overview.data.total_transactions)} • &lt;0.37
                        </div>
                      </div>

                      <div className="p-3 rounded-md bg-[#121317]/60 border border-[#1C1D22]/80">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono text-[#5E616E] uppercase">REVIEW</span>
                          <span className="h-1.5 w-1.5 rounded-full bg-[#C7A66B]" />
                        </div>
                        <div className="text-base font-mono font-medium text-[#C7A66B] mt-1.5">
                          {formatNumber(overview.data.risk_distribution.medium)}
                        </div>
                        <div className="text-[10px] font-mono text-[#777A88] mt-0.5">
                          {formatPct(overview.data.risk_distribution.medium / overview.data.total_transactions)} • 0.37–0.70
                        </div>
                      </div>

                      <div className="p-3 rounded-md bg-[#121317]/60 border border-[#1C1D22]/80">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono text-[#5E616E] uppercase">HIGH</span>
                          <span className="h-1.5 w-1.5 rounded-full bg-[#C47A63]" />
                        </div>
                        <div className="text-base font-mono font-medium text-[#C47A63] mt-1.5">
                          {formatNumber(overview.data.risk_distribution.high)}
                        </div>
                        <div className="text-[10px] font-mono text-[#777A88] mt-0.5">
                          {formatPct(overview.data.risk_distribution.high / overview.data.total_transactions)} • 0.70–0.90
                        </div>
                      </div>

                      <div className="p-3 rounded-md bg-[#121317]/60 border border-[#1C1D22]/80">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono text-[#5E616E] uppercase">CRITICAL</span>
                          <span className="h-1.5 w-1.5 rounded-full bg-[#D05B5B]" />
                        </div>
                        <div className="text-base font-mono font-medium text-[#D05B5B] mt-1.5">
                          {formatNumber(overview.data.risk_distribution.critical)}
                        </div>
                        <div className="text-[10px] font-mono text-[#777A88] mt-0.5">
                          {formatPct(overview.data.risk_distribution.critical / overview.data.total_transactions)} • ≥0.90
                        </div>
                      </div>
                    </div>
                  </div>
                </SectionCard>
              </div>

              {/* Fraud Exposure & Volume Composition Card */}
              <div className="lg:col-span-5">
                <SectionCard
                  title="Fraud Exposure"
                  subtitle="Ground-truth classification & exposure split"
                >
                  <div className="h-56 flex items-center justify-center pt-2">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={[
                            {
                              name: "Legitimate",
                              value: overview.data.legitimate_count,
                              fill: "#1C1D22",
                            },
                            {
                              name: "Confirmed Fraud",
                              value: overview.data.fraud_count,
                              fill: "#C47A63",
                            },
                          ]}
                          cx="50%"
                          cy="50%"
                          innerRadius={64}
                          outerRadius={88}
                          stroke="#08080A"
                          strokeWidth={3}
                          paddingAngle={2}
                          dataKey="value"
                        >
                          <Cell fill="#2E3038" />
                          <Cell fill="#D05B5B" />
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "#040406",
                            borderColor: "#1C1D22",
                            borderRadius: "6px",
                            fontSize: "12px",
                            color: "#E2E3E9",
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="space-y-2.5 pt-4 border-t border-[#1C1D22]">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full bg-[#2E3038]" />
                        <span className="text-[#9194A1]">Legitimate Traffic</span>
                      </div>
                      <span className="font-mono text-[#E2E3E9]">
                        {formatNumber(overview.data.legitimate_count)} ({formatPct(1 - overview.data.fraud_rate)})
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full bg-[#D05B5B]" />
                        <span className="text-[#9194A1]">Fraud Incident Volume</span>
                      </div>
                      <span className="font-mono text-[#D05B5B]">
                        {formatNumber(overview.data.fraud_count)} ({formatPct(overview.data.fraud_rate)})
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs pt-1 border-t border-[#1C1D22]/60">
                      <span className="text-[#777A88]">Direct Monetary Loss Exposure</span>
                      <span className="font-mono font-medium text-[#CC9166]">
                        {formatINR(overview.data.fraud_exposure)}
                      </span>
                    </div>
                  </div>
                </SectionCard>
              </div>
            </div>

            {/* Lower Intelligence Row: 3 Panels (Recent High Risk, Networks, Investigation Activity) */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Panel 1: Recent High-Risk Activity */}
              <SectionCard
                title="Recent High-Risk Activity"
                subtitle="Priority transactions flagged by the model"
                action={
                  <Link
                    href="/transactions"
                    className="inline-flex items-center gap-1 text-[11px] font-mono text-[#CC9166] hover:text-[#E2E3E9] transition-colors"
                  >
                    <span>All Ledger</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                }
              >
                {recentRiskTx.status === "loading" && <LoadingState message="Loading high-risk events..." />}
                {recentRiskTx.status === "error" && (
                  <div className="text-xs text-[#C47A63] py-4">Failed to load high-risk ledger.</div>
                )}
                {recentRiskTx.status === "success" && (
                  <div className="divide-y divide-[#1C1D22]">
                    {recentRiskTx.data.transactions.map((tx) => (
                      <div
                        key={tx.transaction_id}
                        className="py-3 flex items-center justify-between gap-3 group hover:bg-[#121317]/40 px-1 rounded transition-colors"
                      >
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <Link
                              href={`/investigate?tx=${tx.transaction_id}`}
                              className="font-mono text-xs text-white group-hover:text-[#CC9166] transition-colors truncate"
                            >
                              {tx.transaction_id}
                            </Link>
                            <RiskBadge level={tx.risk_level} size="xs" />
                          </div>
                          <div className="text-[10px] font-mono text-[#5E616E] mt-0.5 truncate">
                            Cust: {tx.customer_id} • Device: {tx.device_id.slice(0, 8)}
                          </div>
                        </div>
                        <div className="flex items-center gap-3 flex-shrink-0">
                          <div className="text-right">
                            <div className="font-mono text-xs text-[#E2E3E9]">
                              {formatINR(tx.amount)}
                            </div>
                            <div className="text-[10px] font-mono text-[#C47A63]">
                              Score: {tx.risk_score.toFixed(3)}
                            </div>
                          </div>
                          <Link
                            href={`/investigate?tx=${tx.transaction_id}`}
                            className="inline-flex items-center gap-1 text-[11px] font-mono text-[#CC9166] hover:text-white px-2 py-1 rounded bg-[#121317] border border-[#1C1D22] hover:border-[#CC9166]/50 transition-colors"
                            title={`Investigate transaction ${tx.transaction_id}`}
                          >
                            <span>Investigate</span>
                            <ArrowRight className="h-3 w-3" />
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </SectionCard>

              {/* Panel 2: FraudDNA Networks */}
              <SectionCard
                title="FraudDNA Networks"
                subtitle="Coordinated syndicates & clusters"
                action={
                  <Link
                    href="/frauddna"
                    className="inline-flex items-center gap-1 text-[11px] font-mono text-[#CC9166] hover:text-[#E2E3E9] transition-colors"
                  >
                    <span>Graph View</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                }
              >
                {clusters.status === "loading" && <LoadingState message="Loading network clusters..." />}
                {clusters.status === "error" && (
                  <div className="text-xs text-[#C47A63] py-4">Failed to load clusters.</div>
                )}
                {clusters.status === "success" && (
                  <div className="divide-y divide-[#1C1D22]">
                    {clusters.data.clusters.map((c) => (
                      <div
                        key={c.cluster_id}
                        className="py-3 group hover:bg-[#121317]/40 px-1 rounded transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs text-white font-medium">
                              {c.cluster_id}
                            </span>
                            <RiskBadge
                              level={
                                c.cluster_risk_score >= 0.9
                                  ? "critical"
                                  : c.cluster_risk_score >= 0.7
                                  ? "high"
                                  : "medium"
                              }
                              size="xs"
                            />
                          </div>
                          <span className="font-mono text-xs text-[#CC9166]">
                            {formatINR(c.suspicious_transaction_amount)}
                          </span>
                        </div>
                        <div className="mt-1 flex items-center justify-between text-[10px] font-mono text-[#5E616E]">
                          <span>
                            {c.transaction_count} txns • {c.customer_count} cust • {c.device_count} dev
                          </span>
                          <span className="text-[#9194A1] truncate max-w-[140px]">
                            {c.primary_reason}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </SectionCard>

              {/* Panel 3: Investigation Activity */}
              <SectionCard
                title="Investigation Activity"
                subtitle="Autonomous forensic reasoning pipeline"
                action={
                  <Link
                    href="/investigate"
                    className="inline-flex items-center gap-1 text-[11px] font-mono text-[#CC9166] hover:text-[#E2E3E9] transition-colors"
                  >
                    <span>Console</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                }
              >
                <div className="space-y-4">
                  <div className="p-3.5 rounded-md bg-[#121317] border border-[#1C1D22] space-y-2">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-[#8FAF9B] animate-pulse" />
                      <span className="text-xs font-mono font-medium text-white">
                        Bounded Read-Only Agent Active
                      </span>
                    </div>
                    <p className="text-xs text-[#9194A1] leading-relaxed">
                      Investigates transactions using read-only graph traversal, SHAP
                      feature attributions, and grounded regulatory defense guidelines.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-[#5E616E]">
                      Inspection Capabilities
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs font-mono text-[#9194A1]">
                      <div className="p-2 rounded bg-[#040406] border border-[#1C1D22] flex items-center gap-2">
                        <CheckCircle2 className="h-3.5 w-3.5 text-[#CC9166]" />
                        <span>7 Forensic Tools</span>
                      </div>
                      <div className="p-2 rounded bg-[#040406] border border-[#1C1D22] flex items-center gap-2">
                        <CheckCircle2 className="h-3.5 w-3.5 text-[#AE9357]" />
                        <span>Vector RAG Grounded</span>
                      </div>
                      <div className="p-2 rounded bg-[#040406] border border-[#1C1D22] flex items-center gap-2">
                        <CheckCircle2 className="h-3.5 w-3.5 text-[#8FAF9B]" />
                        <span>Deterministic Decider</span>
                      </div>
                      <div className="p-2 rounded bg-[#040406] border border-[#1C1D22] flex items-center gap-2">
                        <CheckCircle2 className="h-3.5 w-3.5 text-[#777A88]" />
                        <span>Immutable Audit Trail</span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-2">
                    <Link
                      href="/investigate"
                      className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-md bg-[#CC9166] text-[#08080A] font-medium text-xs hover:bg-[#CC9166]/90 transition-all font-sans"
                    >
                      <Search className="h-3.5 w-3.5" />
                      <span>Launch Forensic Investigation</span>
                    </Link>
                  </div>
                </div>
              </SectionCard>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
