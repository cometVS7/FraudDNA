"use client";

import { useState, useCallback, useMemo } from "react";
import { DashboardLayout } from "@/components/layout";
import {
  RiskBadge,
  LoadingState,
  ErrorState,
  EmptyState,
  SectionCard,
  formatINR,
} from "@/components/ui";
import { useAsync } from "@/hooks/use-async";
import { fetchClusters, fetchClusterGraph } from "@/lib/api";
import type { ClustersResponse, GraphData, ClusterSummary } from "@/lib/api";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const ENTITY_COLORS: Record<string, string> = {
  customer: "#3b82f6",
  transaction: "#10b981",
  device: "#8b5cf6",
  ip: "#f59e0b",
  card: "#ec4899",
  merchant: "#06b6d4",
};

const ENTITY_ABBREV: Record<string, string> = {
  customer: "CU",
  transaction: "TX",
  device: "DV",
  ip: "IP",
  card: "CD",
  merchant: "ME",
};

function buildReactFlowData(
  graphData: GraphData
): { nodes: Node[]; edges: Edge[] } {
  const nodeCount = graphData.nodes.length;
  const radius = Math.max(300, nodeCount * 30);

  const nodes: Node[] = graphData.nodes.map((n, i) => {
    const angle = (2 * Math.PI * i) / nodeCount;
    const x = radius * Math.cos(angle) + radius + 100;
    const y = radius * Math.sin(angle) + radius + 100;
    const color = ENTITY_COLORS[n.entity_type] || "#6b7280";
    const isHighRisk = n.risk_score >= 0.7;

    return {
      id: n.id,
      position: { x, y },
      data: {
        label: (
          <div className="text-center">
            <div
              className="mx-auto mb-1 rounded-full flex items-center justify-center text-white text-[10px] font-bold"
              style={{
                width: isHighRisk ? 36 : 28,
                height: isHighRisk ? 36 : 28,
                backgroundColor: color,
                boxShadow: isHighRisk ? `0 0 12px ${color}60` : undefined,
              }}
            >
              {ENTITY_ABBREV[n.entity_type] || "?"}
            </div>
            <div className="text-[9px] text-gray-600 max-w-[80px] truncate">
              {n.raw_id}
            </div>
            {n.risk_score > 0 && (
              <div className={`text-[8px] font-mono font-bold ${n.risk_score >= 0.7 ? "text-red-600" : n.risk_score >= 0.37 ? "text-amber-600" : "text-gray-400"}`}>
                {n.risk_score.toFixed(2)}
              </div>
            )}
          </div>
        ),
      },
      style: {
        background: "white",
        border: `2px solid ${isHighRisk ? "#ef4444" : color + "40"}`,
        borderRadius: "12px",
        padding: "6px",
        fontSize: "10px",
        width: "auto",
        minWidth: "80px",
      },
    };
  });

  const edges: Edge[] = graphData.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.relation,
    style: { stroke: "#d1d5db", strokeWidth: 1.5 },
    labelStyle: { fontSize: 8, fill: "#9ca3af" },
    markerEnd: { type: MarkerType.ArrowClosed, width: 12, height: 12, color: "#d1d5db" },
    animated: false,
  }));

  return { nodes, edges };
}

export default function FraudDNAPage() {
  const [selectedCluster, setSelectedCluster] = useState<string | null>(null);

  const clusters = useAsync<ClustersResponse>(
    () => fetchClusters({ suspicious_only: true, limit: 20, sort_by: "risk_score" }),
    []
  );

  const graphFetcher = useCallback(() => {
    if (!selectedCluster) return Promise.resolve(null);
    return fetchClusterGraph(selectedCluster);
  }, [selectedCluster]);

  const graphData = useAsync<GraphData | null>(graphFetcher, [selectedCluster]);

  const flowData = useMemo(() => {
    if (graphData.status !== "success" || !graphData.data) return null;
    return buildReactFlowData(graphData.data);
  }, [graphData]);

  return (
    <DashboardLayout>
      <div className="space-y-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight">FraudDNA Graph</h2>
          <p className="text-sm text-muted-foreground">
            Interactive relationship graph — discover hidden connections between entities
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Cluster List */}
          <div className="lg:col-span-1">
            <SectionCard title="Suspicious Clusters" subtitle="Select a cluster to explore">
              {clusters.status === "loading" && <LoadingState />}
              {clusters.status === "error" && <ErrorState error={clusters.error} />}
              {clusters.status === "success" && (
                <div className="space-y-1 max-h-[600px] overflow-y-auto">
                  {clusters.data.clusters.length === 0 && (
                    <EmptyState title="No suspicious clusters" />
                  )}
                  {clusters.data.clusters.map((c: ClusterSummary) => (
                    <button
                      key={c.cluster_id}
                      onClick={() => setSelectedCluster(c.cluster_id)}
                      className={`w-full text-left px-3 py-2.5 rounded-lg border transition-all text-xs ${
                        selectedCluster === c.cluster_id
                          ? "bg-primary/10 border-primary/30 shadow-sm"
                          : "border-border/50 hover:bg-muted/30"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-mono font-medium">{c.cluster_id}</span>
                        <RiskBadge
                          level={
                            c.cluster_risk_score >= 0.9
                              ? "critical"
                              : c.cluster_risk_score >= 0.7
                                ? "high"
                                : "medium"
                          }
                          size="xs"
                        />
                      </div>
                      <div className="text-muted-foreground">
                        {c.transaction_count} txns · {c.customer_count} customers · {formatINR(c.suspicious_transaction_amount)}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </SectionCard>
          </div>

          {/* Graph Canvas */}
          <div className="lg:col-span-3">
            <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden" style={{ height: 650 }}>
              {!selectedCluster && (
                <EmptyState
                  title="Select a cluster"
                  description="Choose a suspicious cluster from the left panel to explore its relationship graph"
                />
              )}
              {selectedCluster && graphData.status === "loading" && (
                <LoadingState message="Loading graph data..." />
              )}
              {selectedCluster && graphData.status === "error" && (
                <ErrorState error={graphData.error} />
              )}
              {flowData && (
                <ReactFlow
                  nodes={flowData.nodes}
                  edges={flowData.edges}
                  fitView
                  minZoom={0.2}
                  maxZoom={2}
                  proOptions={{ hideAttribution: true }}
                >
                  <Background color="#f3f4f6" gap={20} />
                  <Controls
                    showInteractive={false}
                    className="bg-white shadow-lg rounded-lg border border-border"
                  />
                  <MiniMap
                    nodeColor={(n) => {
                      const border = n.style?.border as string;
                      if (border?.includes("#ef4444")) return "#ef4444";
                      return "#10b981";
                    }}
                    className="rounded-lg border border-border"
                  />
                </ReactFlow>
              )}
            </div>

            {/* Legend */}
            <div className="flex flex-wrap gap-3 mt-3">
              {Object.entries(ENTITY_COLORS).map(([type, color]) => (
                <div key={type} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <span
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
