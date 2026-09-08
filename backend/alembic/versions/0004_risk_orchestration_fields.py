"""Add multi-layer risk orchestration fields to risk_assessments and category to risk_signals.

Revision ID: 0004_risk_orchestration_fields
Revises: 0003_network_temporal_fields
Create Date: 2026-09-06 23:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_risk_orchestration_fields"
down_revision: str | None = "0003_network_temporal_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add multi-layer composite fields to risk_assessments
    op.add_column(
        "risk_assessments",
        sa.Column("composite_risk_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "risk_assessments",
        sa.Column("confidence_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "risk_assessments",
        sa.Column("entity_risk_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "risk_assessments",
        sa.Column("network_risk_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "risk_assessments",
        sa.Column("behavioral_risk_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "risk_assessments",
        sa.Column("orchestration_version", sa.String(32), nullable=True),
    )
    op.add_column(
        "risk_assessments",
        sa.Column("contribution_breakdown", sa.JSON(), nullable=True),
    )
    op.add_column(
        "risk_assessments",
        sa.Column("explanation_summary", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_risk_assessments_composite_risk_score",
        "risk_assessments",
        ["composite_risk_score"],
        unique=False,
    )

    # 2. Add signal category to risk_signals
    op.add_column(
        "risk_signals",
        sa.Column(
            "category",
            sa.String(32),
            nullable=True,
            server_default="TRANSACTION_SIGNAL",
        ),
    )
    op.create_index(
        "ix_risk_signals_category",
        "risk_signals",
        ["category"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_risk_signals_category", table_name="risk_signals")
    op.drop_column("risk_signals", "category")

    op.drop_index("ix_risk_assessments_composite_risk_score", table_name="risk_assessments")
    op.drop_column("risk_assessments", "explanation_summary")
    op.drop_column("risk_assessments", "contribution_breakdown")
    op.drop_column("risk_assessments", "orchestration_version")
    op.drop_column("risk_assessments", "behavioral_risk_score")
    op.drop_column("risk_assessments", "network_risk_score")
    op.drop_column("risk_assessments", "entity_risk_score")
    op.drop_column("risk_assessments", "confidence_score")
    op.drop_column("risk_assessments", "composite_risk_score")
