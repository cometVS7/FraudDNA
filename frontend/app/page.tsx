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
  Activity,
  Layers,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  ZAxis,
} from "recharts";

const RISK_BAR_COLORS = [
  "#8FAF9B", // Low
  "#C7A66B", // Review / Medium
  "#C47A63", // High
  "#D05B5B", // Critical
];

const DECISION_COLORS = [
  "#8FAF9B", // ALLOW
  "#C7A66B", // REVIEW
  "#D05B5B", // HOLD
];

export default function OverviewPage() {
  const overview = useAsync<OverviewData>(() => fetchOverview(), []);
  const clusters = useAsync<ClustersResponse>(
    () => fetchClusters({ suspicious_only: true, limit: 5 }),
    []
  );
  const recentRiskTx = useAsync<TransactionsResponse>(
    () =>
      fetchTransactions({
        limit: 12,
        sort_by: "risk_score",
        sort_order: "desc",
        suspicious_only: true,
      }),
    []
  );

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Executive Risk Intelligence Header */}
        <div className="border-b border-[#1C1D22] pb-6">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div className="space-y-2">
              <div className="text-[11px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-[#CC9166]" />
                Institutional Risk Intelligence
              </div>
              <h1 className="text-3xl md:text-4xl lg:text-5xl font-serif tracking-tight text-white font-normal">
                See the risk before it becomes a loss.
              </h1>
              <p className="text-sm md:text-base text-[#9194A1] max-w-3xl font-sans leading-relaxed">
                Transaction intelligence, network exposure and decision activity across the enterprise payment infrastructure.
              </p>
            </div>
            <div className="flex items-center gap-2.5 self-start md:self-auto">
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#121317] border border-[#1C1D22] text-[11px] font-mono text-[#9194A1]">
                <Activity className="h-3 w-3 text-[#8FAF9B]" />
                <span>Engine Active</span>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#121317] border border-[#1C1D22] text-[11px] font-mono text-[#AE9357]">
                <Layers className="h-3 w-3 text-[#AE9357]" />
                <span>Policy Controls</span>
              </div>
            </div>
          </div>
        </div>

        {overview.status === "loading" && (
          <LoadingState message="Querying enterprise risk intelligence kernel..." />
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
            {/* Primary Institutional KPI Layer */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard
                label="Transaction Universe"
                value={formatNumber(overview.data.total_transactions)}
                sublabel="Total processed ledger records"
                icon={<TrendingUp className="h-4 w-4" />}
              />
              <MetricCard
                label="Exposure at Risk"
                value={formatINR(overview.data.fraud_exposure)}
                sublabel={`${formatPct(overview.data.fraud_rate)} baseline incident rate`}
                variant="danger"
                icon={<ShieldAlert className="h-4 w-4" />}
              />
              <MetricCard
                label="Priority Transactions"
                value={formatNumber(overview.data.suspicious_transactions)}
                sublabel={`${overview.data.critical_risk_count} critical • threshold ≥ 0.37`}
                variant="warning"
                icon={<Eye className="h-4 w-4" />}
              />
              <MetricCard
                label="Active Risk Networks"
                value={overview.data.suspicious_clusters}
                sublabel={`of ${overview.data.total_clusters} isolated network structures`}
                variant="warning"
                icon={<Share2 className="h-4 w-4" />}
              />
            </div>

            {/* Visual Analytics Layer: Risk Distribution & Decision Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Risk Distribution Card */}
              <div className="lg:col-span-7">
                <SectionCard
                  title="Risk Distribution"
                  subtitle="Transaction universe partitioned by predictive risk severity tiers"
                >
                  <div className="h-68 w-full pt-4">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={[
                          {
                            name: "Low (<0.30)",
                            tier: "Low",
                            value: overview.data.risk_distribution.low,
                            fill: RISK_BAR_COLORS[0],
                          },
                          {
                            name: "Medium (0.30-0.70)",
                            tier: "Medium",
                            value: overview.data.risk_distribution.medium,
                            fill: RISK_BAR_COLORS[1],
                          },
                          {
                            name: "High (0.70-0.90)",
                            tier: "High",
                            value: overview.data.risk_distribution.high,
                            fill: RISK_BAR_COLORS[2],
                          },
                          {
                            name: "Critical (≥0.90)",
                            tier: "Critical",
                            value: overview.data.risk_distribution.critical,
                            fill: RISK_BAR_COLORS[3],
                          },
                        ]}
                        margin={{ top: 12, right: 16, bottom: 4, left: 0 }}
                      >
                        <CartesianGrid
                          strokeDasharray="2 4"
                          stroke="#1C1D22"
                          vertical={false}
                        />
                        <XAxis
                          dataKey="name"
                          tick={{ fill: "#777A88", fontSize: 11, fontFamily: "var(--font-inter)" }}
                          axisLine={{ stroke: "#1C1D22" }}
                          tickLine={false}
                        />
                        <YAxis
                          tick={{ fill: "#777A88", fontSize: 11, fontFamily: "var(--font-mono)" }}
                          axisLine={{ stroke: "#1C1D22" }}
                          tickLine={false}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "#040406",
                            borderColor: "#1C1D22",
                            borderRadius: "6px",
                            boxShadow: "0 10px 30px rgba(0,0,0,0.8)",
                            fontSize: "12px",
                            fontFamily: "var(--font-inter)",
                            color: "#E2E3E9",
                          }}
                          itemStyle={{ color: "#E2E3E9" }}
                          cursor={{ fill: "rgba(255,255,255,0.02)" }}
                        />
                        <Bar
                          dataKey="value"
                          radius={[4, 4, 0, 0]}
                        >
                          {RISK_BAR_COLORS.map((color, idx) => (
                            <Cell key={`cell-${idx}`} fill={color} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="grid grid-cols-4 gap-2 pt-4 mt-2 border-t border-[#1C1D22] text-center">
                    <div>
                      <div className="text-[10px] font-mono text-[#5E616E]">LOW</div>
                      <div className="text-xs font-mono text-[#8FAF9B]">
                        {formatNumber(overview.data.risk_distribution.low)}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] font-mono text-[#5E616E]">MEDIUM</div>
                      <div className="text-xs font-mono text-[#C7A66B]">
                        {formatNumber(overview.data.risk_distribution.medium)}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] font-mono text-[#5E616E]">HIGH</div>
                      <div className="text-xs font-mono text-[#C47A63]">
                        {formatNumber(overview.data.risk_distribution.high)}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] font-mono text-[#5E616E]">CRITICAL</div>
                      <div className="text-xs font-mono text-[#D05B5B]">
                        {formatNumber(overview.data.risk_distribution.critical)}
                      </div>
                    </div>
                  </div>
                </SectionCard>
              </div>

              {/* Decision Engine Activity Card */}
              <div className="lg:col-span-5">
                <SectionCard
                  title="Decision Activity"
                  subtitle="Deterministic policy classification & action distribution"
                >
                  <div className="h-56 flex items-center justify-center pt-2">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={[
                            {
                              name: "ALLOW",
                              value: overview.data.risk_distribution.low,
                              fill: DECISION_COLORS[0],
                            },
                            {
                              name: "REVIEW",
                              value:
                                overview.data.risk_distribution.medium +
                                overview.data.risk_distribution.high,
                              fill: DECISION_COLORS[1],
                            },
                            {
                              name: "HOLD",
                              value: overview.data.risk_distribution.critical,
                              fill: DECISION_COLORS[2],
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
                          <Cell fill="#8FAF9B" />
                          <Cell fill="#C7A66B" />
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
                        <span className="h-2 w-2 rounded-full bg-[#8FAF9B]" />
                        <span className="text-[#9194A1]">ALLOW (Automated Clear)</span>
                      </div>
                      <span className="font-mono text-[#8FAF9B]">
                        {formatNumber(overview.data.risk_distribution.low)} ({formatPct(overview.data.risk_distribution.low / overview.data.total_transactions)})
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full bg-[#C7A66B]" />
                        <span className="text-[#9194A1]">REVIEW (Analyst Escalation)</span>
                      </div>
                      <span className="font-mono text-[#C7A66B]">
                        {formatNumber(overview.data.risk_distribution.medium + overview.data.risk_distribution.high)} ({formatPct((overview.data.risk_distribution.medium + overview.data.risk_distribution.high) / overview.data.total_transactions)})
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs pt-1 border-t border-[#1C1D22]/60">
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full bg-[#D05B5B]" />
                        <span className="text-[#9194A1]">HOLD (Risk Intercepted)</span>
                      </div>
                      <span className="font-mono font-medium text-[#D05B5B]">
                        {formatNumber(overview.data.risk_distribution.critical)} ({formatPct(overview.data.risk_distribution.critical / overview.data.total_transactions)})
                      </span>
                    </div>
                  </div>
                </SectionCard>
              </div>
            </div>

            {/* Secondary Visual Analytics: Risk vs Transaction Value & Network Concentration */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Risk vs Transaction Value Scatter */}
              <div className="lg:col-span-7">
                <SectionCard
                  title="Risk vs Transaction Value"
                  subtitle="Empirical relationship between monetary exposure and evaluated risk score"
                >
                  <div className="h-68 w-full pt-4">
                    {recentRiskTx.status === "success" && (
                      <ResponsiveContainer width="100%" height="100%">
                        <ScatterChart margin={{ top: 12, right: 16, bottom: 8, left: 10 }}>
                          <CartesianGrid strokeDasharray="2 4" stroke="#1C1D22" />
                          <XAxis
                            type="number"
                            dataKey="amount"
                            name="Amount"
                            unit="₹"
                            tick={{ fill: "#777A88", fontSize: 11, fontFamily: "var(--font-mono)" }}
                            axisLine={{ stroke: "#1C1D22" }}
                            tickLine={false}
                          />
                          <YAxis
                            type="number"
                            dataKey="risk_score"
                            name="Risk Score"
                            domain={[0, 1]}
                            tick={{ fill: "#777A88", fontSize: 11, fontFamily: "var(--font-mono)" }}
                            axisLine={{ stroke: "#1C1D22" }}
                            tickLine={false}
                          />
                          <ZAxis range={[60, 140]} />
                          <Tooltip
                            cursor={{ strokeDasharray: "3 3", stroke: "#2E3038" }}
                            contentStyle={{
                              backgroundColor: "#040406",
                              borderColor: "#1C1D22",
                              borderRadius: "6px",
                              fontSize: "12px",
                              color: "#E2E3E9",
                            }}
                            formatter={(value: any, name: any) => [
                              name === "Amount" ? `₹${Number(value).toLocaleString("en-IN")}` : Number(value).toFixed(4),
                              String(name || ""),
                            ]}
                          />
                          <Scatter
                            name="High-Risk Transactions"
                            data={recentRiskTx.data.transactions.map((t) => ({
                              amount: t.amount,
                              risk_score: t.risk_score,
                              id: t.transaction_id,
                            }))}
                            fill="#CC9166"
                          />
                        </ScatterChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                  <div className="pt-3 border-t border-[#1C1D22] flex items-center justify-between text-xs text-[#777A88] font-mono">
                    <span>Scatter: Monitored priority events</span>
                    <span className="text-[#CC9166]">Correlation: High-velocity & High-exposure</span>
                  </div>
                </SectionCard>
              </div>

              {/* Risk Network Concentration */}
              <div className="lg:col-span-5">
                <SectionCard
                  title="Risk Network Concentration"
                  subtitle="Exposure by detected coordinated fraud syndicates"
                  action={
                    <Link
                      href="/frauddna"
                      className="inline-flex items-center gap-1 text-[11px] font-mono text-[#CC9166] hover:text-[#E2E3E9] transition-colors"
                    >
                      <span>Explore Networks</span>
                      <ArrowRight className="h-3 w-3" />
                    </Link>
                  }
                >
                  <div className="divide-y divide-[#1C1D22]">
                    {clusters.status === "loading" && <LoadingState message="Loading risk networks..." />}
                    {clusters.status === "error" && (
                      <div className="text-xs text-[#C47A63] py-4">Failed to load risk networks.</div>
                    )}
                    {clusters.status === "success" && (
                      clusters.data.clusters.map((c) => (
                        <div key={c.cluster_id} className="py-3 group hover:bg-[#121317]/40 px-1 rounded transition-colors">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-xs text-white font-medium">
                                {c.cluster_id}
                              </span>
                              <RiskBadge
                                level={c.cluster_risk_score >= 0.9 ? "critical" : c.cluster_risk_score >= 0.7 ? "high" : "medium"}
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
                      ))
                    )}
                  </div>
                </SectionCard>
              </div>
            </div>

            {/* Lower Intelligence Row: Priority Activity & Case Investigation Entrypoint */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Panel 1: Priority Risk Activity */}
              <div className="lg:col-span-7">
                <SectionCard
                  title="Priority Transaction Activity"
                  subtitle="Transactions requiring immediate investigative review"
                  action={
                    <Link
                      href="/transactions"
                      className="inline-flex items-center gap-1 text-[11px] font-mono text-[#CC9166] hover:text-[#E2E3E9] transition-colors"
                    >
                      <span>Ledger View</span>
                      <ArrowRight className="h-3 w-3" />
                    </Link>
                  }
                >
                  {recentRiskTx.status === "loading" && <LoadingState message="Loading priority events..." />}
                  {recentRiskTx.status === "error" && (
                    <div className="text-xs text-[#C47A63] py-4">Failed to load priority transactions.</div>
                  )}
                  {recentRiskTx.status === "success" && (
                    <div className="divide-y divide-[#1C1D22]">
                      {recentRiskTx.data.transactions.slice(0, 5).map((tx) => (
                        <div
                          key={tx.transaction_id}
                          className="py-3 flex items-center justify-between gap-3 group hover:bg-[#121317]/40 px-1 rounded transition-colors"
                        >
                          <div className="min-w-0">
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
                              Cust: {tx.customer_id} • Device: {tx.device_id.slice(0, 8)} • IP: {tx.ip_address}
                            </div>
                          </div>
                          <div className="text-right flex-shrink-0">
                            <div className="font-mono text-xs text-[#E2E3E9]">
                              {formatINR(tx.amount)}
                            </div>
                            <div className="text-[10px] font-mono text-[#C47A63]">
                              Score: {tx.risk_score.toFixed(4)}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </SectionCard>
              </div>

              {/* Panel 2: Investigation Operations Workstation */}
              <div className="lg:col-span-5">
                <SectionCard
                  title="Investigation Operations"
                  subtitle="Forensic evidence reasoning and policy audit trail"
                  action={
                    <Link
                      href="/investigate"
                      className="inline-flex items-center gap-1 text-[11px] font-mono text-[#CC9166] hover:text-[#E2E3E9] transition-colors"
                    >
                      <span>Workstation</span>
                      <ArrowRight className="h-3 w-3" />
                    </Link>
                  }
                >
                  <div className="space-y-4">
                    <div className="p-3.5 rounded-md bg-[#121317] border border-[#1C1D22] space-y-2">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-2 rounded-full bg-[#8FAF9B] animate-pulse" />
                        <span className="text-xs font-mono font-medium text-white">
                          Forensic Investigation Engine
                        </span>
                      </div>
                      <p className="text-xs text-[#9194A1] leading-relaxed">
                        Multimodal evidence verification across entity relationship graphs, Tree SHAP risk signal attributions, and regulatory defense controls.
                      </p>
                    </div>

                    <div className="space-y-2">
                      <div className="text-[10px] font-mono uppercase tracking-wider text-[#5E616E]">
                        Operational Capabilities
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs font-mono text-[#9194A1]">
                        <div className="p-2 rounded bg-[#040406] border border-[#1C1D22] flex items-center gap-2">
                          <CheckCircle2 className="h-3.5 w-3.5 text-[#CC9166]" />
                          <span>Graph Traversal</span>
                        </div>
                        <div className="p-2 rounded bg-[#040406] border border-[#1C1D22] flex items-center gap-2">
                          <CheckCircle2 className="h-3.5 w-3.5 text-[#AE9357]" />
                          <span>Tree SHAP Signals</span>
                        </div>
                        <div className="p-2 rounded bg-[#040406] border border-[#1C1D22] flex items-center gap-2">
                          <CheckCircle2 className="h-3.5 w-3.5 text-[#8FAF9B]" />
                          <span>Decision Engine</span>
                        </div>
                        <div className="p-2 rounded bg-[#040406] border border-[#1C1D22] flex items-center gap-2">
                          <CheckCircle2 className="h-3.5 w-3.5 text-[#777A88]" />
                          <span>Compliance Audit</span>
                        </div>
                      </div>
                    </div>

                    <div className="pt-2">
                      <Link
                        href="/investigate"
                        className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-md bg-[#CC9166] text-[#08080A] font-medium text-xs hover:bg-[#CC9166]/90 transition-all font-sans"
                      >
                        <Search className="h-3.5 w-3.5" />
                        <span>Launch Case Investigation</span>
                      </Link>
                    </div>
                  </div>
                </SectionCard>
              </div>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
