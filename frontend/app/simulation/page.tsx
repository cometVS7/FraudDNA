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
      // Ensure the user's specific selected threshold is part of the comparison
      const sortedThresholds = Array.from(
        new Set([...targetThresholds, fraudThreshold])
      ).sort((a, b) => a - b);

      const configs: SimulationConfig[] = sortedThresholds.map((t) => ({
        fraud_threshold: t,
        review_threshold: reviewThreshold,
        cost_per_false_positive: costPerFP,
        review_capacity: reviewCapacity,
      }));

      const result = await compareSimulations(configs);
      setComparison(result);

      // Select matching threshold index
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
        {/* Editorial Header */}
        <div className="border-b border-[#1C1D22] pb-5">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div>
              <div className="text-[10px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold">
                COUNTERFACTUAL POLICY OPTIMIZER
              </div>
              <h1 className="text-3xl sm:text-4xl font-serif tracking-tight text-white font-normal mt-1">
                Risk Simulation
              </h1>
              <p className="text-xs sm:text-sm text-[#9194A1] font-sans mt-1">
                Change the policy threshold. See what it would have cost.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <DataLabel label="Financial Risk Laboratory" />
            </div>
          </div>
        </div>

        {/* Laboratory Controls Panel */}
        <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-5">
          <div className="flex items-center justify-between border-b border-[#1C1D22] pb-3 mb-4">
            <div className="flex items-center gap-2">
              <SlidersHorizontal className="h-4 w-4 text-[#CC9166]" />
              <span className="font-mono text-xs text-white font-medium">
                Simulation Parameter Boundaries
              </span>
            </div>
            <button
              onClick={() => executeSimulation()}
              disabled={loading}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-[#CC9166] text-[#08080A] text-xs font-medium hover:bg-[#CC9166]/90 disabled:opacity-40 transition-all font-sans"
            >
              <Play className="h-3 w-3 fill-current" />
              <span>{loading ? "Simulating..." : "Execute Simulation"}</span>
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Fraud Threshold */}
            <div>
              <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                <span className="text-[#777A88]">Fraud Threshold (Hold)</span>
                <span className="text-[#CC9166] font-semibold">{fraudThreshold.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min={0.05}
                max={0.95}
                step={0.01}
                value={fraudThreshold}
                onChange={(e) => setFraudThreshold(parseFloat(e.target.value))}
                className="w-full accent-[#CC9166] cursor-pointer"
              />
              <div className="flex justify-between text-[9px] font-mono text-[#5E616E] mt-1">
                <span>0.05 (Aggressive)</span>
                <span>0.95 (Permissive)</span>
              </div>
            </div>

            {/* Review Threshold */}
            <div>
              <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                <span className="text-[#777A88]">Review Threshold</span>
                <span className="text-[#AE9357] font-semibold">{reviewThreshold.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min={0.05}
                max={Math.min(0.9, fraudThreshold)}
                step={0.01}
                value={reviewThreshold}
                onChange={(e) => setReviewThreshold(parseFloat(e.target.value))}
                className="w-full accent-[#AE9357] cursor-pointer"
              />
              <div className="flex justify-between text-[9px] font-mono text-[#5E616E] mt-1">
                <span>0.05 (Flag Early)</span>
                <span>{fraudThreshold.toFixed(2)} (Cap)</span>
              </div>
            </div>

            {/* Cost Per False Positive */}
            <div>
              <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                <span className="text-[#777A88]">Cost per False Positive</span>
                <span className="text-white font-semibold">₹{costPerFP}</span>
              </div>
              <input
                type="number"
                min={50}
                max={5000}
                step={50}
                value={costPerFP}
                onChange={(e) => setCostPerFP(parseInt(e.target.value) || 350)}
                className="w-full px-3 py-1.5 text-xs bg-[#121317] border border-[#1C1D22] rounded-md text-[#E2E3E9] font-mono focus:outline-none focus:border-[#CC9166]"
              />
              <div className="text-[9px] font-mono text-[#5E616E] mt-1">
                Analyst review + merchant churn friction
              </div>
            </div>

            {/* Review Capacity */}
            <div>
              <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                <span className="text-[#777A88]">Daily Review Capacity</span>
                <span className="text-white font-semibold">{reviewCapacity} txns</span>
              </div>
              <input
                type="number"
                min={100}
                max={5000}
                step={100}
                value={reviewCapacity}
                onChange={(e) => setReviewCapacity(parseInt(e.target.value) || 500)}
                className="w-full px-3 py-1.5 text-xs bg-[#121317] border border-[#1C1D22] rounded-md text-[#E2E3E9] font-mono focus:outline-none focus:border-[#CC9166]"
              />
              <div className="text-[9px] font-mono text-[#5E616E] mt-1">
                Human analyst throughput limit
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
                <div className="p-4 rounded-lg bg-[#121317] border border-[#AE9357]/60 shadow-[0_0_15px_rgba(174,147,87,0.1)]">
                  <div className="text-[10px] font-mono text-[#AE9357] uppercase tracking-wider font-semibold">
                    Net Benefit
                  </div>
                  <div className="text-2xl lg:text-3xl font-serif text-[#AE9357] tracking-tight mt-1">
                    {formatINR(activeResult.net_benefit)}
                  </div>
                  <div className="text-[10px] font-mono text-[#9194A1] mt-0.5">
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
              subtitle="Gilded net benefit curve vs. expected total loss across threshold spectrum"
            >
              <div className="h-72 w-full pt-3">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 10, right: 20, bottom: 0, left: 10 }}>
                    <CartesianGrid strokeDasharray="2 4" stroke="#1C1D22" vertical={false} />
                    <XAxis
                      dataKey="threshold"
                      tick={{ fill: "#777A88", fontSize: 11, fontFamily: "var(--font-mono)" }}
                      axisLine={{ stroke: "#1C1D22" }}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fill: "#777A88", fontSize: 11, fontFamily: "var(--font-mono)" }}
                      axisLine={{ stroke: "#1C1D22" }}
                      tickLine={false}
                      tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#040406",
                        borderColor: "#1C1D22",
                        borderRadius: "6px",
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
                    {/* Primary Analytical Curve: Gilded Treatment */}
                    <Line
                      type="monotone"
                      dataKey="net_benefit"
                      name="Net Benefit"
                      stroke="#AE9357"
                      strokeWidth={2.5}
                      dot={{ fill: "#AE9357", r: 4 }}
                      activeDot={{ r: 6, fill: "#CC9166" }}
                    />
                    <Line
                      type="monotone"
                      dataKey="expected_loss"
                      name="Expected Loss"
                      stroke="#D05B5B"
                      strokeWidth={1.8}
                      dot={{ fill: "#D05B5B", r: 3 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="fraud_prevented"
                      name="Fraud Prevented"
                      stroke="#8FAF9B"
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
                    <tr className="border-b border-[#1C1D22] bg-[#08080A] text-[#5E616E] font-mono text-[10px] uppercase tracking-wider">
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
                  <tbody className="divide-y divide-[#1C1D22]/60 font-mono">
                    {comparison?.results.map((r, i) => {
                      const isSelected = selectedIdx === i;
                      return (
                        <tr
                          key={i}
                          onClick={() => setSelectedIdx(i)}
                          className={`cursor-pointer transition-colors ${
                            isSelected
                              ? "bg-[#121317] text-white"
                              : "hover:bg-[#121317]/40 text-[#9194A1]"
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
                          <td className="py-2.5 px-3 text-right text-[#8FAF9B]">
                            {formatPct(r.recall)}
                          </td>
                          <td className="py-2.5 px-3 text-right">{r.false_positives}</td>
                          <td className="py-2.5 px-3 text-right text-[#8FAF9B]">
                            {formatINR(r.fraud_prevented_amount)}
                          </td>
                          <td className="py-2.5 px-3 text-right text-[#D05B5B]">
                            {formatINR(r.expected_loss)}
                          </td>
                          <td className="py-2.5 px-3 text-right font-semibold text-[#AE9357]">
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
