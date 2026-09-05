"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { DashboardLayout } from "@/components/layout";
import {
  MetricCard,
  RiskBadge,
  DecisionBadge,
  SectionCard,
  LoadingState,
  ErrorState,
  EmptyState,
  DataLabel,
  formatPct,
} from "@/components/ui";
import { useAsync } from "@/hooks/use-async";
import {
  createInvestigation,
  createAgentInvestigation,
  evaluatePolicy,
} from "@/lib/api";
import type {
  InvestigationResponse,
  AgentInvestigationResponse,
  PolicyDecision,
} from "@/lib/api";
import { Search, Shield, Brain, BookOpen, Scale, AlertTriangle, ArrowRight } from "lucide-react";

function InvestigateContent() {
  const searchParams = useSearchParams();
  const initialTx = searchParams.get("tx") || "";
  const [txId, setTxId] = useState(initialTx);
  const [submittedTxId, setSubmittedTxId] = useState(initialTx);

  // Phase 3 Investigation
  const investigation = useAsync<InvestigationResponse | null>(
    () => (submittedTxId ? createInvestigation(submittedTxId) : Promise.resolve(null)),
    [submittedTxId]
  );

  // Phase 5 Agent Investigation
  const agent = useAsync<AgentInvestigationResponse | null>(
    () => (submittedTxId ? createAgentInvestigation(submittedTxId).catch(() => null) : Promise.resolve(null)),
    [submittedTxId]
  );

  // Policy Decision
  const policy = useAsync<PolicyDecision | null>(
    () => (submittedTxId ? evaluatePolicy(submittedTxId).catch(() => null) : Promise.resolve(null)),
    [submittedTxId]
  );

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmittedTxId(txId.trim());
  }

  const inv = investigation.status === "success" ? investigation.data : null;
  const agentData = agent.status === "success" ? agent.data : null;
  const policyData = policy.status === "success" ? policy.data : null;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight">Investigate</h2>
        <p className="text-sm text-muted-foreground">
          Full fraud investigation pipeline: ML → XAI → Graph → RAG → AI Agent → Policy Decision
        </p>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSubmit} className="flex gap-3">
        <div className="relative flex-1 max-w-lg">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Enter transaction ID (e.g. txn_00001)"
            value={txId}
            onChange={(e) => setTxId(e.target.value)}
            className="w-full pl-9 pr-3 py-2.5 text-sm bg-card border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary font-mono"
          />
        </div>
        <button
          type="submit"
          disabled={!txId.trim()}
          className="px-5 py-2.5 text-sm font-medium bg-primary text-primary-foreground rounded-xl hover:opacity-90 disabled:opacity-40 transition-opacity"
        >
          Investigate
        </button>
      </form>

      {/* Loading / Error */}
      {investigation.status === "loading" && <LoadingState message="Running investigation..." />}
      {investigation.status === "error" && (
        <ErrorState error={investigation.error} onRetry={investigation.refetch} />
      )}

      {!submittedTxId && (
        <EmptyState
          title="Enter a transaction ID"
          description="Search for a transaction to run a full fraud investigation"
        />
      )}

      {inv && (
        <>
          {/* Investigation Pipeline Progress */}
          <div className="flex items-center gap-2 text-xs text-muted-foreground overflow-x-auto py-2">
            {[
              { label: "Detection", icon: Shield, done: true },
              { label: "XAI", icon: Brain, done: inv.risk_factors.length > 0 },
              { label: "FraudDNA", icon: ArrowRight, done: inv.related_entities.length > 0 },
              { label: "Evidence", icon: BookOpen, done: inv.evidence.length > 0 },
              { label: "AI Agent", icon: Brain, done: !!agentData },
              { label: "Policy", icon: Scale, done: !!policyData },
            ].map((step, i) => (
              <div key={i} className="flex items-center gap-1.5">
                {i > 0 && <ArrowRight className="h-3 w-3 text-border" />}
                <div
                  className={`flex items-center gap-1 px-2.5 py-1 rounded-full border ${
                    step.done
                      ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                      : "bg-muted/50 border-border text-muted-foreground"
                  }`}
                >
                  <step.icon className="h-3 w-3" />
                  <span>{step.label}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Risk Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              label="Risk Score"
              value={inv.risk_score.toFixed(4)}
              variant={inv.risk_level === "critical" ? "danger" : inv.risk_level === "high" ? "warning" : "default"}
            />
            <MetricCard
              label="Risk Level"
              value={inv.risk_level.toUpperCase()}
              variant={inv.risk_level === "critical" ? "danger" : inv.risk_level === "high" ? "warning" : "default"}
            />
            <MetricCard
              label="Evidence Items"
              value={inv.evidence.length}
              sublabel={`${inv.risk_factors.length} XAI factors`}
            />
            <MetricCard
              label="Status"
              value={inv.status.toUpperCase()}
              variant={inv.status === "completed" ? "success" : "warning"}
            />
          </div>

          {/* Two Column Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* XAI Risk Factors */}
            <SectionCard title="XAI Risk Factors" subtitle="SHAP-derived feature attribution">
              {inv.risk_factors.length === 0 ? (
                <EmptyState title="No XAI factors" description="Model explanation unavailable" />
              ) : (
                <div className="space-y-3">
                  {inv.risk_factors.map((f, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-xs font-mono text-muted-foreground w-5">#{f.rank}</span>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-medium">{f.feature}</span>
                          <span className={`text-xs font-mono font-bold ${f.direction === "increases_risk" ? "text-red-600" : f.direction === "decreases_risk" ? "text-emerald-600" : "text-gray-400"}`}>
                            {f.impact > 0 ? "+" : ""}{f.impact.toFixed(4)}
                          </span>
                        </div>
                        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${f.direction === "increases_risk" ? "bg-red-400" : "bg-emerald-400"}`}
                            style={{ width: `${Math.min(Math.abs(f.impact) * 200, 100)}%` }}
                          />
                        </div>
                        <p className="text-[10px] text-muted-foreground mt-0.5">
                          Value: <span className="font-mono">{String(f.value)}</span>
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </SectionCard>

            {/* FraudDNA Context */}
            <SectionCard title="FraudDNA Context" subtitle="Relationship graph intelligence">
              {/* Related Entities */}
              {inv.related_entities.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-xs font-semibold text-muted-foreground mb-2 uppercase">Related Entities</h4>
                  <div className="space-y-1.5">
                    {inv.related_entities.slice(0, 10).map((e, i) => (
                      <div key={i} className="flex items-center justify-between text-xs px-2 py-1.5 rounded bg-muted/30">
                        <div>
                          <span className="font-mono">{e.entity_id}</span>
                          <span className="text-muted-foreground ml-2">{e.relationship}</span>
                        </div>
                        {Number(e.metadata.connected_customers_count) > 1 && (
                          <span className="text-amber-600 font-medium">
                            {String(e.metadata.connected_customers_count)} customers
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Cluster */}
              {inv.cluster && (
                <div className="p-3 rounded-lg border border-amber-200 bg-amber-50/50">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-semibold">Cluster: {inv.cluster.cluster_id}</span>
                    <RiskBadge level={inv.cluster.is_suspicious ? "high" : "low"} size="xs" />
                  </div>
                  <p className="text-[10px] text-muted-foreground">
                    {inv.cluster.transaction_count} transactions · {inv.cluster.customer_count} customers · Score: {inv.cluster.cluster_risk_score.toFixed(4)}
                  </p>
                  {inv.cluster.primary_reason && (
                    <p className="text-[10px] text-amber-700 mt-1">{inv.cluster.primary_reason}</p>
                  )}
                </div>
              )}
              {!inv.cluster && inv.related_entities.length === 0 && (
                <EmptyState title="No graph context" description="Transaction is isolated in the graph" />
              )}
            </SectionCard>
          </div>

          {/* Evidence */}
          <SectionCard title="Investigation Evidence" subtitle="Deterministic evidence from all signals">
            {inv.evidence.length === 0 ? (
              <EmptyState title="No evidence" />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {inv.evidence.map((e, i) => (
                  <div
                    key={i}
                    className={`p-3 rounded-lg border ${
                      e.severity === "critical"
                        ? "border-red-200 bg-red-50/50"
                        : e.severity === "high"
                          ? "border-orange-200 bg-orange-50/50"
                          : e.severity === "medium"
                            ? "border-amber-200 bg-amber-50/50"
                            : "border-border bg-muted/20"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-mono font-medium">{e.evidence_type}</span>
                      <RiskBadge level={e.severity} size="xs" />
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">{e.description}</p>
                    <p className="text-[10px] text-muted-foreground mt-1.5 font-mono">
                      Source: {e.source}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>

          {/* AI Agent Investigation */}
          {agent.status === "loading" && <LoadingState message="Running AI investigation..." />}
          {agentData && (
            <SectionCard title="AI Investigation" subtitle="LangGraph agent findings">
              <div className="space-y-4">
                <div className="flex items-center gap-3 mb-3">
                  <DataLabel label={`${agentData.findings.agent_steps} steps`} />
                  <DataLabel label={`Confidence: ${formatPct(agentData.findings.confidence)}`} />
                  <DataLabel label={agentData.status} />
                </div>

                <div>
                  <h4 className="text-xs font-semibold text-muted-foreground mb-1 uppercase">Summary</h4>
                  <p className="text-sm text-foreground leading-relaxed">{agentData.findings.summary}</p>
                </div>

                <div>
                  <h4 className="text-xs font-semibold text-muted-foreground mb-1 uppercase">Fraud Hypothesis</h4>
                  <p className="text-sm text-foreground leading-relaxed">{agentData.findings.fraud_hypothesis}</p>
                </div>

                {agentData.findings.evidence.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-muted-foreground mb-2 uppercase">Agent Evidence</h4>
                    <div className="space-y-2">
                      {agentData.findings.evidence.map((e, i) => (
                        <div key={i} className="p-2.5 rounded-lg bg-blue-50/50 border border-blue-100 text-xs">
                          <div className="flex items-center gap-2 mb-1">
                            <RiskBadge level={e.severity} size="xs" />
                            <span className="font-mono text-muted-foreground">{e.source}</span>
                          </div>
                          <p className="text-foreground">{e.snippet}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {agentData.findings.tool_trace.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-muted-foreground mb-2 uppercase">Tool Trace</h4>
                    <div className="space-y-1">
                      {agentData.findings.tool_trace.map((t, i) => (
                        <div key={i} className="flex items-center gap-2 text-xs text-muted-foreground">
                          <span className={`h-1.5 w-1.5 rounded-full ${t.status === "success" ? "bg-emerald-500" : "bg-red-500"}`} />
                          <span className="font-mono">{t.tool_name}</span>
                          <span className="text-[10px]">{t.duration_ms.toFixed(0)}ms</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {agentData.findings.limitations.length > 0 && (
                  <div className="p-2.5 rounded-lg bg-amber-50/50 border border-amber-100">
                    <h4 className="text-xs font-semibold text-amber-700 mb-1 flex items-center gap-1">
                      <AlertTriangle className="h-3 w-3" /> Limitations
                    </h4>
                    <ul className="text-xs text-amber-600 space-y-0.5">
                      {agentData.findings.limitations.map((l, i) => (
                        <li key={i}>• {l}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </SectionCard>
          )}

          {/* Policy Decision */}
          {policy.status === "loading" && <LoadingState message="Evaluating policy..." />}
          {policyData && (
            <div className="bg-card border-2 border-border rounded-xl shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Risk Decision</h3>
                  <p className="text-xs text-muted-foreground">Deterministic Policy Engine</p>
                </div>
                <DecisionBadge action={policyData.action} />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <p className="text-xs text-muted-foreground mb-1 uppercase font-semibold">Decision ID</p>
                  <p className="text-xs font-mono">{policyData.decision_id}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-1 uppercase font-semibold">Policy Version</p>
                  <p className="text-xs font-mono">{policyData.policy_version}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-1 uppercase font-semibold">Deterministic</p>
                  <p className="text-xs">{policyData.is_deterministic ? "✓ Fully Deterministic" : "Partial"}</p>
                </div>
              </div>

              {/* Reason Codes */}
              <div className="mb-3">
                <p className="text-xs text-muted-foreground mb-1.5 uppercase font-semibold">Reason Codes</p>
                <div className="flex flex-wrap gap-1.5">
                  {policyData.reason_codes.map((code, i) => (
                    <span key={i} className="px-2 py-0.5 text-[10px] font-mono rounded bg-muted border border-border text-muted-foreground">
                      {code}
                    </span>
                  ))}
                </div>
              </div>

              {/* Evidence Summary */}
              {policyData.evidence_summary.length > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground mb-1.5 uppercase font-semibold">Evidence Summary</p>
                  <ul className="text-xs text-muted-foreground space-y-0.5">
                    {policyData.evidence_summary.map((s, i) => (
                      <li key={i}>• {s}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* AI Boundary Notice */}
              <div className="mt-4 p-2.5 rounded-lg bg-blue-50/50 border border-blue-100 text-xs text-blue-700">
                <p className="font-semibold mb-0.5">AI ≠ Financial Action</p>
                <p>The AI agent investigates uncertainty. The deterministic policy engine independently controls the financial action. The LLM did not directly block, hold, or allow this transaction.</p>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function InvestigatePage() {
  return (
    <DashboardLayout>
      <Suspense fallback={<LoadingState />}>
        <InvestigateContent />
      </Suspense>
    </DashboardLayout>
  );
}
