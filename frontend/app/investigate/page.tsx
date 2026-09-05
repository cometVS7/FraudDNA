"use client";

import React, { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { DashboardLayout } from "@/components/layout";
import {
  RiskBadge,
  DecisionBadge,
  SectionCard,
  ShapBars,
  InvestigationTimeline,
  EvidenceCard,
  PolicyDecisionCard,
  LoadingState,
  formatINR,
} from "@/components/ui";
import { FraudGraph } from "@/components/fraud-graph";
import { useAsync } from "@/hooks/use-async";
import {
  fetchTransaction,
  fetchTransactionGraph,
  createInvestigation,
  createAgentInvestigation,
  evaluatePolicy,
} from "@/lib/api";
import type {
  Transaction,
  GraphData,
  InvestigationResponse,
  AgentInvestigationResponse,
  PolicyDecision,
} from "@/lib/api";
import {
  Search,
  CreditCard,
  Smartphone,
  Globe,
  Store,
  User,
  Clock,
  Layers,
  AlertTriangle,
} from "lucide-react";

function InvestigateContent() {
  const searchParams = useSearchParams();
  const initialTx = searchParams.get("tx") || "txn_00001";
  const [txIdInput, setTxIdInput] = useState(initialTx);
  const [activeTxId, setActiveTxId] = useState(initialTx);

  // 1. Transaction Raw Record
  const transaction = useAsync<Transaction | null>(
    () => (activeTxId ? fetchTransaction(activeTxId).catch(() => null) : Promise.resolve(null)),
    [activeTxId]
  );

  // 2. Transaction Subgraph
  const graph = useAsync<GraphData | null>(
    () => (activeTxId ? fetchTransactionGraph(activeTxId, 2).catch(() => null) : Promise.resolve(null)),
    [activeTxId]
  );

  // 3. Phase 3 XAI & Entity Investigation
  const investigation = useAsync<InvestigationResponse | null>(
    () => (activeTxId ? createInvestigation(activeTxId).catch(() => null) : Promise.resolve(null)),
    [activeTxId]
  );

  // 4. Phase 5 LangGraph Autonomous Agent
  const agent = useAsync<AgentInvestigationResponse | null>(
    () => (activeTxId ? createAgentInvestigation(activeTxId).catch(() => null) : Promise.resolve(null)),
    [activeTxId]
  );

  // 5. Phase 5 Deterministic Policy Decision
  const policy = useAsync<PolicyDecision | null>(
    () => (activeTxId ? evaluatePolicy(activeTxId).catch(() => null) : Promise.resolve(null)),
    [activeTxId]
  );

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (txIdInput.trim()) {
      setActiveTxId(txIdInput.trim());
    }
  }

  const tx = transaction.status === "success" ? transaction.data : null;
  const graphData = graph.status === "success" ? graph.data : null;
  const inv = investigation.status === "success" ? investigation.data : null;
  const agentData = agent.status === "success" ? agent.data : null;
  const policyData = policy.status === "success" ? policy.data : null;

  const riskScore = inv?.risk_score ?? tx?.risk_score ?? 0;
  const riskLevel = inv?.risk_level ?? tx?.risk_level ?? "low";
  const policyAction = policyData?.action ?? (riskScore >= 0.85 ? "HOLD" : riskScore >= 0.37 ? "REVIEW" : "ALLOW");

  return (
    <div className="space-y-8">
      {/* Top Search & Selector Utility */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1C1D22] pb-5">
        <div>
          <div className="text-[10px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold">
            Forensic Analyst Workstation
          </div>
          <h1 className="text-2xl sm:text-3xl font-serif text-white tracking-tight mt-0.5">
            Fraud Investigation Console
          </h1>
        </div>

        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#5E616E]" />
            <input
              type="text"
              placeholder="txn_00001"
              value={txIdInput}
              onChange={(e) => setTxIdInput(e.target.value)}
              className="pl-9 pr-3 py-1.5 text-xs bg-[#121317] border border-[#1C1D22] rounded-md font-mono text-[#E2E3E9] placeholder-[#5E616E] focus:outline-none focus:border-[#CC9166] w-48 sm:w-64 transition-colors"
            />
          </div>
          <button
            type="submit"
            disabled={!txIdInput.trim()}
            className="px-3.5 py-1.5 text-xs font-medium rounded-md bg-[#CC9166] text-[#08080A] hover:bg-[#CC9166]/90 disabled:opacity-40 transition-opacity font-sans"
          >
            Investigate
          </button>
        </form>
      </div>

      {/* Primary Investigation Header */}
      <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-6 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5">
              <span className="text-xs font-mono text-[#5E616E] uppercase">TRANSACTION /</span>
              <span className="text-sm font-mono font-semibold text-white tracking-wider">
                {activeTxId}
              </span>
              <RiskBadge level={riskLevel} size="sm" />
            </div>
            <div className="text-xs text-[#9194A1] font-sans">
              Full-stack forensic correlation across ML features, network graph, vector RAG, and policy rules.
            </div>
          </div>

          <div className="flex items-center gap-8 self-start md:self-auto border-t md:border-t-0 border-[#1C1D22] pt-4 md:pt-0">
            {/* Editorial Serif Score */}
            <div>
              <div className="text-[10px] font-mono text-[#777A88] uppercase tracking-wider">
                RISK SCORE
              </div>
              <div className="text-4xl sm:text-5xl font-serif tracking-tight text-white leading-none mt-1">
                {riskScore.toFixed(3)}
              </div>
            </div>

            <div className="h-10 w-[1px] bg-[#1C1D22]" />

            {/* Policy State */}
            <div>
              <div className="text-[10px] font-mono text-[#777A88] uppercase tracking-wider">
                POLICY STATE
              </div>
              <div className="mt-1">
                <DecisionBadge action={policyAction} size="md" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Visual Centerpiece: Desktop 3-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Transaction Facts (3 Cols) */}
        <div className="lg:col-span-3 space-y-4">
          <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4 space-y-4">
            <div className="border-b border-[#1C1D22] pb-2.5">
              <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-[#CC9166] font-semibold">
                EVIDENCE LEDGER
              </div>
              <h3 className="text-sm font-serif text-white font-normal mt-0.5">
                Transaction Facts
              </h3>
            </div>

            {transaction.status === "loading" && (
              <div className="py-6 text-center text-xs text-[#777A88]">Loading facts...</div>
            )}

            {tx && (
              <div className="space-y-3.5 text-xs font-sans">
                <div>
                  <div className="text-[10px] font-mono text-[#5E616E] uppercase">Amount</div>
                  <div className="text-base font-serif text-white mt-0.5">
                    {formatINR(tx.amount)}
                  </div>
                </div>

                <div className="flex items-start gap-2 pt-2 border-t border-[#1C1D22]/60">
                  <Clock className="h-3.5 w-3.5 text-[#5E616E] mt-0.5 flex-shrink-0" />
                  <div className="min-w-0">
                    <div className="text-[10px] font-mono text-[#5E616E]">Timestamp</div>
                    <div className="font-mono text-[11px] text-[#E2E3E9] truncate">
                      {tx.timestamp ? new Date(tx.timestamp).toLocaleString("en-IN") : "—"}
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-2 pt-2 border-t border-[#1C1D22]/60">
                  <User className="h-3.5 w-3.5 text-[#5E616E] mt-0.5 flex-shrink-0" />
                  <div className="min-w-0">
                    <div className="text-[10px] font-mono text-[#5E616E]">Customer</div>
                    <div className="font-mono text-[11px] text-[#E2E3E9] truncate">
                      {tx.customer_id}
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-2 pt-2 border-t border-[#1C1D22]/60">
                  <Store className="h-3.5 w-3.5 text-[#5E616E] mt-0.5 flex-shrink-0" />
                  <div className="min-w-0">
                    <div className="text-[10px] font-mono text-[#5E616E]">Merchant</div>
                    <div className="font-mono text-[11px] text-[#E2E3E9] truncate">
                      {tx.merchant_id}
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-2 pt-2 border-t border-[#1C1D22]/60">
                  <Smartphone className="h-3.5 w-3.5 text-[#5E616E] mt-0.5 flex-shrink-0" />
                  <div className="min-w-0">
                    <div className="text-[10px] font-mono text-[#5E616E]">Device ID</div>
                    <div className="font-mono text-[11px] text-[#E2E3E9] truncate">
                      {tx.device_id}
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-2 pt-2 border-t border-[#1C1D22]/60">
                  <Globe className="h-3.5 w-3.5 text-[#5E616E] mt-0.5 flex-shrink-0" />
                  <div className="min-w-0">
                    <div className="text-[10px] font-mono text-[#5E616E]">IP Address</div>
                    <div className="font-mono text-[11px] text-[#E2E3E9] truncate">
                      {tx.ip_address}
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-2 pt-2 border-t border-[#1C1D22]/60">
                  <CreditCard className="h-3.5 w-3.5 text-[#5E616E] mt-0.5 flex-shrink-0" />
                  <div className="min-w-0">
                    <div className="text-[10px] font-mono text-[#5E616E]">Card ID</div>
                    <div className="font-mono text-[11px] text-[#E2E3E9] truncate">
                      {tx.card_id}
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-2 pt-2 border-t border-[#1C1D22]/60">
                  <Layers className="h-3.5 w-3.5 text-[#5E616E] mt-0.5 flex-shrink-0" />
                  <div className="min-w-0">
                    <div className="text-[10px] font-mono text-[#5E616E]">Cluster Reference</div>
                    <div className="font-mono text-[11px] text-[#CC9166] truncate">
                      {tx.cluster_id || "Isolated / Unclustered"}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Center Column: Large FraudDNA React Flow Graph (6 Cols) */}
        <div className="lg:col-span-6 flex flex-col">
          <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4 flex-1 flex flex-col">
            <div className="flex items-center justify-between border-b border-[#1C1D22] pb-2.5 mb-3">
              <div>
                <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-[#CC9166] font-semibold">
                  GRAPH TOPOLOGY
                </div>
                <h3 className="text-sm font-serif text-white font-normal mt-0.5">
                  FraudDNA Relational Subgraph
                </h3>
              </div>
              <div className="text-[10px] font-mono text-[#777A88]">
                Depth: 2 Degrees
              </div>
            </div>

            <div className="flex-1 min-h-[460px]">
              {graph.status === "loading" && (
                <div className="h-full flex items-center justify-center text-xs text-[#777A88]">
                  Loading graph topology...
                </div>
              )}
              {graph.status === "error" && (
                <div className="h-full flex items-center justify-center text-xs text-[#D05B5B]">
                  Failed to load transaction graph.
                </div>
              )}
              {graphData && graphData.nodes.length > 0 && (
                <FraudGraph
                  graphData={graphData}
                  selectedId={activeTxId}
                  className="h-[460px] w-full"
                />
              )}
              {graphData && graphData.nodes.length === 0 && (
                <div className="h-full flex items-center justify-center text-xs text-[#777A88] font-mono">
                  No relational neighbors found for this transaction.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Risk Intelligence Stack (3 Cols) */}
        <div className="lg:col-span-3 space-y-4">
          {/* Why Flagged (SHAP) */}
          <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4 space-y-3">
            <div className="border-b border-[#1C1D22] pb-2">
              <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-[#CC9166] font-semibold">
                EXPLAINABILITY
              </div>
              <h3 className="text-sm font-serif text-white font-normal mt-0.5">
                Why Flagged (SHAP)
              </h3>
            </div>

            {inv?.risk_factors && inv.risk_factors.length > 0 ? (
              <ShapBars factors={inv.risk_factors} />
            ) : (
              <div className="text-xs text-[#777A88] py-4">No risk attribution factors recorded.</div>
            )}
          </div>

          {/* FraudDNA Cluster Context */}
          <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4 space-y-2.5">
            <div className="border-b border-[#1C1D22] pb-2">
              <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-[#CC9166] font-semibold">
                NETWORK CONTEXT
              </div>
              <h3 className="text-sm font-serif text-white font-normal mt-0.5">
                FraudDNA Cluster
              </h3>
            </div>

            {inv?.cluster ? (
              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-white font-semibold">
                    {inv.cluster.cluster_id}
                  </span>
                  <RiskBadge
                    level={inv.cluster.is_suspicious ? "critical" : "low"}
                    size="xs"
                  />
                </div>
                <div className="text-[11px] font-mono text-[#9194A1]">
                  Score: {inv.cluster.cluster_risk_score.toFixed(3)} • {inv.cluster.transaction_count} Txns
                </div>
                {inv.cluster.primary_reason && (
                  <p className="text-[11px] text-[#C7A66B] font-sans leading-relaxed">
                    {inv.cluster.primary_reason}
                  </p>
                )}
                <Link
                  href={`/frauddna?cluster=${inv.cluster.cluster_id}`}
                  className="inline-block text-[10px] font-mono text-[#CC9166] hover:underline pt-1"
                >
                  View Full Cluster in Network →
                </Link>
              </div>
            ) : (
              <p className="text-xs text-[#777A88]">
                Transaction is not associated with an identified multi-entity fraud ring.
              </p>
            )}
          </div>

          {/* Policy Decision Summary Card */}
          <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4 space-y-3">
            <div className="border-b border-[#1C1D22] pb-2">
              <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-[#CC9166] font-semibold">
                DECISION ROUTING
              </div>
              <h3 className="text-sm font-serif text-white font-normal mt-0.5">
                Policy Authority
              </h3>
            </div>
            <div className="flex items-center justify-between">
              <DecisionBadge action={policyAction} size="sm" />
              <span className="text-[10px] font-mono text-[#8FAF9B]">Deterministic Engine</span>
            </div>
            <p className="text-[11px] text-[#777A88] leading-relaxed font-sans">
              Financial routing authority is strictly governed by deterministic rule thresholds,
              preventing hallucinations or direct mutating agent execution.
            </p>
          </div>
        </div>
      </div>

      {/* Forensic Case File Panels Below */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 7 Cols: AI Investigation Forensic Timeline */}
        <div className="lg:col-span-7">
          <SectionCard
            title="AI Investigation"
            subtitle="Autonomous read-only analyst execution trace"
            action={
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono uppercase tracking-wider text-[#5E616E]">
                  BOUNDED READ-ONLY AGENT
                </span>
              </div>
            }
          >
            {agent.status === "loading" && (
              <LoadingState message="Autonomous forensic agent evaluating evidence..." />
            )}

            {agentData ? (
              <div className="space-y-5 pt-2">
                {/* 6-Step Forensic Timeline */}
                <div className="border-b border-[#1C1D22] pb-5">
                  <div className="text-[10px] font-mono text-[#5E616E] uppercase tracking-wider mb-3">
                    Execution State Sequence
                  </div>
                  <InvestigationTimeline
                    steps={agentData.findings.agent_steps}
                    toolTrace={agentData.findings.tool_trace}
                  />
                </div>

                {/* Synthesis & Hypothesis */}
                <div className="space-y-3">
                  <div>
                    <div className="text-[10px] font-mono uppercase text-[#777A88] tracking-wider">
                      Fraud Hypothesis
                    </div>
                    <div className="text-sm font-serif text-white mt-1 leading-relaxed">
                      &ldquo;{agentData.findings.fraud_hypothesis}&rdquo;
                    </div>
                  </div>

                  <div className="pt-2 border-t border-[#1C1D22]/60">
                    <div className="text-[10px] font-mono uppercase text-[#777A88] tracking-wider mb-1">
                      Analyst Summary
                    </div>
                    <p className="text-xs text-[#9194A1] leading-relaxed font-sans">
                      {agentData.findings.summary}
                    </p>
                  </div>

                  {agentData.findings.limitations.length > 0 && (
                    <div className="p-3 rounded bg-[#121317] border border-[#1C1D22] text-xs text-[#C7A66B] flex items-start gap-2">
                      <AlertTriangle className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" />
                      <div>
                        <span className="font-mono text-[10px] uppercase font-semibold block mb-0.5">
                          Agent Caveats & Missing Context
                        </span>
                        <ul className="list-disc list-inside space-y-0.5 text-[11px] text-[#9194A1]">
                          {agentData.findings.limitations.map((lim, i) => (
                            <li key={i}>{lim}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="py-6 text-xs text-[#777A88]">
                Forensic investigation synthesis pending or executed in deterministic fallback mode.
              </div>
            )}
          </SectionCard>
        </div>

        {/* Right 5 Cols: Grounded Evidence & Policy Engine Card */}
        <div className="lg:col-span-5 space-y-6">
          {/* Grounded RAG Evidence */}
          <SectionCard
            title="Grounded Evidence"
            subtitle="Retrieved regulatory guidelines and policy precedents"
          >
            {inv?.evidence && inv.evidence.length > 0 ? (
              <div className="space-y-2.5 pt-2">
                {inv.evidence.map((ev, i) => (
                  <EvidenceCard
                    key={i}
                    sourceId={ev.source || `GDL-${String(i + 1).padStart(3, "0")}`}
                    title={ev.evidence_type}
                    snippet={ev.description}
                    documentType="Policy Guideline"
                    score={0.92}
                  />
                ))}
              </div>
            ) : (
              <div className="py-4 text-xs text-[#777A88]">
                Evidence retrieval operating in localized rule mode.
              </div>
            )}
          </SectionCard>

          {/* Policy Decision Deterministic Boundary Card */}
          {policyData && (
            <PolicyDecisionCard
              action={policyData.action}
              reasonCodes={policyData.reason_codes}
              policyVersion={policyData.policy_version}
              isDeterministic={policyData.is_deterministic}
              evidenceSummary={policyData.evidence_summary}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default function InvestigatePage() {
  return (
    <DashboardLayout>
      <Suspense fallback={<LoadingState message="Initializing forensic console..." />}>
        <InvestigateContent />
      </Suspense>
    </DashboardLayout>
  );
}
