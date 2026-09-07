/**
 * FraudDNA AI Investigation Agent TypeScript Interfaces
 * Corresponds to backend/app/agent/schemas.py.
 */

export type AdvisoryAction =
  | "MANUAL_REVIEW_ESCALATION"
  | "MERCHANT_INQUIRY"
  | "CLOSE_BENIGN"
  | "REQUEST_ADDITIONAL_EVIDENCE"
  | "FREEZE_SUSPICIOUS_ENTITIES";

export interface AgentEvidenceItem {
  id: string;
  category: string;
  source: string;
  source_id?: string | null;
  snippet: string;
  severity: "low" | "medium" | "high" | "critical" | string;
  confidence: number;
  provenance: Record<string, unknown>;
  timestamp: string;
}

export interface ToolExecutionRecord {
  tool_name: string;
  tool_args: Record<string, unknown>;
  status: string;
  duration_ms: number;
  error_message: string | null;
}

export interface AgentFindings {
  investigation_id: string;
  transaction_id: string;
  risk_level: string;
  risk_score: number;
  summary: string;
  fraud_hypothesis: string;
  evidence_items: AgentEvidenceItem[];
  detected_patterns: string[];
  recommended_action: AdvisoryAction | string;
  recommended_actions: string[];
  confidence?: number;
  reasoning: string;
  limitations: string[];
  agent_steps: number;
  tool_trace: ToolExecutionRecord[];
  model_provider?: string;
  model_name?: string;
  is_degraded?: boolean;
  is_persisted?: boolean;
}

export interface AgentInvestigationResponse {
  investigation_id: string;
  transaction_id: string;
  status: string;
  findings: AgentFindings;
  is_persisted: boolean;
  is_degraded: boolean;
  created_at: string;
}
