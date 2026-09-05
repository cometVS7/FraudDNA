"""Tests for Production Packaging and Container Artifacts."""

from pathlib import Path

import joblib
import pandas as pd


def test_required_ml_artifacts_exist_and_loadable() -> None:
    """Verify that the required ML dataset and model artifacts exist and are loadable."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    if not (root_dir / "ml").exists():
        root_dir = Path(__file__).resolve().parent.parent

    data_csv = root_dir / "ml" / "data" / "transactions.csv"
    model_joblib = root_dir / "ml" / "models" / "lightgbm_model.joblib"
    pipeline_joblib = root_dir / "ml" / "models" / "feature_pipeline.joblib"
    metrics_json = root_dir / "ml" / "evaluation" / "metrics.json"

    # 1. Transactions dataset exists, non-empty, and has expected columns
    assert data_csv.exists(), f"Missing required dataset: {data_csv}"
    df = pd.read_csv(data_csv, nrows=10)
    assert len(df) > 0
    assert "transaction_id" in df.columns
    assert "is_fraud" in df.columns

    # 2. LightGBM model exists and deserializes
    assert model_joblib.exists(), f"Missing required model artifact: {model_joblib}"
    model = joblib.load(model_joblib)
    assert hasattr(model, "predict_proba") or hasattr(model, "predict")

    # 3. Feature pipeline exists and deserializes
    assert pipeline_joblib.exists(), f"Missing required pipeline artifact: {pipeline_joblib}"
    pipeline = joblib.load(pipeline_joblib)
    assert hasattr(pipeline, "transform")

    # 4. Evaluation metrics exist
    assert metrics_json.exists(), f"Missing evaluation metrics: {metrics_json}"


def test_dockerfiles_contain_ml_artifacts_copy() -> None:
    """Verify that both backend/Dockerfile and root Dockerfile copy the ML artifacts."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    if not (root_dir / "Dockerfile").exists():
        root_dir = Path(__file__).resolve().parent.parent

    root_dockerfile = root_dir / "Dockerfile"
    backend_dockerfile = root_dir / "backend" / "Dockerfile"

    assert root_dockerfile.exists(), f"Missing {root_dockerfile}"
    root_content = root_dockerfile.read_text(encoding="utf-8")
    assert "COPY ml ./ml" in root_content
    assert "COPY backend/app ./app" in root_content or "COPY app ./app" in root_content

    assert backend_dockerfile.exists(), f"Missing {backend_dockerfile}"
    backend_content = backend_dockerfile.read_text(encoding="utf-8")
    assert "COPY ml ./ml" in backend_content
    assert "COPY backend/app ./app" in backend_content or "COPY app ./app" in backend_content
