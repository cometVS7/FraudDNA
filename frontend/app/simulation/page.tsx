"use client";

import React, { useState, useEffect } from "react";
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
import type { SimulationCompareResponse, SimulationConfig, SimulationResult } from "@/lib/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  SlidersHorizontal,
  Play,
  ShieldCheck,
  ShieldAlert,
  Target,
  DollarSign,
  TrendingUp,
} from "lucide-react";

const PRESET_THRESHOLDS = [0.15, 0.25, 0.37, 0.50, 0.65, 0.80, 0.90];

export default function SimulationPage() {
  const [fraudThreshold, setFraudThreshold] = useState<number>(0.37);
  const [reviewThreshold, setReviewThreshold] = useState<number>(0.20);
  const [costPerFP, setCostPerFP] = useState<number>(350);
  const [reviewCapacity, setReviewCapacity] = useState<number>(500);

  const [comparison, setComparison] = useState<SimulationCompareResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIdx, setSelectedIdx] = useState<number>(2); // Default to 0.37 baseline

  async function executeSimulation(targetThresholds: number[] = PRESET_THRESHOLDS) {
    setLoading(true);
    setError(null);
    try {
      const sortedThresholds = Array.from(
        new Set([...targetThresholds, fraudThreshold])
      ).sort((a, b) => a - b);

      const configs: SimulationConfig[] = sortedThresholds.map((t) => {
        const effectiveReviewThreshold =
          reviewThreshold < t
            ? reviewThreshold
            : Math.max(0.01, Math.min(reviewThreshold, Number((t - 0.01).toFixed(2))));

        return {
          fraud_threshold: t,
          review_threshold: effectiveReviewThreshold,
          cost_per_false_positive: costPerFP,
          review_capacity: reviewCapacity,
        };
      });

      const result = await compareSimulations(configs);
      setComparison(result);

      const matchIdx = result.results.findIndex(
        (r) => Math.abs(r.config.fraud_threshold - fraudThreshold) < 0.001
      );
      setSelectedIdx(matchIdx >= 0 ? matchIdx : result.baseline_index || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation execution failed");
    } finally {
      setLoading(false);
    }
  }

  // Auto-run baseline on mount
  useEffect(() => {
    executeSimulation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const activeResult: SimulationResult | null =
    comparison && comparison.results[selectedIdx] ? comparison.results[selectedIdx] : null;

  // Chart data formatting
  const chartData = comparison
    ? comparison.results.map((r, i) => ({
        index: i,
        threshold: r.config.fraud_threshold.toFixed(2),
        net_benefit: Math.round(r.net_benefit),
        expected_loss: Math.round(r.expected_loss),
        fraud_prevented: Math.round(r.fraud_prevented_amount),
        false_positive_cost: Math.round(r.false_positive_cost),
      }))
    : [];

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="border-b border-white/[0.06] pb-5">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div>
              <div className="text-[10px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold flex items-center gap-1.5">
                <SlidersHorizontal className="h-3.5 w-3.5" />
                <span>COUNTERFACTUAL POLICY OPTIMIZER</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-serif tracking-tight text-white font-normal mt-1">
                Risk & Financial Simulation
              </h1>
              <p className="text-xs text-[#9194A1] font-sans mt-1">
                Tune policy cutoffs, simulate trade-offs between fraud loss and false positive friction, and quantify net financial benefit.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <DataLabel label="Financial Risk Laboratory" />
            </div>
          </div>
        </div>

        {/* Controls Panel */}
        <div className="bg-[#0A0C10]/95 border border-white/[0.08] rounded-xl p-5 shadow-xl backdrop-blur-xl">
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-3 mb-4">
            <div className="flex items-center gap-2">
              <SlidersHorizontal className="h-4 w-4 text-[#CC9166]" />
              <span className="font-mono text-xs text-white font-medium">
                Simulation Parameter Boundaries
              </span>
            </div>
            <button
              onClick={() => executeSimulation()}
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#CC9166] text-[#08080A] text-xs font-bold hover:bg-[#CC9166]/90 disabled:opacity-40 transition-all shadow-md font-sans"
            >
              <Play className="h-3 w-3 fill-current" />
              <span>{loading ? "Simulating..." : "Execute Simulation"}</span>
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Fraud Threshold */}
            <div className="bg-[#12141A] p-3.5 rounded-lg border border-white/[0.06]">
              <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                <span className="text-[#777A88]">Fraud Threshold (Hold)</span>
                <span className="text-[#CC9166] font-bold">{fraudThreshold.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min={0.05}
                max={0.95}
                step={0.01}
                value={fraudThreshold}
                onChange={(e) => {
                  const newFraud = parseFloat(e.target.value);
                  setFraudThreshold(newFraud);
                  if (reviewThreshold >= newFraud) {
                    const safeReview = Math.max(0.01, Number((newFraud - 0.01).toFixed(2)));
                    setReviewThreshold(safeReview);
                  }
                }}
                className="w-full accent-[#CC9166] cursor-pointer"
              />
              <div className="flex justify-between text-[9px] font-mono text-[#5E616E] mt-1">
                <span>0.05 (Strict)</span>
                <span>0.95 (Permissive)</span>
              </div>
            </div>

            {/* Review Threshold */}
            <div className="bg-[#12141A] p-3.5 rounded-lg border border-white/[0.06]">
              <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                <span className="text-[#777A88]">Review Threshold</span>
                <span className="text-[#CC9166] font-bold">{reviewThreshold.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min={0.01}
                max={Math.max(0.01, Number((fraudThreshold - 0.01).toFixed(2)))}
                step={0.01}
                value={Math.min(
                  reviewThreshold,
                  Math.max(0.01, Number((fraudThreshold - 0.01).toFixed(2)))
                )}
                onChange={(e) => {
                  const maxAllowed = Math.max(0.01, Number((fraudThreshold - 0.01).toFixed(2)));
                  const val = Math.min(parseFloat(e.target.value), maxAllowed);
                  setReviewThreshold(val);
                }}
                className="w-full accent-[#CC9166] cursor-pointer"
              />
              <div className="flex justify-between text-[9px] font-mono text-[#5E616E] mt-1">
                <span>0.01 (Flag Early)</span>
                <span>{Math.max(0.01, Number((fraudThreshold - 0.01).toFixed(2))).toFixed(2)} (Cap)</span>
              </div>
            </div>

            {/* Cost Per False Positive */}
            <div className="bg-[#12141A] p-3.5 rounded-lg border border-white/[0.06]">
              <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                <span className="text-[#777A88]">Cost per FP</span>
                <span className="text-white font-bold">₹{costPerFP}</span>
              </div>
              <input
                type="number"
                min={50}
                max={5000}
                step={50}
                value={costPerFP}
                onChange={(e) => setCostPerFP(parseInt(e.target.value) || 350)}
                className="w-full px-3 py-1 text-xs bg-[#0A0C10] border border-white/[0.08] rounded-md text-[#E2E3E9] font-mono focus:outline-none focus:border-[#CC9166]"
              />
              <div className="text-[9px] font-mono text-[#5E616E] mt-1">
                Analyst triage + merchant churn
              </div>
            </div>

            {/* Review Capacity */}
            <div className="bg-[#12141A] p-3.5 rounded-lg border border-white/[0.06]">
              <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                <span className="text-[#777A88]">Daily Review Capacity</span>
                <span className="text-white font-bold">{reviewCapacity} txns</span>
              </div>
              <input
                type="number"
                min={100}
                max={5000}
                step={100}
                value={reviewCapacity}
                onChange={(e) => setReviewCapacity(parseInt(e.target.value) || 500)}
                className="w-full px-3 py-1 text-xs bg-[#0A0C10] border border-white/[0.08] rounded-md text-[#E2E3E9] font-mono focus:outline-none focus:border-[#CC9166]"
              />
              <div className="text-[9px] font-mono text-[#5E616E] mt-1">
                Analyst operations ceiling
              </div>
            </div>
          </div>
        </div>

        {loading && <LoadingState message="Calculating counterfactual loss curves..." />}
        {error && (
          <ErrorState
            title="SIMULATION COMPUTATION FAILED"
            error={error}
            onRetry={() => executeSimulation()}
          />
        )}

        {activeResult && (
          <>
            {/* 10 Required Analytical Metrics Grid */}
            <div className="space-y-3">
              <div className="text-[10px] font-mono uppercase text-[#CC9166] tracking-[0.16em] font-semibold">
                PERFORMANCE AT THRESHOLD {activeResult.config.fraud_threshold.toFixed(2)}
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                {/* 1. Fraud Prevented */}
                <MetricCard
                  label="Fraud Prevented"
                  value={formatINR(activeResult.fraud_prevented_amount)}
                  sublabel={`${activeResult.true_positives} attacks blocked`}
                  variant="success"
                  icon={<ShieldCheck className="h-4 w-4" />}
                />
                {/* 2. Fraud Missed */}
                <MetricCard
                  label="Fraud Missed"
                  value={formatINR(activeResult.fraud_missed_amount)}
                  sublabel={`${activeResult.false_negatives} slipped through`}
                  variant="danger"
                  icon={<ShieldAlert className="h-4 w-4" />}
                />
                {/* 3. False Positives */}
                <MetricCard
                  label="False Positives"
                  value={formatNumber(activeResult.false_positives)}
                  sublabel="Legitimate flagged"
                  variant="warning"
                  icon={<Target className="h-4 w-4" />}
                />
                {/* 4. False-Positive Cost */}
                <MetricCard
                  label="False-Positive Cost"
                  value={formatINR(activeResult.false_positive_cost)}
                  sublabel={`@ ₹${activeResult.config.cost_per_false_positive}/tx`}
                  icon={<DollarSign className="h-4 w-4" />}
                />
                {/* 5. Expected Loss */}
                <MetricCard
                  label="Expected Loss"
                  value={formatINR(activeResult.expected_loss)}
                  sublabel="Missed fraud + FP cost"
                  variant="danger"
                />
                {/* 6. Net Benefit (Gilded Accent) */}
                <div className="p-4 rounded-xl bg-[#0A0C10]/95 border border-[#CC9166]/50 shadow-[0_0_15px_rgba(204,145,102,0.15)] backdrop-blur-xl">
                  <div className="text-[10px] font-mono text-[#CC9166] uppercase tracking-wider font-semibold flex items-center gap-1">
                    <TrendingUp className="h-3 w-3" />
                    <span>Net Benefit</span>
                  </div>
                  <div className="text-2xl lg:text-3xl font-serif text-white tracking-tight mt-1 font-semibold">
                    {formatINR(activeResult.net_benefit)}
                  </div>
                  <div className="text-[10px] font-mono text-[#777A88] mt-0.5">
                    Prevented minus operational friction
                  </div>
                </div>
                {/* 7. Precision */}
                <MetricCard
                  label="Precision"
                  value={formatPct(activeResult.precision)}
                  sublabel="TP / (TP + FP)"
                />
                {/* 8. Recall */}
                <MetricCard
                  label="Recall"
                  value={formatPct(activeResult.recall)}
                  sublabel="TP / (TP + FN)"
                  variant="success"
                />
                {/* 9. F1 Score */}
                <MetricCard
                  label="F1 Score"
                  value={activeResult.f1_score.toFixed(3)}
                  sublabel="Harmonic balance"
                />
                {/* 10. FPR */}
                <MetricCard
                  label="FPR"
                  value={formatPct(activeResult.false_positive_rate)}
                  sublabel="FP / (FP + TN)"
                />
              </div>
            </div>

            {/* Main Analytical Visualization: Risk / Loss Tradeoff */}
            <SectionCard
              title="Risk / Loss Tradeoff"
              subtitle="Net benefit curve vs. expected total loss across threshold spectrum"
            >
              <div className="h-72 w-full pt-3">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 10, right: 20, bottom: 0, left: 10 }}>
                    <CartesianGrid strokeDasharray="2 4" stroke="rgba(255, 255, 255, 0.06)" vertical={false} />
                    <XAxis
                      dataKey="threshold"
                      tick={{ fill: "#777A88", fontSize: 11, fontFamily: "var(--font-mono)" }}
                      axisLine={{ stroke: "rgba(255, 255, 255, 0.08)" }}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fill: "#777A88", fontSize: 11, fontFamily: "var(--font-mono)" }}
                      axisLine={{ stroke: "rgba(255, 255, 255, 0.08)" }}
                      tickLine={false}
                      tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#0A0C10",
                        borderColor: "rgba(255, 255, 255, 0.12)",
                        borderRadius: "8px",
                        fontSize: "12px",
                        fontFamily: "var(--font-mono)",
                        color: "#E2E3E9",
                      }}
                      formatter={(value: unknown) => [formatINR(Number(value)), ""]}
                    />
                    <Legend
                      wrapperStyle={{
                        paddingTop: "12px",
                        fontSize: "11px",
                        fontFamily: "var(--font-sans)",
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="net_benefit"
                      name="Net Benefit"
                      stroke="#CC9166"
                      strokeWidth={2.5}
                      dot={{ fill: "#CC9166", r: 4 }}
                      activeDot={{ r: 6, fill: "#CC9166" }}
                    />
                    <Line
                      type="monotone"
                      dataKey="expected_loss"
                      name="Expected Loss"
                      stroke="#EF4444"
                      strokeWidth={1.8}
                      dot={{ fill: "#EF4444", r: 3 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="fraud_prevented"
                      name="Fraud Prevented"
                      stroke="#10B981"
                      strokeWidth={1.5}
                      strokeDasharray="4 4"
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </SectionCard>

            {/* Comparison Table */}
            <SectionCard
              title="Threshold Scenario Matrix"
              subtitle="Counterfactual trade-offs across simulated operating points"
            >
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-white/[0.06] bg-[#0E1017]/80 text-[#777A88] font-mono text-[10px] uppercase tracking-wider">
                      <th className="py-2.5 px-3">SCENARIO</th>
                      <th className="py-2.5 px-3">THRESHOLD</th>
                      <th className="py-2.5 px-3 text-right">PRECISION</th>
                      <th className="py-2.5 px-3 text-right">RECALL</th>
                      <th className="py-2.5 px-3 text-right">FALSE POSITIVES</th>
                      <th className="py-2.5 px-3 text-right">FRAUD PREVENTED</th>
                      <th className="py-2.5 px-3 text-right">EXPECTED LOSS</th>
                      <th className="py-2.5 px-3 text-right">NET BENEFIT</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.04] font-mono">
                    {comparison?.results.map((r, i) => {
                      const isSelected = selectedIdx === i;
                      return (
                        <tr
                          key={i}
                          onClick={() => setSelectedIdx(i)}
                          className={`cursor-pointer transition-colors ${
                            isSelected
                              ? "bg-[#14161F] text-white"
                              : "hover:bg-[#12141A]/50 text-[#9194A1]"
                          }`}
                        >
                          <td className="py-2.5 px-3">
                            <span className="flex items-center gap-1.5">
                              {isSelected && (
                                <span className="h-1.5 w-1.5 rounded-full bg-[#CC9166]" />
                              )}
                              <span>Scenario #{i + 1}</span>
                            </span>
                          </td>
                          <td className="py-2.5 px-3 font-semibold text-white">
                            {r.config.fraud_threshold.toFixed(2)}
                          </td>
                          <td className="py-2.5 px-3 text-right">{formatPct(r.precision)}</td>
                          <td className="py-2.5 px-3 text-right text-[#10B981]">
                            {formatPct(r.recall)}
                          </td>
                          <td className="py-2.5 px-3 text-right">{r.false_positives}</td>
                          <td className="py-2.5 px-3 text-right text-[#10B981]">
                            {formatINR(r.fraud_prevented_amount)}
                          </td>
                          <td className="py-2.5 px-3 text-right text-[#EF4444]">
                            {formatINR(r.expected_loss)}
                          </td>
                          <td className="py-2.5 px-3 text-right font-semibold text-[#CC9166]">
                            {formatINR(r.net_benefit)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </SectionCard>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
