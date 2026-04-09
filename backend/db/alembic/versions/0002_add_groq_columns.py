"""Add Groq enrichment columns

Revision ID: 0002_add_groq_columns
Revises: 0001_initial_schema
Create Date: 2026-04-09
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_add_groq_columns"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "audits",
        sa.Column("narrative_summary", sa.Text(), nullable=True),
    )
    op.add_column(
        "audits",
        sa.Column("groq_enriched", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.add_column(
        "recommendations",
        sa.Column("mitigation_strategy_enriched", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("recommendations", "mitigation_strategy_enriched")
    op.drop_column("audits", "groq_enriched")
    op.drop_column("audits", "narrative_summary")
