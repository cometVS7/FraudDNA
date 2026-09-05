"""FraudDNA Risk Investigation Service.

Orchestrates transaction-level ML risk scoring, Tree SHAP feature attribution (XAI),
FraudDNA relationship graph neighborhood extraction, cluster context lookup, and
deterministic evidence synthesis.
"""

import hashlib
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.graph.models import EntityType, make_node_id, parse_node_id
from app.graph.service import GraphService, get_graph_service
from app.schemas.investigation import (
    ClusterInvestigationSummary,
    EvidenceSeverity,
    EvidenceSource,
    FactorDirection,
    InvestigationEvidence,
    InvestigationResponse,
    InvestigationStatus,
    RelatedEntity,
    RelatedTransaction,
    RiskFactor,
    RiskLevel,
)

logger = logging.getLogger(__name__)


class TransactionNotFoundError(Exception):
    """Raised when an investigated transaction is not found in the graph or dataset."""

    def __init__(self, transaction_id: str) -> None:
        super().__init__(f"Transaction '{transaction_id}' not found.")
        self.transaction_id = transaction_id


class InvestigationService:
    """Coordinates deterministic risk investigation across ML, XAI, Graph, and Clusters."""

    def __init__(
        self,
        graph_service: GraphService | None = None,
        models_dir: str | Path = "ml/models",
    ) -> None:
        self.graph_service = graph_service or get_graph_service()
        self.models_dir = Path(models_dir)

        self._model: Any | None = None
        self._pipeline: Any | None = None
        self._models_loaded: bool = False
        self._investigations_cache: dict[str, InvestigationResponse] = {}

    def _load_ml_components(self) -> None:
        """Load trained LightGBM model and FeaturePipeline artifacts if available."""
        if self._models_loaded:
            return

        if not self.models_dir.exists():
            alt_models = Path("..") / self.models_dir
            if alt_models.exists():
                self.models_dir = alt_models

        # Ensure repo root containing 'ml' is on sys.path
        for candidate in [
            self.models_dir.resolve().parent,
            self.models_dir.resolve().parent.parent,
            Path.cwd(),
            Path.cwd().parent,
        ]:
            if (candidate / "ml").is_dir() and str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
                break

        model_path = self.models_dir / "lightgbm_model.joblib"
        pipeline_path = self.models_dir / "feature_pipeline.joblib"

        if model_path.exists() and pipeline_path.exists():
            try:
                self._model = joblib.load(model_path)
                self._pipeline = joblib.load(pipeline_path)
            except Exception as e:
                logger.error(f"Failed to load ML components for investigation: {e}", exc_info=True)
                self._model = None
                self._pipeline = None
        else:
            logger.warning(f"ML artifacts not found at {self.models_dir}")
            self._model = None
            self._pipeline = None

        self._models_loaded = True

    def investigate(self, transaction_id: str) -> InvestigationResponse:
        """Execute complete structured risk investigation for a given transaction."""
        self.graph_service.initialize()
        self._load_ml_components()

        # Verify transaction existence
        row_dict = self.graph_service.get_transaction_row(transaction_id)
        tx_node = make_node_id(EntityType.TRANSACTION, transaction_id)
        if row_dict is None and tx_node not in self.graph_service.graph:
            raise TransactionNotFoundError(transaction_id)

        # 1. Deterministic Investigation ID
        investigation_id = self._generate_investigation_id(transaction_id)

        # 2. Risk Score & Categorical Level
        risk_score = self._extract_risk_score(transaction_id, row_dict)
        risk_level = self._map_risk_level(risk_score)

        # 3. XAI / SHAP Factor Attribution
        risk_factors, xai_status_ok = self._compute_xai_factors(row_dict)

        # 4. Graph Relationship Traversal (Direct entities & 2-hop transactions)
        related_entities, related_transactions = self._extract_graph_context(transaction_id)

        # 5. Cluster Membership Lookup
        cluster_summary = self._extract_cluster_context(transaction_id)

        # 6. Deterministic Evidence Synthesis
        evidence = self._synthesize_evidence(
            risk_score=risk_score,
            risk_factors=risk_factors,
            related_entities=related_entities,
            related_transactions=related_transactions,
            cluster=cluster_summary,
        )

        # Overall Status
        status = InvestigationStatus.COMPLETED if xai_status_ok else InvestigationStatus.DEGRADED

        response = InvestigationResponse(
            investigation_id=investigation_id,
            transaction_id=transaction_id,
            risk_score=risk_score,
            risk_level=risk_level,
            risk_factors=risk_factors,
            related_entities=related_entities,
            related_transactions=related_transactions,
            cluster=cluster_summary,
            evidence=evidence,
            status=status,
            generated_at=datetime.utcnow(),
        )

        # Cache for retrieval
        self._investigations_cache[investigation_id] = response
        return response

    def get_investigation_by_id(self, investigation_id: str) -> InvestigationResponse | None:
        """Retrieve a previously calculated or cached investigation by its identifier."""
        return self._investigations_cache.get(investigation_id)

    def _generate_investigation_id(self, transaction_id: str) -> str:
        """Generate a deterministic identifier for an investigation."""
        raw = f"{transaction_id}:v1".encode()
        digest = hashlib.sha256(raw).hexdigest()[:16]
        return f"inv_{digest}"

    def _map_risk_level(self, risk_score: float) -> RiskLevel:
        """Map numerical risk score to categorical severity tier."""
        if risk_score < 0.30:
            return RiskLevel.LOW
        if risk_score < 0.70:
            return RiskLevel.MEDIUM
        if risk_score < 0.90:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL

    def _extract_risk_score(self, transaction_id: str, row_dict: dict[str, Any] | None) -> float:
        """Extract risk score from graph node attributes or compute from ML model."""
        tx_node = make_node_id(EntityType.TRANSACTION, transaction_id)
        if tx_node in self.graph_service.graph:
            node_data = self.graph_service.graph.nodes[tx_node]
            if "risk_score" in node_data:
                return float(round(float(node_data["risk_score"]), 4))

        if self._model is not None and self._pipeline is not None and row_dict is not None:
            try:
                df_single = pd.DataFrame([row_dict])
                X_single, _ = self._pipeline.transform(df_single, update_state=False)
                prob = float(self._model.predict_proba(X_single)[:, 1][0])
                return float(round(prob, 4))
            except Exception:
                pass

        return 0.0

    def _compute_xai_factors(
        self, row_dict: dict[str, Any] | None
    ) -> tuple[list[RiskFactor], bool]:
        """Compute LightGBM Tree SHAP feature attributions for the transaction."""
        if self._model is None or self._pipeline is None or row_dict is None:
            return [], False

        try:
            df_single = pd.DataFrame([row_dict])
            X_single, _ = self._pipeline.transform(df_single, update_state=False)

            # Native LightGBM Tree SHAP calculation
            contribs = self._model.booster_.predict(X_single, pred_contrib=True)[0]
            feature_names = self._pipeline.feature_columns

            factors: list[RiskFactor] = []
            # contribs has length len(feature_names) + 1 (last element is base margin / bias)
            scored_features: list[tuple[str, Any, float]] = []
            for i, feat_name in enumerate(feature_names):
                impact = float(contribs[i])
                val = X_single.iloc[0, i] if hasattr(X_single, "iloc") else X_single[0][i]
                if isinstance(val, (np.floating, float)):
                    val = round(float(val), 4)
                elif isinstance(val, (np.integer, int)):
                    val = int(val)
                scored_features.append((feat_name, val, impact))

            # Sort by absolute impact descending
            scored_features.sort(key=lambda item: abs(item[2]), reverse=True)

            for rank, (feat_name, val, impact) in enumerate(scored_features[:5], start=1):
                if impact > 0.001:
                    direction = FactorDirection.INCREASES_RISK
                elif impact < -0.001:
                    direction = FactorDirection.DECREASES_RISK
                else:
                    direction = FactorDirection.NEUTRAL

                factors.append(
                    RiskFactor(
                        feature=feat_name,
                        value=val,
                        impact=round(impact, 4),
                        direction=direction,
                        rank=rank,
                    )
                )

            return factors, True
        except Exception as e:
            print(f"Warning: Tree SHAP computation failed: {e}")
            return [], False

    def _extract_graph_context(
        self, transaction_id: str
    ) -> tuple[list[RelatedEntity], list[RelatedTransaction]]:
        """Extract direct entity neighbors and 2-hop connected transactions from graph."""
        graph = self.graph_service.graph
        tx_node = make_node_id(EntityType.TRANSACTION, transaction_id)

        related_entities: list[RelatedEntity] = []
        related_transactions: list[RelatedTransaction] = []

        if tx_node not in graph:
            return related_entities, related_transactions

        # 1. Direct Neighbor Entities
        direct_neighbors = list(graph.neighbors(tx_node))
        for neighbor in direct_neighbors:
            n_type, _ = parse_node_id(neighbor)
            edge_attrs = graph.edges[tx_node, neighbor]
            rel_type = edge_attrs.get("relationship", f"connected_to_{n_type}")

            # Inspect entity degree and distinct customer connections
            entity_neighbors = list(graph.neighbors(neighbor))
            connected_customers = [
                n for n in entity_neighbors if parse_node_id(n)[0] == EntityType.CUSTOMER.value
            ]
            num_connected_customers = len(connected_customers)

            metadata: dict[str, Any] = {
                "degree": len(entity_neighbors),
                "connected_customers_count": num_connected_customers,
            }

            # Check for cross-customer sharing on bridge nodes
            if n_type in {"device", "ip", "card"} and num_connected_customers > 1:
                metadata["is_shared_across_customers"] = True
                rel_type = f"shared_{n_type}_across_customers"

            related_entities.append(
                RelatedEntity(
                    entity_type=n_type,
                    entity_id=neighbor,
                    relationship=rel_type,
                    metadata=metadata,
                )
            )

        # 2. Two-Hop Related Transactions via Bridge Entities
        seen_tx: set[str] = {tx_node}
        for neighbor in direct_neighbors:
            n_type, _ = parse_node_id(neighbor)
            # Traverse only through bridge entity types and customer nodes
            if n_type not in {"device", "ip", "card", "customer"}:
                continue

            for second_hop in graph.neighbors(neighbor):
                if second_hop in seen_tx:
                    continue
                sh_type, sh_tx_id = parse_node_id(second_hop)
                if sh_type == EntityType.TRANSACTION.value:
                    seen_tx.add(second_hop)
                    sh_attrs = graph.nodes[second_hop]
                    sh_risk = float(round(float(sh_attrs.get("risk_score", 0.0)), 4))
                    sh_amt = float(round(float(sh_attrs.get("amount", 0.0)), 2))
                    sh_ts = str(sh_attrs.get("timestamp", ""))

                    rel_path = f"shared_{n_type}"
                    related_transactions.append(
                        RelatedTransaction(
                            transaction_id=sh_tx_id,
                            timestamp=sh_ts,
                            amount=sh_amt,
                            risk_score=sh_risk,
                            relationship=rel_path,
                        )
                    )

        # Sort related transactions by risk score descending, then amount, and limit to top 20
        related_transactions.sort(key=lambda t: (-t.risk_score, -t.amount))
        return related_entities, related_transactions[:20]

    def _extract_cluster_context(self, transaction_id: str) -> ClusterInvestigationSummary | None:
        """Lookup cluster details for the transaction if present in a cluster."""
        cluster_id = self.graph_service.get_cluster_id_for_transaction(transaction_id)
        if not cluster_id:
            return None

        detail = self.graph_service.get_cluster_by_id(cluster_id)
        if not detail:
            return None

        return ClusterInvestigationSummary(
            cluster_id=detail.cluster_id,
            cluster_risk_score=detail.cluster_risk_score,
            is_suspicious=detail.is_suspicious,
            transaction_count=detail.transaction_count,
            customer_count=detail.customer_count,
            device_count=detail.device_count,
            ip_count=detail.ip_count,
            card_count=detail.card_count,
            suspicious_transaction_count=detail.suspicious_transaction_count,
            primary_reason=detail.primary_reason,
        )

    def _synthesize_evidence(
        self,
        risk_score: float,
        risk_factors: list[RiskFactor],
        related_entities: list[RelatedEntity],
        related_transactions: list[RelatedTransaction],
        cluster: ClusterInvestigationSummary | None,
    ) -> list[InvestigationEvidence]:
        """Synthesize deterministic, verifiable evidence items from all signals."""
        evidence: list[InvestigationEvidence] = []

        # 1. ML Risk Score Evidence
        if risk_score >= 0.90:
            evidence.append(
                InvestigationEvidence(
                    evidence_type="critical_ml_risk",
                    description=(
                        f"Transaction-level ML fraud risk score is critical ({risk_score:.4f} >= 0.90)."
                    ),
                    severity=EvidenceSeverity.CRITICAL,
                    source=EvidenceSource.RISK_MODEL,
                )
            )
        elif risk_score >= 0.70:
            evidence.append(
                InvestigationEvidence(
                    evidence_type="elevated_ml_risk",
                    description=(
                        f"Transaction-level ML fraud risk score is elevated ({risk_score:.4f} >= 0.70)."
                    ),
                    severity=EvidenceSeverity.HIGH,
                    source=EvidenceSource.RISK_MODEL,
                )
            )
        elif risk_score >= 0.37:
            evidence.append(
                InvestigationEvidence(
                    evidence_type="moderate_ml_risk",
                    description=(
                        f"Transaction-level ML fraud risk score exceeds classification threshold ({risk_score:.4f} >= 0.37)."
                    ),
                    severity=EvidenceSeverity.MEDIUM,
                    source=EvidenceSource.RISK_MODEL,
                )
            )
        else:
            evidence.append(
                InvestigationEvidence(
                    evidence_type="baseline_ml_risk",
                    description=(
                        f"Transaction-level ML fraud risk score is low ({risk_score:.4f} < 0.30)."
                    ),
                    severity=EvidenceSeverity.LOW,
                    source=EvidenceSource.RISK_MODEL,
                )
            )

        # 2. XAI / SHAP Evidence
        for factor in risk_factors:
            if factor.impact >= 0.15 and factor.direction == FactorDirection.INCREASES_RISK:
                evidence.append(
                    InvestigationEvidence(
                        evidence_type="xai_primary_risk_driver",
                        description=(
                            f"Model feature '{factor.feature}' significantly increased risk "
                            f"(impact: +{factor.impact:.4f}, observed value: {factor.value})."
                        ),
                        severity=EvidenceSeverity.HIGH,
                        source=EvidenceSource.SHAP,
                    )
                )

        # 3. FraudDNA Graph Coordination Evidence
        for entity in related_entities:
            cust_count = int(entity.metadata.get("connected_customers_count", 0))
            if cust_count > 1:
                if entity.entity_type == "device":
                    evidence.append(
                        InvestigationEvidence(
                            evidence_type="shared_device_collusion",
                            description=(
                                f"Hardware device '{entity.entity_id}' is shared across "
                                f"{cust_count} distinct customer accounts."
                            ),
                            severity=EvidenceSeverity.HIGH,
                            source=EvidenceSource.FRAUDDNA_GRAPH,
                        )
                    )
                elif entity.entity_type == "ip":
                    evidence.append(
                        InvestigationEvidence(
                            evidence_type="shared_ip_address",
                            description=(
                                f"IP address '{entity.entity_id}' is shared across "
                                f"{cust_count} distinct customer accounts."
                            ),
                            severity=EvidenceSeverity.HIGH
                            if cust_count >= 5
                            else EvidenceSeverity.MEDIUM,
                            source=EvidenceSource.FRAUDDNA_GRAPH,
                        )
                    )
                elif entity.entity_type == "card":
                    evidence.append(
                        InvestigationEvidence(
                            evidence_type="shared_payment_instrument",
                            description=(
                                f"Payment instrument '{entity.entity_id}' is shared across "
                                f"{cust_count} distinct customer accounts."
                            ),
                            severity=EvidenceSeverity.HIGH,
                            source=EvidenceSource.FRAUDDNA_GRAPH,
                        )
                    )

        # 4. Cluster Evidence
        if cluster is not None:
            if cluster.is_suspicious:
                evidence.append(
                    InvestigationEvidence(
                        evidence_type="suspicious_cluster_membership",
                        description=(
                            f"Transaction is a member of suspicious FraudDNA cluster '{cluster.cluster_id}' "
                            f"(score: {cluster.cluster_risk_score:.4f}, {cluster.transaction_count} txs, "
                            f"{cluster.customer_count} accounts). Reason: {cluster.primary_reason}"
                        ),
                        severity=(
                            EvidenceSeverity.CRITICAL
                            if cluster.cluster_risk_score >= 0.90
                            else EvidenceSeverity.HIGH
                        ),
                        source=EvidenceSource.FRAUDDNA_CLUSTER,
                    )
                )
            else:
                evidence.append(
                    InvestigationEvidence(
                        evidence_type="legitimate_cluster_membership",
                        description=(
                            f"Transaction is part of standard connected component '{cluster.cluster_id}' "
                            f"(score: {cluster.cluster_risk_score:.4f}, {cluster.transaction_count} txs)."
                        ),
                        severity=EvidenceSeverity.LOW,
                        source=EvidenceSource.FRAUDDNA_CLUSTER,
                    )
                )

        # 5. Connected High-Risk Transactions Evidence
        high_risk_related = [t for t in related_transactions if t.risk_score >= 0.70]
        if high_risk_related:
            evidence.append(
                InvestigationEvidence(
                    evidence_type="high_risk_related_transactions",
                    description=(
                        f"Discovered {len(high_risk_related)} high-risk connected transaction(s) "
                        f"(score >= 0.70) sharing graph entities with this transaction."
                    ),
                    severity=EvidenceSeverity.HIGH,
                    source=EvidenceSource.FRAUDDNA_GRAPH,
                )
            )

        return evidence


# Global Singleton Instance
_investigation_service_instance: InvestigationService | None = None


def get_investigation_service() -> InvestigationService:
    """Dependency provider for InvestigationService singleton."""
    global _investigation_service_instance
    if _investigation_service_instance is None:
        _investigation_service_instance = InvestigationService()
    return _investigation_service_instance
