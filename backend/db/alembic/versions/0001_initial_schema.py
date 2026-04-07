"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-07
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("api_key", sa.String(length=60), nullable=False),
        sa.Column("role", sa.Enum("admin", "analyst", "viewer", name="user_role"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("api_key"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_api_key", "users", ["api_key"])

    op.create_table(
        "models",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "use_case",
            sa.Enum(
                "credit_approval",
                "fraud_detection",
                "underwriting",
                "insurance",
                "other",
                name="model_use_case",
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "audits",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("model_id", sa.String(length=36), sa.ForeignKey("models.id"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("queued", "processing", "completed", "failed", name="audit_status"),
            nullable=False,
        ),
        sa.Column(
            "overall_verdict",
            sa.Enum("PASS", "CONDITIONAL_PASS", "FAIL", name="audit_verdict"),
            nullable=True,
        ),
        sa.Column("dataset_row_count", sa.Integer(), nullable=True),
        sa.Column("protected_attributes", sa.JSON(), nullable=False),
        sa.Column("selected_metrics", sa.JSON(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("ground_truth_column", sa.String(length=255), nullable=True),
        sa.Column("prediction_column", sa.String(length=255), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "fairness_results",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("audit_id", sa.String(length=36), sa.ForeignKey("audits.id"), nullable=False),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("protected_attribute", sa.String(length=255), nullable=False),
        sa.Column("privileged_value", sa.Float(), nullable=False),
        sa.Column("unprivileged_value", sa.Float(), nullable=False),
        sa.Column("disparity", sa.Float(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("status", sa.Enum("PASS", "FAIL", name="result_status"), nullable=False),
        sa.Column("confidence_interval_lower", sa.Float(), nullable=False),
        sa.Column("confidence_interval_upper", sa.Float(), nullable=False),
        sa.Column("p_value", sa.Float(), nullable=False),
        sa.Column("sample_size_privileged", sa.Integer(), nullable=False),
        sa.Column("sample_size_unprivileged", sa.Integer(), nullable=False),
        sa.Column("interpretation", sa.Text(), nullable=False),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("audit_id", sa.String(length=36), sa.ForeignKey("audits.id"), nullable=False),
        sa.Column(
            "priority",
            sa.Enum("high", "medium", "low", name="recommendation_priority"),
            nullable=False,
        ),
        sa.Column("issue", sa.Text(), nullable=False),
        sa.Column("mitigation_strategy", sa.Text(), nullable=False),
        sa.Column(
            "implementation_effort",
            sa.Enum("low", "medium", "high", name="implementation_effort"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("resource_id", sa.String(length=36), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_table("recommendations")
    op.drop_table("fairness_results")
    op.drop_table("audits")
    op.drop_table("models")
    op.drop_index("ix_users_api_key", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
