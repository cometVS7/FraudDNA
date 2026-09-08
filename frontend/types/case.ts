/**
 * FraudDNA Case Management TypeScript Interfaces
 * Corresponds to backend/app/schemas/case.py and domain CaseModel.
 */

export type CaseStatus = "NEW" | "IN_REVIEW" | "ESCALATED" | "RESOLVED" | "CLOSED";
export type CasePriority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface CaseCreateRequest {
  title: string;
  priority?: CasePriority;
  owner?: string | null;
  notes?: string | null;
  investigation_id?: string | null;
}

export interface CaseStatusUpdateRequest {
  status: CaseStatus;
  notes?: string | null;
  owner?: string | null;
}

export interface CaseResponse {
  id: string;
  title: string;
  status: CaseStatus;
  priority: CasePriority;
  owner: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  investigation_ids: string[];
}

export interface CaseListResponse {
  items: CaseResponse[];
  total_count: number;
  limit: number;
  offset: number;
}
