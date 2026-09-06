"""FraudDNA Risk Network Intelligence Application Service.

Coordinates multi-hop pathfinding, syndicate pattern detection, risk propagation,
exposure profiling, temporal timelines, and machine-readable evidence findings.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundDomainError, ValidationDomainError
from app.graph.network_analytics import NetworkAnalyticsEngine
from app.graph.paths import PathIntelligenceEngine
from app.graph.syndicate import SyndicateDetector
from app.models.domain import TransactionModel
from app.repositories.entity_repository import EntityRepository
from app.repositories.network_repository import NetworkRepository
from app.schemas.network_intelligence import (
    EntityNetworkIntelligenceResponse,
    NetworkExposure,
    NetworkFinding,
    NetworkIntelligenceResponse,
    NetworkPath,
    NetworkTimeline,
    PathSearchResponse,
    SyndicatePattern,
)

logger = logging.getLogger(__name__)


class NetworkIntelligenceService:
    """Application service for deep risk network intelligence and syndicate analytics."""

    def __init__(
        self,
        network_repo: NetworkRepository | None = None,
        entity_repo: EntityRepository | None = None,
        analytics_engine: NetworkAnalyticsEngine | None = None,
        syndicate_detector: SyndicateDetector | None = None,
        path_engine: PathIntelligenceEngine | None = None,
    ) -> None:
        self.network_repo = network_repo or NetworkRepository()
        self.entity_repo = entity_repo or EntityRepository()
        self.analytics_engine = analytics_engine or NetworkAnalyticsEngine()
        self.syndicate_detector = syndicate_detector or SyndicateDetector()
        self.path_engine = path_engine or PathIntelligenceEngine()

    def get_network_intelligence(
        self,
        session: Session,
        network_id: str,
        as_of: datetime | None = None,
        max_nodes: int = 100,
        max_transactions: int = 100,
    ) -> NetworkIntelligenceResponse:
        """Generate comprehensive intelligence package for a risk network."""
        net = self.network_repo.get_by_id(session, network_id)
        if not net:
            raise NotFoundDomainError(
                f"Risk network '{network_id}' not found.",
                details={"network_id": network_id},
            )

        # 1. Fetch member transactions and entities with temporal filtering
        txs, _ = self.network_repo.get_network_transactions(
            session=session,
            network_id=network_id,
            limit=max_transactions,
            offset=0,
        )
        if as_of is not None:
            txs = [t for t in txs if t.timestamp <= as_of]

        member_entities = self.network_repo.get_network_member_entities(session, network_id)

        # 2. Build bounded network graph
        subgraph = self.network_repo.get_network_graph(
            session=session,
            network_id=network_id,
            max_nodes=max_nodes,
            max_transactions=max_transactions,
        )

        # 3. Compute Analytics
        exposure = self.analytics_engine.compute_network_exposure(
            network_id=network_id,
            transactions=txs,
            member_entities=member_entities,
        )
        topology = self.analytics_engine.compute_network_topology_metrics(
            graph_data=subgraph,
            member_entities=member_entities,
        )
        timeline = self.analytics_engine.compute_temporal_timeline(
            network_id=network_id,
            transactions=txs,
            as_of=as_of,
        )
        propagated_score, risk_tier, confidence = (
            self.analytics_engine.calculate_propagated_network_risk(
                exposure=exposure,
                topology=topology,
                timeline=timeline,
                transactions=txs,
            )
        )

        # 4. Detect Syndicate Attack Patterns
        patterns = self.syndicate_detector.evaluate_syndicate_patterns(
            transactions=txs,
            member_entities=member_entities,
            graph_data=subgraph,
            as_of=as_of,
        )

        # 5. Extract Key Network Connection Paths
        key_paths = self.path_engine.extract_key_network_paths(
            graph_data=subgraph,
            max_paths=5,
        )

        # 6. Synthesize Structured Findings
        findings = self.analytics_engine.synthesize_network_findings(
            network_id=network_id,
            exposure=exposure,
            patterns=patterns,
            propagated_score=propagated_score,
            tier=risk_tier,
            transactions=txs,
            member_entities=member_entities,
        )

        return NetworkIntelligenceResponse(
            network_id=net.id,
            network_name=net.network_name or f"Coordinated Fraud Syndicate {net.id}",
            status=net.status,
            is_suspicious=net.is_suspicious,
            primary_reason=net.primary_reason or "Detected risk network",
            propagated_risk_score=propagated_score,
            risk_tier=risk_tier,
            confidence_score=confidence,
            exposure=exposure,
            topology=topology,
            patterns=patterns,
            key_paths=key_paths,
            timeline=timeline,
            findings=findings,
            subgraph=subgraph,
            as_of=as_of,
        )

    def get_network_paths(
        self,
        session: Session,
        network_id: str,
        source_id: str | None = None,
        target_id: str | None = None,
        max_depth: int = 3,
        max_paths: int = 10,
    ) -> list[NetworkPath]:
        """Discover ranked connection paths within a network subgraph."""
        net = self.network_repo.get_by_id(session, network_id)
        if not net:
            raise NotFoundDomainError(
                f"Risk network '{network_id}' not found.",
                details={"network_id": network_id},
            )

        subgraph = self.network_repo.get_network_graph(
            session=session,
            network_id=network_id,
            max_nodes=200,
            max_transactions=150,
        )

        if source_id and target_id:
            return self.path_engine.find_paths_between_entities(
                graph_data=subgraph,
                source_id=source_id,
                target_id=target_id,
                max_depth=max_depth,
                max_paths=max_paths,
            )

        return self.path_engine.extract_key_network_paths(
            graph_data=subgraph,
            max_paths=max_paths,
        )

    def find_paths_between_entities(
        self,
        session: Session,
        source_id: str,
        target_id: str,
        source_type: str = "customer",
        target_type: str = "customer",
        max_depth: int = 3,
        max_paths: int = 10,
    ) -> PathSearchResponse:
        """Find connection paths between two arbitrary entities across the graph."""
        if max_depth < 1 or max_depth > 4:
            raise ValidationDomainError(
                f"Search depth must be between 1 and 4. Requested: {max_depth}",
                details={"max_depth": max_depth},
            )

        # Retrieve bounded neighborhood around source entity
        source_graph = self.entity_repo.get_bounded_neighborhood(
            session=session,
            entity_type=source_type,
            entity_id=source_id,
            depth=min(max_depth, 3),
            max_nodes=250,
            max_transactions=200,
        )

        paths = self.path_engine.find_paths_between_entities(
            graph_data=source_graph,
            source_id=f"{source_type.lower()}:{source_id}",
            target_id=f"{target_type.lower()}:{target_id}",
            max_depth=max_depth,
            max_paths=max_paths,
        )

        return PathSearchResponse(
            source_id=source_id,
            target_id=target_id,
            paths_found=len(paths),
            paths=paths,
        )

    def get_network_timeline(
        self,
        session: Session,
        network_id: str,
        as_of: datetime | None = None,
    ) -> NetworkTimeline:
        """Retrieve temporal activity timeline for a risk network."""
        net = self.network_repo.get_by_id(session, network_id)
        if not net:
            raise NotFoundDomainError(
                f"Risk network '{network_id}' not found.",
                details={"network_id": network_id},
            )

        txs, _ = self.network_repo.get_network_transactions(session, network_id, limit=250)
        return self.analytics_engine.compute_temporal_timeline(
            network_id=network_id, transactions=txs, as_of=as_of
        )

    def get_network_exposure(
        self,
        session: Session,
        network_id: str,
        as_of: datetime | None = None,
    ) -> NetworkExposure:
        """Retrieve financial and entity exposure metrics for a risk network."""
        net = self.network_repo.get_by_id(session, network_id)
        if not net:
            raise NotFoundDomainError(
                f"Risk network '{network_id}' not found.",
                details={"network_id": network_id},
            )

        txs, _ = self.network_repo.get_network_transactions(session, network_id, limit=250)
        if as_of is not None:
            txs = [t for t in txs if t.timestamp <= as_of]
        member_entities = self.network_repo.get_network_member_entities(session, network_id)
        return self.analytics_engine.compute_network_exposure(
            network_id=network_id, transactions=txs, member_entities=member_entities
        )

    def get_network_patterns(
        self,
        session: Session,
        network_id: str,
        as_of: datetime | None = None,
    ) -> list[SyndicatePattern]:
        """Retrieve detected attack patterns for a risk network."""
        net = self.network_repo.get_by_id(session, network_id)
        if not net:
            raise NotFoundDomainError(
                f"Risk network '{network_id}' not found.",
                details={"network_id": network_id},
            )

        txs, _ = self.network_repo.get_network_transactions(session, network_id, limit=250)
        member_entities = self.network_repo.get_network_member_entities(session, network_id)
        subgraph = self.network_repo.get_network_graph(session, network_id, max_nodes=200)

        return self.syndicate_detector.evaluate_syndicate_patterns(
            transactions=txs,
            member_entities=member_entities,
            graph_data=subgraph,
            as_of=as_of,
        )

    def get_network_findings(
        self,
        session: Session,
        network_id: str,
        as_of: datetime | None = None,
    ) -> list[NetworkFinding]:
        """Retrieve structured machine-readable findings for a risk network."""
        intel = self.get_network_intelligence(session=session, network_id=network_id, as_of=as_of)
        return intel.findings

    def get_entity_network_intelligence(
        self,
        session: Session,
        entity_type: str,
        entity_id: str,
        as_of: datetime | None = None,
    ) -> EntityNetworkIntelligenceResponse:
        """Retrieve risk network context for a specific entity."""
        # Find affiliated networks
        cond = self.entity_repo._get_entity_tx_filter(entity_type, entity_id)
        stmt = (
            select(TransactionModel.network_id)
            .where(cond, TransactionModel.network_id.is_not(None))
            .distinct()
        )
        if as_of is not None:
            stmt = stmt.where(TransactionModel.timestamp <= as_of)

        network_ids = [n for n in session.execute(stmt).scalars().all() if n]
        primary_net_id = network_ids[0] if network_ids else None

        net_risk = 0.0
        patterns: list[SyndicatePattern] = []
        findings: list[NetworkFinding] = []

        if primary_net_id:
            net = self.network_repo.get_by_id(session, primary_net_id)
            if net:
                net_risk = float(net.risk_score)
            patterns = self.get_network_patterns(session, primary_net_id, as_of=as_of)
            findings = self.get_network_findings(session, primary_net_id, as_of=as_of)

        # Cross-customer sharing count
        sharing_count = self.entity_repo._get_cross_customer_sharing_count(
            session=session,
            entity_type=entity_type,
            entity_id=entity_id,
            ref_time=as_of or datetime.now(UTC),
        )

        # Find key paths in ego graph
        ego_graph = self.entity_repo.get_bounded_neighborhood(
            session=session,
            entity_type=entity_type,
            entity_id=entity_id,
            depth=2,
            max_nodes=50,
        )
        key_paths = self.path_engine.extract_key_network_paths(ego_graph, max_paths=3)

        return EntityNetworkIntelligenceResponse(
            entity_type=entity_type.lower(),
            entity_id=entity_id,
            network_id=primary_net_id,
            is_network_member=primary_net_id is not None,
            network_risk_score=net_risk,
            connected_networks_count=len(network_ids),
            cross_customer_sharing_count=sharing_count,
            patterns=patterns,
            key_paths=key_paths,
            findings=findings,
        )

    get_entity_network_context = get_entity_network_intelligence


_network_intelligence_service_instance: NetworkIntelligenceService | None = None


def get_network_intelligence_service() -> NetworkIntelligenceService:
    """Dependency provider for NetworkIntelligenceService."""
    global _network_intelligence_service_instance
    if _network_intelligence_service_instance is None:
        _network_intelligence_service_instance = NetworkIntelligenceService()
    return _network_intelligence_service_instance
