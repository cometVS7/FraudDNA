"use client";

import React from "react";
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
  Target,
  Award,
  ShieldCheck,
  ShieldAlert,
  DollarSign,
  AlertTriangle,
  Info,
} from "lucide-react";
export default function EvaluationPage() {
  const evalData = useAsync<EvaluationMetrics>(() => fetchEvaluation(), []);

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Editorial Header */}
        <div className="border-b border-[#1C1D22] pb-5">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div>
              <div className="text-[10px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold">
                HELD-OUT TEST SET
              </div>
              <h1 className="text-3xl sm:text-4xl font-serif tracking-tight text-white font-normal mt-1">
                Model Evaluation
              </h1>
              <p className="text-xs text-[#9194A1] font-sans mt-1">
                Rigorous out-of-time evaluation benchmarked on unseen chronological holdout data.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <DataLabel label="Synthetic Dataset • Deterministic Seed • Held-Out Evaluation" />
            </div>
          </div>
        </div>

        {evalData.status === "loading" && (
          <LoadingState message="Retrieving held-out evaluation benchmarks..." />
        )}
        {evalData.status === "error" && (
          <ErrorState
            title="EVALUATION METRICS UNAVAILABLE"
            error={evalData.error}
            onRetry={evalData.refetch}
          />
        )}

        {evalData.status === "success" && (
          <>
            {/* Primary Hero Analytical Banner */}
            <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="space-y-2">
                  <div className="text-[10px] font-mono text-[#AE9357] uppercase tracking-wider font-semibold">
                    PRIMARY GENERALIZATION BENCHMARK
                  </div>
                  <div className="text-4xl sm:text-6xl font-serif text-white tracking-tight leading-none">
                    {evalData.data.metrics.pr_auc.toFixed(4)}
                    <span className="text-sm font-mono text-[#777A88] font-normal ml-3">
                      PR-AUC
                    </span>
                  </div>
                  <p className="text-xs text-[#9194A1] max-w-xl font-sans leading-relaxed">
                    Evaluated across {formatNumber(evalData.data.held_out_test_size)} held-out test
                    transactions with zero data contamination or future leakage.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4 border-t md:border-t-0 md:border-l border-[#1C1D22] pt-4 md:pt-0 md:pl-6">
                  <div>
                    <div className="text-[10px] font-mono text-[#5E616E] uppercase">
                      OPERATING THRESHOLD
                    </div>
                    <div className="text-xl font-mono text-white mt-0.5">
                      {evalData.data.selected_operating_threshold}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] font-mono text-[#5E616E] uppercase">
                      F1 HARMONIC SCORE
                    </div>
                    <div className="text-xl font-mono text-[#AE9357] mt-0.5">
                      {evalData.data.metrics.f1_score.toFixed(3)}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] font-mono text-[#5E616E] uppercase">
                      CONFIRMED FRAUD
                    </div>
                    <div className="text-xl font-mono text-[#D05B5B] mt-0.5">
                      {evalData.data.actual_fraud_count}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] font-mono text-[#5E616E] uppercase">
                      NET BUSINESS BENEFIT
                    </div>
                    <div className="text-xl font-mono text-[#8FAF9B] mt-0.5">
                      {formatINR(evalData.data.cost_and_financial_impact.net_business_benefit_inr)}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Supporting Metrics: 8 Key Cards */}
            <div className="space-y-2">
              <div className="text-[10px] font-mono uppercase text-[#CC9166] tracking-[0.16em] font-semibold">
                CORE BENCHMARK SUITE
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {/* 1. Precision */}
                <MetricCard
                  label="Precision"
                  value={formatPct(evalData.data.metrics.precision)}
                  sublabel="TP / (TP + FP)"
                  variant="success"
                  icon={<Target className="h-4 w-4" />}
                />
                {/* 2. Recall */}
                <MetricCard
                  label="Recall"
                  value={formatPct(evalData.data.metrics.recall)}
                  sublabel="TP / (TP + FN)"
                  variant="success"
                  icon={<Award className="h-4 w-4" />}
                />
                {/* 3. F1 */}
                <MetricCard
                  label="F1 Score"
                  value={evalData.data.metrics.f1_score.toFixed(3)}
                  sublabel="Balanced F-measure"
                />
                {/* 4. PR-AUC */}
                <MetricCard
                  label="PR-AUC"
                  value={evalData.data.metrics.pr_auc.toFixed(4)}
                  sublabel="Area under PR curve"
                />
                {/* 5. FPR */}
                <MetricCard
                  label="False Positive Rate"
                  value={formatPct(evalData.data.metrics.false_positive_rate)}
                  sublabel={`${evalData.data.confusion_matrix.false_positives} FP events`}
                  variant="warning"
                  icon={<AlertTriangle className="h-4 w-4" />}
                />
                {/* 6. False-Positive Cost */}
                <MetricCard
                  label="False-Positive Cost"
                  value={formatINR(
                    evalData.data.cost_and_financial_impact.false_positive_monetary_cost_inr
                  )}
                  sublabel={`@ ₹${evalData.data.cost_and_financial_impact.cost_per_false_positive_inr}/fp`}
                  icon={<DollarSign className="h-4 w-4" />}
                />
                {/* 7. Fraud Prevented */}
                <MetricCard
                  label="Fraud Prevented"
                  value={formatINR(
                    evalData.data.cost_and_financial_impact.fraud_prevented_amount_inr
                  )}
                  sublabel="Direct loss mitigation"
                  variant="success"
                  icon={<ShieldCheck className="h-4 w-4" />}
                />
                {/* 8. Fraud Missed */}
                <MetricCard
                  label="Fraud Missed"
                  value={formatINR(
                    evalData.data.cost_and_financial_impact.fraud_missed_amount_inr
                  )}
                  sublabel={`${evalData.data.confusion_matrix.false_negatives} false negatives`}
                  variant="danger"
                  icon={<ShieldAlert className="h-4 w-4" />}
                />
              </div>
            </div>

            {/* Visuals: Confusion Matrix & Attack Scenario Breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Confusion Matrix (5 Cols) */}
              <div className="lg:col-span-5">
                <SectionCard
                  title="Confusion Matrix"
                  subtitle={`Performance partition at threshold ${evalData.data.selected_operating_threshold}`}
                >
                  <div className="grid grid-cols-2 gap-3 pt-2">
                    <div className="p-4 rounded-md bg-[#121317] border border-[#8FAF9B]/40 text-center">
                      <div className="text-[10px] font-mono text-[#8FAF9B] uppercase font-semibold">
                        True Positives (TP)
                      </div>
                      <div className="text-3xl font-serif text-white mt-1">
                        {formatNumber(evalData.data.confusion_matrix.true_positives)}
                      </div>
                      <div className="text-[10px] font-mono text-[#777A88] mt-1">
                        Correctly Blocked Fraud
                      </div>
                    </div>

                    <div className="p-4 rounded-md bg-[#121317] border border-[#C7A66B]/40 text-center">
                      <div className="text-[10px] font-mono text-[#C7A66B] uppercase font-semibold">
                        False Positives (FP)
                      </div>
                      <div className="text-3xl font-serif text-white mt-1">
                        {formatNumber(evalData.data.confusion_matrix.false_positives)}
                      </div>
                      <div className="text-[10px] font-mono text-[#777A88] mt-1">
                        Legitimate Flagged
                      </div>
                    </div>

                    <div className="p-4 rounded-md bg-[#121317] border border-[#D05B5B]/40 text-center">
                      <div className="text-[10px] font-mono text-[#D05B5B] uppercase font-semibold">
                        False Negatives (FN)
                      </div>
                      <div className="text-3xl font-serif text-white mt-1">
                        {formatNumber(evalData.data.confusion_matrix.false_negatives)}
                      </div>
                      <div className="text-[10px] font-mono text-[#777A88] mt-1">
                        Undetected Fraud
                      </div>
                    </div>

                    <div className="p-4 rounded-md bg-[#121317] border border-[#1C1D22] text-center">
                      <div className="text-[10px] font-mono text-[#777A88] uppercase font-semibold">
                        True Negatives (TN)
                      </div>
                      <div className="text-3xl font-serif text-white mt-1">
                        {formatNumber(evalData.data.confusion_matrix.true_negatives)}
                      </div>
                      <div className="text-[10px] font-mono text-[#5E616E] mt-1">
                        Clean Transactions
                      </div>
                    </div>
                  </div>
                </SectionCard>
              </div>

              {/* Breakdown by Attack Scenario (7 Cols) */}
              <div className="lg:col-span-7">
                <SectionCard
                  title="Scenario Catch Rates"
                  subtitle="Model sensitivity across distinct fraud attack typologies"
                >
                  <div className="space-y-3 pt-2">
                    {Object.entries(evalData.data.breakdown_by_scenario).map(([scenario, stat]) => {
                      const catchPct = stat.catch_rate;
                      return (
                        <div
                          key={scenario}
                          className="p-3 rounded-md bg-[#121317] border border-[#1C1D22] space-y-1.5"
                        >
                          <div className="flex items-center justify-between text-xs font-mono">
                            <span className="text-white font-medium capitalize">
                              {scenario.replace(/_/g, " ")}
                            </span>
                            <span className="text-[#8FAF9B] font-semibold">
                              {formatPct(catchPct)} ({stat.caught_count}/{stat.total_count})
                            </span>
                          </div>
                          <div className="h-1.5 w-full bg-[#1C1D22] rounded-full overflow-hidden">
                            <div
                              className="h-full bg-[#8FAF9B] rounded-full transition-all"
                              style={{ width: `${Math.min(catchPct * 100, 100)}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </SectionCard>
              </div>
            </div>

            {/* Methodology & Synthetic Provenance Notice */}
            <div className="p-4 rounded-lg bg-[#040406] border border-[#1C1D22] text-xs text-[#777A88] flex items-start gap-2.5">
              <Info className="h-4 w-4 text-[#CC9166] mt-0.5 flex-shrink-0" />
              <div className="leading-relaxed font-sans">
                <span className="text-[#E2E3E9] font-medium font-mono text-[11px] block mb-0.5">
                  EVALUATION PROVENANCE & METHODOLOGY
                </span>
                Trained using chronological split (Train 70% / Val 15% / Held-Out Test 15%). Thresholds
                are tuned exclusively on validation splits with zero test feedback. Synthetic data
                generated with deterministic seed #42 to simulate real-world card testing, credential
                stuffing, and coordinated syndicate topologies.
              </div>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
