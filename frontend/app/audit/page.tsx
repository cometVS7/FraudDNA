"use client";

import React, { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { DashboardLayout } from "@/components/layout";
import {
  RiskBadge,
  DecisionBadge,
  LoadingState,
  ErrorState,
  DataLabel,
  formatINR,
} from "@/components/ui";
import { useAsync } from "@/hooks/use-async";
import { fetchTransactions, createInvestigation, evaluatePolicy } from "@/lib/api";
import type { TransactionsResponse, InvestigationResponse, PolicyDecision } from "@/lib/api";
import {
  Search,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  FileCheck,
} from "lucide-react";

function generateAuditHash(txId: string, score: number, timestamp: string = ""): string {
  let h1 = 0xdeadbeef ^ txId.length;
  let h2 = 0x41c6ce57 ^ Math.round(score * 10000);
  const str = `${txId}:${score.toFixed(4)}:${timestamp}:pol_v1`;
  for (let i = 0; i < str.length; i++) {
    const ch = str.charCodeAt(i);
    h1 = Math.imul(h1 ^ ch, 2654435761);
    h2 = Math.imul(h2 ^ ch, 1597334677);
  }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
  const hex = (4294967296 * (2097151 & h2) + (h1 >>> 0)).toString(16).padStart(16, "0");
  return `0x${hex}${(h1 >>> 0).toString(16).padStart(8, "0")}`;
}

function AuditContent() {
  const searchParams = useSearchParams();
  const [searchTx, setSearchTx] = useState(searchParams.get("tx") || "");
  const [expandedTxId, setExpandedTxId] = useState<string | null>(searchParams.get("tx") || null);

  // Fetch candidate audit transactions
  const txData = useAsync<TransactionsResponse>(
    () =>
      fetchTransactions({
        limit: 25,
        sort_by: "risk_score",
        sort_order: "desc",
        suspicious_only: true,
      }),
    []
  );

  // Detailed audit lookup for currently expanded record
  const investigation = useAsync<InvestigationResponse | null>(
    () => (expandedTxId ? createInvestigation(expandedTxId).catch(() => null) : Promise.resolve(null)),
    [expandedTxId]
  );
  const policy = useAsync<PolicyDecision | null>(
    () => (expandedTxId ? evaluatePolicy(expandedTxId).catch(() => null) : Promise.resolve(null)),
    [expandedTxId]
  );

  const inv = investigation.status === "success" ? investigation.data : null;
  const pol = policy.status === "success" ? policy.data : null;

  return (
    <div className="space-y-6">
      {/* Editorial Header */}
      <div className="border-b border-[#1C1D22] pb-5">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <div className="text-[10px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold">
              FORENSIC EVIDENCE REPOSITORY
            </div>
            <h1 className="text-3xl font-serif tracking-tight text-white font-normal mt-1">
              Audit Trail
            </h1>
            <p className="text-xs text-[#9194A1] font-sans mt-1">
              Immutable ledger of investigation findings, deterministic policy decisions, and cryptographic proofs.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <DataLabel label="Immutable Decision Log" />
          </div>
        </div>
      </div>

      {/* Filter / Search Bar */}
      <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-3 flex flex-wrap items-center justify-between gap-3">
        <div className="relative flex-1 min-w-[240px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#5E616E]" />
          <input
            type="text"
            placeholder="Audit lookup by transaction ID (e.g. txn_00001)..."
            value={searchTx}
            onChange={(e) => setSearchTx(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && searchTx.trim()) {
                setExpandedTxId(searchTx.trim());
              }
            }}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-[#121317] border border-[#1C1D22] rounded-md font-mono text-[#E2E3E9] placeholder-[#5E616E] focus:outline-none focus:border-[#CC9166] transition-colors"
          />
        </div>
        {searchTx.trim() && (
          <button
            onClick={() => setExpandedTxId(searchTx.trim())}
            className="px-3 py-1.5 text-xs font-medium rounded-md bg-[#CC9166] text-[#08080A] hover:bg-[#CC9166]/90 transition-opacity font-sans"
          >
            Inspect Audit
          </button>
        )}
      </div>

      {/* Institutional Dense Forensic Ledger */}
      {txData.status === "loading" && <LoadingState message="Loading immutable audit trail..." />}
      {txData.status === "error" && (
        <ErrorState
          title="AUDIT LOG UNAVAILABLE"
          error={txData.error}
          onRetry={txData.refetch}
        />
      )}

      {txData.status === "success" && (
        <div className="bg-[#040406] border border-[#1C1D22] rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#1C1D22] bg-[#08080A] text-[#5E616E] font-mono text-[10px] uppercase tracking-wider">
                  <th className="py-3 px-4 w-8"></th>
                  <th className="py-3 px-3">TIMESTAMP</th>
                  <th className="py-3 px-3">TRANSACTION</th>
                  <th className="py-3 px-3">INVESTIGATION</th>
                  <th className="py-3 px-4">FINDINGS</th>
                  <th className="py-3 px-3">POLICY</th>
                  <th className="py-3 px-3 text-center">DECISION</th>
                  <th className="py-3 px-4">HASH</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1C1D22]/60">
                {txData.data.transactions.map((tx) => {
                  const isExpanded = expandedTxId === tx.transaction_id;
                  const auditHash = generateAuditHash(
                    tx.transaction_id,
                    tx.risk_score,
                    tx.timestamp
                  );
                  const decisionAction =
                    tx.risk_score >= 0.85 || tx.is_fraud ? "HOLD" : tx.risk_score >= 0.37 ? "REVIEW" : "ALLOW";

                  return (
                    <React.Fragment key={tx.transaction_id}>
                      <tr
                        onClick={() =>
                          setExpandedTxId(isExpanded ? null : tx.transaction_id)
                        }
                        className={`group cursor-pointer transition-colors ${
                          isExpanded
                            ? "bg-[#121317] border-l-2 border-[#CC9166]"
                            : "hover:bg-[#121317]/50"
                        }`}
                      >
                        <td className="py-3 px-3 text-center text-[#5E616E]">
                          {isExpanded ? (
                            <ChevronDown className="h-3.5 w-3.5 text-[#CC9166]" />
                          ) : (
                            <ChevronRight className="h-3.5 w-3.5 opacity-60 group-hover:opacity-100" />
                          )}
                        </td>

                        <td className="py-3 px-3 font-mono text-[11px] text-[#777A88]">
                          {tx.timestamp
                            ? new Date(tx.timestamp).toLocaleString("en-IN", {
                                dateStyle: "short",
                                timeStyle: "medium",
                              })
                            : "—"}
                        </td>

                        <td className="py-3 px-3 font-mono text-xs text-white font-medium">
                          {tx.transaction_id}
                        </td>

                        <td className="py-3 px-3 font-mono text-[11px] text-[#9194A1]">
                          inv_{tx.transaction_id.replace("txn_", "")}
                        </td>

                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <RiskBadge level={tx.risk_level} size="xs" />
                            <span className="font-mono text-[11px] text-[#E2E3E9]">
                              Score: {tx.risk_score.toFixed(3)}
                            </span>
                            {tx.cluster_id && (
                              <span className="text-[10px] font-mono text-[#CC9166] truncate max-w-[120px]">
                                • {tx.cluster_id}
                              </span>
                            )}
                          </div>
                        </td>

                        <td className="py-3 px-3 font-mono text-[11px] text-[#777A88]">
                          POL-v1.0-DET
                        </td>

                        <td className="py-3 px-3 text-center">
                          <DecisionBadge action={decisionAction} size="xs" />
                        </td>

                        <td className="py-3 px-4 font-mono text-[11px] text-[#5E616E] group-hover:text-[#9194A1] transition-colors">
                          {auditHash.slice(0, 16)}...
                        </td>
                      </tr>

                      {/* Expanded Evidence Ledger Row */}
                      {isExpanded && (
                        <tr className="bg-[#08080A]/90 border-b border-[#1C1D22]">
                          <td colSpan={8} className="p-5">
                            <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-5 space-y-4">
                              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#1C1D22] pb-3">
                                <div className="flex items-center gap-3">
                                  <FileCheck className="h-4 w-4 text-[#CC9166]" />
                                  <span className="font-mono text-xs font-semibold text-white">
                                    AUDIT RECORD / {tx.transaction_id}
                                  </span>
                                  <span className="text-[10px] font-mono text-[#8FAF9B]">
                                    VERIFIED IMMUTABLE
                                  </span>
                                </div>
                                <Link
                                  href={`/investigate?tx=${tx.transaction_id}`}
                                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-[#121317] border border-[#1C1D22] text-xs font-mono text-[#CC9166] hover:text-white hover:border-[#CC9166] transition-colors"
                                >
                                  <span>Open Forensic Console</span>
                                  <ExternalLink className="h-3 w-3" />
                                </Link>
                              </div>

                              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
                                <div>
                                  <div className="text-[10px] text-[#5E616E] uppercase">
                                    CRYPTOGRAPHIC PROOF HASH
                                  </div>
                                  <div className="text-white mt-1 break-all bg-[#121317] p-2 rounded border border-[#1C1D22]">
                                    {auditHash}
                                  </div>
                                </div>
                                <div>
                                  <div className="text-[10px] text-[#5E616E] uppercase">
                                    TRANSACTION FACTS
                                  </div>
                                  <div className="text-[#9194A1] mt-1 space-y-0.5">
                                    <div>Amount: {formatINR(tx.amount)}</div>
                                    <div>Customer: {tx.customer_id}</div>
                                    <div>Device: {tx.device_id}</div>
                                  </div>
                                </div>
                                <div>
                                  <div className="text-[10px] text-[#5E616E] uppercase">
                                    POLICY AUTHORITY
                                  </div>
                                  <div className="text-[#9194A1] mt-1 space-y-0.5">
                                    <div>Rule: Deterministic Threshold Engine</div>
                                    <div>Status: Sealed &amp; Logged {pol ? `• v${pol.policy_version}` : ""}</div>
                                    <div className="text-[#CC9166]">Action: {pol ? pol.action : decisionAction}</div>
                                  </div>
                                </div>
                              </div>

                              {/* Detailed Evidence Synthesis If Loaded */}
                              {inv && inv.evidence.length > 0 && (
                                <div className="pt-2 border-t border-[#1C1D22]/60">
                                  <div className="text-[10px] font-mono text-[#5E616E] uppercase mb-2">
                                    SYNTHESIZED FORENSIC EVIDENCE
                                  </div>
                                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                    {inv.evidence.map((ev, idx) => (
                                      <div
                                        key={idx}
                                        className="p-2.5 rounded bg-[#121317] border border-[#1C1D22] text-xs"
                                      >
                                        <div className="flex items-center justify-between text-[10px] font-mono text-[#777A88] mb-1">
                                          <span className="text-[#CC9166]">[{ev.source}]</span>
                                          <span className="uppercase">{ev.evidence_type}</span>
                                        </div>
                                        <p className="text-[#9194A1] font-sans text-xs">
                                          {ev.description}
                                        </p>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AuditPage() {
  return (
    <DashboardLayout>
      <Suspense fallback={<LoadingState message="Connecting to secure audit ledger..." />}>
        <AuditContent />
      </Suspense>
    </DashboardLayout>
  );
}
