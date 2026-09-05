"""Unit tests for the Risk Investigation Service."""

import pytest

from app.schemas.investigation import (
    EvidenceSeverity,
    EvidenceSource,
    FactorDirection,
    InvestigationStatus,
    RiskLevel,
)
from app.services.investigation import (
    InvestigationService,
    TransactionNotFoundError,
    get_investigation_service,
)


@pytest.fixture
def investigation_service() -> InvestigationService:
    """Fixture providing initialized InvestigationService."""
    service = get_investigation_service()
    service.graph_service.initialize()
    return service


def test_investigate_valid_transaction(investigation_service: InvestigationService) -> None:
    """Verify that a valid transaction returns a complete investigation response."""
    graph_service = investigation_service.graph_service
    assert len(graph_service.transactions_by_id) > 0
    sample_tx_id = next(iter(graph_service.transactions_by_id.keys()))

    result = investigation_service.investigate(sample_tx_id)

    assert result.transaction_id == sample_tx_id
    assert result.investigation_id.startswith("inv_")
    assert 0.0 <= result.risk_score <= 1.0
    assert isinstance(result.risk_level, RiskLevel)
    assert result.status in (InvestigationStatus.COMPLETED, InvestigationStatus.DEGRADED)
    assert isinstance(result.risk_factors, list)
    assert isinstance(result.related_entities, list)
    assert isinstance(result.related_transactions, list)
    assert isinstance(result.evidence, list)
    assert len(result.evidence) > 0


def test_investigate_unknown_transaction(investigation_service: InvestigationService) -> None:
    """Verify that an unknown transaction ID raises TransactionNotFoundError."""
    with pytest.raises(TransactionNotFoundError) as exc_info:
        investigation_service.investigate("non_existent_txn_999999")

    assert "non_existent_txn_999999" in str(exc_info.value)


def test_deterministic_investigation_id(investigation_service: InvestigationService) -> None:
    """Verify that investigation IDs are strictly deterministic and reproducible."""
    tx_id = "txn_sample_test_123"
    id1 = investigation_service._generate_investigation_id(tx_id)
    id2 = investigation_service._generate_investigation_id(tx_id)
    assert id1 == id2
    assert id1.startswith("inv_")
    assert len(id1) == 20  # "inv_" (4) + 16 hex chars = 20


def test_risk_level_mapping(investigation_service: InvestigationService) -> None:
    """Verify deterministic risk level boundaries."""
    assert investigation_service._map_risk_level(0.0) == RiskLevel.LOW
    assert investigation_service._map_risk_level(0.299) == RiskLevel.LOW
    assert investigation_service._map_risk_level(0.30) == RiskLevel.MEDIUM
    assert investigation_service._map_risk_level(0.699) == RiskLevel.MEDIUM
    assert investigation_service._map_risk_level(0.70) == RiskLevel.HIGH
    assert investigation_service._map_risk_level(0.899) == RiskLevel.HIGH
    assert investigation_service._map_risk_level(0.90) == RiskLevel.CRITICAL
    assert investigation_service._map_risk_level(1.0) == RiskLevel.CRITICAL


def test_xai_shap_factors_extraction(investigation_service: InvestigationService) -> None:
    """Verify that Tree SHAP factor attributions are correctly calculated and ranked."""
    graph_service = investigation_service.graph_service
    sample_tx_id = next(iter(graph_service.transactions_by_id.keys()))
    row_dict = graph_service.get_transaction_row(sample_tx_id)
    assert row_dict is not None

    factors, success = investigation_service._compute_xai_factors(row_dict)
    if success:
        assert len(factors) > 0
        assert len(factors) <= 5
        # Check ranking ordering
        for i, factor in enumerate(factors, start=1):
            assert factor.rank == i
            assert isinstance(factor.feature, str)
            assert factor.direction in (
                FactorDirection.INCREASES_RISK,
                FactorDirection.DECREASES_RISK,
                FactorDirection.NEUTRAL,
            )


def test_graceful_xai_degradation(investigation_service: InvestigationService) -> None:
    """Verify that missing ML components degrades gracefully without crashing."""
    # Test with None row
    factors, success = investigation_service._compute_xai_factors(None)
    assert factors == []
    assert not success


def test_graph_context_extraction(investigation_service: InvestigationService) -> None:
    """Verify that direct entities and 2-hop related transactions are extracted from the graph."""
    graph_service = investigation_service.graph_service
    sample_tx_id = next(iter(graph_service.transactions_by_id.keys()))

    entities, transactions = investigation_service._extract_graph_context(sample_tx_id)

    assert len(entities) > 0
    entity_types = {e.entity_type for e in entities}
    # A standard transaction connects to customer, device, ip, card, merchant
    assert "customer" in entity_types
    assert isinstance(transactions, list)


def test_cluster_context_extraction(investigation_service: InvestigationService) -> None:
    """Verify cluster membership extraction for cluster member and non-cluster case."""
    graph_service = investigation_service.graph_service

    if graph_service.clusters:
        first_cluster = graph_service.clusters[0]
        if first_cluster.member_transaction_ids:
            cluster_tx_id = first_cluster.member_transaction_ids[0]
            cluster_info = investigation_service._extract_cluster_context(cluster_tx_id)
            assert cluster_info is not None
            assert cluster_info.cluster_id == first_cluster.cluster_id
            assert cluster_info.cluster_risk_score == first_cluster.cluster_risk_score
            assert cluster_info.is_suspicious == first_cluster.is_suspicious

    # Non-existent transaction cluster
    no_cluster = investigation_service._extract_cluster_context("non_existent_tx_abc")
    assert no_cluster is None


def test_evidence_synthesis_determinism_and_traceability(
    investigation_service: InvestigationService,
) -> None:
    """Verify that synthesized evidence items are deterministic, categorized, and traceable."""
    graph_service = investigation_service.graph_service
    sample_tx_id = next(iter(graph_service.transactions_by_id.keys()))

    res1 = investigation_service.investigate(sample_tx_id)
    res2 = investigation_service.investigate(sample_tx_id)

    # Check stability
    assert res1.investigation_id == res2.investigation_id
    assert res1.risk_score == res2.risk_score
    assert len(res1.evidence) == len(res2.evidence)

    for item in res1.evidence:
        assert isinstance(item.evidence_type, str)
        assert isinstance(item.description, str)
        assert item.severity in (
            EvidenceSeverity.LOW,
            EvidenceSeverity.MEDIUM,
            EvidenceSeverity.HIGH,
            EvidenceSeverity.CRITICAL,
        )
        assert item.source in (
            EvidenceSource.RISK_MODEL,
            EvidenceSource.SHAP,
            EvidenceSource.FRAUDDNA_GRAPH,
            EvidenceSource.FRAUDDNA_CLUSTER,
        )


def test_investigation_caching_and_lookup(
    investigation_service: InvestigationService,
) -> None:
    """Verify that completed investigations can be retrieved by their ID."""
    graph_service = investigation_service.graph_service
    sample_tx_id = next(iter(graph_service.transactions_by_id.keys()))

    created = investigation_service.investigate(sample_tx_id)
    retrieved = investigation_service.get_investigation_by_id(created.investigation_id)

    assert retrieved is not None
    assert retrieved.investigation_id == created.investigation_id
    assert retrieved.transaction_id == sample_tx_id
