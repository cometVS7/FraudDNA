"""Unit tests for temporal leakage-safe feature pipeline."""

import numpy as np
import pandas as pd

from ml.data.generator import DatasetConfig, SyntheticDataGenerator
from ml.features.engineering import FeaturePipeline


def test_feature_pipeline_no_future_leakage() -> None:
    """Verify that altering future transactions does not change past features."""
    config = DatasetConfig(seed=42, num_transactions=200)
    df = SyntheticDataGenerator(config).generate()

    # Split into first 100 and remaining 100
    df_first_100 = df.iloc[:100].copy()

    # Create mutated future where subsequent transactions have extreme amounts
    df_mutated_future = df.copy()
    df_mutated_future.iloc[100:, df_mutated_future.columns.get_loc("amount")] = 999999.0

    # Fit pipeline on normal dataset
    p1 = FeaturePipeline()
    p1.fit(df_first_100)
    X1, _ = p1.transform(df_first_100, update_state=True)

    # Transform mutated future dataset
    p2 = FeaturePipeline()
    p2.fit(df_first_100)
    X2_full, _ = p2.transform(df_mutated_future, update_state=True)
    X2_first_100 = X2_full.iloc[:100].copy()

    # Features for the first 100 transactions must be identical regardless of future values
    pd.testing.assert_frame_equal(X1, X2_first_100)


def test_feature_pipeline_output_integrity() -> None:
    """Verify that feature transformation returns non-empty, finite numeric matrices."""
    config = DatasetConfig(seed=99, num_transactions=300)
    df = SyntheticDataGenerator(config).generate()

    pipeline = FeaturePipeline()
    X, y = pipeline.fit_transform(df)

    assert len(X) == 300
    assert y is not None
    assert len(y) == 300
    assert not X.isnull().values.any()
    assert not np.isinf(X.values).any()
    assert len(pipeline.feature_columns) > 10
