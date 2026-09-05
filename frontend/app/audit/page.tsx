"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { DashboardLayout } from "@/components/layout";
import {
  RiskBadge,
  DecisionBadge,
  SectionCard,
  LoadingState,
  ErrorState,
  EmptyState,
  DataLabel,
  formatINR,
} from "@/components/ui";
import { useAsync } from "@/hooks/use-async";
import { fetchTransactions, createInvestigation, evaluatePolicy } from "@/lib/api";
import type { TransactionsResponse, InvestigationResponse, PolicyDecision } from "@/lib/api";
import { Search, ClipboardList } from "lucide-react";
import Link from "next/link";

function AuditContent() {
  const searchParams = useSearchParams();
  const [searchTx, setSearchTx] = useState(searchParams.get("tx") || "");

  // Fetch high-risk transactions as audit candidates
  const txData = useAsync<TransactionsResponse>(
    () => fetchTransactions({ limit: 20, sort_by: "risk_score", sort_order: "desc", suspicious_only: true }),
    []
  );

  // Individual audit lookup
  const [selectedTx, setSelectedTx] = useState<string | null>(searchParams.get("tx") || null);
  const investigation = useAsync<InvestigationResponse | null>(
    () => (selectedTx ? createInvestigation(selectedTx) : Promise.resolve(null)),
    [selectedTx]
  );
  const policy = useAsync<PolicyDecision | null>(
    () => (selectedTx ? evaluatePolicy(selectedTx).catch(() => null) : Promise.resolve(null)),
    [selectedTx]
  );

  const inv = investigation.status === "success" ? investigation.data : null;
  const pol = policy.status === "success" ? policy.data : null;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight flex items-center gap-2">
            <ClipboardList className="h-5 w-5 text-primary" />
            Audit Trail
          </h2>
          <p className="text-sm text-muted-foreground">
            Investigation and decision audit records
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search transaction ID..."
              value={searchTx}
              onChange={(e) => setSearchTx(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && searchTx.trim()) {
                  setSelectedTx(searchTx.trim());
                }
              }}
              className="pl-8 pr-3 py-1.5 text-xs rounded-md border border-input bg-background font-mono w-60"
            />
          </div>
          <button
            onClick={() => searchTx.trim() && setSelectedTx(searchTx.trim())}
            className="px-3 py-1.5 text-xs font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
          >
            Audit
          </button>
          <DataLabel label="Investigation History" />
        </div>
      </div>

      {/* Recent High-Risk Investigations */}
      <SectionCard title="High-Risk Transactions" subtitle="Select a transaction to view its audit trail">
        {txData.status === "loading" && <LoadingState />}
        {txData.status === "error" && <ErrorState error={txData.error} onRetry={txData.refetch} />}
        {txData.status === "success" && (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-muted-foreground uppercase tracking-wider border-b border-border">
                  <th className="text-left py-2 px-3 font-medium">Transaction</th>
                  <th className="text-right py-2 px-3 font-medium">Amount</th>
                  <th className="text-center py-2 px-3 font-medium">Risk</th>
                  <th className="text-center py-2 px-3 font-medium">Level</th>
                  <th className="text-left py-2 px-3 font-medium">Cluster</th>
                  <th className="text-center py-2 px-3 font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {txData.data.transactions.map((tx) => (
                  <tr
                    key={tx.transaction_id}
                    onClick={() => setSelectedTx(tx.transaction_id)}
                    className={`border-b border-border/50 cursor-pointer transition-colors ${
                      selectedTx === tx.transaction_id ? "bg-primary/5" : "hover:bg-muted/20"
                    }`}
                  >
                    <td className="py-2 px-3 font-mono">{tx.transaction_id}</td>
                    <td className="py-2 px-3 text-right font-mono">{formatINR(tx.amount)}</td>
                    <td className="py-2 px-3 text-center font-mono font-bold">{tx.risk_score.toFixed(4)}</td>
                    <td className="py-2 px-3 text-center">
                      <RiskBadge level={tx.risk_level} size="xs" />
                    </td>
                    <td className="py-2 px-3 font-mono text-muted-foreground">{tx.cluster_id || "—"}</td>
                    <td className="py-2 px-3 text-center">
                      <button className="text-primary font-medium hover:underline">
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>

      {/* Audit Detail */}
      {selectedTx && (
        <>
          {investigation.status === "loading" && <LoadingState message="Loading audit trail..." />}
          {investigation.status === "error" && <ErrorState error={investigation.error} />}

          {inv && (
            <SectionCard title={`Audit: ${selectedTx}`} subtitle={`Investigation: ${inv.investigation_id}`}>
              <div className="space-y-4">
                {/* Audit Timeline */}
                <div className="relative pl-6 border-l-2 border-border space-y-4">
                  {/* Detection */}
                  <div className="relative">
                    <div className="absolute -left-[25px] top-0.5 h-3 w-3 rounded-full bg-primary border-2 border-white" />
                    <div className="text-xs">
                      <span className="font-semibold">Detection</span>
                      <span className="text-muted-foreground ml-2">{inv.generated_at ? new Date(inv.generated_at).toLocaleString() : "—"}</span>
                      <p className="text-muted-foreground mt-0.5">
                        Risk Score: <span className="font-mono font-bold">{inv.risk_score.toFixed(4)}</span> · Level: {inv.risk_level.toUpperCase()}
                      </p>
                    </div>
                  </div>

                  {/* XAI */}
                  {inv.risk_factors.length > 0 && (
                    <div className="relative">
                      <div className="absolute -left-[25px] top-0.5 h-3 w-3 rounded-full bg-blue-500 border-2 border-white" />
                      <div className="text-xs">
                        <span className="font-semibold">XAI Analysis</span>
                        <p className="text-muted-foreground mt-0.5">
                          {inv.risk_factors.length} SHAP factors analyzed.
                          Top driver: <span className="font-mono">{inv.risk_factors[0]?.feature}</span> ({inv.risk_factors[0]?.impact > 0 ? "+" : ""}{inv.risk_factors[0]?.impact.toFixed(4)})
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Graph */}
                  <div className="relative">
                    <div className="absolute -left-[25px] top-0.5 h-3 w-3 rounded-full bg-purple-500 border-2 border-white" />
                    <div className="text-xs">
                      <span className="font-semibold">FraudDNA Graph</span>
                      <p className="text-muted-foreground mt-0.5">
                        {inv.related_entities.length} related entities · {inv.related_transactions.length} connected transactions
                        {inv.cluster ? ` · Cluster: ${inv.cluster.cluster_id}` : " · No cluster"}
                      </p>
                    </div>
                  </div>

                  {/* Evidence */}
                  <div className="relative">
                    <div className="absolute -left-[25px] top-0.5 h-3 w-3 rounded-full bg-amber-500 border-2 border-white" />
                    <div className="text-xs">
                      <span className="font-semibold">Evidence Synthesis</span>
                      <p className="text-muted-foreground mt-0.5">
                        {inv.evidence.length} evidence items from {new Set(inv.evidence.map((e) => e.source)).size} sources
                      </p>
                      <div className="mt-1 space-y-0.5">
                        {inv.evidence.slice(0, 5).map((e, i) => (
                          <p key={i} className="text-muted-foreground">
                            • <span className="font-mono">[{e.source}]</span> {e.description.slice(0, 100)}...
                          </p>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Policy Decision */}
                  {pol && (
                    <div className="relative">
                      <div className="absolute -left-[25px] top-0.5 h-3 w-3 rounded-full bg-emerald-500 border-2 border-white" />
                      <div className="text-xs">
                        <span className="font-semibold">Policy Decision</span>
                        <span className="ml-2">
                          <DecisionBadge action={pol.action} />
                        </span>
                        <p className="text-muted-foreground mt-1">
                          Decision ID: <span className="font-mono">{pol.decision_id}</span>
                        </p>
                        <p className="text-muted-foreground">
                          Policy: {pol.policy_version} · Deterministic: {pol.is_deterministic ? "✓" : "✗"}
                        </p>
                        <div className="mt-1 flex flex-wrap gap-1">
                          {pol.reason_codes.map((code, i) => (
                            <span key={i} className="px-1.5 py-0.5 text-[9px] font-mono rounded bg-muted border border-border/50">
                              {code}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Status */}
                  <div className="relative">
                    <div className="absolute -left-[25px] top-0.5 h-3 w-3 rounded-full bg-gray-400 border-2 border-white" />
                    <div className="text-xs">
                      <span className="font-semibold">Status</span>
                      <p className="text-muted-foreground mt-0.5">
                        Investigation: {inv.status.toUpperCase()} · Complete
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex gap-2 mt-4">
                  <Link
                    href={`/investigate?tx=${selectedTx}`}
                    className="px-3 py-1.5 text-xs font-medium text-primary border border-primary/30 rounded-lg hover:bg-primary/5 transition-colors"
                  >
                    Full Investigation →
                  </Link>
                </div>
              </div>
            </SectionCard>
          )}
        </>
      )}

      {!selectedTx && (
        <EmptyState title="Select a transaction" description="Click on a high-risk transaction to view its audit trail" />
      )}
    </div>
  );
}

export default function AuditPage() {
  return (
    <DashboardLayout>
      <Suspense fallback={<LoadingState />}>
        <AuditContent />
      </Suspense>
    </DashboardLayout>
  );
}
