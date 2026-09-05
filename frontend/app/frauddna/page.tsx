"use client";

import React, { useState, useCallback, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { DashboardLayout } from "@/components/layout";
import {
  RiskBadge,
  LoadingState,
  ErrorState,
  EmptyState,
  formatINR,
} from "@/components/ui";
import { FraudGraph } from "@/components/fraud-graph";
import { useAsync } from "@/hooks/use-async";
import { fetchClusters, fetchClusterGraph } from "@/lib/api";
import type { ClustersResponse, GraphData, ClusterSummary, GraphNode } from "@/lib/api";
import {
  Share2,
  ExternalLink,
  Users,
  Smartphone,
  CreditCard,
  Store,
  ShieldAlert,
  Network,
  Activity,
} from "lucide-react";

function FraudDNAContent() {
  const searchParams = useSearchParams();
  const initialCluster = searchParams.get("cluster") || null;
  const [selectedClusterId, setSelectedClusterId] = useState<string | null>(initialCluster);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const clusters = useAsync<ClustersResponse>(
    () => fetchClusters({ suspicious_only: true, limit: 30, sort_by: "risk_score" }),
    []
  );

  const clustersData = clusters.status === "success" ? clusters.data : null;

  // Set default selected cluster if none selected
  useEffect(() => {
    if (!selectedClusterId && clustersData && clustersData.clusters.length > 0) {
      setSelectedClusterId(clustersData.clusters[0].cluster_id);
    }
  }, [selectedClusterId, clustersData]);

  const graphFetcher = useCallback(() => {
    if (!selectedClusterId) return Promise.resolve(null);
    return fetchClusterGraph(selectedClusterId);
  }, [selectedClusterId]);

  const graphData = useAsync<GraphData | null>(graphFetcher, [selectedClusterId]);
  const graph = graphData.status === "success" ? graphData.data : null;

  const currentClusterSummary = clustersData?.clusters.find(
    (c: ClusterSummary) => c.cluster_id === selectedClusterId
  );

  // Derive priority entities directly from real graph nodes
  const priorityEntities = graph
    ? graph.nodes
        .filter((n) => n.risk_score > 0 || n.entity_type === "transaction")
        .sort((a, b) => b.risk_score - a.risk_score)
        .slice(0, 5)
    : [];

  return (
    <div className="space-y-6">
      {/* Editorial Header */}
      <div className="border-b border-[#1C1D22] pb-5">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <div className="text-[10px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-[#CC9166]" />
              Relational Risk Intelligence
            </div>
            <h1 className="text-3xl font-serif tracking-tight text-white font-normal mt-1">
              Risk Networks
            </h1>
            <p className="text-xs text-[#9194A1] font-sans mt-1">
              Connected entities revealing coordinated exposure across shared devices, payment cards, and IP clusters.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#121317] border border-[#1C1D22] text-[11px] font-mono text-[#AE9357]">
              <Network className="h-3 w-3 text-[#AE9357]" />
              <span>Bipartite Graph Kernel</span>
            </div>
            {clustersData && (
              <span className="text-xs font-mono text-[#777A88]">
                {clustersData.total_clusters} Risk Networks
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Main Canvas & Inspector Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Cluster Selection List (3 Cols) */}
        <div className="lg:col-span-3 space-y-3">
          <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-3">
            <div className="text-[10px] font-mono text-[#5E616E] uppercase tracking-wider mb-2 px-1 flex items-center justify-between">
              <span>ACTIVE RISK NETWORKS</span>
              <span className="text-[#CC9166] font-semibold">{clustersData?.clusters.length || 0}</span>
            </div>

            {clusters.status === "loading" && <LoadingState message="Loading risk networks..." />}
            {clusters.status === "error" && (
              <ErrorState title="NETWORK ERROR" error={clusters.error} onRetry={clusters.refetch} />
            )}

            {clustersData && (
              <div className="space-y-1.5 max-h-[640px] overflow-y-auto pr-1 custom-scrollbar">
                {clustersData.clusters.map((c: ClusterSummary) => {
                  const isSelected = selectedClusterId === c.cluster_id;
                  return (
                    <button
                      key={c.cluster_id}
                      onClick={() => {
                        setSelectedClusterId(c.cluster_id);
                        setSelectedNode(null);
                      }}
                      className={`w-full text-left p-2.5 rounded-md border transition-all text-xs ${
                        isSelected
                          ? "bg-[#121317] border-[#CC9166] shadow-[0_0_12px_rgba(204,145,102,0.15)]"
                          : "bg-[#08080A] border-[#1C1D22] hover:bg-[#121317]/60 text-[#9194A1] hover:text-[#E2E3E9]"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-mono text-xs font-semibold text-white">
                          {c.cluster_id}
                        </span>
                        <RiskBadge
                          level={
                            c.cluster_risk_score >= 0.85
                              ? "critical"
                              : c.cluster_risk_score >= 0.6
                              ? "high"
                              : "medium"
                          }
                          size="xs"
                        />
                      </div>
                      <div className="flex items-center justify-between text-[10px] font-mono text-[#777A88]">
                        <span>{c.transaction_count} Txns • {c.customer_count} Cust</span>
                        <span className="text-[#CC9166]">
                          {formatINR(c.suspicious_transaction_amount)}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Center: Large Graph Canvas (6 Cols) */}
        <div className="lg:col-span-6 flex flex-col">
          <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4 flex-1 flex flex-col">
            <div className="flex items-center justify-between border-b border-[#1C1D22] pb-3 mb-3">
              <div className="flex items-center gap-2">
                <Share2 className="h-4 w-4 text-[#CC9166]" />
                <span className="font-mono text-xs text-white font-medium">
                  {selectedClusterId ? `Network Topology / ${selectedClusterId}` : "Network Canvas"}
                </span>
              </div>
              {graph && (
                <div className="text-[10px] font-mono text-[#777A88]">
                  {graph.total_nodes} Entities • {graph.total_edges} Relationships
                </div>
              )}
            </div>

            <div className="flex-1 min-h-[580px]">
              {!selectedClusterId && (
                <EmptyState
                  title="SELECT A RISK NETWORK"
                  description="Choose a risk network from the left selector to inspect topology."
                />
              )}
              {selectedClusterId && graphData.status === "loading" && (
                <LoadingState message="Mapping network entity topology..." />
              )}
              {selectedClusterId && graphData.status === "error" && (
                <ErrorState title="GRAPH FAILED" error={graphData.error} onRetry={graphData.refetch} />
              )}
              {graph && (
                <FraudGraph
                  graphData={graph}
                  selectedId={selectedNode?.id}
                  onSelectNode={(node) => setSelectedNode(node)}
                  className="h-[580px] w-full"
                />
              )}
            </div>
          </div>
        </div>

        {/* Right: Side Intelligence Panel (3 Cols) */}
        <div className="lg:col-span-3 space-y-4">
          {/* Side Intelligence Panel Card */}
          {currentClusterSummary && (
            <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4 space-y-4">
              <div className="border-b border-[#1C1D22] pb-2.5">
                <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-[#CC9166] font-semibold flex items-center gap-1.5">
                  <Activity className="h-3 w-3 text-[#CC9166]" />
                  Network Intelligence
                </div>
                <h3 className="text-base font-serif text-white font-normal mt-0.5">
                  {currentClusterSummary.cluster_id}
                </h3>
              </div>

              {/* 1. Network Risk */}
              <div className="p-2.5 rounded bg-[#121317] border border-[#1C1D22] space-y-1">
                <div className="text-[10px] font-mono uppercase text-[#777A88] flex items-center justify-between">
                  <span>Network Risk</span>
                  <RiskBadge
                    level={currentClusterSummary.is_suspicious ? "critical" : "low"}
                    size="xs"
                  />
                </div>
                <div className="text-2xl font-serif text-white tracking-tight">
                  {currentClusterSummary.cluster_risk_score.toFixed(4)}
                </div>
              </div>

              {/* 2. Transaction Exposure */}
              <div className="p-2.5 rounded bg-[#121317] border border-[#1C1D22] space-y-1">
                <div className="text-[10px] font-mono uppercase text-[#777A88] flex items-center justify-between">
                  <span>Transaction Exposure</span>
                  <ShieldAlert className="h-3.5 w-3.5 text-[#D05B5B]" />
                </div>
                <div className="text-2xl font-serif text-[#D05B5B] tracking-tight">
                  {formatINR(currentClusterSummary.suspicious_transaction_amount)}
                </div>
                <div className="text-[10px] font-mono text-[#777A88]">
                  Across {currentClusterSummary.transaction_count} flagged transactions
                </div>
              </div>

              {/* 3. Entity Concentration */}
              <div className="space-y-1.5 pt-1">
                <div className="text-[10px] font-mono text-[#777A88] uppercase tracking-wider">
                  Entity Concentration
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="p-2 rounded bg-[#08080A] border border-[#1C1D22] flex items-center gap-1.5">
                    <Users className="h-3.5 w-3.5 text-[#CC9166]" />
                    <span>{currentClusterSummary.customer_count} Cust</span>
                  </div>
                  <div className="p-2 rounded bg-[#08080A] border border-[#1C1D22] flex items-center gap-1.5">
                    <Smartphone className="h-3.5 w-3.5 text-[#AE9357]" />
                    <span>{currentClusterSummary.device_count} Dev</span>
                  </div>
                  <div className="p-2 rounded bg-[#08080A] border border-[#1C1D22] flex items-center gap-1.5">
                    <CreditCard className="h-3.5 w-3.5 text-[#8FAF9B]" />
                    <span>{currentClusterSummary.card_count} Cards</span>
                  </div>
                  <div className="p-2 rounded bg-[#08080A] border border-[#1C1D22] flex items-center gap-1.5">
                    <Store className="h-3.5 w-3.5 text-[#777A88]" />
                    <span>{currentClusterSummary.merchant_count} Merch</span>
                  </div>
                </div>
              </div>

              {/* 4. Attack Signature */}
              {currentClusterSummary.primary_reason && (
                <div className="pt-2 border-t border-[#1C1D22] space-y-1">
                  <div className="text-[10px] font-mono text-[#5E616E] uppercase">
                    Attack Signature
                  </div>
                  <p className="text-xs text-[#C7A66B] font-sans leading-relaxed">
                    {currentClusterSummary.primary_reason}
                  </p>
                </div>
              )}

              {/* 5. Priority Entities */}
              {priorityEntities.length > 0 && (
                <div className="pt-2 border-t border-[#1C1D22] space-y-2">
                  <div className="text-[10px] font-mono text-[#5E616E] uppercase tracking-wider">
                    Priority Entities
                  </div>
                  <div className="space-y-1.5">
                    {priorityEntities.map((node) => (
                      <div
                        key={node.id}
                        className="flex items-center justify-between text-xs font-mono p-1.5 rounded bg-[#08080A] border border-[#1C1D22]"
                      >
                        <span className="text-[#E2E3E9] truncate max-w-[130px]">
                          {node.raw_id || node.id}
                        </span>
                        {node.entity_type === "transaction" ? (
                          <Link
                            href={`/investigate?tx=${node.raw_id || node.id}`}
                            className="text-[10px] text-[#CC9166] hover:underline flex items-center gap-0.5"
                          >
                            <span>Audit</span>
                            <ExternalLink className="h-2.5 w-2.5" />
                          </Link>
                        ) : (
                          <span className="text-[10px] text-[#777A88] uppercase">
                            {node.entity_type}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Node Inspector Card (when a user clicks a node) */}
          {selectedNode && (
            <div className="bg-[#040406] border border-[#CC9166]/50 rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-[#1C1D22] pb-2">
                <span className="text-[10px] font-mono uppercase text-[#CC9166] font-semibold">
                  Selected Entity
                </span>
                <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-[#121317] text-[#9194A1]">
                  {selectedNode.entity_type}
                </span>
              </div>
              <div className="space-y-1.5 text-xs font-mono">
                <div className="text-white font-semibold break-all">
                  {selectedNode.raw_id || selectedNode.id}
                </div>
                {selectedNode.risk_score > 0 && (
                  <div className="text-[11px] text-[#D05B5B]">
                    Risk Score: {selectedNode.risk_score.toFixed(4)}
                  </div>
                )}
                {selectedNode.entity_type === "transaction" && (
                  <div className="pt-2">
                    <Link
                      href={`/investigate?tx=${selectedNode.raw_id || selectedNode.id}`}
                      className="inline-flex items-center gap-1 text-xs font-sans text-[#CC9166] hover:underline"
                    >
                      <span>Open in Case Workstation</span>
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function FraudDNAPage() {
  return (
    <DashboardLayout>
      <Suspense fallback={<LoadingState message="Connecting to relational risk engine..." />}>
        <FraudDNAContent />
      </Suspense>
    </DashboardLayout>
  );
}
