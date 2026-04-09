"""Pydantic schemas for all API request/response shapes."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── Auth ────────────────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class RegisterResponse(BaseModel):
    user_id: str
    api_key: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    session_token: str
    user: "UserBrief"


class UserBrief(BaseModel):
    id: str
    email: str
    name: str


# ── Model ───────────────────────────────────────────────────────────────────


class ModelCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    use_case: str = Field(
        pattern=r"^(credit_approval|fraud_detection|underwriting|insurance|other)$"
    )
    description: str | None = None


class ModelResponse(BaseModel):
    model_id: str
    name: str
    use_case: str
    description: str | None
    created_at: datetime


class ModelListResponse(BaseModel):
    models: list[ModelResponse]


# ── Protected Attribute config (nested in audit) ────────────────────────────


class ProtectedAttributeConfig(BaseModel):
    name: str = Field(description="Column name in the CSV")
    type: str = Field(pattern=r"^(binary|categorical)$")
    privileged_group: str
    unprivileged_group: str


# ── Audit ───────────────────────────────────────────────────────────────────


class AuditCreateMeta(BaseModel):
    """JSON metadata sent along with the file upload."""

    model_id: str
    prediction_column: str
    ground_truth_column: str | None = None
    protected_attributes: list[ProtectedAttributeConfig]
    selected_metrics: list[str]


class AuditCreateResponse(BaseModel):
    audit_id: str
    status: str
    created_at: datetime


class FairnessResultResponse(BaseModel):
    metric_name: str
    protected_attribute: str
    privileged_value: float
    unprivileged_value: float
    disparity: float
    threshold: float
    status: str
    confidence_interval_lower: float
    confidence_interval_upper: float
    p_value: float
    sample_size_privileged: int
    sample_size_unprivileged: int
    interpretation: str


class RecommendationResponse(BaseModel):
    priority: str
    issue: str
    mitigation_strategy: str
    mitigation_strategy_enriched: str | None = None
    implementation_effort: str


class AuditDetailResponse(BaseModel):
    audit_id: str
    status: str
    overall_verdict: str | None
    dataset_row_count: int | None
    results: list[FairnessResultResponse]
    recommendations: list[RecommendationResponse]
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    narrative_summary: str | None = None
    groq_enriched: bool = False


class AuditSummary(BaseModel):
    audit_id: str
    model_id: str
    model_name: str
    status: str
    overall_verdict: str | None
    created_at: datetime
    groq_enriched: bool = False


class AuditListResponse(BaseModel):
    audits: list[AuditSummary]
    total: int
    page: int
    per_page: int


# ── Metrics catalog ─────────────────────────────────────────────────────────


class MetricInfo(BaseModel):
    name: str
    display_name: str
    category: str
    description: str
    use_cases: list[str]
    limitations: list[str]
    requires_ground_truth: bool


class MetricCatalogResponse(BaseModel):
    metrics: list[MetricInfo]


# ── Generic ─────────────────────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    error: str
    detail: str
    remediation: str | None = None
