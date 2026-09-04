"""FraudDNA LightGBM Risk Model Training & Validation Threshold Tuning Pipeline.

Splits data strictly by time (70% Train, 15% Validation, 15% Held-Out Test).
Selects operating threshold on Validation data ONLY.
Persists model, feature pipeline, and model metadata artifacts.
"""

import json
import sys
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.metrics import f1_score

from ml.data.generator import DatasetConfig, SyntheticDataGenerator
from ml.features.engineering import FeaturePipeline


def train_model(
    data_path: str | Path = "ml/data/transactions.csv",
    models_dir: str | Path = "ml/models",
    cost_per_fp: float = 350.0,
    seed: int = 42,
) -> dict[str, Any]:
    """Train LightGBM fraud model, tune validation threshold, and persist artifacts."""
    models_path = Path(models_dir)
    models_path.mkdir(parents=True, exist_ok=True)
    csv_path = Path(data_path)

    # 1. Load or generate dataset
    if csv_path.exists():
        print(f"Loading existing transactions from {csv_path}...")
        df = pd.read_csv(csv_path)
    else:
        print("Dataset not found. Generating synthetic dataset...")
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        gen = SyntheticDataGenerator(DatasetConfig(seed=seed, num_transactions=25000))
        df = gen.generate()
        df.to_csv(csv_path, index=False)

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by="timestamp").reset_index(drop=True)

    # 2. Strict Chronological Split (70% Train, 15% Validation, 15% Held-Out Test)
    n = len(df)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    df_train = df.iloc[:train_end].copy()
    df_val = df.iloc[train_end:val_end].copy()
    df_test = df.iloc[val_end:].copy()

    print(
        f"Dataset split: Train={len(df_train)}, Val={len(df_val)}, Test={len(df_test)}"
    )
    print(f"Train fraud rate: {df_train['is_fraud'].mean():.4f}")
    print(f"Val fraud rate: {df_val['is_fraud'].mean():.4f}")
    print(f"Test fraud rate: {df_test['is_fraud'].mean():.4f}")

    # 3. Fit feature pipeline on Train and transform sequentially
    pipeline = FeaturePipeline()
    X_train, y_train = pipeline.fit_transform(df_train)
    X_val, y_val = pipeline.transform(df_val, update_state=True)
    _X_test, y_test = pipeline.transform(df_test, update_state=True)

    assert y_val is not None and y_test is not None

    # 4. Train LightGBM Binary Classifier
    print("Training LightGBM classifier...")
    lgbm = LGBMClassifier(
        n_estimators=150,
        learning_rate=0.05,
        max_depth=6,
        num_leaves=31,
        class_weight="balanced",
        random_state=seed,
        n_jobs=-1,
        verbose=-1,
    )
    lgbm.fit(X_train, y_train)

    # 5. Tune Decision Threshold on VALIDATION set only
    val_probs_raw = lgbm.predict_proba(X_val)
    val_probs = np.asarray(val_probs_raw)[:, 1]

    best_threshold = 0.5
    best_score = -1.0
    threshold_candidates = np.arange(0.10, 0.90, 0.01)

    for thresh in threshold_candidates:
        val_preds = (val_probs >= thresh).astype(int)
        score = f1_score(y_val, val_preds, zero_division=0)
        if score > best_score:
            best_score = float(score)
            best_threshold = float(thresh)

    print(
        f"Optimal Validation Threshold: {best_threshold:.2f} (Validation F1: {best_score:.4f})"
    )

    # 6. Save model and metadata artifacts
    model_file = models_path / "lightgbm_model.joblib"
    pipeline_file = models_path / "feature_pipeline.joblib"
    meta_file = models_path / "model_metadata.json"

    joblib.dump(lgbm, model_file)
    joblib.dump(pipeline, pipeline_file)

    metadata = {
        "model_type": "LightGBM Binary Classifier",
        "algorithm": "lightgbm.LGBMClassifier",
        "version": "0.1.0",
        "feature_names": pipeline.feature_columns,
        "feature_count": len(pipeline.feature_columns),
        "selected_validation_threshold": round(best_threshold, 4),
        "validation_f1_at_threshold": round(best_score, 4),
        "cost_per_fp_inr": cost_per_fp,
        "hyperparameters": {
            "n_estimators": 150,
            "learning_rate": 0.05,
            "max_depth": 6,
            "num_leaves": 31,
            "class_weight": "balanced",
            "random_state": seed,
        },
        "dataset_summary": {
            "total_records": n,
            "train_size": len(df_train),
            "val_size": len(df_val),
            "test_size": len(df_test),
            "train_fraud_rate": float(round(df_train["is_fraud"].mean(), 4)),
            "val_fraud_rate": float(round(df_val["is_fraud"].mean(), 4)),
            "test_fraud_rate": float(round(df_test["is_fraud"].mean(), 4)),
            "split_type": "Strict Chronological Temporal Split (70/15/15)",
        },
    }

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Artifacts persisted to {models_path}")
    return metadata


if __name__ == "__main__":
    train_model()
