"use client";

import { DashboardLayout } from "@/components/layout";
import {
  MetricCard,
  SectionCard,
  LoadingState,
  ErrorState,
  DataLabel,
  formatINR,
  formatPct,
  formatNumber,
} from "@/components/ui";
import { useAsync } from "@/hooks/use-async";
import { fetchEvaluation } from "@/lib/api";
import type { EvaluationMetrics } from "@/lib/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { BarChart3, Target, AlertTriangle, IndianRupee } from "lucide-react";

export default function EvaluationPage() {
  const data = useAsync<EvaluationMetrics>(() => fetchEvaluation(), []);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight">Model Evaluation</h2>
            <p className="text-sm text-muted-foreground">
              Phase 1 LightGBM held-out test set evaluation
            </p>
          </div>
          <DataLabel label="Synthetic Held-Out Evaluation" />
        </div>

        {data.status === "loading" && <LoadingState message="Loading evaluation..." />}
        {data.status === "error" && <ErrorState error={data.error} onRetry={data.refetch} />}

        {data.status === "success" && (
          <>
            {/* Methodology Banner */}
            <div className="bg-blue-50/50 border border-blue-100 rounded-xl p-4">
              <p className="text-xs text-blue-700 font-medium mb-1">Evaluation Methodology</p>
              <p className="text-xs text-blue-600 leading-relaxed">
                Chronological train/validation/test split. Threshold ({data.data.selected_operating_threshold}) selected on validation set only.
                Final metrics computed on held-out test set ({formatNumber(data.data.held_out_test_size)} transactions).
                No label leakage. No future-information leakage. Seed-reproducible.
              </p>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              <MetricCard
                label="Precision"
                value={formatPct(data.data.metrics.precision)}
                variant="success"
                icon={<Target className="h-4 w-4" />}
              />
              <MetricCard
                label="Recall"
                value={formatPct(data.data.metrics.recall)}
                variant="success"
                icon={<BarChart3 className="h-4 w-4" />}
              />
              <MetricCard
                label="F1 Score"
                value={formatPct(data.data.metrics.f1_score)}
                variant="success"
              />
              <MetricCard
                label="PR-AUC"
                value={data.data.metrics.pr_auc.toFixed(4)}
                variant="success"
              />
              <MetricCard
                label="FPR"
                value={formatPct(data.data.metrics.false_positive_rate)}
                sublabel={`${data.data.confusion_matrix.false_positives} FP`}
                variant="warning"
                icon={<AlertTriangle className="h-4 w-4" />}
              />
              <MetricCard
                label="Net Benefit"
                value={formatINR(data.data.cost_and_financial_impact.net_business_benefit_inr)}
                variant="success"
                icon={<IndianRupee className="h-4 w-4" />}
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Confusion Matrix */}
              <SectionCard title="Confusion Matrix" subtitle={`Threshold: ${data.data.selected_operating_threshold}`}>
                <div className="grid grid-cols-2 gap-3 max-w-sm mx-auto">
                  <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-center">
                    <p className="text-xs text-emerald-600 font-medium mb-1">True Positives</p>
                    <p className="text-2xl font-bold text-emerald-700">{formatNumber(data.data.confusion_matrix.true_positives)}</p>
                  </div>
                  <div className="p-4 rounded-lg bg-amber-50 border border-amber-200 text-center">
                    <p className="text-xs text-amber-600 font-medium mb-1">False Positives</p>
                    <p className="text-2xl font-bold text-amber-700">{formatNumber(data.data.confusion_matrix.false_positives)}</p>
                  </div>
                  <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-center">
                    <p className="text-xs text-red-600 font-medium mb-1">False Negatives</p>
                    <p className="text-2xl font-bold text-red-700">{formatNumber(data.data.confusion_matrix.false_negatives)}</p>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-center">
                    <p className="text-xs text-slate-600 font-medium mb-1">True Negatives</p>
                    <p className="text-2xl font-bold text-slate-700">{formatNumber(data.data.confusion_matrix.true_negatives)}</p>
                  </div>
                </div>
              </SectionCard>

              {/* Financial Impact */}
              <SectionCard title="Financial Impact" subtitle="Cost and benefit analysis (INR)">
                <div className="space-y-3">
                  {[
                    { label: "Total Fraud Exposure", value: data.data.cost_and_financial_impact.total_fraud_loss_exposure_inr, color: "text-red-600" },
                    { label: "Fraud Prevented", value: data.data.cost_and_financial_impact.fraud_prevented_amount_inr, color: "text-emerald-600" },
                    { label: "Fraud Missed", value: data.data.cost_and_financial_impact.fraud_missed_amount_inr, color: "text-red-600" },
                    { label: "FP Cost", value: data.data.cost_and_financial_impact.false_positive_monetary_cost_inr, color: "text-amber-600" },
                    { label: "Net Business Benefit", value: data.data.cost_and_financial_impact.net_business_benefit_inr, color: "text-emerald-700" },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center justify-between py-2 border-b border-border/50 last:border-0">
                      <span className="text-xs text-muted-foreground">{item.label}</span>
                      <span className={`text-sm font-mono font-bold ${item.color}`}>{formatINR(item.value)}</span>
                    </div>
                  ))}
                </div>
                <p className="text-[10px] text-muted-foreground mt-3">
                  Cost per FP: ₹{data.data.cost_and_financial_impact.cost_per_false_positive_inr}
                </p>
              </SectionCard>
            </div>

            {/* Scenario Breakdown */}
            <SectionCard title="Detection by Scenario" subtitle="Catch rate across fraud patterns">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={Object.entries(data.data.breakdown_by_scenario).map(([name, s]) => ({
                      name: name.replace(/_/g, " "),
                      catch_rate: s.catch_rate,
                      total: s.total_count,
                      caught: s.caught_count,
                    }))}
                    margin={{ top: 8, right: 8, bottom: 40, left: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-20} textAnchor="end" />
                    <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ borderRadius: "8px", border: "1px solid #e5e7eb", fontSize: "12px" }}
                      formatter={(v: unknown) => formatPct(Number(v) || 0)}
                    />
                    <Bar dataKey="catch_rate" name="Catch Rate" radius={[4, 4, 0, 0]}>
                      {Object.entries(data.data.breakdown_by_scenario).map(([, s], i) => (
                        <Cell key={i} fill={s.catch_rate >= 0.9 ? "#10b981" : s.catch_rate >= 0.5 ? "#f59e0b" : "#ef4444"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-muted-foreground uppercase tracking-wider border-b border-border">
                      <th className="text-left py-2 px-3 font-medium">Scenario</th>
                      <th className="text-right py-2 px-3 font-medium">Total</th>
                      <th className="text-right py-2 px-3 font-medium">Caught</th>
                      <th className="text-right py-2 px-3 font-medium">Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(data.data.breakdown_by_scenario).map(([name, s]) => (
                      <tr key={name} className="border-b border-border/50">
                        <td className="py-2 px-3 font-medium">{name.replace(/_/g, " ")}</td>
                        <td className="py-2 px-3 text-right font-mono">{formatNumber(s.total_count)}</td>
                        <td className="py-2 px-3 text-right font-mono">{formatNumber(s.caught_count)}</td>
                        <td className="py-2 px-3 text-right font-mono font-bold">{formatPct(s.catch_rate)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </SectionCard>

            {/* Disclaimer */}
            <div className="bg-amber-50/50 border border-amber-100 rounded-xl p-4 text-xs text-amber-700">
              <p className="font-semibold mb-1">⚠ Synthetic Evaluation</p>
              <p>These metrics are computed on a synthetic held-out test set. Synthetic benchmark performance does not equal production fraud detection performance. Results demonstrate methodology integrity, not deployment readiness.</p>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
