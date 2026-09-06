"""Add first_seen and last_seen temporal fields to risk_networks table.

Revision ID: 0003_network_temporal_fields
Revises: 0002_v2_domain_schema
Create Date: 2026-09-06 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_network_temporal_fields"
down_revision: str | None = "0002_v2_domain_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "risk_networks",
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "risk_networks",
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("risk_networks", "last_seen")
    op.drop_column("risk_networks", "first_seen")
