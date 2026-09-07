"""Create FraudDNA V2 persistent relational domain schema.

Revision ID: 0002_v2_domain_schema
Revises: 0001_rag_tables
Create Date: 2026-09-06 17:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_v2_domain_schema"
down_revision: str | None = "0001_rag_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. customers
    op.create_table(
        "customers",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("account_age_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("risk_tier", sa.String(length=32), nullable=False, server_default="LOW"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_customers_created_at", "customers", ["created_at"])
    op.create_index("ix_customers_status", "customers", ["status"])
    op.create_index("ix_customers_risk_score", "customers", ["risk_score"])

    # 2. accounts
    op.create_table(
        "accounts",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "customer_id",
            sa.String(length=64),
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("account_type", sa.String(length=32), nullable=False, server_default="SAVINGS"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("risk_tier", sa.String(length=32), nullable=False, server_default="LOW"),
    )
    op.create_index("ix_accounts_customer_id", "accounts", ["customer_id"])
    op.create_index("ix_accounts_status", "accounts", ["status"])

    # 3. cards
    op.create_table(
        "cards",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("card_type", sa.String(length=32), nullable=False, server_default="CREDIT"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column(
            "first_seen",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_seen",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("risk_tier", sa.String(length=32), nullable=False, server_default="LOW"),
    )
    op.create_index("ix_cards_first_seen", "cards", ["first_seen"])
    op.create_index("ix_cards_risk_score", "cards", ["risk_score"])
    op.create_index("ix_cards_status", "cards", ["status"])

    # 4. devices
    op.create_table(
        "devices",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("device_fingerprint", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column(
            "first_seen",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_seen",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("risk_tier", sa.String(length=32), nullable=False, server_default="LOW"),
    )
    op.create_index("ix_devices_first_seen", "devices", ["first_seen"])
    op.create_index("ix_devices_risk_score", "devices", ["risk_score"])
    op.create_index("ix_devices_status", "devices", ["status"])

    # 5. ip_addresses
    op.create_table(
        "ip_addresses",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("ip_address", sa.String(length=64), nullable=False, unique=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column(
            "first_seen",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_seen",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("risk_tier", sa.String(length=32), nullable=False, server_default="LOW"),
    )
    op.create_index("ix_ip_addresses_ip_address", "ip_addresses", ["ip_address"])
    op.create_index("ix_ip_addresses_first_seen", "ip_addresses", ["first_seen"])
    op.create_index("ix_ip_addresses_risk_score", "ip_addresses", ["risk_score"])
    op.create_index("ix_ip_addresses_status", "ip_addresses", ["status"])

    # 6. merchants
    op.create_table(
        "merchants",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("merchant_category", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("risk_tier", sa.String(length=32), nullable=False, server_default="LOW"),
    )
    op.create_index("ix_merchants_merchant_category", "merchants", ["merchant_category"])
    op.create_index("ix_merchants_status", "merchants", ["status"])
    op.create_index("ix_merchants_risk_score", "merchants", ["risk_score"])

    # 7. risk_networks
    op.create_table(
        "risk_networks",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("network_name", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_suspicious", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("primary_reason", sa.String(length=255), nullable=True),
        sa.Column("transaction_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("customer_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("device_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("card_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ip_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("merchant_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_risk_networks_risk_score", "risk_networks", ["risk_score"])
    op.create_index("ix_risk_networks_is_suspicious", "risk_networks", ["is_suspicious"])
    op.create_index("ix_risk_networks_status", "risk_networks", ["status"])

    # 8. transactions
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("payment_method", sa.String(length=32), nullable=False),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("is_fraud", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "fraud_scenario",
            sa.String(length=64),
            nullable=False,
            server_default="legitimate",
        ),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("risk_tier", sa.String(length=32), nullable=False, server_default="LOW"),
        sa.Column("decision_action", sa.String(length=16), nullable=True),
        sa.Column(
            "customer_id",
            sa.String(length=64),
            sa.ForeignKey("customers.id"),
            nullable=False,
        ),
        sa.Column(
            "account_id",
            sa.String(length=64),
            sa.ForeignKey("accounts.id"),
            nullable=True,
        ),
        sa.Column(
            "card_id",
            sa.String(length=64),
            sa.ForeignKey("cards.id"),
            nullable=True,
        ),
        sa.Column(
            "device_id",
            sa.String(length=64),
            sa.ForeignKey("devices.id"),
            nullable=True,
        ),
        sa.Column(
            "ip_id",
            sa.String(length=64),
            sa.ForeignKey("ip_addresses.id"),
            nullable=True,
        ),
        sa.Column(
            "merchant_id",
            sa.String(length=64),
            sa.ForeignKey("merchants.id"),
            nullable=False,
        ),
        sa.Column(
            "network_id",
            sa.String(length=64),
            sa.ForeignKey("risk_networks.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_transactions_timestamp", "transactions", ["timestamp"])
    op.create_index("ix_transactions_customer_id", "transactions", ["customer_id"])
    op.create_index("ix_transactions_account_id", "transactions", ["account_id"])
    op.create_index("ix_transactions_card_id", "transactions", ["card_id"])
    op.create_index("ix_transactions_device_id", "transactions", ["device_id"])
    op.create_index("ix_transactions_ip_id", "transactions", ["ip_id"])
    op.create_index("ix_transactions_merchant_id", "transactions", ["merchant_id"])
    op.create_index("ix_transactions_network_id", "transactions", ["network_id"])
    op.create_index("ix_transactions_risk_score", "transactions", ["risk_score"])
    op.create_index("ix_transactions_risk_tier", "transactions", ["risk_tier"])
    op.create_index("ix_transactions_is_fraud", "transactions", ["is_fraud"])
    op.create_index("ix_transactions_decision_action", "transactions", ["decision_action"])
    op.create_index(
        "ix_transactions_customer_timestamp",
        "transactions",
        ["customer_id", "timestamp"],
    )
    op.create_index(
        "ix_transactions_device_timestamp",
        "transactions",
        ["device_id", "timestamp"],
    )
    op.create_index(
        "ix_transactions_card_timestamp",
        "transactions",
        ["card_id", "timestamp"],
    )
    op.create_index(
        "ix_transactions_risk_timestamp",
        "transactions",
        ["risk_score", "timestamp"],
    )

    # 9. models
    op.create_table(
        "models",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("model_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("operating_threshold", sa.Float(), nullable=False, server_default="0.37"),
        sa.Column("feature_names", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("feature_count", sa.Integer(), nullable=False, server_default="18"),
        sa.Column("metrics", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("artifact_path", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_models_status", "models", ["status"])

    # 10. risk_assessments
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "transaction_id",
            sa.String(length=64),
            sa.ForeignKey("transactions.id"),
            nullable=False,
        ),
        sa.Column(
            "model_id",
            sa.String(length=64),
            sa.ForeignKey("models.id"),
            nullable=True,
        ),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_tier", sa.String(length=32), nullable=False),
        sa.Column("feature_version", sa.String(length=32), nullable=False, server_default="v1.0"),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_risk_assessments_transaction_id", "risk_assessments", ["transaction_id"])
    op.create_index("ix_risk_assessments_risk_score", "risk_assessments", ["risk_score"])
    op.create_index("ix_risk_assessments_generated_at", "risk_assessments", ["generated_at"])

    # 11. risk_signals
    op.create_table(
        "risk_signals",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "assessment_id",
            sa.String(length=64),
            sa.ForeignKey("risk_assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("feature_name", sa.String(length=64), nullable=False),
        sa.Column("feature_value", sa.Float(), nullable=False),
        sa.Column("impact", sa.Float(), nullable=False),
        sa.Column("direction", sa.String(length=32), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_risk_signals_assessment_id", "risk_signals", ["assessment_id"])
    op.create_index("ix_risk_signals_feature_name", "risk_signals", ["feature_name"])

    # 12. policies
    op.create_table(
        "policies",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("policy_name", sa.String(length=128), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False, unique=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("rules_config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "effective_from",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_policies_status", "policies", ["status"])

    # 13. decisions
    op.create_table(
        "decisions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "transaction_id",
            sa.String(length=64),
            sa.ForeignKey("transactions.id"),
            nullable=False,
        ),
        sa.Column(
            "policy_id",
            sa.String(length=64),
            sa.ForeignKey("policies.id"),
            nullable=True,
        ),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("reason_codes", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("evidence_summary", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("is_deterministic", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_decisions_transaction_id", "decisions", ["transaction_id"])
    op.create_index("ix_decisions_action", "decisions", ["action"])
    op.create_index("ix_decisions_generated_at", "decisions", ["generated_at"])

    # 14. cases
    op.create_table(
        "cases",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="NEW"),
        sa.Column("priority", sa.String(length=16), nullable=False, server_default="MEDIUM"),
        sa.Column("owner", sa.String(length=128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_cases_status", "cases", ["status"])
    op.create_index("ix_cases_priority", "cases", ["priority"])
    op.create_index("ix_cases_owner", "cases", ["owner"])
    op.create_index("ix_cases_created_at", "cases", ["created_at"])

    # 15. investigations
    op.create_table(
        "investigations",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="OPEN"),
        sa.Column("priority", sa.String(length=16), nullable=False, server_default="MEDIUM"),
        sa.Column(
            "trigger_type",
            sa.String(length=64),
            nullable=False,
            server_default="TRANSACTION_RISK",
        ),
        sa.Column(
            "primary_transaction_id",
            sa.String(length=64),
            sa.ForeignKey("transactions.id"),
            nullable=False,
        ),
        sa.Column(
            "primary_network_id",
            sa.String(length=64),
            sa.ForeignKey("risk_networks.id"),
            nullable=True,
        ),
        sa.Column(
            "case_id",
            sa.String(length=64),
            sa.ForeignKey("cases.id"),
            nullable=True,
        ),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("risk_level", sa.String(length=32), nullable=False, server_default="LOW"),
        sa.Column("assigned_to", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_investigations_status", "investigations", ["status"])
    op.create_index("ix_investigations_priority", "investigations", ["priority"])
    op.create_index("ix_investigations_primary_tx", "investigations", ["primary_transaction_id"])
    op.create_index("ix_investigations_primary_network", "investigations", ["primary_network_id"])
    op.create_index("ix_investigations_case_id", "investigations", ["case_id"])
    op.create_index("ix_investigations_created_at", "investigations", ["created_at"])

    # 16. evidence
    op.create_table(
        "evidence",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "investigation_id",
            sa.String(length=64),
            sa.ForeignKey("investigations.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "case_id",
            sa.String(length=64),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="LOW"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_evidence_investigation_id", "evidence", ["investigation_id"])
    op.create_index("ix_evidence_case_id", "evidence", ["case_id"])
    op.create_index("ix_evidence_evidence_type", "evidence", ["evidence_type"])

    # 17. ai_findings
    op.create_table(
        "ai_findings",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "investigation_id",
            sa.String(length=64),
            sa.ForeignKey("investigations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("finding_type", sa.String(length=64), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("agent_version", sa.String(length=32), nullable=False, server_default="1.0.0"),
        sa.Column("tool_trace_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("limitations", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_ai_findings_investigation_id", "ai_findings", ["investigation_id"])

    # 18. intelligence_sources
    op.create_table(
        "intelligence_sources",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False, server_default="1.0"),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("source_path", sa.String(length=512), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_intel_sources_type", "intelligence_sources", ["source_type"])

    # 19. audit_events
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("actor", sa.String(length=128), nullable=False, server_default="system"),
        sa.Column("actor_type", sa.String(length=32), nullable=False, server_default="SERVICE"),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("previous_hash", sa.String(length=64), nullable=True),
        sa.Column("event_hash", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_audit_events_timestamp", "audit_events", ["timestamp"])
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_events_entity_type", "audit_events", ["entity_type"])
    op.create_index("ix_audit_events_entity_id", "audit_events", ["entity_id"])


def downgrade() -> None:
    # Drop tables in reverse order of creation to satisfy foreign key constraints
    op.drop_table("audit_events")
    op.drop_table("intelligence_sources")
    op.drop_table("ai_findings")
    op.drop_table("evidence")
    op.drop_table("investigations")
    op.drop_table("cases")
    op.drop_table("decisions")
    op.drop_table("policies")
    op.drop_table("risk_signals")
    op.drop_table("risk_assessments")
    op.drop_table("models")
    op.drop_table("transactions")
    op.drop_table("risk_networks")
    op.drop_table("merchants")
    op.drop_table("ip_addresses")
    op.drop_table("devices")
    op.drop_table("cards")
    op.drop_table("accounts")
    op.drop_table("customers")
