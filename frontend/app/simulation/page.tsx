"use client";

import { useState } from "react";
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
import { compareSimulations } from "@/lib/api";
import type { SimulationCompareResponse, SimulationConfig } from "@/lib/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  Legend,
} from "recharts";
import { SlidersHorizontal, Play, TrendingUp, AlertTriangle, IndianRupee } from "lucide-react";

const DEFAULT_THRESHOLDS = [0.10, 0.20, 0.30, 0.37, 0.50, 0.70, 0.90];

export default function SimulationPage() {
  const [costPerFP, setCostPerFP] = useState(350);
  const [reviewCapacity, setReviewCapacity] = useState(500);
  const [customThresholds, setCustomThresholds] = useState(DEFAULT_THRESHOLDS.join(", "));
  const [comparison, setComparison] = useState<SimulationCompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);

  async function runComparison() {
    setLoading(true);
    setError(null);
    try {
      const thresholds = customThresholds
        .split(",")
        .map((s) => parseFloat(s.trim()))
        .filter((n) => !isNaN(n) && n > 0 && n < 1);

      if (thresholds.length < 2) {
        setError("At least 2 valid thresholds required (between 0 and 1).");
        setLoading(false);
        return;
      }

      const configs: SimulationConfig[] = thresholds.map((t) => ({
        fraud_threshold: t,
        cost_per_false_positive: costPerFP,
        review_capacity: reviewCapacity,
      }));

      const result = await compareSimulations(configs);
      setComparison(result);
      setSelectedIdx(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation failed");
    }
    setLoading(false);
  }

  const selected = selectedIdx !== null && comparison ? comparison.results[selectedIdx] : null;

  // Chart data
  const chartData = comparison
    ? comparison.results.map((r) => ({
        threshold: r.config.fraud_threshold,
        precision: r.precision,
        recall: r.recall,
        f1: r.f1_score,
        fpr: r.false_positive_rate,
        fp: r.false_positives,
        expected_loss: r.expected_loss,
        net_benefit: r.net_benefit,
        fraud_prevented: r.fraud_prevented_amount,
        fraud_missed: r.fraud_missed_amount,
      }))
    : [];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight">Risk Simulation</h2>
            <p className="text-sm text-muted-foreground">
              Evaluate threshold configurations against the existing dataset
            </p>
          </div>
          <DataLabel label="Synthetic Dataset" />
        </div>

        {/* Controls */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <SlidersHorizontal className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold">Simulation Parameters</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="text-xs text-muted-foreground font-medium block mb-1.5">
                Thresholds (comma-separated)
              </label>
              <input
                type="text"
                value={customThresholds}
                onChange={(e) => setCustomThresholds(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 font-mono"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground font-medium block mb-1.5">
                Cost per False Positive (₹)
              </label>
              <input
                type="number"
                value={costPerFP}
                onChange={(e) => setCostPerFP(Number(e.target.value))}
                min={0}
                className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 font-mono"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground font-medium block mb-1.5">
                Review Capacity
              </label>
              <input
                type="number"
                value={reviewCapacity}
                onChange={(e) => setReviewCapacity(Number(e.target.value))}
                min={0}
                className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 font-mono"
              />
            </div>
          </div>

          <button
            onClick={runComparison}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2.5 text-sm font-medium bg-primary text-primary-foreground rounded-xl hover:opacity-90 disabled:opacity-40 transition-opacity"
          >
            <Play className="h-4 w-4" />
            {loading ? "Running..." : "Run Simulation"}
          </button>
        </div>

        {loading && <LoadingState message="Computing simulation..." />}
        {error && <ErrorState error={error} onRetry={runComparison} />}

        {comparison && (
          <>
            {/* KPI Summary for Selected or Best */}
            {(() => {
              const best = selected || comparison.results.reduce((a, b) => a.net_benefit > b.net_benefit ? a : b);
              return (
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                  <MetricCard
                    label="Threshold"
                    value={best.config.fraud_threshold.toFixed(2)}
                    sublabel={selected ? "Selected" : "Best net benefit"}
                    icon={<SlidersHorizontal className="h-4 w-4" />}
                  />
                  <MetricCard
                    label="Fraud Prevented"
                    value={formatINR(best.fraud_prevented_amount)}
                    variant="success"
                    icon={<TrendingUp className="h-4 w-4" />}
                  />
                  <MetricCard
                    label="Fraud Missed"
                    value={formatINR(best.fraud_missed_amount)}
                    variant="danger"
                    icon={<AlertTriangle className="h-4 w-4" />}
                  />
                  <MetricCard
                    label="False Positives"
                    value={formatNumber(best.false_positives)}
                    sublabel={`Cost: ${formatINR(best.false_positive_cost)}`}
                    variant="warning"
                  />
                  <MetricCard
                    label="Net Benefit"
                    value={formatINR(best.net_benefit)}
                    variant={best.net_benefit >= 0 ? "success" : "danger"}
                    icon={<IndianRupee className="h-4 w-4" />}
                  />
                  <MetricCard
                    label="Precision / Recall"
                    value={`${formatPct(best.precision)} / ${formatPct(best.recall)}`}
                    sublabel={`F1: ${formatPct(best.f1_score)}`}
                  />
                </div>
              );
            })()}

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Precision / Recall / F1 */}
              <SectionCard title="Precision, Recall & F1" subtitle="Classification performance vs threshold">
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="threshold" tick={{ fontSize: 11 }} />
                      <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={{ borderRadius: "8px", border: "1px solid #e5e7eb", fontSize: "12px" }} />
                      <Legend wrapperStyle={{ fontSize: "11px" }} />
                      <Line type="monotone" dataKey="precision" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
                      <Line type="monotone" dataKey="recall" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
                      <Line type="monotone" dataKey="f1" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </SectionCard>

              {/* Expected Loss */}
              <SectionCard title="Expected Loss & Net Benefit" subtitle="Financial impact vs threshold">
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="threshold" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={{ borderRadius: "8px", border: "1px solid #e5e7eb", fontSize: "12px" }} formatter={(v: unknown) => formatINR(Number(v) || 0)} />
                      <Legend wrapperStyle={{ fontSize: "11px" }} />
                      <Bar dataKey="net_benefit" name="Net Benefit" radius={[4, 4, 0, 0]}>
                        {chartData.map((d, i) => (
                          <Cell key={i} fill={d.net_benefit >= 0 ? "#10b981" : "#ef4444"} />
                        ))}
                      </Bar>
                      <Bar dataKey="expected_loss" name="Expected Loss" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </SectionCard>

              {/* False Positives */}
              <SectionCard title="False Positives" subtitle="FP count vs threshold">
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="threshold" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={{ borderRadius: "8px", border: "1px solid #e5e7eb", fontSize: "12px" }} />
                      <Bar dataKey="fp" name="False Positives" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </SectionCard>

              {/* Fraud Prevented vs Missed */}
              <SectionCard title="Fraud Impact" subtitle="Prevented vs missed fraud amount">
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="threshold" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={{ borderRadius: "8px", border: "1px solid #e5e7eb", fontSize: "12px" }} formatter={(v: unknown) => formatINR(Number(v) || 0)} />
                      <Legend wrapperStyle={{ fontSize: "11px" }} />
                      <Bar dataKey="fraud_prevented" name="Prevented" fill="#10b981" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="fraud_missed" name="Missed" fill="#ef4444" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </SectionCard>
            </div>

            {/* Comparison Table */}
            <SectionCard title="Threshold Comparison" subtitle="Side-by-side evaluation of all configurations">
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-muted-foreground uppercase tracking-wider border-b border-border">
                      <th className="text-left py-2 px-3 font-medium">Threshold</th>
                      <th className="text-right py-2 px-3 font-medium">TP</th>
                      <th className="text-right py-2 px-3 font-medium">FP</th>
                      <th className="text-right py-2 px-3 font-medium">FN</th>
                      <th className="text-right py-2 px-3 font-medium">Precision</th>
                      <th className="text-right py-2 px-3 font-medium">Recall</th>
                      <th className="text-right py-2 px-3 font-medium">F1</th>
                      <th className="text-right py-2 px-3 font-medium">FP Cost</th>
                      <th className="text-right py-2 px-3 font-medium">Fraud Missed</th>
                      <th className="text-right py-2 px-3 font-medium">Expected Loss</th>
                      <th className="text-right py-2 px-3 font-medium">Net Benefit</th>
                      <th className="text-center py-2 px-3 font-medium">Review</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparison.results.map((r, i) => (
                      <tr
                        key={i}
                        onClick={() => setSelectedIdx(i)}
                        className={`border-b border-border/50 cursor-pointer transition-colors ${
                          selectedIdx === i
                            ? "bg-primary/5"
                            : r.config.fraud_threshold === 0.37
                              ? "bg-emerald-50/30"
                              : "hover:bg-muted/20"
                        }`}
                      >
                        <td className="py-2 px-3 font-mono font-semibold">
                          {r.config.fraud_threshold.toFixed(2)}
                          {r.config.fraud_threshold === 0.37 && (
                            <span className="ml-1.5 text-[9px] text-emerald-600 font-normal">current</span>
                          )}
                        </td>
                        <td className="py-2 px-3 text-right font-mono">{r.true_positives}</td>
                        <td className="py-2 px-3 text-right font-mono text-amber-600">{r.false_positives}</td>
                        <td className="py-2 px-3 text-right font-mono text-red-600">{r.false_negatives}</td>
                        <td className="py-2 px-3 text-right font-mono">{formatPct(r.precision)}</td>
                        <td className="py-2 px-3 text-right font-mono">{formatPct(r.recall)}</td>
                        <td className="py-2 px-3 text-right font-mono">{formatPct(r.f1_score)}</td>
                        <td className="py-2 px-3 text-right font-mono">{formatINR(r.false_positive_cost)}</td>
                        <td className="py-2 px-3 text-right font-mono">{formatINR(r.fraud_missed_amount)}</td>
                        <td className="py-2 px-3 text-right font-mono">{formatINR(r.expected_loss)}</td>
                        <td className={`py-2 px-3 text-right font-mono font-bold ${r.net_benefit >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                          {formatINR(r.net_benefit)}
                        </td>
                        <td className="py-2 px-3 text-center">
                          {r.review_capacity_exceeded ? (
                            <span className="text-red-600">⚠ Over</span>
                          ) : (
                            <span className="text-emerald-600">✓</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <p className="text-[10px] text-muted-foreground mt-3">
                Lower threshold → catches more fraud → increases false positives. Higher threshold → reduces false positives → may allow more fraud through.
              </p>
            </SectionCard>

            {/* Financial Formulas */}
            <div className="bg-muted/30 rounded-xl border border-border p-4 text-xs text-muted-foreground font-mono">
              <p className="font-semibold text-foreground mb-2 font-sans text-sm">Financial Model</p>
              <p>expected_loss = fraud_missed_amount + false_positive_cost</p>
              <p>net_benefit   = fraud_prevented_amount - false_positive_cost</p>
              <p>false_positive_cost = false_positive_count × cost_per_false_positive</p>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
