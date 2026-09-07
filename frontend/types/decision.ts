/**
 * FraudDNA Deterministic Policy Decision TypeScript Interfaces
 * Corresponds to backend/app/schemas/decision.py.
 */

export type PolicyAction = "ALLOW" | "REVIEW" | "HOLD";

export interface PolicyDecision {
  decision_id: string;
  transaction_id: string;
  action: PolicyAction | string;
  reason_codes: string[];
  risk_score: number;
  risk_level: string;
  cluster_id: string | null;
  policy_version: string;
  evidence_summary: string[];
  created_at: string;
  is_deterministic: boolean;
}
