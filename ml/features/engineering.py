"""FraudDNA Temporal & Leakage-Safe Feature Engineering Pipeline.

Computes point-in-time features strictly using past observations (t < T_current)
to prevent data leakage across train, validation, and held-out test splits.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


@dataclass
class EntityHistoricalState:
    """Maintains point-in-time historical state for feature generation."""

    customer_tx_times: dict[str, list[datetime]] = field(
        default_factory=lambda: defaultdict(list)
    )
    customer_tx_amounts: dict[str, list[float]] = field(
        default_factory=lambda: defaultdict(list)
    )
    device_tx_times: dict[str, list[datetime]] = field(
        default_factory=lambda: defaultdict(list)
    )
    device_customers: dict[str, set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )
    ip_tx_times: dict[str, list[datetime]] = field(
        default_factory=lambda: defaultdict(list)
    )
    ip_customers: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    card_tx_times: dict[str, list[datetime]] = field(
        default_factory=lambda: defaultdict(list)
    )
    card_customers: dict[str, set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )


class FeaturePipeline:
    """Leak-free feature engineering pipeline for transaction risk modeling."""

    def __init__(self) -> None:
        self.state = EntityHistoricalState()
        self.is_fitted = False
        self.global_mean_amount: float = 2500.0
        self.merchant_cat_encoder: dict[str, int] = {}
        self.payment_method_encoder: dict[str, int] = {}
        self.feature_columns: list[str] = []

    def _compute_point_in_time_features(
        self,
        df: pd.DataFrame,
        update_state: bool = True,
    ) -> pd.DataFrame:
        """Compute point-in-time historical features sequentially without future leakage."""
        df_sorted = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df_sorted["timestamp"]):
            df_sorted["timestamp"] = pd.to_datetime(df_sorted["timestamp"])
        df_sorted = df_sorted.sort_values(by="timestamp").reset_index(drop=True)

        n = len(df_sorted)
        cust_prior_tx_count = np.zeros(n, dtype=np.float32)
        cust_prior_mean_amt = np.zeros(n, dtype=np.float32)
        cust_amount_ratio = np.zeros(n, dtype=np.float32)
        cust_hours_since_last = np.zeros(n, dtype=np.float32)

        dev_prior_customers = np.zeros(n, dtype=np.float32)
        dev_velocity_24h = np.zeros(n, dtype=np.float32)

        ip_prior_customers = np.zeros(n, dtype=np.float32)
        ip_velocity_24h = np.zeros(n, dtype=np.float32)

        card_prior_customers = np.zeros(n, dtype=np.float32)
        card_velocity_24h = np.zeros(n, dtype=np.float32)

        for i in range(n):
            row = df_sorted.iloc[i]
            cid = str(row["customer_id"])
            did = str(row["device_id"])
            ipid = str(row["ip_address"])
            crd = str(row["card_id"])
            amt = float(row["amount"])
            raw_ts = row["timestamp"]
            ts: datetime = (
                raw_ts.to_pydatetime() if hasattr(raw_ts, "to_pydatetime") else raw_ts
            )

            # 1. Customer History Features
            c_times = self.state.customer_tx_times[cid]
            c_amts = self.state.customer_tx_amounts[cid]

            cust_prior_tx_count[i] = len(c_times)
            if c_times:
                prior_mean = float(np.mean(c_amts))
                cust_prior_mean_amt[i] = prior_mean
                cust_amount_ratio[i] = amt / max(prior_mean, 1.0)
                last_time = c_times[-1]
                delta_hrs = (ts - last_time).total_seconds() / 3600.0
                cust_hours_since_last[i] = min(max(delta_hrs, 0.0), 720.0)
            else:
                cust_prior_mean_amt[i] = self.global_mean_amount
                cust_amount_ratio[i] = amt / self.global_mean_amount
                cust_hours_since_last[i] = 720.0

            # 2. Device Features
            dev_custs = self.state.device_customers[did]
            dev_prior_customers[i] = len(dev_custs)
            d_times = self.state.device_tx_times[did]
            cutoff_24h = ts - timedelta(hours=24)
            dev_velocity_24h[i] = sum(1 for t in reversed(d_times) if t >= cutoff_24h)

            # 3. IP Features
            ip_custs = self.state.ip_customers[ipid]
            ip_prior_customers[i] = len(ip_custs)
            i_times = self.state.ip_tx_times[ipid]
            ip_velocity_24h[i] = sum(1 for t in reversed(i_times) if t >= cutoff_24h)

            # 4. Card Features
            card_custs = self.state.card_customers[crd]
            card_prior_customers[i] = len(card_custs)
            card_times = self.state.card_tx_times[crd]
            card_velocity_24h[i] = sum(
                1 for t in reversed(card_times) if t >= cutoff_24h
            )

            if update_state:
                self.state.customer_tx_times[cid].append(ts)
                self.state.customer_tx_amounts[cid].append(amt)
                self.state.device_tx_times[did].append(ts)
                self.state.device_customers[did].add(cid)
                self.state.ip_tx_times[ipid].append(ts)
                self.state.ip_customers[ipid].add(cid)
                self.state.card_tx_times[crd].append(ts)
                self.state.card_customers[crd].add(cid)

        feat_df = df_sorted.copy()
        feat_df["cust_prior_tx_count"] = cust_prior_tx_count
        feat_df["cust_prior_mean_amt"] = cust_prior_mean_amt
        feat_df["cust_amount_ratio"] = cust_amount_ratio
        feat_df["cust_hours_since_last"] = cust_hours_since_last

        feat_df["dev_prior_customers"] = dev_prior_customers
        feat_df["dev_velocity_24h"] = dev_velocity_24h

        feat_df["ip_prior_customers"] = ip_prior_customers
        feat_df["ip_velocity_24h"] = ip_velocity_24h

        feat_df["card_prior_customers"] = card_prior_customers
        feat_df["card_velocity_24h"] = card_velocity_24h

        feat_df["log_amount"] = np.log1p(feat_df["amount"].astype(float))
        feat_df["hour_of_day"] = feat_df["timestamp"].dt.hour
        feat_df["day_of_week"] = feat_df["timestamp"].dt.dayofweek
        feat_df["is_night"] = (
            (feat_df["hour_of_day"] >= 0) & (feat_df["hour_of_day"] < 6)
        ).astype(int)

        return feat_df

    def fit(self, df_train: pd.DataFrame) -> "FeaturePipeline":
        """Fit feature encoders and baseline statistics on training data only."""
        if not pd.api.types.is_datetime64_any_dtype(df_train["timestamp"]):
            df_train = df_train.copy()
            df_train["timestamp"] = pd.to_datetime(df_train["timestamp"])

        self.global_mean_amount = float(df_train["amount"].mean())

        mcats = sorted(df_train["merchant_category"].dropna().unique().tolist())
        self.merchant_cat_encoder = {cat: idx for idx, cat in enumerate(mcats)}

        pmethods = sorted(df_train["payment_method"].dropna().unique().tolist())
        self.payment_method_encoder = {pm: idx for idx, pm in enumerate(pmethods)}

        self.is_fitted = True
        return self

    def transform(
        self, df: pd.DataFrame, update_state: bool = True
    ) -> tuple[pd.DataFrame, np.ndarray | None]:
        """Transform raw dataframe into numeric feature matrix X and target y."""
        if not self.is_fitted:
            raise RuntimeError(
                "FeaturePipeline must be fitted on training data before transform."
            )

        feat_df = self._compute_point_in_time_features(df, update_state=update_state)

        feat_df["merchant_cat_code"] = feat_df["merchant_category"].map(
            lambda x: self.merchant_cat_encoder.get(str(x), -1)
        )
        feat_df["payment_method_code"] = feat_df["payment_method"].map(
            lambda x: self.payment_method_encoder.get(str(x), -1)
        )

        self.feature_columns = [
            "amount",
            "log_amount",
            "customer_account_age_days",
            "hour_of_day",
            "day_of_week",
            "is_night",
            "merchant_cat_code",
            "payment_method_code",
            "cust_prior_tx_count",
            "cust_prior_mean_amt",
            "cust_amount_ratio",
            "cust_hours_since_last",
            "dev_prior_customers",
            "dev_velocity_24h",
            "ip_prior_customers",
            "ip_velocity_24h",
            "card_prior_customers",
            "card_velocity_24h",
        ]

        X = feat_df[self.feature_columns].copy()
        X = X.fillna(0.0).replace([np.inf, -np.inf], 0.0)

        y = (
            np.asarray(feat_df["is_fraud"].values)
            if "is_fraud" in feat_df.columns
            else None
        )

        return X, y

    def fit_transform(self, df_train: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
        """Fit encoders on training data and transform."""
        self.fit(df_train)
        X, y = self.transform(df_train, update_state=True)
        if y is None:
            raise ValueError("Target 'is_fraud' column missing from training set.")
        return X, y
