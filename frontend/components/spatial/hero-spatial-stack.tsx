"use client";

import React, { useState, useRef, useEffect } from "react";
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
  const cardStackRef = useRef<HTMLDivElement>(null);
  const layer1Ref = useRef<HTMLDivElement>(null);
  const layer2Ref = useRef<HTMLDivElement>(null);
  const layer3Ref = useRef<HTMLDivElement>(null);

  const [exploded, setExploded] = useState(false);
  const [activeLayer, setActiveLayer] = useState<number | null>(null);

  // Physics animation refs (Lerp smoothing)
  const rafId = useRef<number | null>(null);
  const targetRot = useRef({ x: 14, y: -10 });
  const currentRot = useRef({ x: 14, y: -10 });
  const isHovered = useRef(false);

  useEffect(() => {
    const isCoarse = window.matchMedia("(pointer: coarse)").matches;
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (isCoarse || prefersReducedMotion || !containerRef.current) {
      return;
    }

    const animate = () => {
      // Smooth interpolation
      const factor = isHovered.current ? 0.08 : 0.05;
      currentRot.current.x += (targetRot.current.x - currentRot.current.x) * factor;
      currentRot.current.y += (targetRot.current.y - currentRot.current.y) * factor;

      if (cardStackRef.current) {
        cardStackRef.current.style.transform = `rotateX(${currentRot.current.x.toFixed(
          2
        )}deg) rotateY(${currentRot.current.y.toFixed(2)}deg)`;
      }

      // Parallax shifts on layers
      const shiftX = (currentRot.current.y - -10) * 0.5;
      const shiftY = (currentRot.current.x - 14) * 0.5;

      if (layer1Ref.current) {
        layer1Ref.current.style.transform = `translate3d(${-shiftX * 1.5}px, ${
          -shiftY * 1.5
        }px, ${exploded ? 150 : 80}px) translateY(${exploded ? -35 : -10}px)`;
      }
      if (layer2Ref.current) {
        layer2Ref.current.style.transform = `translate3d(${-shiftX * 0.8}px, ${
          -shiftY * 0.8
        }px, 0px) translateY(0px)`;
      }
      if (layer3Ref.current) {
        layer3Ref.current.style.transform = `translate3d(${-shiftX * 0.3}px, ${
          -shiftY * 0.3
        }px, ${exploded ? -150 : -80}px) translateY(${exploded ? 35 : 10}px)`;
      }

      rafId.current = requestAnimationFrame(animate);
    };

    const handleMouseMove = (e: Event) => {
      const mouseEvent = e as MouseEvent;
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const x = mouseEvent.clientX - rect.left - rect.width / 2;
      const y = mouseEvent.clientY - rect.top - rect.height / 2;

      // Restrained, realistic rotation angles (-12 to +14 deg max)
      const targetY = (x / (rect.width / 2)) * 12 - 10;
      const targetX = -(y / (rect.height / 2)) * 10 + 14;

      targetRot.current.x = targetX;
      targetRot.current.y = targetY;
      isHovered.current = true;
    };

    const handleMouseLeave = () => {
      isHovered.current = false;
      targetRot.current.x = 14;
      targetRot.current.y = -10;
    };

    const el = containerRef.current;
    el.addEventListener("mousemove", handleMouseMove);
    el.addEventListener("mouseleave", handleMouseLeave);

    rafId.current = requestAnimationFrame(animate);

    return () => {
      el.removeEventListener("mousemove", handleMouseMove);
      el.removeEventListener("mouseleave", handleMouseLeave);
      if (rafId.current) cancelAnimationFrame(rafId.current);
    };
  }, [exploded]);

  return (
    <div className="relative w-full max-w-5xl mx-auto flex flex-col items-center justify-center py-6">
      {/* Interactive Controls Pill */}
      <div className="flex items-center gap-3 mb-4 z-20">
        <button
          onClick={() => setExploded(!exploded)}
          className={`px-4 py-1.5 rounded-full text-xs font-mono transition-all duration-300 flex items-center gap-2 border select-none ${
            exploded
              ? "bg-cyan-500/15 text-cyan-300 border-cyan-400/30 shadow-[0_0_15px_rgba(0,229,255,0.2)]"
              : "bg-white/[0.04] text-slate-400 border-white/[0.08] hover:text-white hover:bg-white/[0.08]"
          }`}
          aria-label={exploded ? "Collapse 3D spatial layers" : "Expand 3D spatial layers"}
        >
          <Layers className="h-3.5 w-3.5 text-cyan-400" />
          <span>{exploded ? "Collapse Spatial Layers" : "Explode Spatial Layers"}</span>
        </button>
        <span className="text-[11px] font-mono text-slate-500 hidden sm:inline">
          Move cursor to orbit spatial perspective
        </span>
      </div>

      {/* 3D Viewport Stage */}
      <div
        ref={containerRef}
        style={{ perspective: "1800px" }}
        className="relative w-full h-[500px] sm:h-[560px] flex items-center justify-center cursor-default select-none"
      >
        {/* Ambient Subtle Volumetric Halos */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[480px] h-[320px] bg-gradient-to-tr from-cyan-500/10 via-blue-600/10 to-purple-600/5 rounded-full blur-[110px] pointer-events-none" />
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 w-[360px] h-[140px] bg-rose-500/10 rounded-full blur-[90px] pointer-events-none" />

        {/* 3D Transform Container */}
        <div
          ref={cardStackRef}
          style={{
            transform: "rotateX(14deg) rotateY(-10deg)",
            transformStyle: "preserve-3d",
            willChange: "transform",
          }}
          className="relative w-[340px] sm:w-[480px] md:w-[560px] h-[360px] sm:h-[390px]"
        >
          {/* ========================================================
              LAYER 1 (TOP) — TRANSACTIONS LOOK NORMAL
              ======================================================== */}
          <div
            ref={layer1Ref}
            onClick={() => setActiveLayer(1)}
            style={{
              transform: `translateZ(${exploded ? 150 : 80}px) translateY(${
                exploded ? -35 : -10
              }px)`,
              transformStyle: "preserve-3d",
              willChange: "transform",
            }}
            className={`absolute inset-0 rounded-2xl p-5 backdrop-blur-2xl border transition-all duration-300 group cursor-pointer ${
              activeLayer === 1
                ? "bg-[#0A101C]/92 border-cyan-400/80 shadow-[0_20px_50px_rgba(0,0,0,0.6),0_0_30px_rgba(0,229,255,0.25)]"
                : "bg-[#080E18]/85 border-cyan-500/25 hover:border-cyan-400/50 shadow-[0_16px_40px_rgba(0,0,0,0.5)]"
            }`}
          >
            {/* Top Layer Header */}
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
                <span className="text-[10px] font-mono tracking-widest text-cyan-300 uppercase font-semibold">
                  Layer 01 • Transaction Stream (Demo)
                </span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/[0.04] border border-white/[0.08] text-slate-400">
                Incoming Feed
              </span>
            </div>

            {/* Transaction Rows */}
            <div className="mt-3 space-y-2">
              <div className="flex items-center justify-between p-2 rounded-xl bg-white/[0.02] border border-white/[0.04] text-xs font-mono">
                <div className="flex items-center gap-2">
                  <span className="text-slate-300 font-medium">₹1,299.00</span>
                  <span className="text-[10px] text-slate-500">tx_0001987 • Retail Gateway</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                  ALLOW (0.04)
                </span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-xl bg-white/[0.02] border border-white/[0.04] text-xs font-mono">
                <div className="flex items-center gap-2">
                  <span className="text-slate-300 font-medium">₹3,499.00</span>
                  <span className="text-[10px] text-slate-500">tx_0001988 • Quick Commerce</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                  ALLOW (0.09)
                </span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-xl bg-white/[0.02] border border-white/[0.04] text-xs font-mono">
                <div className="flex items-center gap-2">
                  <span className="text-slate-300 font-medium">₹2,499.00</span>
                  <span className="text-[10px] text-slate-500">tx_0001990 • Travel UPI</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                  ALLOW (0.12)
                </span>
              </div>

              {/* Target Flagged Golden Transaction */}
              <div className="flex items-center justify-between p-2 rounded-xl bg-cyan-950/40 border border-cyan-400/40 text-xs font-mono shadow-[0_0_20px_rgba(0,229,255,0.12)]">
                <div className="flex items-center gap-2">
                  <span className="text-cyan-300 font-bold">₹99,999.00</span>
                  <span className="text-[10px] text-cyan-200/80">tx_0001991 • Electronics</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/40 font-semibold">
                  HOLD (0.9994)
                </span>
              </div>
            </div>

            {/* Layer Floating Tag Label */}
            <div className="absolute -right-3 -top-3.5 bg-gradient-to-r from-cyan-500 to-teal-400 text-[#06080E] px-3 py-1 rounded-full text-[10px] font-mono font-bold shadow-[0_4px_12px_rgba(0,229,255,0.4)]">
              TRANSACTIONS Look normal.
            </div>
          </div>

          {/* ========================================================
              LAYER 2 (MIDDLE) — RELATIONSHIPS REVEAL THE TRUTH
              ======================================================== */}
          <div
            ref={layer2Ref}
            onClick={() => setActiveLayer(2)}
            style={{
              transform: "translateZ(0px) translateY(0px)",
              transformStyle: "preserve-3d",
              willChange: "transform",
            }}
            className={`absolute inset-0 rounded-2xl p-5 backdrop-blur-2xl border transition-all duration-300 group cursor-pointer ${
              activeLayer === 2
                ? "bg-[#110B24]/92 border-purple-400/80 shadow-[0_20px_50px_rgba(0,0,0,0.6),0_0_30px_rgba(168,85,247,0.25)]"
                : "bg-[#0C081A]/85 border-purple-500/25 hover:border-purple-400/50 shadow-[0_16px_40px_rgba(0,0,0,0.5)]"
            }`}
          >
            {/* Middle Layer Header */}
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
              <div className="flex items-center gap-2">
                <Share2 className="h-4 w-4 text-purple-400" />
                <span className="text-[10px] font-mono tracking-widest text-purple-300 uppercase font-semibold">
                  Layer 02 • Entity & Topology Discovery
                </span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/[0.04] border border-white/[0.08] text-purple-300">
                Multi-Hop Expansion
              </span>
            </div>

            {/* Simulated Topology Network Visualizer */}
            <div className="mt-3 relative h-40 rounded-xl bg-purple-950/15 border border-purple-500/15 overflow-hidden flex items-center justify-center p-3">
              {/* Connecting SVG graph lines */}
              <svg className="absolute inset-0 w-full h-full stroke-purple-400/30" strokeWidth="1.5">
                <line x1="20%" y1="30%" x2="50%" y2="50%" strokeDasharray="3 3" />
                <line x1="80%" y1="25%" x2="50%" y2="50%" strokeDasharray="3 3" />
                <line x1="30%" y1="75%" x2="50%" y2="50%" />
                <line x1="70%" y1="80%" x2="50%" y2="50%" />
              </svg>

              {/* Central Shared Hub */}
              <div className="relative z-10 flex flex-col items-center">
                <div className="h-11 w-11 rounded-full bg-gradient-to-tr from-purple-600 to-cyan-500 p-0.5 shadow-[0_0_16px_rgba(168,85,247,0.5)]">
                  <div className="h-full w-full rounded-full bg-[#0d091e] flex items-center justify-center">
                    <Fingerprint className="h-5 w-5 text-cyan-300" />
                  </div>
                </div>
                <span className="mt-1 text-[9px] font-mono text-purple-200 font-bold bg-purple-900/60 px-2 py-0.5 rounded border border-purple-400/30">
                  Shared Device: dev_88921a
                </span>
              </div>

              {/* Surrounding Ring Nodes */}
              <div className="absolute top-2.5 left-3 text-[9px] font-mono px-2 py-0.5 rounded bg-black/50 border border-purple-500/20 text-slate-300">
                cust_000412 • IP: 103.21.244.11
              </div>
              <div className="absolute top-2.5 right-3 text-[9px] font-mono px-2 py-0.5 rounded bg-black/50 border border-purple-500/20 text-slate-300">
                cust_000789 • 5 Linked Accounts
              </div>
              <div className="absolute bottom-2.5 left-3 text-[9px] font-mono px-2 py-0.5 rounded bg-black/50 border border-purple-500/20 text-slate-300">
                Card Fingerprint Match
              </div>
              <div className="absolute bottom-2.5 right-3 text-[9px] font-mono px-2 py-0.5 rounded bg-black/50 border border-purple-500/20 text-slate-300">
                Mule Terminal Collusion
              </div>
            </div>

            {/* Layer Floating Tag Label */}
            <div className="absolute -left-3 -top-3.5 bg-gradient-to-r from-purple-600 to-indigo-500 text-white px-3 py-1 rounded-full text-[10px] font-mono font-bold shadow-[0_4px_12px_rgba(168,85,247,0.4)]">
              RELATIONSHIPS Reveal the truth.
            </div>
          </div>

          {/* ========================================================
              LAYER 3 (BOTTOM) — INTELLIGENCE STOPS FRAUD
              ======================================================== */}
          <div
            ref={layer3Ref}
            onClick={() => setActiveLayer(3)}
            style={{
              transform: `translateZ(${exploded ? -150 : -80}px) translateY(${
                exploded ? 35 : 10
              }px)`,
              transformStyle: "preserve-3d",
              willChange: "transform",
            }}
            className={`absolute inset-0 rounded-2xl p-5 backdrop-blur-2xl border transition-all duration-300 group cursor-pointer ${
              activeLayer === 3
                ? "bg-[#1E080C]/92 border-rose-400/80 shadow-[0_20px_50px_rgba(0,0,0,0.6),0_0_30px_rgba(244,63,94,0.25)]"
                : "bg-[#140508]/85 border-rose-500/25 hover:border-rose-400/50 shadow-[0_16px_40px_rgba(0,0,0,0.5)]"
            }`}
          >
            {/* Bottom Layer Header */}
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-rose-400" />
                <span className="text-[10px] font-mono tracking-widest text-rose-300 uppercase font-semibold">
                  Layer 03 • Authoritative Policy & AI Advisory
                </span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950/60 border border-rose-500/30 text-rose-300 font-semibold">
                HOLD ENFORCED
              </span>
            </div>

            {/* Syndicate Details Box */}
            <div className="mt-3 p-3 rounded-xl bg-rose-950/20 border border-rose-500/20 space-y-2 text-xs font-mono">
              <div className="flex items-center justify-between">
                <span className="text-rose-200 font-semibold flex items-center gap-1.5">
                  <Flame className="h-3.5 w-3.5 text-rose-400" />
                  DEVICE_REUSE_RING Detected
                </span>
                <span className="text-[10px] text-rose-400 font-bold">Score: 0.9994</span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                <div className="p-2 rounded-lg bg-black/40 border border-rose-900/30">
                  <div className="text-[9px] text-slate-400 uppercase">Authoritative Policy</div>
                  <div className="text-rose-400 font-bold mt-0.5">HOLD (Deterministic)</div>
                </div>
                <div className="p-2 rounded-lg bg-black/40 border border-rose-900/30">
                  <div className="text-[9px] text-slate-400 uppercase">AI Recommendation</div>
                  <div className="text-amber-300 font-bold mt-0.5">MANUAL_REVIEW_ESCALATION</div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-1 text-[10px] text-slate-400">
                <span>Hash-Chained Audit Trail</span>
                <Link
                  href="/investigate?tx=tx_0001991"
                  className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1"
                >
                  <span>Launch Investigation</span>
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </div>
            </div>

            {/* Layer Floating Tag Label */}
            <div className="absolute -right-3 -bottom-3.5 bg-gradient-to-r from-rose-600 to-red-500 text-white px-3 py-1 rounded-full text-[10px] font-mono font-bold shadow-[0_4px_12px_rgba(244,63,94,0.4)]">
              INTELLIGENCE Stops fraud.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
