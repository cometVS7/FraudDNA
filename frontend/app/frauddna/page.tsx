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
  DataLabel,
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
  Layers,
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

  return (
    <div className="space-y-6">
      {/* Editorial Header */}
      <div className="border-b border-[#1C1D22] pb-5">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <div className="text-[10px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold">
              RELATIONAL RISK MAPPING
            </div>
            <h1 className="text-3xl font-serif tracking-tight text-white font-normal mt-1">
              FraudDNA
            </h1>
            <p className="text-xs text-[#9194A1] font-sans mt-1">
              Find the relationships that individual transactions hide.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <DataLabel label="Graph Topology" />
            {clustersData && (
              <span className="text-xs font-mono text-[#777A88]">
                {clustersData.total_clusters} Coordinated Clusters
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
            <div className="text-[10px] font-mono text-[#5E616E] uppercase tracking-wider mb-2 px-1">
              SUSPICIOUS NETWORKS ({clustersData?.clusters.length || 0})
            </div>

            {clusters.status === "loading" && <LoadingState message="Loading clusters..." />}
            {clusters.status === "error" && (
              <ErrorState title="NETWORK ERROR" error={clusters.error} onRetry={clusters.refetch} />
            )}

            {clustersData && (
              <div className="space-y-1.5 max-h-[620px] overflow-y-auto pr-1 custom-scrollbar">
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
                  {graph.total_nodes} Nodes • {graph.total_edges} Edges
                </div>
              )}
            </div>

            <div className="flex-1 min-h-[580px]">
              {!selectedClusterId && (
                <EmptyState
                  title="SELECT A CLUSTER"
                  description="Choose a suspicious network from the left ledger to inspect topology."
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

        {/* Right: Cluster & Node Inspector (3 Cols) */}
        <div className="lg:col-span-3 space-y-4">
          {/* Cluster Deep Inspector Card */}
          {currentClusterSummary && (
            <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4 space-y-3.5">
              <div className="border-b border-[#1C1D22] pb-2.5">
                <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-[#CC9166] font-semibold">
                  CLUSTER METRICS
                </div>
                <h3 className="text-base font-serif text-white font-normal mt-0.5">
                  {currentClusterSummary.cluster_id}
                </h3>
              </div>

              <div className="space-y-2.5 text-xs font-mono">
                <div className="flex items-center justify-between">
                  <span className="text-[#777A88]">Cluster Risk Score:</span>
                  <span className="font-semibold text-white">
                    {currentClusterSummary.cluster_risk_score.toFixed(4)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#777A88]">Suspicious Status:</span>
                  <RiskBadge
                    level={currentClusterSummary.is_suspicious ? "critical" : "low"}
                    size="xs"
                  />
                </div>
                <div className="flex items-center justify-between border-t border-[#1C1D22]/60 pt-2">
                  <span className="text-[#777A88] flex items-center gap-1.5">
                    <Layers className="h-3 w-3 text-[#5E616E]" />
                    <span>Transactions</span>
                  </span>
                  <span className="text-white">{currentClusterSummary.transaction_count}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#777A88] flex items-center gap-1.5">
                    <Users className="h-3 w-3 text-[#5E616E]" />
                    <span>Customers</span>
                  </span>
                  <span className="text-white">{currentClusterSummary.customer_count}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#777A88] flex items-center gap-1.5">
                    <Smartphone className="h-3 w-3 text-[#5E616E]" />
                    <span>Devices</span>
                  </span>
                  <span className="text-white">{currentClusterSummary.device_count}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#777A88] flex items-center gap-1.5">
                    <CreditCard className="h-3 w-3 text-[#5E616E]" />
                    <span>Cards</span>
                  </span>
                  <span className="text-white">{currentClusterSummary.card_count}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#777A88] flex items-center gap-1.5">
                    <Store className="h-3 w-3 text-[#5E616E]" />
                    <span>Merchants</span>
                  </span>
                  <span className="text-white">{currentClusterSummary.merchant_count}</span>
                </div>
                <div className="flex items-center justify-between border-t border-[#1C1D22]/60 pt-2">
                  <span className="text-[#777A88]">Total Fraud Volume:</span>
                  <span className="text-[#CC9166] font-semibold">
                    {formatINR(currentClusterSummary.suspicious_transaction_amount)}
                  </span>
                </div>
              </div>

              {currentClusterSummary.primary_reason && (
                <div className="pt-2 border-t border-[#1C1D22]">
                  <div className="text-[10px] font-mono text-[#5E616E] uppercase mb-1">
                    Primary Attack Signature
                  </div>
                  <p className="text-xs text-[#C7A66B] font-sans leading-relaxed">
                    {currentClusterSummary.primary_reason}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Node Inspector Card (when a user clicks a node) */}
          {selectedNode && (
            <div className="bg-[#040406] border border-[#CC9166]/50 rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-[#1C1D22] pb-2">
                <span className="text-[10px] font-mono uppercase text-[#CC9166] font-semibold">
                  Selected Node
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
                      <span>Open in Forensic Console</span>
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
      <Suspense fallback={<LoadingState message="Connecting to FraudDNA graph engine..." />}>
        <FraudDNAContent />
      </Suspense>
    </DashboardLayout>
  );
}
