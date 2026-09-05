"""FraudDNA Simulation Schemas.

Pydantic models for simulation configuration, results, and comparison payloads.

Financial Model:
    expected_loss = fraud_missed_amount + false_positive_cost
    net_benefit   = fraud_prevented_amount - false_positive_cost
    fraud_prevented_amount = sum(amount) for true positives
    fraud_missed_amount    = sum(amount) for false negatives
    false_positive_cost    = false_positive_count * cost_per_false_positive
"""

import hashlib
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class SimulationConfig(BaseModel):
    """Configurable parameters for a single simulation run."""

    model_config = ConfigDict(extra="forbid")

    fraud_threshold: float = Field(
        0.37,
        ge=0.01,
        le=0.99,
        description="ML risk score threshold; scores >= this are flagged as fraud.",
    )
    review_threshold: float | None = Field(
        None,
        ge=0.01,
        le=0.99,
        description="Optional lower threshold for REVIEW band. Scores between review and fraud threshold go to REVIEW.",
    )
    cost_per_false_positive: float = Field(
        350.0,
        ge=0.0,
        description="Operational cost (INR) per false-positive case.",
    )
    avg_fraud_loss: float | None = Field(
        None,
        ge=0.0,
        description="Optional override for average fraud loss per missed transaction (INR). If None, actual amounts are used.",
    )
    review_capacity: int = Field(
        500,
        ge=0,
        description="Maximum number of transactions that can be manually reviewed per cycle.",
    )

    @field_validator("review_threshold")
    @classmethod
    def review_below_fraud(cls, v: float | None, info: ValidationInfo) -> float | None:
        """Ensure review_threshold < fraud_threshold when both are set."""
        if v is not None and info.data:
            fraud_th = info.data.get("fraud_threshold", 0.37)
            if v >= fraud_th:
                msg = "review_threshold must be less than fraud_threshold"
                raise ValueError(msg)
        return v


class SimulationResult(BaseModel):
    """Complete simulation output for a single configuration."""

    model_config = ConfigDict(extra="forbid")

    simulation_id: str = Field(..., description="Deterministic identifier for this simulation run.")
    config: SimulationConfig = Field(..., description="Configuration used for this simulation.")

    # Population counts
    total_transactions: int = Field(..., description="Total transactions evaluated.")
    actual_fraud_count: int = Field(..., description="Ground-truth fraud transactions.")
    actual_legitimate_count: int = Field(..., description="Ground-truth legitimate transactions.")

    # Classification counts
    predicted_fraud_count: int = Field(
        ..., description="Transactions flagged as fraud at threshold."
    )
    true_positives: int = Field(..., description="Correctly flagged fraud (TP).")
    false_positives: int = Field(..., description="Incorrectly flagged legitimate (FP).")
    true_negatives: int = Field(..., description="Correctly passed legitimate (TN).")
    false_negatives: int = Field(..., description="Missed fraud (FN).")

    # Performance metrics
    precision: float = Field(..., description="TP / (TP + FP).")
    recall: float = Field(..., description="TP / (TP + FN).")
    f1_score: float = Field(..., description="Harmonic mean of precision and recall.")
    false_positive_rate: float = Field(..., description="FP / (FP + TN).")

    # Financial model
    gross_fraud_exposure: float = Field(
        ..., description="Total amount of all fraud transactions (INR)."
    )
    fraud_prevented_amount: float = Field(
        ..., description="Amount of fraud caught by threshold (INR)."
    )
    fraud_missed_amount: float = Field(
        ..., description="Amount of fraud missed at threshold (INR)."
    )
    false_positive_cost: float = Field(
        ..., description="Total operational cost from false positives (INR)."
    )
    expected_loss: float = Field(
        ...,
        description="fraud_missed_amount + false_positive_cost (INR).",
    )
    net_benefit: float = Field(
        ...,
        description="fraud_prevented_amount - false_positive_cost (INR).",
    )

    # Review metrics
    review_volume: int = Field(..., description="Number of transactions requiring manual review.")
    review_capacity: int = Field(..., description="Configured review capacity.")
    review_capacity_exceeded: bool = Field(
        ..., description="Whether review volume exceeds capacity."
    )

    # Metadata
    is_deterministic: bool = Field(default=True, description="Always True.")
    evaluated_at: datetime = Field(
        default_factory=datetime.utcnow, description="UTC timestamp of simulation."
    )
    data_label: str = Field(default="synthetic_dataset", description="Label for the dataset used.")


class SimulationRequest(BaseModel):
    """Request payload to run a single simulation."""

    model_config = ConfigDict(extra="forbid")

    config: SimulationConfig = Field(
        default_factory=lambda: SimulationConfig.model_validate({}),
        description="Simulation configuration parameters.",
    )


class SimulationCompareRequest(BaseModel):
    """Request payload to compare multiple threshold configurations."""

    model_config = ConfigDict(extra="forbid")

    configs: list[SimulationConfig] = Field(
        ...,
        min_length=2,
        max_length=20,
        description="List of configurations to compare (2-20).",
    )


class SimulationCompareResponse(BaseModel):
    """Response for a multi-configuration comparison."""

    model_config = ConfigDict(extra="forbid")

    comparison_id: str = Field(..., description="Deterministic identifier for this comparison.")
    results: list[SimulationResult] = Field(
        ..., description="Ordered simulation results for each configuration."
    )
    baseline_index: int = Field(
        default=0, description="Index of baseline configuration for relative comparison."
    )
    evaluated_at: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp.")


def generate_simulation_id(config: SimulationConfig) -> str:
    """Generate a deterministic simulation ID from configuration."""
    raw = (
        f"sim:{config.fraud_threshold:.4f}:{config.review_threshold}:"
        f"{config.cost_per_false_positive:.2f}:{config.review_capacity}"
    ).encode()
    return f"sim_{hashlib.sha256(raw).hexdigest()[:16]}"


def generate_comparison_id(configs: list[SimulationConfig]) -> str:
    """Generate a deterministic comparison ID from all configs."""
    parts = "|".join(f"{c.fraud_threshold:.4f}:{c.cost_per_false_positive:.2f}" for c in configs)
    raw = f"cmp:{parts}".encode()
    return f"cmp_{hashlib.sha256(raw).hexdigest()[:16]}"
