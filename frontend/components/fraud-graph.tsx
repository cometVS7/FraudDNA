"use client";

import React, { useMemo } from "react";
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
import type { GraphData, GraphNode } from "@/lib/api";

const ENTITY_ICONS: Record<string, string> = {
  transaction: "TX",
  customer: "CU",
  device: "DV",
  ip: "IP",
  card: "CD",
  merchant: "ME",
};

interface FraudGraphProps {
  graphData: GraphData;
  selectedId?: string;
  onSelectNode?: (node: GraphNode) => void;
  className?: string;
}

export function FraudGraph({
  graphData,
  selectedId,
  onSelectNode,
  className = "h-[450px] w-full",
}: FraudGraphProps) {
  const { nodes, edges } = useMemo(() => {
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
      return { nodes: [], edges: [] };
    }

    const nodeCount = graphData.nodes.length;
    // Radial / Concentric Layout
    const centerNode = graphData.nodes.find(
      (n) => n.id === selectedId || n.raw_id === selectedId || n.entity_type === "transaction"
    ) || graphData.nodes[0];

    const radius = Math.max(220, Math.min(nodeCount * 36, 450));
    const centerX = radius + 60;
    const centerY = radius + 60;

    const flowNodes: Node[] = graphData.nodes.map((n, idx) => {
      const isSelected =
        n.id === selectedId ||
        n.raw_id === selectedId ||
        (selectedId && n.id.includes(selectedId));
      const isCenter = n.id === centerNode.id;
      const isCritical = n.risk_score >= 0.85;
      const isHigh = n.risk_score >= 0.7;

      let x = centerX;
      let y = centerY;

      if (!isCenter) {
        // Place other nodes evenly on the circle
        const otherNodes = graphData.nodes.filter((node) => node.id !== centerNode.id);
        const otherIdx = otherNodes.findIndex((node) => node.id === n.id);
        const angle = (2 * Math.PI * (otherIdx >= 0 ? otherIdx : idx)) / Math.max(1, otherNodes.length);
        x = centerX + radius * Math.cos(angle);
        y = centerY + radius * Math.sin(angle);
      }

      // Border and accent styling
      let borderColor = "#2E3038";
      let boxShadow = "none";
      if (isSelected) {
        borderColor = "#CC9166"; // Warm Copper
        boxShadow = "0 0 16px rgba(204, 145, 102, 0.25)";
      } else if (isCritical) {
        borderColor = "#D05B5B"; // Critical Risk
        boxShadow = "0 0 12px rgba(208, 91, 91, 0.2)";
      } else if (isHigh) {
        borderColor = "#C47A63"; // High Risk
      }

      const typeAbbrev = ENTITY_ICONS[n.entity_type.toLowerCase()] || "EN";

      return {
        id: n.id,
        position: { x, y },
        data: {
          rawNode: n,
          label: (
            <div
              className="flex items-center gap-2 text-left cursor-pointer select-none"
              onClick={() => onSelectNode && onSelectNode(n)}
            >
              <div
                className={`h-6 w-6 rounded flex items-center justify-center text-[10px] font-mono font-semibold flex-shrink-0 transition-colors ${
                  isSelected
                    ? "bg-[#CC9166] text-[#08080A]"
                    : isCritical
                    ? "bg-[#D05B5B]/20 text-[#D05B5B] border border-[#D05B5B]/40"
                    : "bg-[#1C1D22] text-[#9194A1]"
                }`}
              >
                {typeAbbrev}
              </div>
              <div className="min-w-0 pr-1">
                <div className="text-[11px] font-mono text-[#E2E3E9] truncate max-w-[110px]">
                  {n.raw_id || n.label || n.id}
                </div>
                <div className="text-[9px] font-mono text-[#5E616E] flex items-center gap-1.5 leading-tight">
                  <span className="capitalize">{n.entity_type}</span>
                  {n.risk_score > 0 && (
                    <span
                      className={`font-semibold ${
                        n.risk_score >= 0.7
                          ? "text-[#D05B5B]"
                          : n.risk_score >= 0.37
                          ? "text-[#C7A66B]"
                          : "text-[#8FAF9B]"
                      }`}
                    >
                      {n.risk_score.toFixed(2)}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ),
        },
        style: {
          backgroundColor: "#121317",
          border: `1px solid ${borderColor}`,
          borderRadius: "8px",
          padding: "6px 10px",
          boxShadow,
          width: "auto",
          minWidth: "130px",
          maxWidth: "180px",
          transition: "border-color 0.2s ease, box-shadow 0.2s ease",
        },
      };
    });

    const flowEdges: Edge[] = graphData.edges.map((e) => {
      const isConnectedToSelected =
        selectedId &&
        (e.source === selectedId ||
          e.target === selectedId ||
          e.source.includes(selectedId) ||
          e.target.includes(selectedId));

      return {
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.relation || undefined,
        animated: false,
        style: {
          stroke: isConnectedToSelected ? "#CC9166" : "#2E3038",
          strokeWidth: isConnectedToSelected ? 1.8 : 1,
          opacity: isConnectedToSelected ? 0.9 : 0.6,
        },
        labelStyle: {
          fill: "#5E616E",
          fontSize: 9,
          fontFamily: "var(--font-mono)",
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isConnectedToSelected ? "#CC9166" : "#2E3038",
          width: 10,
          height: 10,
        },
      };
    });

    return { nodes: flowNodes, edges: flowEdges };
  }, [graphData, selectedId, onSelectNode]);

  return (
    <div className={`relative rounded-lg overflow-hidden border border-[#1C1D22] bg-[#040406] ${className}`}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        minZoom={0.2}
        maxZoom={2.0}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#1C1D22" gap={20} size={1} />
        <Controls
          className="!bg-[#121317] !border !border-[#1C1D22] !rounded-md overflow-hidden !shadow-none [&>button]:!bg-[#121317] [&>button]:!border-b [&>button]:!border-[#1C1D22] [&>button]:!text-[#9194A1] [&>button:hover]:!bg-[#1C1D22] [&>button:hover]:!text-white"
        />
        <MiniMap
          nodeColor={(node) => {
            if (node.id === selectedId || (selectedId && node.id.includes(selectedId))) {
              return "#CC9166";
            }
            return "#2E3038";
          }}
          maskColor="rgba(4, 4, 6, 0.75)"
          className="!bg-[#040406] !border !border-[#1C1D22] !rounded-md"
        />
      </ReactFlow>

      {/* Subtle Legend Overlay */}
      <div className="absolute top-3 left-3 pointer-events-none bg-[#08080A]/85 backdrop-blur-xs border border-[#1C1D22] px-2.5 py-1.5 rounded text-[10px] font-mono text-[#777A88] flex items-center gap-3">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-xs border border-[#CC9166] bg-[#CC9166]/20" />
          <span>Selected</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-xs border border-[#D05B5B] bg-[#D05B5B]/20" />
          <span>Critical</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-xs border border-[#2E3038] bg-[#121317]" />
          <span>Entity</span>
        </span>
      </div>
    </div>
  );
}
