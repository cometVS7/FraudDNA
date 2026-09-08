"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Share2,
  Lock,
  ArrowRight,
  Fingerprint,
  Sliders,
  Sparkles,
} from "lucide-react";
import { MagneticButton } from "../design-system/magnetic-button";

// ====================================================================
// SECTION 02: HIDDEN NETWORKS
// ====================================================================
export function SectionHiddenNetworks() {
  const [activeNode, setActiveNode] = useState<string>("dev_88921a");

  return (
    <section className="relative w-full max-w-6xl mx-auto px-4 sm:px-6 py-20 border-t border-white/[0.06]">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        {/* Left Copy */}
        <div className="lg:col-span-5 space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-400/20 text-xs font-mono text-purple-300 uppercase tracking-widest">
            <span>02</span>
            <span className="text-slate-600">•</span>
            <span>Syndicate Topology</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-serif text-white font-normal tracking-tight">
            Fraud rarely travels alone.
          </h2>
          <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
            Organized fraud syndicates distribute transactions across mock accounts,
            rotated IP subnets, and shared physical hardware. FraudDNA&apos;s bounded graph
            engine traverses entity relationships to identify collusive clusters before settlement.
          </p>
          <div className="space-y-3 pt-2">
            <div className="flex items-start gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.05]">
              <Fingerprint className="h-5 w-5 text-purple-400 mt-0.5 flex-shrink-0" />
              <div className="text-xs">
                <span className="font-semibold text-white font-mono">Hardware Fingerprint Clustering</span>
                <p className="text-slate-400 mt-0.5">Multiple mock identities bound to a single physical device identifier.</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.05]">
              <Share2 className="h-5 w-5 text-cyan-400 mt-0.5 flex-shrink-0" />
              <div className="text-xs">
                <span className="font-semibold text-white font-mono">Coordinated Syndicate Patterns</span>
                <p className="text-slate-400 mt-0.5">Automated detection of DEVICE_REUSE_RING and velocity anomalies.</p>
              </div>
            </div>
          </div>
          <div className="pt-2">
            <MagneticButton
              href="/frauddna"
              variant="secondary"
              icon={<ArrowRight className="h-4 w-4" />}
            >
              Explore Network Graph
            </MagneticButton>
          </div>
        </div>

        {/* Right Interactive Graph Sandbox */}
        <div className="lg:col-span-7">
          <div className="relative rounded-3xl p-6 bg-[#080C16]/85 backdrop-blur-2xl border border-purple-500/20 shadow-[0_16px_48px_rgba(0,0,0,0.5)]">
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-4 mb-4">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-purple-400 animate-pulse" />
                <span className="text-xs font-mono uppercase tracking-wider text-purple-200 font-semibold">
                  Illustrative Topology Sandbox
                </span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-500/30">
                Depth ≤ 3 Hops
              </span>
            </div>

            {/* Interactive Graph Canvas */}
            <div className="relative h-72 sm:h-80 rounded-2xl bg-black/40 border border-white/[0.05] overflow-hidden flex items-center justify-center p-4">
              {/* SVG Connecting Links */}
              <svg className="absolute inset-0 w-full h-full stroke-purple-500/25" strokeWidth="1.5">
                <line x1="50%" y1="50%" x2="25%" y2="25%" />
                <line x1="50%" y1="50%" x2="75%" y2="25%" />
                <line x1="50%" y1="50%" x2="20%" y2="75%" />
                <line x1="50%" y1="50%" x2="80%" y2="75%" />
                <line x1="50%" y1="50%" x2="50%" y2="15%" strokeDasharray="4 4" />
              </svg>

              {/* Central Node */}
              <button
                onClick={() => setActiveNode("dev_88921a")}
                className={`relative z-10 p-3.5 rounded-full border transition-all duration-300 flex flex-col items-center cursor-pointer ${
                  activeNode === "dev_88921a"
                    ? "bg-purple-600/30 border-purple-400 shadow-[0_0_25px_rgba(168,85,247,0.5)] scale-105"
                    : "bg-purple-950/40 border-purple-500/30 hover:border-purple-400/60"
                }`}
                aria-label="Inspect shared device node dev_88921a"
              >
                <Fingerprint className="h-7 w-7 text-cyan-300" />
                <span className="text-[10px] font-mono text-purple-200 mt-1 font-bold">dev_88921a</span>
              </button>

              {/* Satellite Node 1 */}
              <button
                onClick={() => setActiveNode("tx_0001991")}
                className={`absolute top-6 left-6 p-2.5 rounded-xl border text-xs font-mono transition-all duration-200 cursor-pointer ${
                  activeNode === "tx_0001991"
                    ? "bg-rose-950/80 border-rose-400 text-rose-200 shadow-[0_0_16px_rgba(244,63,94,0.4)]"
                    : "bg-[#0E1322] border-white/[0.08] text-slate-300 hover:border-rose-400/40"
                }`}
              >
                <div className="font-bold text-rose-400">tx_0001991</div>
                <div className="text-[10px] text-slate-400">₹99,999.00</div>
              </button>

              {/* Satellite Node 2 */}
              <button
                onClick={() => setActiveNode("cust_000412")}
                className={`absolute top-6 right-6 p-2.5 rounded-xl border text-xs font-mono transition-all duration-200 cursor-pointer ${
                  activeNode === "cust_000412"
                    ? "bg-cyan-950/80 border-cyan-400 text-cyan-200 shadow-[0_0_16px_rgba(0,229,255,0.4)]"
                    : "bg-[#0E1322] border-white/[0.08] text-slate-300 hover:border-cyan-400/40"
                }`}
              >
                <div className="font-bold text-cyan-300">cust_000412</div>
                <div className="text-[10px] text-slate-400">Identity #1</div>
              </button>

              {/* Satellite Node 3 */}
              <button
                onClick={() => setActiveNode("ip_subnet")}
                className={`absolute bottom-6 left-6 p-2.5 rounded-xl border text-xs font-mono transition-all duration-200 cursor-pointer ${
                  activeNode === "ip_subnet"
                    ? "bg-purple-950/80 border-purple-400 text-purple-200 shadow-[0_0_16px_rgba(168,85,247,0.4)]"
                    : "bg-[#0E1322] border-white/[0.08] text-slate-300 hover:border-purple-400/40"
                }`}
              >
                <div className="font-bold text-purple-300">103.21.244.0/24</div>
                <div className="text-[10px] text-slate-400">Shared Subnet</div>
              </button>

              {/* Satellite Node 4 */}
              <button
                onClick={() => setActiveNode("merchant_terminal")}
                className={`absolute bottom-6 right-6 p-2.5 rounded-xl border text-xs font-mono transition-all duration-200 cursor-pointer ${
                  activeNode === "merchant_terminal"
                    ? "bg-amber-950/80 border-amber-400 text-amber-200 shadow-[0_0_16px_rgba(245,158,11,0.4)]"
                    : "bg-[#0E1322] border-white/[0.08] text-slate-300 hover:border-amber-400/40"
                }`}
              >
                <div className="font-bold text-amber-300">Mule Terminal</div>
                <div className="text-[10px] text-slate-400">Merchant Entity</div>
              </button>
            </div>

            {/* Selected Node Inspector Footer */}
            <div className="mt-4 p-3 rounded-xl bg-white/[0.02] border border-white/[0.05] flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">Selected Graph Entity:</span>
              <span className="text-cyan-300 font-bold">{activeNode}</span>
              <span className="text-slate-500">Bounded Surface (Max 250 Nodes)</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ====================================================================
// SECTION 03: EXPLAINABLE RISK & SHAP
// ====================================================================
export function SectionExplainableRisk() {
  const [selectedFeature, setSelectedFeature] = useState<number | null>(0);

  const features = [
    {
      name: "network_risk_score",
      impact: "+0.420",
      description: "Elevated density of linked high-risk entities within 2-hop graph neighborhood.",
      color: "bg-rose-500",
      width: "84%",
    },
    {
      name: "velocity_1h_count",
      impact: "+0.280",
      description: "Transaction frequency exceeds historical customer baseline by 6.8x within 1 hour.",
      color: "bg-rose-500/80",
      width: "56%",
    },
    {
      name: "amount_to_avg_ratio",
      impact: "+0.145",
      description: "Transaction value of ₹99,999.00 vs historical profile average of ₹2,400.00.",
      color: "bg-amber-500",
      width: "30%",
    },
    {
      name: "device_trust_score",
      impact: "-0.085",
      description: "Hardware signature identified across previous authenticated sessions.",
      color: "bg-emerald-500",
      width: "18%",
    },
  ];

  return (
    <section className="relative w-full max-w-6xl mx-auto px-4 sm:px-6 py-20 border-t border-white/[0.06]">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        {/* Left Interactive Waterfall Visualizer */}
        <div className="lg:col-span-7 order-2 lg:order-1">
          <div className="rounded-3xl p-6 bg-[#080D18]/85 backdrop-blur-2xl border border-cyan-500/20 shadow-[0_16px_48px_rgba(0,0,0,0.5)] space-y-4">
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-4">
              <div className="flex items-center gap-2">
                <Sliders className="h-4 w-4 text-cyan-400" />
                <span className="text-xs font-mono uppercase tracking-wider text-cyan-200 font-semibold">
                  SHAP Feature Attribution • tx_0001991
                </span>
              </div>
              <span className="text-xs font-mono text-rose-400 font-bold bg-rose-950/60 px-2 py-0.5 rounded border border-rose-500/30">
                Score: 0.9994 (CRITICAL)
              </span>
            </div>

            <div className="space-y-2.5">
              {features.map((feat, idx) => (
                <div
                  key={idx}
                  onClick={() => setSelectedFeature(idx)}
                  className={`p-3 rounded-xl border transition-all duration-200 cursor-pointer ${
                    selectedFeature === idx
                      ? "bg-white/[0.05] border-cyan-400/50 shadow-[0_0_16px_rgba(0,229,255,0.12)]"
                      : "bg-white/[0.02] border-white/[0.04] hover:border-white/[0.1]"
                  }`}
                >
                  <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                    <span className="text-slate-200 font-medium">{feat.name}</span>
                    <span
                      className={`font-semibold ${
                        feat.impact.startsWith("+") ? "text-rose-400" : "text-emerald-400"
                      }`}
                    >
                      {feat.impact} SHAP
                    </span>
                  </div>
                  {/* Visual Bar */}
                  <div className="w-full h-1.5 bg-black/40 rounded-full overflow-hidden">
                    <div
                      style={{ width: feat.width }}
                      className={`h-full rounded-full ${feat.color}`}
                    />
                  </div>
                  {selectedFeature === idx && (
                    <p className="mt-2 text-[11px] text-slate-400 font-sans leading-relaxed">
                      {feat.description}
                    </p>
                  )}
                </div>
              ))}
            </div>

            <div className="p-3 rounded-xl bg-black/40 border border-white/[0.05] flex items-center justify-between text-[11px] font-mono text-slate-400">
              <span>Baseline E[f(x)]: 0.120</span>
              <span>Attribution Sum: +0.8794</span>
              <span className="text-rose-400 font-bold">f(x) = 0.9994</span>
            </div>
          </div>
        </div>

        {/* Right Copy */}
        <div className="lg:col-span-5 space-y-6 order-1 lg:order-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-400/20 text-xs font-mono text-cyan-300 uppercase tracking-widest">
            <span>03</span>
            <span className="text-slate-600">•</span>
            <span>Explainable AI</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-serif text-white font-normal tracking-tight">
            Don&apos;t just flag risk. Explain it.
          </h2>
          <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
            Black-box scores fail audits and frustrate investigation teams. FraudDNA pairs raw ML
            probabilities with exact SHAP feature attributions, explaining the exact mathematical
            factors behind every score elevation.
          </p>
          <div className="pt-2">
            <MagneticButton
              href="/investigate?tx=tx_0001991"
              variant="primary"
              icon={<ArrowRight className="h-4 w-4" />}
            >
              Inspect tx_0001991 SHAP
            </MagneticButton>
          </div>
        </div>
      </div>
    </section>
  );
}

// ====================================================================
// SECTION 04: DUAL DECISION MATRIX (POLICY VS AI ADVISORY)
// ====================================================================
export function SectionDecisionMatrix() {
  return (
    <section className="relative w-full max-w-6xl mx-auto px-4 sm:px-6 py-20 border-t border-white/[0.06]">
      <div className="text-center max-w-3xl mx-auto space-y-3 mb-16">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-400/20 text-xs font-mono text-emerald-300 uppercase tracking-widest">
          <span>04</span>
          <span className="text-slate-600">•</span>
          <span>Architectural Invariant</span>
        </div>
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-serif text-white font-normal tracking-tight">
          The Machine Investigates. The Policy Decides.
        </h2>
        <p className="text-slate-400 text-sm sm:text-base leading-relaxed max-w-2xl mx-auto">
          FraudDNA strictly separates analytical intelligence from financial authority.
          AI agents synthesize evidence and recommend actions, but deterministic policy engines
          govern final financial execution.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
        {/* Left: Authoritative Policy */}
        <div className="p-6 rounded-3xl bg-[#14080B]/80 backdrop-blur-xl border border-rose-500/25 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-rose-500/15 pb-3">
            <div className="flex items-center gap-2">
              <Lock className="h-4 w-4 text-rose-400" />
              <span className="text-xs font-mono uppercase tracking-wider text-rose-300 font-semibold">
                Authoritative Policy Engine
              </span>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-500/30 font-bold">
              FINANCIAL GATE
            </span>
          </div>
          <div className="text-2xl font-serif text-white font-bold">
            Deterministic Authority
          </div>
          <p className="text-xs text-slate-300 font-sans leading-relaxed">
            Directly governs transaction execution with zero ambiguity:
            <span className="font-mono text-rose-400 font-bold"> ALLOW</span>,
            <span className="font-mono text-amber-400 font-bold"> REVIEW</span>, or
            <span className="font-mono text-rose-400 font-bold"> HOLD</span>.
          </p>
          <div className="p-3 rounded-xl bg-black/50 border border-rose-900/30 text-xs font-mono text-rose-200">
            Rule #R-901: Risk &ge; 0.90 &rarr; Immediate HOLD (Deterministic Policy Execution)
          </div>
        </div>

        {/* Right: AI Advisory Investigator */}
        <div className="p-6 rounded-3xl bg-[#090E1C]/80 backdrop-blur-xl border border-cyan-500/25 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-cyan-500/15 pb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-cyan-400" />
              <span className="text-xs font-mono uppercase tracking-wider text-cyan-300 font-semibold">
                AI Advisory Investigator
              </span>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/30 font-bold">
              ZERO FINANCIAL POWER
            </span>
          </div>
          <div className="text-2xl font-serif text-white font-bold">
            Forensic Intelligence
          </div>
          <p className="text-xs text-slate-300 font-sans leading-relaxed">
            Multi-tool read-only agent that traverses topology, evaluates SHAP factors, and cites regulations:
            <span className="font-mono text-amber-300 font-bold"> MANUAL_REVIEW_ESCALATION</span> or
            <span className="font-mono text-emerald-300 font-bold"> CLOSE_BENIGN</span>.
          </p>
          <div className="p-3 rounded-xl bg-black/50 border border-cyan-900/30 text-xs font-mono text-cyan-200">
            Advisory Output: Recommends manual analyst escalation based on multi-infrastructure collusion.
          </div>
        </div>
      </div>
    </section>
  );
}

// ====================================================================
// SECTION 05: GROUNDED EVIDENCE & RAG
// ====================================================================
export function SectionGroundedEvidence() {
  return (
    <section className="relative w-full max-w-6xl mx-auto px-4 sm:px-6 py-20 border-t border-white/[0.06]">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        {/* Left Copy */}
        <div className="lg:col-span-5 space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-400/20 text-xs font-mono text-amber-300 uppercase tracking-widest">
            <span>05</span>
            <span className="text-slate-600">•</span>
            <span>Grounded Compliance</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-serif text-white font-normal tracking-tight">
            Every conclusion has a source.
          </h2>
          <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
            AI hallucinations are unacceptable in regulatory compliance. FraudDNA indexes
            official RBI digital payment guidelines, account takeover frameworks, and AML
            typologies in a high-density vector store.
          </p>
          <div className="pt-2">
            <MagneticButton
              href="/investigate?tx=tx_0001991"
              variant="secondary"
              icon={<ArrowRight className="h-4 w-4" />}
            >
              View RAG Citations
            </MagneticButton>
          </div>
        </div>

        {/* Right Citation Cards */}
        <div className="lg:col-span-7 space-y-3">
          <div className="p-4 rounded-2xl bg-[#090E1A]/80 backdrop-blur-xl border border-white/[0.08] hover:border-cyan-500/20 transition-all space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-semibold text-amber-400">
                RBI Digital Lending Guidelines (RBI/2022-23/111) §4.2
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/[0.04] text-slate-400">
                Similarity: 0.94
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed font-sans">
              &ldquo;Any transaction showing automated velocity spikes or hardware identifier re-use across unrelated customer profiles requires mandatory enhanced due diligence (EDD).&rdquo;
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-[#090E1A]/80 backdrop-blur-xl border border-white/[0.08] hover:border-cyan-500/20 transition-all space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-semibold text-cyan-400">
                Syndicate Typology Matrix: Ring Collusion Typology
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/[0.04] text-slate-400">
                Similarity: 0.91
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed font-sans">
              &ldquo;Detection of multiple payment attempts from the same hardware UUID within a 15-minute window indicates coordinated bot-driven or mule-account drain attempts.&rdquo;
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

// ====================================================================
// SECTION 06 & 07: WORKFLOW & AUDIT SEAL
// ====================================================================
export function SectionWorkflowAndAudit() {
  return (
    <section className="relative w-full max-w-6xl mx-auto px-4 sm:px-6 py-20 border-t border-white/[0.06]">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Section 06: Case Workflow */}
        <div className="p-6 rounded-3xl bg-[#080C16]/85 backdrop-blur-xl border border-white/[0.08] space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-400/20 text-xs font-mono text-blue-300 uppercase tracking-widest">
            <span>06</span>
            <span className="text-slate-600">•</span>
            <span>Case Lifecycle</span>
          </div>
          <h3 className="text-2xl font-serif text-white">From Signal to Action</h3>
          <p className="text-xs sm:text-sm text-slate-400 leading-relaxed font-sans">
            Cases transition through strict state machines from automated triage to analyst review,
            evidence attachment, and final regulatory resolution.
          </p>
          <div className="flex items-center justify-between pt-2 text-xs font-mono text-slate-300">
            <span className="px-2.5 py-1 rounded-lg bg-white/[0.04] border border-white/[0.08]">NEW</span>
            <span>&rarr;</span>
            <span className="px-2.5 py-1 rounded-lg bg-amber-500/15 border border-amber-400/30 text-amber-300 font-semibold">
              INVESTIGATING
            </span>
            <span>&rarr;</span>
            <span className="px-2.5 py-1 rounded-lg bg-rose-500/15 border border-rose-400/30 text-rose-300 font-semibold">
              ESCALATED
            </span>
            <span>&rarr;</span>
            <span className="px-2.5 py-1 rounded-lg bg-emerald-500/15 border border-emerald-400/30 text-emerald-300 font-semibold">
              RESOLVED
            </span>
          </div>
          <div className="pt-2">
            <Link
              href="/cases"
              className="text-xs font-mono text-cyan-300 hover:text-cyan-200 flex items-center gap-1 font-semibold"
            >
              <span>Go to Case Queue</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>

        {/* Section 07: Trust & Audit */}
        <div className="p-6 rounded-3xl bg-[#080C16]/85 backdrop-blur-xl border border-white/[0.08] space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-400/20 text-xs font-mono text-emerald-300 uppercase tracking-widest">
            <span>07</span>
            <span className="text-slate-600">•</span>
            <span>Cryptographic Trust</span>
          </div>
          <h3 className="text-2xl font-serif text-white">SHA-256 Audit Chain</h3>
          <p className="text-xs sm:text-sm text-slate-400 leading-relaxed font-sans">
            Every agent action, policy evaluation, and analyst verdict is sealed in a tamper-evident
            SHA-256 hash chain, providing verifiable provenance for regulatory audits.
          </p>
          <div className="p-3 rounded-xl bg-black/60 border border-emerald-500/20 text-xs font-mono space-y-1 text-slate-300">
            <div className="text-[10px] text-slate-500">HASH-CHAINED PROVENANCE LEDGER:</div>
            <div className="text-emerald-400 font-bold truncate">
              sha256: 7f89c2a1b948df6e038ac5e781190bc2...
            </div>
          </div>
          <div className="pt-2">
            <Link
              href="/audit"
              className="text-xs font-mono text-emerald-400 hover:text-emerald-300 flex items-center gap-1 font-semibold"
            >
              <span>Inspect Audit Ledger</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
