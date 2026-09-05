"use client";

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
import { fetchOverview, fetchClusters } from "@/lib/api";
import type { OverviewData, ClustersResponse } from "@/lib/api";
import {
  Shield,
  AlertTriangle,
  Eye,
  GitBranch,
  IndianRupee,
  TrendingUp,
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
} from "recharts";

const RISK_COLORS = {
  low: "#10b981",
  medium: "#f59e0b",
  high: "#f97316",
  critical: "#ef4444",
};

export default function OverviewPage() {
  const overview = useAsync<OverviewData>(() => fetchOverview(), []);
  const clusters = useAsync<ClustersResponse>(
    () => fetchClusters({ suspicious_only: true, limit: 5 }),
    []
  );

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-foreground">
              Risk Overview
            </h2>
            <p className="text-sm text-muted-foreground">
              FraudDNA fraud intelligence dashboard
            </p>
          </div>
          <DataLabel label="Synthetic Dataset" />
        </div>

        {overview.status === "loading" && <LoadingState message="Loading overview..." />}
        {overview.status === "error" && (
          <ErrorState error={overview.error} onRetry={overview.refetch} />
        )}

        {overview.status === "success" && (
          <>
            {/* KPI Cards Row */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <MetricCard
                label="Transactions"
                value={formatNumber(overview.data.total_transactions)}
                sublabel="Total volume"
                icon={<TrendingUp className="h-4 w-4" />}
              />
              <MetricCard
                label="Fraud Detected"
                value={formatNumber(overview.data.fraud_count)}
                sublabel={`${formatPct(overview.data.fraud_rate)} rate`}
                variant="danger"
                icon={<AlertTriangle className="h-4 w-4" />}
              />
              <MetricCard
                label="Suspicious"
                value={formatNumber(overview.data.suspicious_transactions)}
                sublabel="Score ≥ 0.37"
                variant="warning"
                icon={<Eye className="h-4 w-4" />}
              />
              <MetricCard
                label="High Risk"
                value={formatNumber(overview.data.high_risk_count)}
                sublabel={`${overview.data.critical_risk_count} critical`}
                variant="danger"
                icon={<Shield className="h-4 w-4" />}
              />
              <MetricCard
                label="Fraud Clusters"
                value={overview.data.suspicious_clusters}
                sublabel={`of ${overview.data.total_clusters} total`}
                variant="warning"
                icon={<GitBranch className="h-4 w-4" />}
              />
              <MetricCard
                label="Fraud Exposure"
                value={formatINR(overview.data.fraud_exposure)}
                sublabel="Total fraud amount"
                variant="danger"
                icon={<IndianRupee className="h-4 w-4" />}
              />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Risk Distribution */}
              <SectionCard title="Risk Distribution" subtitle="Transaction classification by risk tier">
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={[
                        {
                          name: "Low",
                          value: overview.data.risk_distribution.low,
                          fill: RISK_COLORS.low,
                        },
                        {
                          name: "Medium",
                          value: overview.data.risk_distribution.medium,
                          fill: RISK_COLORS.medium,
                        },
                        {
                          name: "High",
                          value: overview.data.risk_distribution.high,
                          fill: RISK_COLORS.high,
                        },
                        {
                          name: "Critical",
                          value: overview.data.risk_distribution.critical,
                          fill: RISK_COLORS.critical,
                        },
                      ]}
                      margin={{ top: 8, right: 8, bottom: 0, left: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip
                        contentStyle={{
                          borderRadius: "8px",
                          border: "1px solid #e5e7eb",
                          fontSize: "12px",
                        }}
                      />
                      <Bar
                        dataKey="value"
                        radius={[6, 6, 0, 0]}
                        fill="#10b981"
                      >
                        {[
                          RISK_COLORS.low,
                          RISK_COLORS.medium,
                          RISK_COLORS.high,
                          RISK_COLORS.critical,
                        ].map((color, idx) => (
                          <Cell key={idx} fill={color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </SectionCard>

              {/* Fraud vs Legitimate */}
              <SectionCard title="Fraud vs Legitimate" subtitle="Ground-truth classification">
                <div className="h-64 flex items-center justify-center">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={[
                          {
                            name: "Legitimate",
                            value: overview.data.legitimate_count,
                          },
                          {
                            name: "Fraud",
                            value: overview.data.fraud_count,
                          },
                        ]}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={3}
                        dataKey="value"
                      >
                        <Cell fill="#10b981" />
                        <Cell fill="#ef4444" />
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          borderRadius: "8px",
                          border: "1px solid #e5e7eb",
                          fontSize: "12px",
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex justify-center gap-6 mt-2">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
                    Legitimate ({formatNumber(overview.data.legitimate_count)})
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="h-2.5 w-2.5 rounded-full bg-red-500" />
                    Fraud ({formatNumber(overview.data.fraud_count)})
                  </div>
                </div>
              </SectionCard>
            </div>

            {/* Suspicious Clusters Table */}
            {clusters.status === "success" &&
              clusters.data.clusters.length > 0 && (
                <SectionCard
                  title="Suspicious Clusters"
                  subtitle="Top coordinated fraud patterns detected by FraudDNA"
                >
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-xs text-muted-foreground uppercase tracking-wider border-b border-border">
                          <th className="text-left py-2 px-3 font-medium">Cluster</th>
                          <th className="text-left py-2 px-3 font-medium">Risk</th>
                          <th className="text-right py-2 px-3 font-medium">Txns</th>
                          <th className="text-right py-2 px-3 font-medium">Customers</th>
                          <th className="text-right py-2 px-3 font-medium">Amount</th>
                          <th className="text-left py-2 px-3 font-medium">Reason</th>
                        </tr>
                      </thead>
                      <tbody>
                        {clusters.data.clusters.map((c) => (
                          <tr
                            key={c.cluster_id}
                            className="border-b border-border/50 hover:bg-muted/30 transition-colors"
                          >
                            <td className="py-2.5 px-3 font-mono text-xs">
                              {c.cluster_id}
                            </td>
                            <td className="py-2.5 px-3">
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
                            </td>
                            <td className="py-2.5 px-3 text-right font-mono text-xs">
                              {c.transaction_count}
                            </td>
                            <td className="py-2.5 px-3 text-right font-mono text-xs">
                              {c.customer_count}
                            </td>
                            <td className="py-2.5 px-3 text-right font-mono text-xs">
                              {formatINR(c.suspicious_transaction_amount)}
                            </td>
                            <td className="py-2.5 px-3 text-xs text-muted-foreground max-w-[200px] truncate">
                              {c.primary_reason}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </SectionCard>
              )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
