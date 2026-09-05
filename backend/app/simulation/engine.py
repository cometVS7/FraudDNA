"""FraudDNA Risk Simulation Engine.

Deterministic engine that replays the existing transaction dataset against
configurable risk thresholds and cost parameters, producing classification
metrics and financial impact analysis.

Financial Model (explicit formulas):
    false_positive_cost   = false_positive_count × cost_per_false_positive
    fraud_prevented       = Σ amount(TP)
    fraud_missed          = Σ amount(FN)
    expected_loss         = fraud_missed + false_positive_cost
    net_benefit           = fraud_prevented - false_positive_cost

No new model is trained. The existing Phase 1 LightGBM risk scores are used.
"""

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.core.config import ensure_ml_on_sys_path
from app.simulation.schemas import (
    SimulationConfig,
    SimulationResult,
    generate_simulation_id,
)

logger = logging.getLogger(__name__)


class SimulationEngine:
    """Deterministic threshold simulation engine operating on the existing dataset."""

    def __init__(
        self,
        data_path: str | Path = "ml/data/transactions.csv",
        models_dir: str | Path = "ml/models",
    ) -> None:
        self.data_path = Path(data_path)
        self.models_dir = Path(models_dir)

        self._df: pd.DataFrame | None = None
        self._risk_scores: dict[str, float] = {}
        self._amounts: dict[str, float] = {}
        self._labels: dict[str, int] = {}
        self._loaded: bool = False

    def _load_data(self) -> None:
        """Load transaction dataset and compute risk scores using Phase 1 model."""
        if self._loaded:
            return

        if not self.data_path.exists():
            alt_data = Path("..") / self.data_path
            if alt_data.exists():
                self.data_path = alt_data

        if not self.models_dir.exists():
            alt_models = Path("..") / self.models_dir
            if alt_models.exists():
                self.models_dir = alt_models

        if not self.data_path.exists():
            raise FileNotFoundError(f"Transaction dataset not found at {self.data_path}")

        df = pd.read_csv(self.data_path)
        self._df = df

        # Extract ground truth labels
        for _, row in df.iterrows():
            tx_id = str(row["transaction_id"])
            self._labels[tx_id] = int(row.get("is_fraud", 0))
            self._amounts[tx_id] = float(row.get("amount", 0.0))

        # Compute risk scores using Phase 1 model
        self._risk_scores = self._score_all_transactions(df)
        self._loaded = True

    def _score_all_transactions(self, df: pd.DataFrame) -> dict[str, float]:
        """Score all transactions with the Phase 1 LightGBM model."""
        if not self.models_dir.exists():
            alt_models = Path("..") / self.models_dir
            if alt_models.exists():
                self.models_dir = alt_models

        # Ensure repo root containing 'ml' is on sys.path
        ensure_ml_on_sys_path()

        model_file = self.models_dir / "lightgbm_model.joblib"
        pipeline_file = self.models_dir / "feature_pipeline.joblib"

        if model_file.exists() and pipeline_file.exists():
            try:
                model = joblib.load(model_file)
                pipeline = joblib.load(pipeline_file)
                X, _ = pipeline.transform(df, update_state=False)
                raw_probs = model.predict_proba(X)
                probs = np.asarray(raw_probs)[:, 1]
                scores = {
                    str(tx_id): round(float(p), 4)
                    for tx_id, p in zip(df["transaction_id"], probs, strict=True)
                }
                del X
                del raw_probs
                del probs
                return scores
            except Exception as e:
                logger.error(f"Could not score transactions for simulation: {e}", exc_info=True)
                raise RuntimeError(f"Simulation scoring failed: {e}") from e

        raise FileNotFoundError(f"Simulation ML model artifacts not found at {self.models_dir}")

    def run_simulation(self, config: SimulationConfig) -> SimulationResult:
        """Execute a deterministic simulation with the given configuration.

        This method does NOT mutate the underlying transaction data.
        """
        self._load_data()

        threshold = config.fraud_threshold
        cost_per_fp = config.cost_per_false_positive

        # Classification
        tp = 0
        fp = 0
        tn = 0
        fn = 0
        fraud_prevented_amt = 0.0
        fraud_missed_amt = 0.0
        review_volume = 0

        for tx_id, label in self._labels.items():
            score = self._risk_scores.get(tx_id, 0.0)
            amount = self._amounts.get(tx_id, 0.0)
            predicted_fraud = score >= threshold

            # Count review-band transactions
            if config.review_threshold is not None:
                if config.review_threshold <= score < threshold:
                    review_volume += 1

            if label == 1:  # Actually fraud
                if predicted_fraud:
                    tp += 1
                    fraud_prevented_amt += amount
                else:
                    fn += 1
                    fraud_missed_amt += amount
            else:  # Actually legitimate
                if predicted_fraud:
                    fp += 1
                else:
                    tn += 1

        # If no review threshold, all flagged transactions need review
        if config.review_threshold is None:
            review_volume = tp + fp

        total = tp + fp + tn + fn
        actual_fraud = tp + fn
        actual_legit = tn + fp
        predicted_fraud_count = tp + fp

        # Performance metrics (guard against division by zero)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        # Financial model
        gross_fraud_exposure = fraud_prevented_amt + fraud_missed_amt
        false_positive_cost = fp * cost_per_fp
        expected_loss = fraud_missed_amt + false_positive_cost
        net_benefit = fraud_prevented_amt - false_positive_cost

        simulation_id = generate_simulation_id(config)

        return SimulationResult(
            simulation_id=simulation_id,
            config=config,
            total_transactions=total,
            actual_fraud_count=actual_fraud,
            actual_legitimate_count=actual_legit,
            predicted_fraud_count=predicted_fraud_count,
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            false_positive_rate=round(fpr, 4),
            gross_fraud_exposure=round(gross_fraud_exposure, 2),
            fraud_prevented_amount=round(fraud_prevented_amt, 2),
            fraud_missed_amount=round(fraud_missed_amt, 2),
            false_positive_cost=round(false_positive_cost, 2),
            expected_loss=round(expected_loss, 2),
            net_benefit=round(net_benefit, 2),
            review_volume=review_volume,
            review_capacity=config.review_capacity,
            review_capacity_exceeded=review_volume > config.review_capacity,
        )

    def get_transaction_count(self) -> int:
        """Return total number of transactions in the dataset."""
        self._load_data()
        return len(self._labels)

    def get_fraud_count(self) -> int:
        """Return number of ground-truth fraud transactions."""
        self._load_data()
        return sum(1 for v in self._labels.values() if v == 1)

    def get_dataset_summary(self) -> dict[str, Any]:
        """Return basic dataset summary for UI consumption."""
        self._load_data()
        total = len(self._labels)
        fraud_count = sum(1 for v in self._labels.values() if v == 1)
        amounts = list(self._amounts.values())

        return {
            "total_transactions": total,
            "fraud_count": fraud_count,
            "legitimate_count": total - fraud_count,
            "fraud_rate": round(fraud_count / total, 4) if total > 0 else 0.0,
            "total_amount": round(sum(amounts), 2),
            "mean_amount": round(sum(amounts) / total, 2) if total > 0 else 0.0,
            "data_label": "synthetic_dataset",
        }


# Global Singleton Instance
_simulation_engine_instance: SimulationEngine | None = None


def get_simulation_engine() -> SimulationEngine:
    """Dependency provider for SimulationEngine singleton."""
    global _simulation_engine_instance
    if _simulation_engine_instance is None:
        _simulation_engine_instance = SimulationEngine()
    return _simulation_engine_instance
