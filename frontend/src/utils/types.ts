export type MetricInfo = {
  name: string;
  display_name: string;
  category: string;
  description: string;
  use_cases: string[];
  limitations: string[];
  requires_ground_truth: boolean;
};

export type AuditSummary = {
  audit_id: string;
  model_id: string;
  model_name: string;
  status: string;
  overall_verdict: string | null;
  created_at: string;
  groq_enriched: boolean;
};

export type AuditListResponse = {
  audits: AuditSummary[];
  total: number;
  page: number;
  per_page: number;
};

export type FairnessResult = {
  metric_name: string;
  protected_attribute: string;
  privileged_value: number;
  unprivileged_value: number;
  disparity: number;
  threshold: number;
  status: string;
  confidence_interval_lower: number;
  confidence_interval_upper: number;
  p_value: number;
  sample_size_privileged: number;
  sample_size_unprivileged: number;
  interpretation: string;
};

export type Recommendation = {
  priority: string;
  issue: string;
  mitigation_strategy: string;
  mitigation_strategy_enriched: string | null;
  implementation_effort: string;
};

export type AuditDetail = {
  audit_id: string;
  status: string;
  overall_verdict: string | null;
  dataset_row_count: number | null;
  protected_attributes: string[];
  results: FairnessResult[];
  recommendations: Recommendation[];
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  narrative_summary: string | null;
  groq_enriched: boolean;
};

export type ModelCreateResponse = {
  model_id: string;
  name: string;
  use_case: string;
  description: string | null;
  created_at: string;
};
