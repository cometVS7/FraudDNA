"""FraudDNA Deterministic Policy Engine.

Evaluates multi-signal transaction context (ML, XAI, Graph, Cluster, RAG)
against deterministic rules to produce audit-grade ALLOW / REVIEW / HOLD decisions.
"""

import hashlib
import logging
from datetime import datetime

from app.core.config import settings
from app.graph.models import EntityType, make_node_id
from app.graph.service import GraphService, get_graph_service
from app.policy.models import PolicyDecision
from app.policy.rules import evaluate_policy_rules
from app.rag.retrieval import RAGService
from app.schemas.investigation import InvestigationResponse
from app.services.investigation import (
    InvestigationService,
    TransactionNotFoundError,
    get_investigation_service,
)

logger = logging.getLogger(__name__)


class PolicyEngine:
    """Executes deterministic policy rules without LLM randomness or external side effects."""

    def __init__(
        self,
        investigation_service: InvestigationService | None = None,
        graph_service: GraphService | None = None,
        rag_service: RAGService | None = None,
        policy_version: str | None = None,
    ) -> None:
        self.investigation_service = investigation_service or get_investigation_service()
        self.graph_service = graph_service or get_graph_service()
        self.rag_service = rag_service or RAGService()
        self.policy_version = policy_version or settings.POLICY_VERSION

    def evaluate_transaction(
        self,
        transaction_id: str,
        risk_score_override: float | None = None,
    ) -> PolicyDecision:
        """Evaluate a transaction deterministically against the policy matrix."""
        self.graph_service.initialize()

        # 1. Transaction existence check
        row_dict = self.graph_service.get_transaction_row(transaction_id)
        tx_node = make_node_id(EntityType.TRANSACTION, transaction_id)
        if row_dict is None and tx_node not in self.graph_service.graph:
            raise TransactionNotFoundError(transaction_id)

        # 2. Extract Phase 3 deterministic investigation context
        inv: InvestigationResponse = self.investigation_service.investigate(transaction_id)
        risk_score = risk_score_override if risk_score_override is not None else inv.risk_score

        # 3. Cluster metrics
        is_suspicious_cluster = False
        cluster_risk_score = 0.0
        cluster_id = None
        if inv.cluster is not None:
            cluster_id = inv.cluster.cluster_id
            is_suspicious_cluster = inv.cluster.is_suspicious
            cluster_risk_score = inv.cluster.cluster_risk_score

        # 4. Count shared cross-customer hardware devices, IPs, and cards
        shared_devices = 0
        shared_ips = 0
        shared_cards = 0

        for entity in inv.related_entities:
            cust_count = int(entity.metadata.get("connected_customers_count", 0))
            if cust_count > 1:
                if entity.entity_type == "device":
                    shared_devices += cust_count
                elif entity.entity_type == "ip":
                    shared_ips += cust_count
                elif entity.entity_type == "card":
                    shared_cards += cust_count

        # 5. Check RAG store status
        rag_status = "active"
        try:
            status_resp = self.rag_service.get_status()
            rag_status = status_resp.mode
        except Exception:
            rag_status = "unavailable"

        # 6. Evaluate pure deterministic rules
        action, reason_codes, evidence_summary = evaluate_policy_rules(
            risk_score=risk_score,
            is_suspicious_cluster=is_suspicious_cluster,
            cluster_risk_score=cluster_risk_score,
            cluster_id=cluster_id,
            shared_device_count=shared_devices,
            shared_ip_count=shared_ips,
            shared_card_count=shared_cards,
            rag_status=rag_status,
            investigation_status=inv.status.value,
        )

        # 7. Generate deterministic decision ID
        raw = f"{transaction_id}:{risk_score:.4f}:{self.policy_version}:{action.value}".encode()
        decision_id = f"dec_{hashlib.sha256(raw).hexdigest()[:16]}"

        return PolicyDecision(
            decision_id=decision_id,
            transaction_id=transaction_id,
            action=action,
            reason_codes=reason_codes,
            risk_score=round(risk_score, 4),
            risk_level=inv.risk_level.value,
            cluster_id=cluster_id,
            policy_version=self.policy_version,
            evidence_summary=evidence_summary,
            created_at=datetime.utcnow(),
            is_deterministic=True,
        )
