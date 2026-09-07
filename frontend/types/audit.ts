/**
 * FraudDNA Audit Trail TypeScript Interfaces
 * Corresponds to backend/app/schemas/audit.py and domain AuditEventModel.
 */

export interface AuditEventResponse {
  id: string;
  timestamp: string;
  actor: string;
  actor_type: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  payload_hash: string;
  previous_hash: string | null;
  event_hash: string;
  payload: Record<string, unknown>;
}

export interface AuditEventListResponse {
  items: AuditEventResponse[];
  total_count: number;
  limit: number;
  offset: number;
}

export interface AuditChainVerifyResponse {
  is_valid: boolean;
  total_verified: number;
  head_event_hash: string | null;
  verified_at: string;
  message: string;
}
