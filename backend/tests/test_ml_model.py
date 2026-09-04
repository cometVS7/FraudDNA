"""Unit tests for LightGBM model training and loading."""

import tempfile
from pathlib import Path

import joblib

from ml.data.generator import DatasetConfig, SyntheticDataGenerator
from ml.training.train import train_model


def test_model_training_and_serialization() -> None:
    """Verify that model trains, saves metadata, and can be loaded back."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        csv_file = tmp_path / "test_tx.csv"
        models_dir = tmp_path / "models"

        gen = SyntheticDataGenerator(DatasetConfig(seed=42, num_transactions=600))
        df = gen.generate()
        df.to_csv(csv_file, index=False)

        metadata = train_model(
            data_path=csv_file,
            models_dir=models_dir,
            seed=42,
        )

        assert (models_dir / "lightgbm_model.joblib").exists()
        assert (models_dir / "feature_pipeline.joblib").exists()
        assert (models_dir / "model_metadata.json").exists()
        assert 0.0 < metadata["selected_validation_threshold"] < 1.0

        # Verify model loading
        loaded_model = joblib.load(models_dir / "lightgbm_model.joblib")
        loaded_pipeline = joblib.load(models_dir / "feature_pipeline.joblib")

        # Test single transaction scoring
        sample_df = df.iloc[:5].copy()
        X_sample, _ = loaded_pipeline.transform(sample_df, update_state=False)
        probs = loaded_model.predict_proba(X_sample)[:, 1]

        assert len(probs) == 5
        assert (probs >= 0.0).all() and (probs <= 1.0).all()
