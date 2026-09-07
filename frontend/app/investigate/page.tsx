"use client";

import React, { useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout";
import { HeroHeader } from "@/components/workbench/hero-header";
import { DecisionIntelligenceCard } from "@/components/workbench/decision-intelligence";
import { TransactionLedger } from "@/components/workbench/transaction-ledger";
import { EntityProfileDrawer } from "@/components/workbench/entity-profile-drawer";
import { SyndicatePatternBadges } from "@/components/workbench/syndicate-pattern-badges";
import { ShapWaterfall } from "@/components/workbench/shap-waterfall";
import { EvidenceExplorer } from "@/components/workbench/evidence-explorer";
import { AIDossierCard } from "@/components/workbench/ai-dossier-card";
import { RagCitationsCard } from "@/components/workbench/rag-citations-card";
import { CaseActionToolbar } from "@/components/workbench/case-action-toolbar";
import { PathSearchDialog } from "@/components/workbench/path-search-dialog";
import { CaseCreateModal } from "@/components/cases/case-create-modal";
import { FraudGraph } from "@/components/fraud-graph";
import { useAsync } from "@/hooks/use-async";
import {
  fetchTransaction,
  fetchTransactionGraph,
  createInvestigation,
  createAgentInvestigation,
  evaluatePolicy,
  fetchCase,
} from "@/lib/api";
import type {
  Transaction,
  GraphData,
  GraphNode,
  InvestigationResponse,
  AgentInvestigationResponse,
  PolicyDecision,
  CaseResponse,
} from "@/lib/api";
import {
  Search,
  Share2,
  Route,
  Network,
} from "lucide-react";

function InvestigateContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialTx = searchParams.get("tx") || "tx_0001991";
  const initialCaseId = searchParams.get("case_id") || null;

  const [txIdInput, setTxIdInput] = useState(initialTx);
  const [activeTxId, setActiveTxId] = useState(initialTx);
  const [activeCaseId, setActiveCaseId] = useState<string | null>(initialCaseId);
  const [activeTab, setActiveTab] = useState<"graph" | "syndicates" | "evidence">("graph");
  const [selectedEntity, setSelectedEntity] = useState<{ type: string; id: string } | null>(null);
  const [isPathSearchOpen, setIsPathSearchOpen] = useState(false);
  const [isCreateCaseOpen, setIsCreateCaseOpen] = useState(false);
  const [graphDepth, setGraphDepth] = useState<number>(2);

  // 1. Transaction Facts
  const txData = useAsync<Transaction | null>(
    () => (activeTxId ? fetchTransaction(activeTxId).catch(() => null) : Promise.resolve(null)),
    [activeTxId]
  );

  // 2. Transaction Ego-Graph
  const graphData = useAsync<GraphData | null>(
    () =>
      activeTxId
        ? fetchTransactionGraph(activeTxId, graphDepth).catch(() => null)
        : Promise.resolve(null),
    [activeTxId, graphDepth]
  );

  // 3. Phase 3 XAI & Entity Investigation
  const invData = useAsync<InvestigationResponse | null>(
    () => (activeTxId ? createInvestigation(activeTxId).catch(() => null) : Promise.resolve(null)),
    [activeTxId]
  );

  // 4. Phase 5 LangGraph Autonomous Agent
  const agentData = useAsync<AgentInvestigationResponse | null>(
    () => (activeTxId ? createAgentInvestigation(activeTxId, 8).catch(() => null) : Promise.resolve(null)),
    [activeTxId]
  );

  // 5. Phase 5 Deterministic Policy Decision
  const policyData = useAsync<PolicyDecision | null>(
    () => (activeTxId ? evaluatePolicy(activeTxId).catch(() => null) : Promise.resolve(null)),
    [activeTxId]
  );

  // 6. Optional Bound Case Record
  const caseRecord = useAsync<CaseResponse | null>(
    () => (activeCaseId ? fetchCase(activeCaseId).catch(() => null) : Promise.resolve(null)),
    [activeCaseId]
  );

  const tx = txData.status === "success" ? txData.data : null;
  const graph = graphData.status === "success" ? graphData.data : null;
  const inv = invData.status === "success" ? invData.data : null;
  const agent = agentData.status === "success" ? agentData.data : null;
  const policy = policyData.status === "success" ? policyData.data : null;
  const caseData = caseRecord.status === "success" ? caseRecord.data : null;

  const riskScore = inv?.risk_score ?? agent?.findings?.risk_score ?? tx?.risk_score ?? 0;
  const riskLevel = inv?.risk_level ?? agent?.findings?.risk_level ?? tx?.risk_level ?? "low";

  function handleSelectTx(newTxId: string) {
    setTxIdInput(newTxId);
    setActiveTxId(newTxId);
    router.replace(`/investigate?tx=${newTxId}${activeCaseId ? `&case_id=${activeCaseId}` : ""}`, {
      scroll: false,
    });
  }

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (txIdInput.trim()) {
      handleSelectTx(txIdInput.trim());
    }
  }

  function handleOpenEntity(type: string, id: string) {
    setSelectedEntity({ type, id });
  }

  function handleSelectGraphNode(node: GraphNode) {
    setSelectedEntity({
      type: node.entity_type || "entity",
      id: node.raw_id || node.id,
    });
  }

  return (
    <div className="space-y-6">
      {/* Search Bar & Workspace Utility Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1C1D22] pb-4">
        <div>
          <div className="text-[10px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold">
            FORENSIC WORKBENCH
          </div>
          <h1 className="text-2xl sm:text-3xl font-serif text-white tracking-tight mt-0.5">
            Investigation Workbench
          </h1>
        </div>

        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#5E616E]" />
            <input
              type="text"
              placeholder="e.g. tx_0001991"
              value={txIdInput}
              onChange={(e) => setTxIdInput(e.target.value)}
              className="pl-9 pr-3 py-1.5 text-xs bg-[#121317] border border-[#1C1D22] rounded font-mono text-[#E2E3E9] placeholder-[#5E616E] focus:outline-none focus:border-[#CC9166] w-48 sm:w-64 transition-colors"
            />
          </div>
          <button
            type="submit"
            disabled={!txIdInput.trim()}
            className="px-3.5 py-1.5 text-xs font-medium rounded bg-[#CC9166] text-[#08080A] hover:bg-[#CC9166]/90 disabled:opacity-40 transition-opacity font-sans"
          >
            Investigate
          </button>
        </form>
      </div>

      {/* Hero Header */}
      <HeroHeader
        transactionId={activeTxId}
        riskScore={riskScore}
        riskLevel={riskLevel}
        policyDecision={policy}
        caseId={activeCaseId}
        onSelectTx={handleSelectTx}
        onRequestCreateCase={() => setIsCreateCaseOpen(true)}
      />

      {/* Decision Intelligence Demarcation Card */}
      <DecisionIntelligenceCard
        policyDecision={policy}
        agentFindings={agent?.findings || null}
        riskScore={riskScore}
      />

      {/* Primary 3-Column Desktop Forensic Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Facts & XAI (3 Cols) */}
        <div className="lg:col-span-3 space-y-6">
          <TransactionLedger
            transaction={tx}
            loading={txData.status === "loading"}
            onOpenEntity={handleOpenEntity}
          />
          <ShapWaterfall
            factors={inv?.risk_factors || []}
            loading={invData.status === "loading"}
          />
        </div>

        {/* Center Column: Network Intelligence & Graph (6 Cols) */}
        <div className="lg:col-span-6 space-y-6">
          <div className="bg-[#040406] border border-[#1C1D22] rounded-lg overflow-hidden shadow-2xl">
            {/* Center Tab Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-[#1C1D22] bg-[#08080A]">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveTab("graph")}
                  className={`flex items-center gap-1.5 px-3 py-1 text-xs font-mono rounded transition-colors ${
                    activeTab === "graph"
                      ? "bg-[#1C1D22] text-[#CC9166] font-semibold border border-[#2E3038]"
                      : "text-[#777A88] hover:text-white"
                  }`}
                >
                  <Share2 className="h-3.5 w-3.5" />
                  <span>Network Graph</span>
                </button>
                <button
                  onClick={() => setActiveTab("syndicates")}
                  className={`flex items-center gap-1.5 px-3 py-1 text-xs font-mono rounded transition-colors ${
                    activeTab === "syndicates"
                      ? "bg-[#1C1D22] text-[#CC9166] font-semibold border border-[#2E3038]"
                      : "text-[#777A88] hover:text-white"
                  }`}
                >
                  <Network className="h-3.5 w-3.5" />
                  <span>Syndicates</span>
                </button>
              </div>

              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1 text-[11px] font-mono text-[#777A88]">
                  <span>Depth:</span>
                  <select
                    value={graphDepth}
                    onChange={(e) => setGraphDepth(Number(e.target.value))}
                    className="bg-[#121317] border border-[#1C1D22] rounded px-1.5 py-0.5 text-xs text-white"
                  >
                    <option value={1}>1</option>
                    <option value={2}>2</option>
                    <option value={3}>3</option>
                  </select>
                </div>
                <button
                  onClick={() => setIsPathSearchOpen(true)}
                  className="flex items-center gap-1 px-2.5 py-1 text-[10px] font-mono text-[#CC9166] hover:text-white bg-[#121317] border border-[#1C1D22] hover:border-[#CC9166]/40 rounded transition-colors"
                >
                  <Route className="h-3 w-3" />
                  <span>Find Paths</span>
                </button>
              </div>
            </div>

            {/* Visualizer Area */}
            <div className="p-4">
              {activeTab === "graph" && graph && (
                <FraudGraph
                  graphData={graph}
                  selectedId={activeTxId}
                  onSelectNode={handleSelectGraphNode}
                  className="h-[480px] w-full"
                />
              )}

              {activeTab === "syndicates" && (
                <div className="space-y-4">
                  <SyndicatePatternBadges
                    patterns={agent?.findings?.detected_patterns || ["DEVICE_REUSE_RING", "CARD_SHARING_RING", "MULTI_INFRASTRUCTURE_COLLUSION"]}
                  />
                  {graph && (
                    <FraudGraph
                      graphData={graph}
                      selectedId={activeTxId}
                      onSelectNode={handleSelectGraphNode}
                      className="h-[360px] w-full"
                    />
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Syndicate Patterns Overview (Always accessible beneath graph) */}
          {activeTab === "graph" && (
            <SyndicatePatternBadges
              patterns={agent?.findings?.detected_patterns || ["DEVICE_REUSE_RING", "CARD_SHARING_RING", "MULTI_INFRASTRUCTURE_COLLUSION"]}
            />
          )}

          {/* Regulatory Typologies */}
          <RagCitationsCard query="syndicate fraud playbooks" />
        </div>

        {/* Right Column: AI Findings, Evidence & Workflow (3 Cols) */}
        <div className="lg:col-span-3 space-y-6">
          <CaseActionToolbar
            caseData={caseData}
            onCaseUpdated={(updated) => setActiveCaseId(updated.id)}
            onRequestCreateCase={() => setIsCreateCaseOpen(true)}
          />

          <AIDossierCard
            findings={agent?.findings || null}
            loading={agentData.status === "loading"}
          />

          <EvidenceExplorer
            evidenceItems={agent?.findings?.evidence_items || []}
            loading={agentData.status === "loading"}
          />
        </div>
      </div>

      {/* Entity Profile Drawer */}
      <EntityProfileDrawer
        entityType={selectedEntity?.type || null}
        entityId={selectedEntity?.id || null}
        isOpen={Boolean(selectedEntity)}
        onClose={() => setSelectedEntity(null)}
        onSelectTransaction={handleSelectTx}
      />

      {/* Path Search Dialog */}
      <PathSearchDialog
        isOpen={isPathSearchOpen}
        onClose={() => setIsPathSearchOpen(false)}
        defaultSourceId={activeTxId}
      />

      {/* Case Creation Modal */}
      <CaseCreateModal
        isOpen={isCreateCaseOpen}
        onClose={() => setIsCreateCaseOpen(false)}
        onCreated={(newCase) => setActiveCaseId(newCase.id)}
        initialTransactionId={activeTxId}
        initialTitle={`Investigation Case for ${activeTxId}`}
      />
    </div>
  );
}

export default function InvestigatePage() {
  return (
    <DashboardLayout>
      <Suspense fallback={<div className="p-8 text-center text-xs text-[#777A88]">Loading workbench...</div>}>
        <InvestigateContent />
      </Suspense>
    </DashboardLayout>
  );
}
