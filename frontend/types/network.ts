/**
 * FraudDNA Risk Network Intelligence TypeScript Interfaces
 * Corresponds to backend/app/schemas/network_intelligence.py and cluster.py.
 */

export interface SyndicatePattern {
  pattern_type: string;
  triggered: boolean;
  confidence: number;
  severity: "low" | "medium" | "high" | "critical" | string;
  description: string;
  contributing_entities: string[];
  evidence_ids: string[];
}

export interface NetworkExposure {
  network_id: string;
  total_gross_exposure_inr: number;
  total_transactions: number;
  suspicious_transactions: number;
  total_customers: number;
  total_devices: number;
  total_ips: number;
  total_cards: number;
  total_merchants: number;
}

export interface NetworkTimelinePoint {
  timestamp: string;
  transaction_id: string;
  amount: number;
  risk_score: number;
  device_id: string | null;
  card_id: string | null;
  ip_address: string | null;
}

export interface NetworkTimeline {
  network_id: string;
  first_seen: string | null;
  last_seen: string | null;
  duration_days: number;
  burst_velocity_tx_per_hour: number;
  is_active_burst: boolean;
  timeline_points: NetworkTimelinePoint[];
}

export interface NetworkFinding {
  id: string;
  finding_type: string;
  severity: string;
  statement: string;
  confidence: number;
  evidence_sources: string[];
}

export interface NetworkPath {
  path_id: string;
  length: number;
  nodes: string[];
  edges: string[];
  risk_score: number;
  path_description: string;
}

export interface PathSearchRequest {
  source_id: string;
  target_id: string;
  source_type?: string;
  target_type?: string;
  max_depth?: number;
  max_paths?: number;
}

export interface PathSearchResponse {
  source_id: string;
  target_id: string;
  paths_found: number;
  paths: NetworkPath[];
}

export interface NetworkIntelligenceResponse {
  network_id: string;
  network_risk_score: number;
  risk_level: string;
  is_suspicious_cluster: boolean;
  exposure: NetworkExposure;
  timeline: NetworkTimeline;
  syndicate_patterns: SyndicatePattern[];
  findings: NetworkFinding[];
  recommended_actions: string[];
  evaluated_at: string;
}
