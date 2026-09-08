"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  FileText,
  Share2,
  Cpu,
  ShieldCheck,
  ArrowRight,
} from "lucide-react";

interface CardData {
  id: number;
  title: string;
  category: string;
  icon: React.ReactNode;
  rotation: number;
  translateX: number;
  translateY: number;
  badge: string;
  badgeColor: string;
  content: React.ReactNode;
}

export function FannedCardStack() {
  const [hoveredCard, setHoveredCard] = useState<number | null>(null);
  const [selectedCard, setSelectedCard] = useState<number>(0);

  const cards: CardData[] = [
    {
      id: 0,
      title: "Transaction Fact",
      category: "Layer 01 • Atomic Fact",
      icon: <FileText className="h-4 w-4 text-cyan-400" />,
      rotation: -10,
      translateX: -90,
      translateY: 15,
      badge: "₹99,999.00",
      badgeColor: "bg-cyan-500/15 text-cyan-300 border-cyan-400/25",
      content: (
        <div className="space-y-2.5 text-xs font-mono">
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
            <span className="text-slate-400">Transaction ID</span>
            <span className="text-white font-semibold">tx_0001991</span>
          </div>
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
            <span className="text-slate-400">Customer ID</span>
            <span className="text-cyan-300">cust_000412</span>
          </div>
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
            <span className="text-slate-400">Merchant</span>
            <span className="text-white">Electronics Retail</span>
          </div>
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
            <span className="text-slate-400">ML Base Score</span>
            <span className="text-rose-400 font-bold">0.9994 (CRITICAL)</span>
          </div>
          <div className="p-2 rounded-xl bg-cyan-950/30 border border-cyan-500/20 text-[11px] text-slate-300 font-sans leading-relaxed">
            In isolation, the payment appears as a normal high-value checkout. Topological depth reveals hidden infrastructure collusion.
          </div>
        </div>
      ),
    },
    {
      id: 1,
      title: "Syndicate Topology",
      category: "Layer 02 • Graph Discovery",
      icon: <Share2 className="h-4 w-4 text-purple-400" />,
      rotation: -3,
      translateX: -30,
      translateY: 0,
      badge: "Ring Detected",
      badgeColor: "bg-purple-500/15 text-purple-300 border-purple-400/25",
      content: (
        <div className="space-y-2.5 text-xs font-mono">
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
            <span className="text-slate-400">Shared Hardware</span>
            <span className="text-purple-300 font-semibold">dev_88921a</span>
          </div>
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
            <span className="text-slate-400">Collusion Type</span>
            <span className="text-white">DEVICE_REUSE_RING</span>
          </div>
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
            <span className="text-slate-400">Multi-Account Link</span>
            <span className="text-white">5 Synthetic Identities</span>
          </div>
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
            <span className="text-slate-400">Graph Depth</span>
            <span className="text-purple-300 font-bold">≤ 3 Hops</span>
          </div>
          <div className="p-2 rounded-xl bg-purple-950/30 border border-purple-500/20 text-[11px] text-slate-300 font-sans leading-relaxed">
            Sub-millisecond entity expansion unrolls shared devices, rotating IP subnets, and mock account nodes.
          </div>
        </div>
      ),
    },
    {
      id: 2,
      title: "Forensic Dossier",
      category: "Layer 03 • Explainable AI",
      icon: <Cpu className="h-4 w-4 text-amber-400" />,
      rotation: 3,
      translateX: 30,
      translateY: 0,
      badge: "SHAP + RAG",
      badgeColor: "bg-amber-500/15 text-amber-300 border-amber-400/25",
      content: (
        <div className="space-y-2.5 text-xs font-mono">
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
            <span className="text-slate-400">Top SHAP Driver</span>
            <span className="text-amber-300 font-semibold">network_risk (+0.42)</span>
          </div>
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
            <span className="text-slate-400">Velocity Factor</span>
            <span className="text-white">velocity_1h (+0.28)</span>
          </div>
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
            <span className="text-slate-400">Regulatory Source</span>
            <span className="text-white">RBI §4.2 Digital Lending</span>
          </div>
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
            <span className="text-slate-400">AI Advisory</span>
            <span className="text-amber-300 font-bold">MANUAL_REVIEW</span>
          </div>
          <div className="p-2 rounded-xl bg-amber-950/30 border border-amber-500/20 text-[11px] text-slate-300 font-sans leading-relaxed">
            Autonomous agent synthesizes multi-hop evidence and regulatory citations with strictly zero financial authority.
          </div>
        </div>
      ),
    },
    {
      id: 3,
      title: "Policy Authority",
      category: "Layer 04 • Enforced Security",
      icon: <ShieldCheck className="h-4 w-4 text-emerald-400" />,
      rotation: 10,
      translateX: 90,
      translateY: 15,
      badge: "HOLD Enforced",
      badgeColor: "bg-rose-500/15 text-rose-300 border-rose-400/25",
      content: (
        <div className="space-y-2.5 text-xs font-mono">
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
            <span className="text-slate-400">Authoritative Action</span>
            <span className="text-rose-400 font-bold">HOLD (Deterministic)</span>
          </div>
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
            <span className="text-slate-400">Deterministic Rule</span>
            <span className="text-white">Rule #R-901 Critical Risk</span>
          </div>
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
            <span className="text-slate-400">Audit Provenance</span>
            <span className="text-cyan-300">SHA-256 Audit Chain</span>
          </div>
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
            <span className="text-slate-400">Case Routing</span>
            <span className="text-emerald-400 font-semibold">Triage Queue Active</span>
          </div>
          <div className="p-2 rounded-xl bg-emerald-950/30 border border-emerald-500/20 text-[11px] text-slate-300 font-sans leading-relaxed">
            Cryptographically chained event ledger guarantees full traceability for compliance audits.
          </div>
        </div>
      ),
    },
  ];

  return (
    <div className="relative w-full max-w-6xl mx-auto px-4 sm:px-6 py-20">
      {/* Section 01 Header */}
      <div className="text-center max-w-3xl mx-auto space-y-3 mb-16">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.03] border border-white/[0.08] text-xs font-mono text-cyan-300 uppercase tracking-widest">
          <span>01</span>
          <span className="text-slate-600">•</span>
          <span>From Transaction to Truth</span>
        </div>
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-serif font-normal text-white tracking-tight">
          More Than a Transaction View
        </h2>
        <p className="text-sm sm:text-base text-slate-400 font-sans leading-relaxed max-w-2xl mx-auto">
          Traditional filters judge isolated payments. FraudDNA fans out the entire
          investigation surface—from atomic transactions to graph topologies, SHAP
          feature attribution, and deterministic policy enforcement.
        </p>
      </div>

      {/* 3D Fanned Cards Deck */}
      <div className="relative h-[480px] sm:h-[520px] flex items-center justify-center my-4">
        {/* Ambient Subtle Glow */}
        <div className="absolute w-[540px] h-[260px] bg-gradient-to-r from-cyan-500/10 via-purple-500/10 to-blue-500/10 rounded-full blur-[110px] pointer-events-none" />

        {/* 4 Fanned Cards */}
        <div className="relative w-full max-w-4xl h-full flex items-center justify-center">
          {cards.map((card, idx) => {
            const isHovered = hoveredCard === card.id;
            const isSelected = selectedCard === card.id;
            const zIndex = isHovered || isSelected ? 30 : 10 + idx;

            return (
              <div
                key={card.id}
                onMouseEnter={() => setHoveredCard(card.id)}
                onMouseLeave={() => setHoveredCard(null)}
                onClick={() => setSelectedCard(card.id)}
                style={{
                  transform: isHovered
                    ? `translateX(${card.translateX * 0.35}px) translateY(${
                        card.translateY - 25
                      }px) rotate(0deg) scale(1.03)`
                    : `translateX(${card.translateX}px) translateY(${card.translateY}px) rotate(${card.rotation}deg) scale(1)`,
                  zIndex,
                  transition: "all 0.35s cubic-bezier(0.2, 0.8, 0.2, 1)",
                }}
                className={`absolute w-[290px] sm:w-[330px] rounded-2xl p-5 backdrop-blur-2xl border cursor-pointer select-none ${
                  isHovered || isSelected
                    ? "bg-[#090E18]/96 border-cyan-400/70 shadow-[0_20px_50px_rgba(0,0,0,0.65),0_0_25px_rgba(0,229,255,0.15)] ring-1 ring-cyan-400/30"
                    : "bg-[#070B12]/85 border-white/[0.08] hover:border-white/[0.15] shadow-[0_12px_32px_rgba(0,0,0,0.55)]"
                }`}
              >
                {/* Card Top Pill Header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2.5">
                    <div className="p-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08]">
                      {card.icon}
                    </div>
                    <div>
                      <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                        {card.category}
                      </div>
                      <div className="text-sm font-semibold text-white font-serif">
                        {card.title}
                      </div>
                    </div>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-mono border ${card.badgeColor}`}
                  >
                    {card.badge}
                  </span>
                </div>

                {/* Card Interior Data */}
                {card.content}

                {/* Bottom Action */}
                <div className="mt-4 pt-3 border-t border-white/[0.06] flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-500">Click to focus layer</span>
                  <Link
                    href="/investigate?tx=tx_0001991"
                    className="text-cyan-300 hover:text-cyan-200 flex items-center gap-1 font-semibold group"
                  >
                    <span>Investigate</span>
                    <ArrowRight className="h-3 w-3 group-hover:translate-x-0.5 transition-transform" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
