/**
 * FraudDNA Frontend API Client
 *
 * Centralized, typed API layer for backend communication.
 * Connects with FastAPI v1 endpoints with strong typing, error formatting,
 * and correlation propagation.
 */

import type {
  CaseCreateRequest,
  CaseListResponse,
  CaseResponse,
  CaseStatusUpdateRequest,
} from "@/types/case";
import type {
  NetworkExposure,
  NetworkFinding,
  NetworkIntelligenceResponse,
  NetworkPath,
  NetworkTimeline,
  PathSearchRequest,
  PathSearchResponse,
  SyndicatePattern,
} from "@/types/network";
import type {
  AgentInvestigationResponse,
} from "@/types/agent";
import type {
  AuditChainVerifyResponse,
  AuditEventListResponse,
  AuditEventResponse,
} from "@/types/audit";

export * from "@/types/case";
export * from "@/types/network";
export * from "@/types/agent";
export * from "@/types/audit";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface RequestOptions {
  method?: string;
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined | null>;
}

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(`API Error ${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

export function formatErrorDetail(detail: unknown): string {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => {
      if (typeof item === "object" && item !== null) {
        const entry = item as Record<string, unknown>;
        let loc = "";
        if (Array.isArray(entry.loc)) {
          const relevant = entry.loc.filter((p) => p !== "body");
          loc = relevant.join(".");
        }
        const rawMsg = typeof entry.msg === "string" ? entry.msg : JSON.stringify(entry);
        const msg = rawMsg.replace(/^Value error,\s*/i, "");
        return loc ? `${loc}: ${msg}` : msg;
      }
      return String(item);
    });
    return messages.join("; ");
  }
  if (typeof detail === "object" && detail !== null) {
    try {
      return JSON.stringify(detail);
    } catch {
      return String(detail);
    }
  }
  return String(detail ?? "");
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, params } = options;

  let url = `${API_BASE}${endpoint}`;

  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const qs = searchParams.toString();
    if (qs) url += `?${qs}`;
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const res = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const errBody = await res.json();
      if (errBody.detail !== undefined) {
        detail = formatErrorDetail(errBody.detail);
      } else if (errBody.message) {
        detail = String(errBody.message);
      } else {
        detail = formatErrorDetail(errBody);
      }
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail);
  }

  return res.json() as Promise<T>;
}

// ─── Health ──────────────────────────────────────────────────
export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
}

export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

// ─── Overview ────────────────────────────────────────────────
export interface OverviewData {
  total_transactions: number;
  fraud_count: number;
  legitimate_count: number;
  fraud_rate: number;
  total_amount: number;
  fraud_exposure: number;
  suspicious_transactions: number;
  high_risk_count: number;
  critical_risk_count: number;
  total_clusters: number;
  suspicious_clusters: number;
  risk_distribution: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  data_label: string;
}

export function fetchOverview(): Promise<OverviewData> {
  return request<OverviewData>("/overview");
}

// ─── Transactions ────────────────────────────────────────────
export interface Transaction {
  transaction_id: string;
  amount: number;
  timestamp: string;
  customer_id: string;
  merchant_id: string;
  device_id: string;
  ip_address: string;
  card_id: string;
  risk_score: number;
  risk_level: string;
  is_fraud: boolean;
  cluster_id: string | null;
}

export interface TransactionsResponse {
  total: number;
  limit: number;
  offset: number;
  transactions: Transaction[];
}

export function fetchTransactions(params?: {
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: string;
  risk_level?: string;
  suspicious_only?: boolean;
  search?: string;
}): Promise<TransactionsResponse> {
  return request<TransactionsResponse>("/transactions", { params });
}

export function fetchTransaction(id: string): Promise<Transaction> {
  return request<Transaction>(`/transactions/${id}`);
}

// ─── Cases (V2-09 Core) ──────────────────────────────────────
export function fetchCases(params?: {
  limit?: number;
  offset?: number;
  status?: string;
  priority?: string;
  owner?: string;
}): Promise<CaseListResponse> {
  return request<CaseListResponse>("/cases", { params });
}

export function createCase(data: CaseCreateRequest): Promise<CaseResponse> {
  return request<CaseResponse>("/cases", {
    method: "POST",
    body: data,
  });
}

export function fetchCase(caseId: string): Promise<CaseResponse> {
  return request<CaseResponse>(`/cases/${caseId}`);
}

export function updateCaseStatus(caseId: string, data: CaseStatusUpdateRequest): Promise<CaseResponse> {
  return request<CaseResponse>(`/cases/${caseId}/status`, {
    method: "PATCH",
    body: data,
  });
}

// ─── Graph ───────────────────────────────────────────────────
export interface GraphNode {
  id: string;
  raw_id: string;
  entity_type: string;
  label: string;
  risk_score: number;
  amount: number | null;
  timestamp: string | null;
  metadata: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
  weight: number;
  metadata: Record<string, unknown>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  total_edges: number;
}

export function fetchTransactionGraph(transactionId: string, depth?: number): Promise<GraphData> {
  return request<GraphData>(`/graph/transaction/${transactionId}`, {
    params: depth ? { depth } : undefined,
  });
}

export function fetchClusterGraph(clusterId: string): Promise<GraphData> {
  return request<GraphData>(`/graph/cluster/${clusterId}`);
}

// ─── Networks & Intelligence (V2-07) ─────────────────────────
export interface ClusterSummary {
  cluster_id: string;
  cluster_risk_score: number;
  is_suspicious: boolean;
  transaction_count: number;
  customer_count: number;
  device_count: number;
  ip_count: number;
  card_count: number;
  merchant_count: number;
  suspicious_transaction_count: number;
  total_transaction_amount: number;
  suspicious_transaction_amount: number;
  primary_reason: string;
}

export interface ClustersResponse {
  total_clusters: number;
  limit: number;
  offset: number;
  clusters: ClusterSummary[];
}

export function fetchClusters(params?: {
  min_risk?: number;
  suspicious_only?: boolean;
  limit?: number;
  offset?: number;
  sort_by?: string;
}): Promise<ClustersResponse> {
  return request<ClustersResponse>("/clusters", { params });
}

export function fetchNetworkIntelligence(networkId: string, params?: {
  as_of?: string;
  max_nodes?: number;
}): Promise<NetworkIntelligenceResponse> {
  return request<NetworkIntelligenceResponse>(`/networks/${networkId}/intelligence`, { params });
}

export function fetchNetworkGraph(networkId: string, maxNodes?: number): Promise<GraphData> {
  return request<GraphData>(`/networks/${networkId}/graph`, {
    params: maxNodes ? { max_nodes: maxNodes } : undefined,
  });
}

export function fetchNetworkPaths(networkId: string, limit?: number): Promise<NetworkPath[]> {
  return request<NetworkPath[]>(`/networks/${networkId}/paths`, {
    params: limit ? { limit } : undefined,
  });
}

export function fetchNetworkTimeline(networkId: string): Promise<NetworkTimeline> {
  return request<NetworkTimeline>(`/networks/${networkId}/timeline`);
}

export function fetchNetworkExposure(networkId: string): Promise<NetworkExposure> {
  return request<NetworkExposure>(`/networks/${networkId}/exposure`);
}

export function fetchNetworkPatterns(networkId: string): Promise<SyndicatePattern[]> {
  return request<SyndicatePattern[]>(`/networks/${networkId}/patterns`);
}

export function fetchNetworkFindings(networkId: string): Promise<NetworkFinding[]> {
  return request<NetworkFinding[]>(`/networks/${networkId}/findings`);
}

export function searchNetworkPaths(payload: PathSearchRequest): Promise<PathSearchResponse> {
  return request<PathSearchResponse>("/networks/paths/search", {
    method: "POST",
    body: payload,
  });
}

// ─── Entities (V2-06) ────────────────────────────────────────
export interface EntityProfileResponse {
  entity_type: string;
  entity_id: string;
  risk_score: number;
  risk_tier: string;
  status: string;
  first_seen: string | null;
  last_seen: string | null;
  lifetime_transaction_count?: number;
  lifetime_volume_inr?: number;
  distinct_devices_count?: number;
  distinct_cards_count?: number;
  distinct_ips_count?: number;
  shared_entity_count?: number;
  [key: string]: unknown;
}

export function fetchEntityProfile(entityType: string, entityId: string, asOf?: string): Promise<EntityProfileResponse> {
  return request<EntityProfileResponse>(`/entities/${entityType}/${entityId}`, {
    params: asOf ? { as_of: asOf } : undefined,
  });
}

export function fetchEntityGraph(entityType: string, entityId: string, params?: {
  depth?: number;
  max_nodes?: number;
}): Promise<GraphData> {
  return request<GraphData>(`/entities/${entityType}/${entityId}/graph`, { params });
}

// ─── Investigations (Deterministic V2-03) ────────────────────
export interface RiskFactor {
  feature: string;
  value: unknown;
  impact: number;
  direction: string;
  rank: number;
}

export interface RelatedEntity {
  entity_type: string;
  entity_id: string;
  relationship: string;
  metadata: Record<string, unknown>;
}

export interface RelatedTransaction {
  transaction_id: string;
  timestamp: string;
  amount: number;
  risk_score: number;
  relationship: string;
}

export interface InvestigationEvidence {
  evidence_type: string;
  description: string;
  severity: string;
  source: string;
}

export interface ClusterInvestigationSummary {
  cluster_id: string;
  cluster_risk_score: number;
  is_suspicious: boolean;
  transaction_count: number;
  customer_count: number;
  device_count: number;
  ip_count: number;
  card_count: number;
  suspicious_transaction_count: number;
  primary_reason: string | null;
}

export interface InvestigationResponse {
  investigation_id: string;
  transaction_id: string;
  risk_score: number;
  risk_level: string;
  risk_factors: RiskFactor[];
  related_entities: RelatedEntity[];
  related_transactions: RelatedTransaction[];
  cluster: ClusterInvestigationSummary | null;
  evidence: InvestigationEvidence[];
  status: string;
  generated_at: string;
}

export function createInvestigation(transactionId: string): Promise<InvestigationResponse> {
  return request<InvestigationResponse>("/investigations", {
    method: "POST",
    body: { transaction_id: transactionId },
  });
}

export function getInvestigation(investigationId: string): Promise<InvestigationResponse> {
  return request<InvestigationResponse>(`/investigations/${investigationId}`);
}

// ─── AI Agent Investigation (V2-08) ──────────────────────────
export function createAgentInvestigation(transactionId: string, maxSteps?: number): Promise<AgentInvestigationResponse> {
  return request<AgentInvestigationResponse>("/agent/investigate", {
    method: "POST",
    body: { transaction_id: transactionId, max_steps: maxSteps },
  });
}

export function getAgentInvestigation(investigationId: string): Promise<AgentInvestigationResponse> {
  return request<AgentInvestigationResponse>(`/agent/investigate/${investigationId}`);
}

// ─── Policy Decision (Deterministic V2-04) ───────────────────
export interface PolicyDecision {
  decision_id: string;
  transaction_id: string;
  action: string;
  reason_codes: string[];
  risk_score: number;
  risk_level: string;
  cluster_id: string | null;
  policy_version: string;
  evidence_summary: string[];
  created_at: string;
  is_deterministic: boolean;
}

export function evaluatePolicy(transactionId: string): Promise<PolicyDecision> {
  return request<PolicyDecision>("/decisions/evaluate", {
    method: "POST",
    body: { transaction_id: transactionId },
  });
}

// ─── Audit Trail (V2-04 & V2-06) ─────────────────────────────
export function fetchAuditEvents(params?: {
  limit?: number;
  offset?: number;
  entity_type?: string;
  entity_id?: string;
  event_type?: string;
  actor?: string;
}): Promise<AuditEventListResponse> {
  return request<AuditEventListResponse>("/audit", { params });
}

export function fetchAuditEvent(eventId: string): Promise<AuditEventResponse> {
  return request<AuditEventResponse>(`/audit/${eventId}`);
}

export function verifyAuditChain(): Promise<AuditChainVerifyResponse> {
  return request<AuditChainVerifyResponse>("/audit/verify/chain");
}

// ─── Simulation & Evaluation ─────────────────────────────────
export interface SimulationConfig {
  fraud_threshold: number;
  review_threshold?: number | null;
  cost_per_false_positive: number;
  avg_fraud_loss?: number | null;
  review_capacity: number;
}

export interface SimulationResult {
  simulation_id: string;
  config: SimulationConfig;
  total_transactions: number;
  actual_fraud_count: number;
  actual_legitimate_count: number;
  predicted_fraud_count: number;
  true_positives: number;
  false_positives: number;
  true_negatives: number;
  false_negatives: number;
  precision: number;
  recall: number;
  f1_score: number;
  false_positive_rate: number;
  gross_fraud_exposure: number;
  fraud_prevented_amount: number;
  fraud_missed_amount: number;
  false_positive_cost: number;
  expected_loss: number;
  net_benefit: number;
  review_volume: number;
  review_capacity: number;
  review_capacity_exceeded: boolean;
  is_deterministic: boolean;
  data_label: string;
}

export interface SimulationCompareResponse {
  comparison_id: string;
  results: SimulationResult[];
  baseline_index: number;
}

export function runSimulation(config: SimulationConfig): Promise<SimulationResult> {
  return request<SimulationResult>("/simulations", {
    method: "POST",
    body: { config },
  });
}

export function compareSimulations(configs: SimulationConfig[]): Promise<SimulationCompareResponse> {
  return request<SimulationCompareResponse>("/simulations/compare", {
    method: "POST",
    body: { configs },
  });
}

export interface EvaluationMetrics {
  evaluation_type: string;
  held_out_test_size: number;
  actual_fraud_count: number;
  predicted_fraud_count: number;
  selected_operating_threshold: number;
  metrics: {
    precision: number;
    recall: number;
    f1_score: number;
    pr_auc: number;
    roc_auc: number;
    false_positive_rate: number;
  };
  confusion_matrix: {
    true_negatives: number;
    false_positives: number;
    false_negatives: number;
    true_positives: number;
  };
  cost_and_financial_impact: {
    cost_per_false_positive_inr: number;
    false_positive_count: number;
    false_positive_monetary_cost_inr: number;
    total_fraud_loss_exposure_inr: number;
    fraud_prevented_amount_inr: number;
    fraud_missed_amount_inr: number;
    net_business_benefit_inr: number;
  };
  breakdown_by_scenario: Record<string, {
    total_count: number;
    caught_count: number;
    catch_rate: number;
  }>;
}

export function fetchEvaluation(): Promise<EvaluationMetrics> {
  return request<EvaluationMetrics>("/evaluation");
}

export interface RAGSearchResult {
  source_id: string;
  document_title: string;
  chunk_id: string;
  content: string;
  similarity: number;
  metadata: Record<string, unknown>;
}

export interface RAGSearchResponse {
  query: string;
  results: RAGSearchResult[];
  total_results: number;
}

export function searchRAG(query: string, topK?: number): Promise<RAGSearchResponse> {
  return request<RAGSearchResponse>("/rag/search", {
    method: "POST",
    body: { query, top_k: topK || 5 },
  });
}
