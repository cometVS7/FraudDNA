"use client";

import React, { useState, useRef } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  ArrowRight,
  Layers,
  Share2,
  Flame,
  Fingerprint,
} from "lucide-react";

export function HeroSpatialStack() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [tilt, setTilt] = useState({ rotateX: 20, rotateY: -15, isHovered: false });
  const [exploded, setExploded] = useState(false);
  const [activeLayer, setActiveLayer] = useState<number | null>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;

    // Normalizing tilt angles
    const rotateY = (x / (rect.width / 2)) * 18 - 12;
    const rotateX = -(y / (rect.height / 2)) * 18 + 18;
    setTilt({ rotateX, rotateY, isHovered: true });
  };

  const handleMouseLeave = () => {
    setTilt({ rotateX: 20, rotateY: -15, isHovered: false });
  };

  return (
    <div className="relative w-full max-w-5xl mx-auto flex flex-col items-center justify-center py-8">
      {/* Interactive Controls Pill */}
      <div className="flex items-center gap-3 mb-6 z-20">
        <button
          onClick={() => setExploded(!exploded)}
          className={`px-4 py-1.5 rounded-full text-xs font-mono transition-all duration-200 flex items-center gap-2 border ${
            exploded
              ? "bg-cyan-500/20 text-cyan-300 border-cyan-400/40 shadow-[0_0_15px_rgba(0,229,255,0.3)]"
              : "bg-white/5 text-slate-400 border-white/10 hover:text-white hover:bg-white/10"
          }`}
        >
          <Layers className="h-3.5 w-3.5 text-cyan-400" />
          <span>{exploded ? "Collapse 3D Stack" : "Explode Spatial Layers"}</span>
        </button>
        <span className="text-[11px] font-mono text-slate-500 hidden sm:inline">
          Move cursor to orbit spatial perspective
        </span>
      </div>

      {/* 3D Viewport Stage */}
      <div
        ref={containerRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={{ perspective: "1600px" }}
        className="relative w-full h-[520px] sm:h-[580px] flex items-center justify-center cursor-grab active:cursor-grabbing"
      >
        {/* Ambient Volumetric Halos */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[350px] bg-gradient-to-tr from-cyan-500/20 via-blue-600/20 to-purple-600/10 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 w-[380px] h-[160px] bg-red-500/15 rounded-full blur-[80px] pointer-events-none" />

        {/* 3D Transform Container */}
        <div
          style={{
            transform: `rotateX(${tilt.rotateX}deg) rotateY(${tilt.rotateY}deg)`,
            transformStyle: "preserve-3d",
            transition: tilt.isHovered
              ? "transform 0.1s ease-out"
              : "transform 0.8s cubic-bezier(0.2, 0.8, 0.2, 1)",
          }}
          className="relative w-[340px] sm:w-[480px] md:w-[560px] h-[360px] sm:h-[400px]"
        >
          {/* ========================================================
              LAYER 1 (TOP) — TRANSACTIONS LOOK NORMAL
              ======================================================== */}
          <div
            onClick={() => setActiveLayer(1)}
            style={{
              transform: `translateZ(${exploded ? "160px" : "90px"}) translateY(${
                exploded ? "-40px" : "-15px"
              })`,
              transformStyle: "preserve-3d",
            }}
            className={`absolute inset-0 rounded-2xl p-5 backdrop-blur-xl border transition-all duration-300 group ${
              activeLayer === 1
                ? "bg-[#0c1424]/90 border-cyan-400 shadow-[0_0_40px_rgba(0,229,255,0.4)]"
                : "bg-[#09101d]/85 border-cyan-500/30 hover:border-cyan-400/60 shadow-[0_20px_50px_rgba(0,0,0,0.5)]"
            }`}
          >
            {/* Top Layer Header */}
            <div className="flex items-center justify-between border-b border-cyan-500/20 pb-3">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
                <span className="text-[11px] font-mono tracking-widest text-cyan-300 uppercase font-bold">
                  Layer 01 • Live Transactions
                </span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-500/30 text-cyan-200">
                ₹8,92,400 / min
              </span>
            </div>

            {/* Transaction Rows */}
            <div className="mt-3 space-y-2">
              <div className="flex items-center justify-between p-2 rounded-lg bg-white/[0.04] border border-white/[0.05] text-xs font-mono">
                <div className="flex items-center gap-2">
                  <span className="text-slate-300 font-medium">₹1,299</span>
                  <span className="text-[10px] text-slate-400">tx_0001987 • Amazon Pay</span>
                </div>
                <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  ALLOW (0.04)
                </span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-white/[0.04] border border-white/[0.05] text-xs font-mono">
                <div className="flex items-center gap-2">
                  <span className="text-slate-300 font-medium">₹3,499</span>
                  <span className="text-[10px] text-slate-400">tx_0001988 • Swiggy UPI</span>
                </div>
                <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  ALLOW (0.09)
                </span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-white/[0.04] border border-white/[0.05] text-xs font-mono">
                <div className="flex items-center gap-2">
                  <span className="text-slate-300 font-medium">₹2,499</span>
                  <span className="text-[10px] text-slate-400">tx_0001990 • Flipkart Quick</span>
                </div>
                <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  ALLOW (0.12)
                </span>
              </div>

              {/* Target Flagged Golden Transaction */}
              <div className="flex items-center justify-between p-2 rounded-lg bg-cyan-950/40 border border-cyan-400/40 text-xs font-mono shadow-[0_0_15px_rgba(0,229,255,0.15)]">
                <div className="flex items-center gap-2">
                  <span className="text-cyan-300 font-bold">₹99,999</span>
                  <span className="text-[10px] text-cyan-200/80">tx_0001991 • Merchant_9921</span>
                </div>
                <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/40 font-semibold">
                  HOLD (0.94)
                </span>
              </div>
            </div>

            {/* Layer Floating Tag Label */}
            <div className="absolute -right-6 -top-4 bg-cyan-500 text-black px-3 py-1 rounded-full text-[10px] font-mono font-bold shadow-[0_0_15px_rgba(0,229,255,0.8)]">
              TRANSACTIONS Look normal.
            </div>
          </div>

          {/* ========================================================
              LAYER 2 (MIDDLE) — RELATIONSHIPS REVEAL THE TRUTH
              ======================================================== */}
          <div
            onClick={() => setActiveLayer(2)}
            style={{
              transform: `translateZ(${exploded ? "0px" : "0px"}) translateY(${
                exploded ? "0px" : "0px"
              })`,
              transformStyle: "preserve-3d",
            }}
            className={`absolute inset-0 rounded-2xl p-5 backdrop-blur-xl border transition-all duration-300 group ${
              activeLayer === 2
                ? "bg-[#140e2b]/90 border-purple-400 shadow-[0_0_40px_rgba(168,85,247,0.4)]"
                : "bg-[#0d091e]/85 border-purple-500/30 hover:border-purple-400/60 shadow-[0_20px_50px_rgba(0,0,0,0.6)]"
            }`}
          >
            {/* Middle Layer Header */}
            <div className="flex items-center justify-between border-b border-purple-500/20 pb-3">
              <div className="flex items-center gap-2">
                <Share2 className="h-4 w-4 text-purple-400" />
                <span className="text-[11px] font-mono tracking-widest text-purple-300 uppercase font-bold">
                  Layer 02 • Entity & Topology Graph
                </span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950/60 border border-purple-500/30 text-purple-200">
                17 Nodes Linked
              </span>
            </div>

            {/* Simulated Topology Network Visualizer */}
            <div className="mt-3 relative h-44 rounded-xl bg-purple-950/20 border border-purple-500/20 overflow-hidden flex items-center justify-center p-3">
              {/* Connecting SVG graph lines */}
              <svg className="absolute inset-0 w-full h-full stroke-purple-400/40" strokeWidth="1.5">
                <line x1="20%" y1="30%" x2="50%" y2="50%" strokeDasharray="3 3" />
                <line x1="80%" y1="25%" x2="50%" y2="50%" strokeDasharray="3 3" />
                <line x1="30%" y1="75%" x2="50%" y2="50%" />
                <line x1="70%" y1="80%" x2="50%" y2="50%" />
              </svg>

              {/* Central Shared Hub */}
              <div className="relative z-10 flex flex-col items-center">
                <div className="h-12 w-12 rounded-full bg-gradient-to-tr from-purple-600 to-cyan-500 p-0.5 shadow-[0_0_20px_rgba(168,85,247,0.8)] animate-pulse">
                  <div className="h-full w-full rounded-full bg-[#0d091e] flex items-center justify-center">
                    <Fingerprint className="h-6 w-6 text-cyan-300" />
                  </div>
                </div>
                <span className="mt-1 text-[9px] font-mono text-purple-200 font-bold bg-purple-900/60 px-2 py-0.5 rounded border border-purple-400/40">
                  Shared Device: dev_88921a
                </span>
              </div>

              {/* Surrounding Ring Nodes */}
              <div className="absolute top-3 left-4 text-[9px] font-mono px-2 py-1 rounded bg-black/60 border border-purple-500/30 text-slate-300">
                cust_1092 • IP: 103.21.244.11
              </div>
              <div className="absolute top-3 right-4 text-[9px] font-mono px-2 py-1 rounded bg-black/60 border border-purple-500/30 text-slate-300">
                cust_4481 • IP: 103.21.244.14
              </div>
              <div className="absolute bottom-3 left-4 text-[9px] font-mono px-2 py-1 rounded bg-black/60 border border-purple-500/30 text-slate-300">
                cust_7729 • Card Fingerprint
              </div>
              <div className="absolute bottom-3 right-4 text-[9px] font-mono px-2 py-1 rounded bg-black/60 border border-purple-500/30 text-slate-300">
                Merchant #9921 Collusion
              </div>
            </div>

            {/* Layer Floating Tag Label */}
            <div className="absolute -left-6 -top-4 bg-purple-500 text-white px-3 py-1 rounded-full text-[10px] font-mono font-bold shadow-[0_0_15px_rgba(168,85,247,0.8)]">
              RELATIONSHIPS Reveal the truth.
            </div>
          </div>

          {/* ========================================================
              LAYER 3 (BOTTOM) — INTELLIGENCE STOPS FRAUD
              ======================================================== */}
          <div
            onClick={() => setActiveLayer(3)}
            style={{
              transform: `translateZ(${exploded ? "-160px" : "-90px"}) translateY(${
                exploded ? "40px" : "15px"
              })`,
              transformStyle: "preserve-3d",
            }}
            className={`absolute inset-0 rounded-2xl p-5 backdrop-blur-xl border transition-all duration-300 group ${
              activeLayer === 3
                ? "bg-[#250a10]/90 border-rose-400 shadow-[0_0_40px_rgba(244,63,94,0.5)]"
                : "bg-[#18060a]/85 border-rose-500/30 hover:border-rose-400/60 shadow-[0_20px_50px_rgba(0,0,0,0.7)]"
            }`}
          >
            {/* Bottom Layer Header */}
            <div className="flex items-center justify-between border-b border-rose-500/20 pb-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-rose-400" />
                <span className="text-[11px] font-mono tracking-widest text-rose-300 uppercase font-bold">
                  Layer 03 • Syndicate Intelligence & Policy
                </span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950/60 border border-rose-500/40 text-rose-200 font-bold">
                HOLD ENFORCED
              </span>
            </div>

            {/* Syndicate Details Box */}
            <div className="mt-3 p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 space-y-2 text-xs font-mono">
              <div className="flex items-center justify-between">
                <span className="text-rose-200 font-bold flex items-center gap-1.5">
                  <Flame className="h-3.5 w-3.5 text-rose-400" />
                  DEVICE_REUSE_RING + MULTI_INFRASTRUCTURE
                </span>
                <span className="text-[10px] text-rose-400 font-bold">Risk: 99.4%</span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                <div className="p-2 rounded bg-black/40 border border-rose-900/40">
                  <div className="text-[9px] text-slate-400 uppercase">Authoritative Policy</div>
                  <div className="text-rose-400 font-bold mt-0.5">HOLD (Non-Overridable)</div>
                </div>
                <div className="p-2 rounded bg-black/40 border border-rose-900/40">
                  <div className="text-[9px] text-slate-400 uppercase">AI Recommendation</div>
                  <div className="text-amber-300 font-bold mt-0.5">MANUAL_REVIEW_ESCALATION</div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-1 text-[10px] text-slate-400">
                <span>RAG Verified: Section 4.2 ATO Guidelines</span>
                <Link
                  href="/investigate?tx=tx_0001991"
                  className="text-cyan-400 hover:text-cyan-300 font-bold flex items-center gap-1"
                >
                  <span>Open Dossier</span>
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </div>
            </div>

            {/* Layer Floating Tag Label */}
            <div className="absolute -right-6 -bottom-4 bg-rose-600 text-white px-3 py-1 rounded-full text-[10px] font-mono font-bold shadow-[0_0_15px_rgba(244,63,94,0.8)]">
              INTELLIGENCE Stops fraud.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
