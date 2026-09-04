"""Unit tests for synthetic dataset generator."""

import pandas as pd

from ml.data.generator import DatasetConfig, SyntheticDataGenerator


def test_synthetic_data_generator_deterministic_seed() -> None:
    """Verify that same seed generates identical dataset."""
    config1 = DatasetConfig(seed=42, num_transactions=200)
    config2 = DatasetConfig(seed=42, num_transactions=200)

    df1 = SyntheticDataGenerator(config1).generate()
    df2 = SyntheticDataGenerator(config2).generate()

    pd.testing.assert_frame_equal(df1, df2)


def test_synthetic_dataset_schema_and_entities() -> None:
    """Verify required entity identifiers and feature columns exist."""
    config = DatasetConfig(seed=123, num_transactions=500)
    df = SyntheticDataGenerator(config).generate()

    required_columns = [
        "transaction_id",
        "timestamp",
        "customer_id",
        "customer_account_age_days",
        "merchant_id",
        "merchant_category",
        "amount",
        "payment_method",
        "device_id",
        "ip_address",
        "card_id",
        "city",
        "is_fraud",
        "fraud_scenario",
    ]

    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"

    assert len(df) == 500
    assert set(df["is_fraud"].unique()).issubset({0, 1})
    assert df["amount"].min() > 0


def test_fraud_scenarios_presence() -> None:
    """Verify presence of both individual anomalies and coordinated network patterns."""
    config = DatasetConfig(seed=42, num_transactions=2000, target_fraud_rate=0.05)
    df = SyntheticDataGenerator(config).generate()

    scenarios = set(df["fraud_scenario"].unique())
    assert "legitimate" in scenarios
    assert "individual_anomaly" in scenarios
    assert any("coordinated" in s for s in scenarios)

    fraud_df = df[df["is_fraud"] == 1]
    assert len(fraud_df) > 0
    assert (fraud_df["fraud_scenario"] != "legitimate").all()
