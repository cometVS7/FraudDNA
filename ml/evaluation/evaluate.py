"""FraudDNA Held-Out Test Set Evaluation Module.

Evaluates the trained LightGBM model on the held-out test split using the threshold
determined during validation. Calculates precision, recall, F1, PR-AUC, confusion matrix,
FPR, and false-positive monetary cost.
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
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from ml.features.engineering import FeaturePipeline


def evaluate_held_out(
    data_path: str | Path = "ml/data/transactions.csv",
    models_dir: str | Path = "ml/models",
    output_metrics_path: str | Path = "ml/evaluation/metrics.json",
    cost_per_fp: float = 350.0,
) -> dict[str, Any]:
    """Perform unbiased evaluation on held-out test split."""
    models_path = Path(models_dir)
    meta_path = models_path / "model_metadata.json"
    model_path = models_path / "lightgbm_model.joblib"

    if not model_path.exists() or not meta_path.exists():
        raise FileNotFoundError(
            "Trained model or metadata not found. Run training first."
        )

    # Load artifacts
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    threshold = float(metadata["selected_validation_threshold"])
    model = joblib.load(model_path)

    # Load dataset
    csv_path = Path(data_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset {csv_path} does not exist.")

    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by="timestamp").reset_index(drop=True)

    n = len(df)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    df_train = df.iloc[:train_end].copy()
    df_val = df.iloc[train_end:val_end].copy()
    df_test = df.iloc[val_end:].copy()

    # Reconstruct state cleanly across Train -> Val -> Test
    pipeline = FeaturePipeline()
    pipeline.fit(df_train)
    _ = pipeline.transform(df_train, update_state=True)
    _ = pipeline.transform(df_val, update_state=True)
    X_test, y_test = pipeline.transform(df_test, update_state=True)

    if y_test is None:
        raise ValueError("Held-out test set missing target labels.")

    # Model inference
    raw_probs = model.predict_proba(X_test)
    y_probs = np.asarray(raw_probs)[:, 1]
    y_preds = (y_probs >= threshold).astype(int)

    # Core Metrics
    prec = float(precision_score(y_test, y_preds, zero_division=0))
    rec = float(recall_score(y_test, y_preds, zero_division=0))
    f1 = float(f1_score(y_test, y_preds, zero_division=0))
    pr_auc = float(average_precision_score(y_test, y_probs))
    roc_auc = float(roc_auc_score(y_test, y_probs))

    cm = confusion_matrix(y_test, y_preds)
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    # Financial & False-Positive Cost Calculations
    fp_monetary_cost = round(float(fp * cost_per_fp), 2)

    test_amounts = df_test["amount"].values
    total_fraud_loss_exposure = float(round(float(test_amounts[y_test == 1].sum()), 2))
    fraud_prevented_amount = float(
        round(float(test_amounts[(y_test == 1) & (y_preds == 1)].sum()), 2)
    )
    fraud_missed_amount = float(
        round(float(test_amounts[(y_test == 1) & (y_preds == 0)].sum()), 2)
    )
    net_business_benefit = float(round(fraud_prevented_amount - fp_monetary_cost, 2))

    metrics_payload: dict[str, Any] = {
        "evaluation_type": "Synthetic Held-Out Test Set Evaluation",
        "held_out_test_size": len(df_test),
        "actual_fraud_count": int(y_test.sum()),
        "predicted_fraud_count": int(y_preds.sum()),
        "selected_operating_threshold": threshold,
        "metrics": {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "pr_auc": round(pr_auc, 4),
            "roc_auc": round(roc_auc, 4),
            "false_positive_rate": round(fpr, 4),
        },
        "confusion_matrix": {
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "true_positives": tp,
        },
        "cost_and_financial_impact": {
            "cost_per_false_positive_inr": cost_per_fp,
            "false_positive_count": fp,
            "false_positive_monetary_cost_inr": fp_monetary_cost,
            "total_fraud_loss_exposure_inr": total_fraud_loss_exposure,
            "fraud_prevented_amount_inr": fraud_prevented_amount,
            "fraud_missed_amount_inr": fraud_missed_amount,
            "net_business_benefit_inr": net_business_benefit,
        },
        "breakdown_by_scenario": {},
    }

    # Scenario Breakdown in Held-Out Test
    df_test_scored = df_test.copy()
    df_test_scored["pred_fraud"] = y_preds
    for scenario, group in df_test_scored.groupby("fraud_scenario"):
        scen_name = str(scenario)
        total_s = len(group)
        caught_s = int(group["pred_fraud"].sum())
        metrics_payload["breakdown_by_scenario"][scen_name] = {
            "total_count": total_s,
            "caught_count": caught_s,
            "catch_rate": round(caught_s / total_s, 4) if total_s > 0 else 0.0,
        }

    # Save metrics.json
    out_path = Path(output_metrics_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)

    print("=======================================================")
    print("      FraudDNA Held-Out Test Set Evaluation Report     ")
    print("=======================================================")
    print(f"Test Set Size:       {len(df_test):,} transactions")
    print(f"Actual Fraud Cases:  {int(y_test.sum())} ({y_test.mean():.2%})")
    print(f"Selected Threshold:  {threshold:.2f} (from validation set)")
    print("-------------------------------------------------------")
    print(f"Precision:           {prec:.4f}")
    print(f"Recall:              {rec:.4f}")
    print(f"F1 Score:            {f1:.4f}")
    print(f"PR-AUC:              {pr_auc:.4f}")
    print(f"ROC-AUC:             {roc_auc:.4f}")
    print(f"False Positive Rate: {fpr:.4f}")
    print("-------------------------------------------------------")
    print(f"Confusion Matrix:    TP={tp} | FP={fp} | TN={tn} | FN={fn}")
    print(f"FP Monetary Cost:    INR {fp_monetary_cost:,.2f} (@ INR {cost_per_fp}/FP)")
    print(f"Fraud Prevented:     INR {fraud_prevented_amount:,.2f}")
    print(f"Net Benefit:         INR {net_business_benefit:,.2f}")
    print("=======================================================")

    return metrics_payload


if __name__ == "__main__":
    evaluate_held_out()
