"""Unit tests for held-out evaluation module and cost calculations."""

import tempfile
from pathlib import Path

from ml.data.generator import DatasetConfig, SyntheticDataGenerator
from ml.evaluation.evaluate import evaluate_held_out
from ml.training.train import train_model


def test_held_out_evaluation_and_metrics_calculation() -> None:
    """Verify that held-out evaluation outputs consistent confusion matrix and cost metrics."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        csv_file = tmp_path / "test_tx.csv"
        models_dir = tmp_path / "models"
        metrics_file = tmp_path / "metrics.json"

        # Generate small dataset
        gen = SyntheticDataGenerator(DatasetConfig(seed=42, num_transactions=800))
        df = gen.generate()
        df.to_csv(csv_file, index=False)

        train_model(data_path=csv_file, models_dir=models_dir, seed=42)

        results = evaluate_held_out(
            data_path=csv_file,
            models_dir=models_dir,
            output_metrics_path=metrics_file,
            cost_per_fp=350.0,
        )

        assert metrics_file.exists()
        assert results["held_out_test_size"] == int(len(df) * 0.15)
        cm = results["confusion_matrix"]
        total_cm = (
            cm["true_positives"]
            + cm["false_positives"]
            + cm["true_negatives"]
            + cm["false_negatives"]
        )
        assert total_cm == results["held_out_test_size"]

        # Cost verification
        expected_fp_cost = cm["false_positives"] * 350.0
        assert (
            results["cost_and_financial_impact"]["false_positive_monetary_cost_inr"]
            == expected_fp_cost
        )
        assert 0.0 <= results["metrics"]["precision"] <= 1.0
        assert 0.0 <= results["metrics"]["recall"] <= 1.0
        assert 0.0 <= results["metrics"]["pr_auc"] <= 1.0
