"""Tests for FraudDNA Risk Simulation Engine.

Covers:
- Baseline configuration
- Threshold changes and precision/recall tradeoff
- False-positive cost and fraud loss
- Review capacity
- Edge cases
- Deterministic repeated execution
- Invalid input
- No mutation of source data
"""

import pytest
from pydantic import ValidationError

from app.simulation.engine import SimulationEngine
from app.simulation.schemas import (
    SimulationCompareRequest,
    SimulationConfig,
    SimulationResult,
    generate_comparison_id,
    generate_simulation_id,
)


@pytest.fixture
def engine() -> SimulationEngine:
    """Create a SimulationEngine using the default dataset."""
    return SimulationEngine()


class TestSimulationEngine:
    """Test suite for the simulation engine core logic."""

    def test_baseline_simulation(self, engine: SimulationEngine) -> None:
        """Baseline simulation with default config produces valid results."""
        config = SimulationConfig()
        result = engine.run_simulation(config)

        assert isinstance(result, SimulationResult)
        assert result.total_transactions > 0
        assert result.actual_fraud_count >= 0
        assert result.actual_legitimate_count >= 0
        assert result.total_transactions == (
            result.actual_fraud_count + result.actual_legitimate_count
        )

        # Classification counts sum up
        assert result.total_transactions == (
            result.true_positives
            + result.false_positives
            + result.true_negatives
            + result.false_negatives
        )

        # Predicted fraud = TP + FP
        assert result.predicted_fraud_count == result.true_positives + result.false_positives

        # Metrics are in valid ranges
        assert 0.0 <= result.precision <= 1.0
        assert 0.0 <= result.recall <= 1.0
        assert 0.0 <= result.f1_score <= 1.0
        assert 0.0 <= result.false_positive_rate <= 1.0

    def test_deterministic_repeated_execution(self, engine: SimulationEngine) -> None:
        """Same configuration produces identical results."""
        config = SimulationConfig(fraud_threshold=0.50, cost_per_false_positive=200.0)
        r1 = engine.run_simulation(config)
        r2 = engine.run_simulation(config)

        assert r1.simulation_id == r2.simulation_id
        assert r1.true_positives == r2.true_positives
        assert r1.false_positives == r2.false_positives
        assert r1.true_negatives == r2.true_negatives
        assert r1.false_negatives == r2.false_negatives
        assert r1.precision == r2.precision
        assert r1.recall == r2.recall
        assert r1.net_benefit == r2.net_benefit

    def test_lower_threshold_increases_recall(self, engine: SimulationEngine) -> None:
        """Lowering the threshold should increase recall (catch more fraud)."""
        high = engine.run_simulation(SimulationConfig(fraud_threshold=0.70))
        low = engine.run_simulation(SimulationConfig(fraud_threshold=0.20))

        # Lower threshold catches >= as much fraud
        assert low.recall >= high.recall
        assert low.true_positives >= high.true_positives

    def test_higher_threshold_reduces_false_positives(self, engine: SimulationEngine) -> None:
        """Raising the threshold should reduce false positives."""
        low = engine.run_simulation(SimulationConfig(fraud_threshold=0.20))
        high = engine.run_simulation(SimulationConfig(fraud_threshold=0.70))

        assert high.false_positives <= low.false_positives

    def test_false_positive_cost_impact(self, engine: SimulationEngine) -> None:
        """Higher cost_per_false_positive increases false_positive_cost."""
        cheap = engine.run_simulation(
            SimulationConfig(fraud_threshold=0.37, cost_per_false_positive=100.0)
        )
        expensive = engine.run_simulation(
            SimulationConfig(fraud_threshold=0.37, cost_per_false_positive=1000.0)
        )

        # Same FP count but different costs
        assert cheap.false_positives == expensive.false_positives
        if cheap.false_positives > 0:
            assert expensive.false_positive_cost > cheap.false_positive_cost

    def test_financial_model_formulas(self, engine: SimulationEngine) -> None:
        """Verify financial model: expected_loss and net_benefit formulas."""
        result = engine.run_simulation(SimulationConfig(fraud_threshold=0.37))

        # expected_loss = fraud_missed_amount + false_positive_cost
        expected_loss = result.fraud_missed_amount + result.false_positive_cost
        assert abs(result.expected_loss - expected_loss) < 0.01

        # net_benefit = fraud_prevented_amount - false_positive_cost
        net_benefit = result.fraud_prevented_amount - result.false_positive_cost
        assert abs(result.net_benefit - net_benefit) < 0.01

        # gross_fraud_exposure = fraud_prevented + fraud_missed
        gross = result.fraud_prevented_amount + result.fraud_missed_amount
        assert abs(result.gross_fraud_exposure - gross) < 0.01

    def test_review_capacity(self, engine: SimulationEngine) -> None:
        """Review capacity flag is set correctly."""
        # Very low capacity should be exceeded for aggressive threshold
        result = engine.run_simulation(SimulationConfig(fraud_threshold=0.10, review_capacity=1))
        if result.review_volume > 1:
            assert result.review_capacity_exceeded is True

        # Very high capacity should not be exceeded
        result2 = engine.run_simulation(
            SimulationConfig(fraud_threshold=0.90, review_capacity=100000)
        )
        assert result2.review_capacity_exceeded is False

    def test_extreme_threshold_near_zero(self, engine: SimulationEngine) -> None:
        """Very low threshold flags nearly everything."""
        result = engine.run_simulation(SimulationConfig(fraud_threshold=0.01))
        # Should flag almost all transactions
        assert result.predicted_fraud_count >= result.actual_fraud_count

    def test_extreme_threshold_near_one(self, engine: SimulationEngine) -> None:
        """Very high threshold flags almost nothing."""
        result = engine.run_simulation(SimulationConfig(fraud_threshold=0.99))
        # Most fraud will be missed
        assert result.false_negatives >= 0
        assert result.predicted_fraud_count <= result.actual_fraud_count

    def test_no_mutation_of_source_data(self, engine: SimulationEngine) -> None:
        """Running simulation does not mutate the source dataset."""
        engine._load_data()
        labels_before = dict(engine._labels)
        amounts_before = dict(engine._amounts)
        scores_before = dict(engine._risk_scores)

        engine.run_simulation(SimulationConfig(fraud_threshold=0.20))
        engine.run_simulation(SimulationConfig(fraud_threshold=0.80))

        assert engine._labels == labels_before
        assert engine._amounts == amounts_before
        assert engine._risk_scores == scores_before

    def test_is_deterministic_flag(self, engine: SimulationEngine) -> None:
        """Result always has is_deterministic=True."""
        result = engine.run_simulation(SimulationConfig())
        assert result.is_deterministic is True

    def test_dataset_summary(self, engine: SimulationEngine) -> None:
        """Dataset summary returns valid counts."""
        summary = engine.get_dataset_summary()
        assert summary["total_transactions"] > 0
        assert summary["fraud_count"] >= 0
        assert summary["legitimate_count"] >= 0
        assert summary["total_transactions"] == (
            summary["fraud_count"] + summary["legitimate_count"]
        )


class TestSimulationSchemas:
    """Test suite for simulation schemas and validation."""

    def test_valid_config(self) -> None:
        """Valid configuration passes validation."""
        config = SimulationConfig(
            fraud_threshold=0.50,
            cost_per_false_positive=500.0,
            review_capacity=100,
        )
        assert config.fraud_threshold == 0.50

    def test_threshold_range(self) -> None:
        """Threshold must be between 0.01 and 0.99."""
        with pytest.raises(ValidationError):
            SimulationConfig(fraud_threshold=0.0)

        with pytest.raises(ValidationError):
            SimulationConfig(fraud_threshold=1.0)

    def test_negative_cost_rejected(self) -> None:
        """Negative cost_per_false_positive is rejected."""
        with pytest.raises(ValidationError):
            SimulationConfig(cost_per_false_positive=-100.0)

    def test_review_threshold_must_be_below_fraud(self) -> None:
        """review_threshold must be less than fraud_threshold."""
        with pytest.raises(ValidationError):
            SimulationConfig(fraud_threshold=0.50, review_threshold=0.60)

    def test_simulation_id_deterministic(self) -> None:
        """Simulation IDs are deterministic for the same config."""
        c1 = SimulationConfig(fraud_threshold=0.37)
        c2 = SimulationConfig(fraud_threshold=0.37)
        assert generate_simulation_id(c1) == generate_simulation_id(c2)

    def test_simulation_id_changes_with_threshold(self) -> None:
        """Different thresholds produce different IDs."""
        c1 = SimulationConfig(fraud_threshold=0.30)
        c2 = SimulationConfig(fraud_threshold=0.50)
        assert generate_simulation_id(c1) != generate_simulation_id(c2)

    def test_compare_request_min_configs(self) -> None:
        """Comparison requires at least 2 configs."""
        with pytest.raises(ValidationError):
            SimulationCompareRequest(configs=[SimulationConfig()])

    def test_comparison_id_deterministic(self) -> None:
        """Comparison IDs are deterministic."""
        configs = [
            SimulationConfig(fraud_threshold=0.30),
            SimulationConfig(fraud_threshold=0.50),
        ]
        id1 = generate_comparison_id(configs)
        id2 = generate_comparison_id(configs)
        assert id1 == id2


class TestSimulationAPI:
    """Test simulation API endpoints via the FastAPI test client."""

    def test_run_simulation_endpoint(self) -> None:
        """POST /api/v1/simulations returns valid simulation."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/simulations",
            json={"config": {"fraud_threshold": 0.37, "cost_per_false_positive": 350.0}},
        )
        assert response.status_code == 200
        data = response.json()
        assert "simulation_id" in data
        assert data["total_transactions"] > 0
        assert data["is_deterministic"] is True

    def test_compare_endpoint(self) -> None:
        """POST /api/v1/simulations/compare returns comparison."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/simulations/compare",
            json={
                "configs": [
                    {"fraud_threshold": 0.20},
                    {"fraud_threshold": 0.37},
                    {"fraud_threshold": 0.50},
                    {"fraud_threshold": 0.70},
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 4
        assert data["comparison_id"].startswith("cmp_")

    def test_invalid_threshold_rejected(self) -> None:
        """Invalid threshold values are rejected."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/simulations",
            json={"config": {"fraud_threshold": 1.5}},
        )
        assert response.status_code == 422

    def test_overview_endpoint(self) -> None:
        """GET /api/v1/overview returns overview data."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        response = client.get("/api/v1/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_transactions" in data
        assert data["total_transactions"] > 0

    def test_transactions_endpoint(self) -> None:
        """GET /api/v1/transactions returns paginated list."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        response = client.get("/api/v1/transactions?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert "total" in data
        assert len(data["transactions"]) <= 10

    def test_evaluation_endpoint(self) -> None:
        """GET /api/v1/evaluation returns metrics."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        response = client.get("/api/v1/evaluation")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
