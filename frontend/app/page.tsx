"use client";

import React from "react";
import Link from "next/link";
import { FloatingNav } from "@/components/navigation/floating-nav";
import { HeroSpatialStack } from "@/components/spatial/hero-spatial-stack";
import { FannedCardStack } from "@/components/spatial/fanned-card-stack";
import {
  SectionHiddenNetworks,
  SectionExplainableRisk,
  SectionDecisionMatrix,
  SectionGroundedEvidence,
  SectionWorkflowAndAudit,
} from "@/components/spatial/sections";
import { StatStrip } from "@/components/design-system/stat-strip";
import { MagneticButton } from "@/components/design-system/magnetic-button";
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
  Shield,
  Sparkles,
  Layers,
  Fingerprint,
} from "lucide-react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
} from "recharts";

export default function SpatialOverviewPage() {
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
    <div className="min-h-screen bg-[#06080E] text-[#E2E3E9] selection:bg-cyan-500/30 selection:text-white relative overflow-x-hidden">
      {/* Floating Spatial Navigation Bar */}
      <FloatingNav />

      {/* ========================================================
          HERO SPATIAL SECTION
          ======================================================== */}
      <section className="relative pt-28 sm:pt-36 pb-16 px-4 sm:px-6 max-w-7xl mx-auto flex flex-col items-center text-center">
        {/* Ambient Top Glows & Cyber Grid */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-gradient-to-b from-cyan-500/15 via-blue-600/10 to-transparent rounded-full blur-[140px] pointer-events-none" />
        <div className="absolute top-20 inset-x-0 h-96 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-25 pointer-events-none" />

        {/* Hero Kicker Pill */}
        <div className="relative inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-400/25 text-xs font-mono text-cyan-300 mb-6 shadow-[0_0_20px_rgba(0,229,255,0.2)]">
          <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
          <span>RAZORPAY 2026 • AI RISK MANAGER • TRACK 02</span>
        </div>

        {/* Main Headline */}
        <h1 className="relative text-4xl sm:text-6xl lg:text-7xl font-serif font-normal text-white tracking-tight max-w-5xl leading-[1.1]">
          Detect the fraud hiding{" "}
          <span className="bg-gradient-to-r from-cyan-400 via-teal-300 to-blue-400 bg-clip-text text-transparent font-medium">
            between the transactions.
          </span>
        </h1>

        {/* Subtitle */}
        <p className="relative mt-6 text-base sm:text-lg text-slate-400 max-w-3xl font-sans leading-relaxed">
          FraudDNA does not merely ask <em>“Is this payment suspicious?”</em> It connects
          invisible infrastructure across devices, accounts, and network topologies to expose
          coordinated syndicates before settlement.
        </p>

        {/* Hero Action CTAs */}
        <div className="relative mt-8 flex flex-wrap items-center justify-center gap-4 z-20">
          <MagneticButton
            href="/investigate?tx=tx_0001991"
            variant="primary"
            size="lg"
            icon={<ArrowRight className="h-4 w-4" />}
          >
            Launch Workbench (tx_0001991)
          </MagneticButton>

          <MagneticButton
            href="/cases"
            variant="glass"
            size="lg"
          >
            Inspect Case Queue
          </MagneticButton>
        </div>

        {/* 3D Spatial Interactive Card Stack */}
        <div className="w-full mt-6">
          <HeroSpatialStack />
        </div>
      </section>

      {/* Live Metric KPI Strip */}
      <StatStrip />

      {/* ========================================================
          SECTION 01: FROM TRANSACTION TO TRUTH (FANNED CARDS)
          ======================================================== */}
      <section id="story-01">
        <FannedCardStack />
      </section>

      {/* ========================================================
          SECTION 02: HIDDEN NETWORKS
          ======================================================== */}
      <SectionHiddenNetworks />

      {/* ========================================================
          SECTION 03: EXPLAINABLE RISK & SHAP
          ======================================================== */}
      <SectionExplainableRisk />

      {/* ========================================================
          SECTION 04: DUAL DECISION MATRIX
          ======================================================== */}
      <SectionDecisionMatrix />

      {/* ========================================================
          SECTION 05: GROUNDED EVIDENCE & RAG
          ======================================================== */}
      <SectionGroundedEvidence />

      {/* ========================================================
          SECTION 06 & 07: WORKFLOW & AUDIT
          ======================================================== */}
      <SectionWorkflowAndAudit />

      {/* ========================================================
          LIVE INTELLIGENCE RADAR DASHBOARD
          ======================================================== */}
      <section id="overview" className="relative w-full max-w-6xl mx-auto px-4 sm:px-6 py-20 border-t border-white/10">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-10">
          <div>
            <div className="text-[11px] font-mono tracking-[0.2em] text-cyan-400 uppercase font-semibold">
              Live Operating Radar
            </div>
            <h2 className="text-3xl sm:text-4xl font-serif text-white tracking-tight mt-1">
              Production Risk & Network Telemetry
            </h2>
            <p className="text-sm text-slate-400 max-w-2xl mt-1">
              Real-time feed connecting active transactions, cluster risks, and agent investigations.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <DataLabel label="Synthetic Dataset" />
            <div className="px-3 py-1 rounded-full bg-white/[0.04] border border-white/10 text-xs font-mono text-slate-400">
              Seed #42
            </div>
          </div>
        </div>

        {overview.status === "loading" && (
          <LoadingState message="Querying live fraud intelligence kernel..." />
        )}
        {overview.status === "error" && (
          <ErrorState
            title="RADAR TELEMETRY OFFLINE"
            error={overview.error}
            onRetry={overview.refetch}
          />
        )}

        {overview.status === "success" && (
          <div className="space-y-8">
            {/* 4 Core Primary KPI Cards */}
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

            {/* Risk Distribution & Exposure Breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Risk Distribution Card */}
              <div className="lg:col-span-7">
                <SectionCard
                  title="Risk Spectrum Distribution"
                  subtitle="Transaction volume partition by ML score severity"
                >
                  <div className="space-y-6 pt-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-[10px] font-mono tracking-wider text-slate-500 uppercase">
                          Total Volume
                        </div>
                        <div className="text-2xl font-serif text-white mt-0.5">
                          {formatNumber(overview.data.total_transactions)}{" "}
                          <span className="text-xs font-sans text-slate-400">txns</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-[10px] font-mono tracking-wider text-slate-500 uppercase">
                          Critical Attack Rate
                        </div>
                        <div className="text-2xl font-mono text-rose-400 mt-0.5">
                          {formatPct(
                            (overview.data.risk_distribution.critical + overview.data.risk_distribution.high) /
                              overview.data.total_transactions
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Stacked Risk Spectrum Bar */}
                    <div className="space-y-2">
                      <div
                        className="relative w-full h-8 bg-black/50 rounded-xl p-1 border border-white/10 flex gap-1 items-center overflow-hidden"
                        role="progressbar"
                        aria-label="Risk score distribution across transactions"
                      >
                        <div
                          style={{
                            flex: `${Math.max(overview.data.risk_distribution.low, 1)} 1 0%`,
                          }}
                          className="h-full rounded-lg bg-emerald-500/80 hover:bg-emerald-400 transition-colors cursor-pointer"
                          title={`Low (<0.37): ${formatNumber(overview.data.risk_distribution.low)}`}
                        />
                        <div
                          style={{
                            flex: `${Math.max(overview.data.risk_distribution.medium, 1)} 1 0%`,
                          }}
                          className="h-full rounded-lg bg-amber-500/80 hover:bg-amber-400 transition-colors cursor-pointer"
                          title={`Review (0.37-0.70): ${formatNumber(overview.data.risk_distribution.medium)}`}
                        />
                        <div
                          style={{
                            flex: `${Math.max(overview.data.risk_distribution.high, 1)} 1 0%`,
                          }}
                          className="h-full rounded-lg bg-orange-500/80 hover:bg-orange-400 transition-colors cursor-pointer"
                          title={`High (0.70-0.90): ${formatNumber(overview.data.risk_distribution.high)}`}
                        />
                        <div
                          style={{
                            flex: `${Math.max(overview.data.risk_distribution.critical, 1)} 1 0%`,
                          }}
                          className="h-full rounded-lg bg-rose-500 hover:bg-rose-400 transition-colors cursor-pointer"
                          title={`Critical (>=0.90): ${formatNumber(overview.data.risk_distribution.critical)}`}
                        />
                      </div>
                      <div className="flex justify-between text-[10px] font-mono text-slate-500 px-1">
                        <span>0.00 (Low)</span>
                        <span>0.37 (Review)</span>
                        <span>0.70 (High)</span>
                        <span>0.90 (Critical)</span>
                        <span>1.00</span>
                      </div>
                    </div>

                    {/* Numerical Tiers */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-white/10">
                      <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                        <span className="text-[10px] font-mono text-slate-400 uppercase">LOW</span>
                        <div className="text-base font-mono font-bold text-emerald-400 mt-1">
                          {formatNumber(overview.data.risk_distribution.low)}
                        </div>
                      </div>
                      <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                        <span className="text-[10px] font-mono text-slate-400 uppercase">REVIEW</span>
                        <div className="text-base font-mono font-bold text-amber-400 mt-1">
                          {formatNumber(overview.data.risk_distribution.medium)}
                        </div>
                      </div>
                      <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                        <span className="text-[10px] font-mono text-slate-400 uppercase">HIGH</span>
                        <div className="text-base font-mono font-bold text-orange-400 mt-1">
                          {formatNumber(overview.data.risk_distribution.high)}
                        </div>
                      </div>
                      <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                        <span className="text-[10px] font-mono text-slate-400 uppercase">CRITICAL</span>
                        <div className="text-base font-mono font-bold text-rose-400 mt-1">
                          {formatNumber(overview.data.risk_distribution.critical)}
                        </div>
                      </div>
                    </div>
                  </div>
                </SectionCard>
              </div>

              {/* Fraud Exposure Composition */}
              <div className="lg:col-span-5">
                <SectionCard
                  title="Fraud Loss Exposure"
                  subtitle="Ground-truth classification & capital risk"
                >
                  <div className="h-52 flex items-center justify-center pt-2">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={[
                            {
                              name: "Legitimate",
                              value: overview.data.legitimate_count,
                              fill: "#1E293B",
                            },
                            {
                              name: "Confirmed Fraud",
                              value: overview.data.fraud_count,
                              fill: "#F43F5E",
                            },
                          ]}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={84}
                          stroke="#06080E"
                          strokeWidth={3}
                          dataKey="value"
                        >
                          <Cell fill="#1E293B" />
                          <Cell fill="#F43F5E" />
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "#0B0F1A",
                            borderColor: "#334155",
                            borderRadius: "8px",
                            fontSize: "12px",
                            color: "#F8FAFC",
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="space-y-2 pt-4 border-t border-white/10 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Legitimate Traffic</span>
                      <span className="font-mono text-slate-200">
                        {formatNumber(overview.data.legitimate_count)} ({formatPct(1 - overview.data.fraud_rate)})
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-rose-400 font-semibold">Fraud Incident Volume</span>
                      <span className="font-mono text-rose-400 font-bold">
                        {formatNumber(overview.data.fraud_count)} ({formatPct(overview.data.fraud_rate)})
                      </span>
                    </div>
                    <div className="flex items-center justify-between pt-1 border-t border-white/10">
                      <span className="text-slate-400">Direct Financial Loss</span>
                      <span className="font-mono font-bold text-cyan-400">
                        {formatINR(overview.data.fraud_exposure)}
                      </span>
                    </div>
                  </div>
                </SectionCard>
              </div>
            </div>

            {/* Lower Row: Recent Priority Ledger, Networks, and Investigation Console */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Panel 1: Recent High Risk */}
              <SectionCard
                title="Priority High-Risk Ledger"
                subtitle="Transactions flagged by ML model"
                action={
                  <Link
                    href="/transactions"
                    className="inline-flex items-center gap-1 text-[11px] font-mono text-cyan-400 hover:text-white"
                  >
                    <span>Ledger</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                }
              >
                {recentRiskTx.status === "loading" && <LoadingState message="Loading high-risk events..." />}
                {recentRiskTx.status === "success" && (
                  <div className="divide-y divide-white/5">
                    {recentRiskTx.data.transactions.map((tx) => (
                      <div
                        key={tx.transaction_id}
                        className="py-3 flex items-center justify-between gap-3 group hover:bg-white/[0.02] px-1 rounded-lg transition-colors"
                      >
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <Link
                              href={`/investigate?tx=${tx.transaction_id}`}
                              className="font-mono text-xs text-white group-hover:text-cyan-400 transition-colors truncate font-semibold"
                            >
                              {tx.transaction_id}
                            </Link>
                            <RiskBadge level={tx.risk_level} size="xs" />
                          </div>
                          <div className="text-[10px] font-mono text-slate-500 mt-0.5 truncate">
                            {tx.customer_id} • {tx.device_id.slice(0, 8)}
                          </div>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <div className="text-right">
                            <div className="font-mono text-xs text-slate-200">
                              {formatINR(tx.amount)}
                            </div>
                            <div className="text-[10px] font-mono text-rose-400">
                              Score: {tx.risk_score.toFixed(3)}
                            </div>
                          </div>
                          <Link
                            href={`/investigate?tx=${tx.transaction_id}`}
                            className="p-1.5 rounded-lg bg-white/5 border border-white/10 hover:border-cyan-400/50 hover:text-cyan-300 text-slate-400 transition-colors"
                            title={`Investigate ${tx.transaction_id}`}
                          >
                            <ArrowRight className="h-3.5 w-3.5" />
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </SectionCard>

              {/* Panel 2: Syndicate Clusters */}
              <SectionCard
                title="Syndicate Clusters"
                subtitle="Identified graph collusions"
                action={
                  <Link
                    href="/frauddna"
                    className="inline-flex items-center gap-1 text-[11px] font-mono text-cyan-400 hover:text-white"
                  >
                    <span>Full Graph</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                }
              >
                {clusters.status === "loading" && <LoadingState message="Loading network clusters..." />}
                {clusters.status === "success" && (
                  <div className="divide-y divide-white/5">
                    {clusters.data.clusters.map((c) => (
                      <div
                        key={c.cluster_id}
                        className="py-3 group hover:bg-white/[0.02] px-1 rounded-lg transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-xs text-white font-semibold">
                            {c.cluster_id}
                          </span>
                          <span className="font-mono text-xs text-cyan-400 font-bold">
                            {formatINR(c.suspicious_transaction_amount)}
                          </span>
                        </div>
                        <div className="mt-1 flex items-center justify-between text-[10px] font-mono text-slate-500">
                          <span>
                            {c.transaction_count} txns • {c.customer_count} cust • {c.device_count} dev
                          </span>
                          <span className="text-slate-400 truncate max-w-[120px]">
                            {c.primary_reason}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </SectionCard>

              {/* Panel 3: Autonomous Investigation Console */}
              <SectionCard
                title="Investigation Workbench"
                subtitle="Autonomous forensic pipeline"
                action={
                  <Link
                    href="/investigate"
                    className="inline-flex items-center gap-1 text-[11px] font-mono text-cyan-400 hover:text-white"
                  >
                    <span>Console</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                }
              >
                <div className="space-y-4">
                  <div className="p-3.5 rounded-2xl bg-cyan-950/30 border border-cyan-500/20 space-y-2">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
                      <span className="text-xs font-mono font-bold text-white">
                        Bounded Read-Only Agent Active
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      Synthesizes multi-hop entity graphs, SHAP explanations, and regulatory
                      defense guidelines without any financial execution permissions.
                    </p>
                  </div>

                  <div className="pt-2">
                    <Link
                      href="/investigate?tx=tx_0001991"
                      className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-black font-bold text-xs hover:from-cyan-400 hover:to-blue-500 transition-all shadow-[0_0_20px_rgba(0,229,255,0.3)]"
                    >
                      <Search className="h-4 w-4" />
                      <span>Investigate Golden Case (tx_0001991)</span>
                    </Link>
                  </div>
                </div>
              </SectionCard>
            </div>
          </div>
        )}
      </section>

      {/* ========================================================
          CINEMATIC FOOTER
          ======================================================== */}
      <footer className="w-full border-t border-white/10 bg-[#04060A] py-12 px-4 sm:px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center">
              <Shield className="h-4 w-4 text-cyan-400" />
            </div>
            <div>
              <div className="text-sm font-semibold text-white">
                Fraud<span className="text-cyan-400">DNA</span>
              </div>
              <div className="text-[10px] font-mono text-slate-500">
                Razorpay AI Buildathon 2026 • Track 02 AI Risk Manager
              </div>
            </div>
          </div>

          <div className="flex items-center gap-6 text-xs font-mono text-slate-400">
            <Link href="/cases" className="hover:text-cyan-400 transition-colors">
              Case Queue
            </Link>
            <Link href="/investigate" className="hover:text-cyan-400 transition-colors">
              Workbench
            </Link>
            <Link href="/frauddna" className="hover:text-cyan-400 transition-colors">
              Networks
            </Link>
            <Link href="/audit" className="hover:text-cyan-400 transition-colors">
              Audit
            </Link>
          </div>

          <div className="text-right">
            <div className="text-[11px] font-mono text-emerald-400 flex items-center gap-1.5 justify-end">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>Deterministic Policy Invariant Active</span>
            </div>
            <div className="text-[10px] font-mono text-slate-600 mt-0.5">
              Zero-HITL Production Platform • Seed #42
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
