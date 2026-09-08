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
import {
  CreditCard,
  Smartphone,
  Globe,
  Store,
  User,
  Zap,
} from "lucide-react";

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
  className = "h-[480px] w-full",
}: FraudGraphProps) {
  const { nodes, edges } = useMemo(() => {
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
      return { nodes: [], edges: [] };
    }

    const nodeCount = graphData.nodes.length;
    // Radial / Concentric Dynamic Layout
    const centerNode =
      graphData.nodes.find(
        (n) => n.id === selectedId || n.raw_id === selectedId || n.entity_type === "transaction"
      ) || graphData.nodes[0];

    const radius = Math.max(200, Math.min(nodeCount * 32, 420));
    const centerX = radius + 80;
    const centerY = radius + 80;

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
        const otherNodes = graphData.nodes.filter((node) => node.id !== centerNode.id);
        const otherIdx = otherNodes.findIndex((node) => node.id === n.id);
        const angle = (2 * Math.PI * (otherIdx >= 0 ? otherIdx : idx)) / Math.max(1, otherNodes.length);
        x = centerX + radius * Math.cos(angle);
        y = centerY + radius * Math.sin(angle);
      }

      // Styling based on risk and selection
      let borderColor = "rgba(255, 255, 255, 0.08)";
      let boxShadow = "0 8px 24px rgba(0, 0, 0, 0.4)";
      let badgeBg = "#181A22";
      let badgeColor = "#9194A1";

      if (isSelected) {
        borderColor = "#CC9166";
        boxShadow = "0 0 20px rgba(204, 145, 102, 0.35), inset 0 0 10px rgba(204, 145, 102, 0.1)";
        badgeBg = "#CC9166";
        badgeColor = "#08080A";
      } else if (isCritical) {
        borderColor = "rgba(239, 68, 68, 0.8)";
        boxShadow = "0 0 18px rgba(239, 68, 68, 0.3)";
        badgeBg = "rgba(239, 68, 68, 0.2)";
        badgeColor = "#EF4444";
      } else if (isHigh) {
        borderColor = "rgba(249, 115, 22, 0.7)";
        boxShadow = "0 0 12px rgba(249, 115, 22, 0.2)";
        badgeBg = "rgba(249, 115, 22, 0.2)";
        badgeColor = "#F97316";
      }

      const entityType = n.entity_type.toLowerCase();

      return {
        id: n.id,
        position: { x, y },
        data: {
          rawNode: n,
          label: (
            <div
              className="flex items-center gap-2.5 text-left cursor-pointer select-none py-0.5"
              onClick={() => onSelectNode && onSelectNode(n)}
            >
              <div
                style={{ backgroundColor: badgeBg, color: badgeColor }}
                className="h-7 w-7 rounded-md flex items-center justify-center text-[10px] font-mono font-bold flex-shrink-0 transition-transform duration-200 group-hover:scale-105"
              >
                {entityType === "transaction" ? (
                  <Zap className="h-3.5 w-3.5" />
                ) : entityType === "customer" ? (
                  <User className="h-3.5 w-3.5" />
                ) : entityType === "device" ? (
                  <Smartphone className="h-3.5 w-3.5" />
                ) : entityType === "card" ? (
                  <CreditCard className="h-3.5 w-3.5" />
                ) : entityType === "ip" ? (
                  <Globe className="h-3.5 w-3.5" />
                ) : entityType === "merchant" ? (
                  <Store className="h-3.5 w-3.5" />
                ) : (
                  n.entity_type.slice(0, 2).toUpperCase()
                )}
              </div>
              <div className="min-w-0 pr-1 flex-1">
                <div className="text-[11px] font-mono text-[#E2E3E9] font-medium truncate max-w-[120px]">
                  {n.raw_id || n.label || n.id}
                </div>
                <div className="text-[9px] font-mono text-[#777A88] flex items-center gap-1.5 leading-tight mt-0.5">
                  <span className="capitalize">{n.entity_type}</span>
                  {n.risk_score > 0 && (
                    <span
                      className={`font-semibold ${
                        n.risk_score >= 0.7
                          ? "text-[#EF4444]"
                          : n.risk_score >= 0.37
                          ? "text-[#F59E0B]"
                          : "text-[#10B981]"
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
          backgroundColor: "#0D0F14",
          border: `1px solid ${borderColor}`,
          borderRadius: "10px",
          padding: "6px 10px",
          boxShadow,
          width: "auto",
          minWidth: "140px",
          maxWidth: "190px",
          transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
        },
      };
    });

    const flowEdges: Edge[] = graphData.edges.map((e) => {
      const isConnectedToSelected = Boolean(
        selectedId &&
          (e.source === selectedId ||
            e.target === selectedId ||
            e.source.includes(selectedId) ||
            e.target.includes(selectedId))
      );

      return {
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.relation || undefined,
        animated: isConnectedToSelected,
        style: {
          stroke: isConnectedToSelected ? "#CC9166" : "rgba(255, 255, 255, 0.12)",
          strokeWidth: isConnectedToSelected ? 2 : 1,
          opacity: isConnectedToSelected ? 1 : 0.6,
        },
        labelStyle: {
          fill: isConnectedToSelected ? "#CC9166" : "#777A88",
          fontSize: 9,
          fontFamily: "var(--font-mono)",
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isConnectedToSelected ? "#CC9166" : "rgba(255, 255, 255, 0.2)",
          width: 8,
          height: 8,
        },
      };
    });

    return { nodes: flowNodes, edges: flowEdges };
  }, [graphData, selectedId, onSelectNode]);

  return (
    <div className={`relative rounded-xl overflow-hidden border border-white/[0.08] bg-[#06080E] ${className}`}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        minZoom={0.2}
        maxZoom={2.0}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#1C1D24" gap={24} size={1} />
        <Controls
          className="!bg-[#0E1017] !border !border-white/[0.08] !rounded-lg overflow-hidden !shadow-2xl [&>button]:!bg-[#0E1017] [&>button]:!border-b [&>button]:!border-white/[0.06] [&>button]:!text-[#9194A1] [&>button:hover]:!bg-[#181A24] [&>button:hover]:!text-white"
        />
        <MiniMap
          nodeColor={(node) => {
            if (node.id === selectedId || (selectedId && node.id.includes(selectedId))) {
              return "#CC9166";
            }
            return "#2E3038";
          }}
          maskColor="rgba(6, 8, 14, 0.85)"
          className="!bg-[#0A0C10] !border !border-white/[0.08] !rounded-lg"
        />
      </ReactFlow>

      {/* Forensic Graph HUD Legend Overlay */}
      <div className="absolute top-3 left-3 pointer-events-none bg-[#0A0C10]/90 backdrop-blur-md border border-white/[0.08] px-3 py-1.5 rounded-lg text-[10px] font-mono text-[#777A88] flex items-center gap-3 shadow-xl">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full border border-[#CC9166] bg-[#CC9166]/40 shadow-[0_0_6px_rgba(204,145,102,0.6)]" />
          <span className="text-white">Active</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full border border-[#EF4444] bg-[#EF4444]/40 shadow-[0_0_6px_rgba(239,68,68,0.6)]" />
          <span className="text-[#EF4444]">Critical</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full border border-white/[0.2] bg-white/[0.08]" />
          <span>Entity</span>
        </span>
      </div>
    </div>
  );
}
