"""SQLAlchemy ORM models for all six FairLens entities."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── User ────────────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(
        Enum("admin", "analyst", "viewer", name="user_role"),
        default="analyst",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    models: Mapped[list["Model"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    audits: Mapped[list["Audit"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


# ── Model ───────────────────────────────────────────────────────────────────


class Model(Base):
    __tablename__ = "models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    use_case: Mapped[str] = mapped_column(
        Enum(
            "credit_approval",
            "fraud_detection",
            "underwriting",
            "insurance",
            "other",
            name="model_use_case",
        ),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    owner: Mapped["User"] = relationship(back_populates="models")
    audits: Mapped[list["Audit"]] = relationship(
        back_populates="model", cascade="all, delete-orphan"
    )


# ── Audit ───────────────────────────────────────────────────────────────────


class Audit(Base):
    __tablename__ = "audits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    model_id: Mapped[str] = mapped_column(String(36), ForeignKey("models.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("queued", "processing", "completed", "failed", name="audit_status"),
        default="queued",
        nullable=False,
    )
    overall_verdict: Mapped[str | None] = mapped_column(
        Enum("PASS", "CONDITIONAL_PASS", "FAIL", name="audit_verdict"),
        nullable=True,
    )
    dataset_row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protected_attributes: Mapped[dict] = mapped_column(JSON, nullable=False)
    selected_metrics: Mapped[list] = mapped_column(JSON, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    ground_truth_column: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prediction_column: Mapped[str] = mapped_column(String(255), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    narrative_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    groq_enriched: Mapped[bool] = mapped_column(default=False, nullable=False)

    model: Mapped["Model"] = relationship(back_populates="audits")
    user: Mapped["User"] = relationship(back_populates="audits")
    results: Mapped[list["FairnessResult"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )


# ── FairnessResult ──────────────────────────────────────────────────────────


class FairnessResult(Base):
    __tablename__ = "fairness_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    audit_id: Mapped[str] = mapped_column(String(36), ForeignKey("audits.id"), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    protected_attribute: Mapped[str] = mapped_column(String(255), nullable=False)
    privileged_value: Mapped[float] = mapped_column(Float, nullable=False)
    unprivileged_value: Mapped[float] = mapped_column(Float, nullable=False)
    disparity: Mapped[float] = mapped_column(Float, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(Enum("PASS", "FAIL", name="result_status"), nullable=False)
    confidence_interval_lower: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_interval_upper: Mapped[float] = mapped_column(Float, nullable=False)
    p_value: Mapped[float] = mapped_column(Float, nullable=False)
    sample_size_privileged: Mapped[int] = mapped_column(Integer, nullable=False)
    sample_size_unprivileged: Mapped[int] = mapped_column(Integer, nullable=False)
    interpretation: Mapped[str] = mapped_column(Text, nullable=False)

    audit: Mapped["Audit"] = relationship(back_populates="results")


# ── Recommendation ──────────────────────────────────────────────────────────


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    audit_id: Mapped[str] = mapped_column(String(36), ForeignKey("audits.id"), nullable=False)
    priority: Mapped[str] = mapped_column(
        Enum("high", "medium", "low", name="recommendation_priority"), nullable=False
    )
    issue: Mapped[str] = mapped_column(Text, nullable=False)
    mitigation_strategy: Mapped[str] = mapped_column(Text, nullable=False)
    implementation_effort: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", name="implementation_effort"), nullable=False
    )
    mitigation_strategy_enriched: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    audit: Mapped["Audit"] = relationship(back_populates="recommendations")


# ── AuditLog ────────────────────────────────────────────────────────────────


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
