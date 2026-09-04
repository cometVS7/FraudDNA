"""FraudDNA Synthetic Payment Dataset Generator.

Generates realistic payment transaction records containing entity relationships
(Customer, Transaction, Device, IP, Card, Merchant) and known ground-truth fraud patterns.

Supports:
- Pattern A: Individual anomalous transactions (amount spikes, off-hour velocity)
- Pattern B: Coordinated abuse networks (device-sharing collusion rings, IP proxy farms, card testing)
- Legitimate baseline transactions with realistic distributions and diurnal cycles.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class DatasetConfig:
    """Configuration parameters for synthetic dataset generation."""

    num_transactions: int = 25000
    num_customers: int = 2000
    num_merchants: int = 150
    num_devices: int = 3000
    num_ips: int = 3500
    num_cards: int = 2500
    seed: int = 42
    start_date: datetime = field(
        default_factory=lambda: datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    )
    days_duration: int = 60
    target_fraud_rate: float = 0.045  # ~4.5% overall fraud


MERCHANT_CATEGORIES = [
    "electronics",
    "digital_goods",
    "fashion",
    "groceries",
    "travel",
    "luxury_goods",
    "utility",
    "crypto_exchange",
    "food_delivery",
    "gaming",
]

PAYMENT_METHODS = ["credit_card", "debit_card", "upi", "netbanking", "wallet"]

CITIES = [
    "Bengaluru",
    "Mumbai",
    "Delhi NCR",
    "Hyderabad",
    "Chennai",
    "Pune",
    "Kolkata",
    "Ahmedabad",
    "Jaipur",
    "Lucknow",
]


class SyntheticDataGenerator:
    """Deterministic generator for synthetic fraud and coordinated abuse dataset."""

    def __init__(self, config: DatasetConfig | None = None) -> None:
        self.config = config or DatasetConfig()
        self.rng = np.random.default_rng(self.config.seed)

    def generate(self) -> pd.DataFrame:
        """Generate full synthetic transaction dataset with entity graph relationships."""
        cfg = self.config

        # 1. Initialize Customer Profiles
        customer_ids = [f"cust_{i:05d}" for i in range(cfg.num_customers)]
        customer_base_amount_mean = np.exp(
            self.rng.normal(loc=7.5, scale=0.8, size=cfg.num_customers)
        )  # ~₹1,800 median
        customer_city = self.rng.choice(CITIES, size=cfg.num_customers)
        customer_account_age_days = self.rng.integers(10, 1000, size=cfg.num_customers)

        # 2. Initialize Merchant Profiles
        merchant_ids = [f"merch_{i:04d}" for i in range(cfg.num_merchants)]
        merchant_cats = self.rng.choice(
            MERCHANT_CATEGORIES,
            size=cfg.num_merchants,
            p=[0.12, 0.15, 0.15, 0.18, 0.08, 0.05, 0.10, 0.04, 0.10, 0.03],
        )

        # 3. Initialize Device, IP, Card Pools
        device_pool = [f"dev_{i:05d}" for i in range(cfg.num_devices)]
        ip_pool = [
            f"198.51.{self.rng.integers(1, 255)}.{self.rng.integers(1, 255)}"
            for _ in range(cfg.num_ips)
        ]
        card_pool = [f"card_{i:05d}" for i in range(cfg.num_cards)]

        # Map typical primary device/card to each customer
        customer_primary_dev = {
            cid: self.rng.choice(device_pool) for cid in customer_ids
        }
        customer_primary_ip = {cid: self.rng.choice(ip_pool) for cid in customer_ids}
        customer_primary_card = {
            cid: self.rng.choice(card_pool) for cid in customer_ids
        }

        # Calculate target counts
        total_n = cfg.num_transactions
        fraud_target_n = int(total_n * cfg.target_fraud_rate)

        # Fraud allocations:
        # ~35% Pattern A (Individual Anomalies)
        # ~65% Pattern B (Coordinated Rings)
        n_pattern_a = int(fraud_target_n * 0.35)
        n_pattern_b = fraud_target_n - n_pattern_a
        n_legitimate = total_n - fraud_target_n

        records: list[dict[str, Any]] = []

        # ==========================================
        # Generate Legitimate Transactions
        # ==========================================
        hour_weights = [
            0.01,
            0.005,
            0.005,
            0.005,
            0.01,
            0.02,
            0.03,
            0.04,
            0.05,
            0.06,
            0.07,
            0.07,
            0.08,
            0.07,
            0.06,
            0.06,
            0.06,
            0.07,
            0.08,
            0.07,
            0.06,
            0.04,
            0.03,
            0.02,
        ]
        hour_probs = np.array(hour_weights) / sum(hour_weights)

        for _ in range(n_legitimate):
            c_idx = int(self.rng.integers(0, cfg.num_customers))
            cid = customer_ids[c_idx]
            base_amt = float(customer_base_amount_mean[c_idx])

            amt = float(
                np.clip(
                    self.rng.lognormal(mean=np.log(max(base_amt, 100)), sigma=0.45),
                    50.0,
                    150000.0,
                )
            )

            day_offset = int(self.rng.integers(0, cfg.days_duration))
            hour = int(self.rng.choice(24, p=hour_probs))
            minute = int(self.rng.integers(0, 60))
            second = int(self.rng.integers(0, 60))
            tx_time = cfg.start_date + timedelta(
                days=day_offset, hours=hour, minutes=minute, seconds=second
            )

            m_idx = int(self.rng.integers(0, cfg.num_merchants))
            mid = merchant_ids[m_idx]
            mcat = merchant_cats[m_idx]

            dev = (
                customer_primary_dev[cid]
                if self.rng.random() < 0.90
                else self.rng.choice(device_pool)
            )
            ip = (
                customer_primary_ip[cid]
                if self.rng.random() < 0.88
                else self.rng.choice(ip_pool)
            )
            card = (
                customer_primary_card[cid]
                if self.rng.random() < 0.92
                else self.rng.choice(card_pool)
            )
            pmethod = str(
                self.rng.choice(PAYMENT_METHODS, p=[0.35, 0.25, 0.25, 0.10, 0.05])
            )

            records.append(
                {
                    "transaction_id": f"tx_{len(records):07d}",
                    "timestamp": tx_time,
                    "customer_id": cid,
                    "customer_account_age_days": int(customer_account_age_days[c_idx]),
                    "merchant_id": mid,
                    "merchant_category": mcat,
                    "amount": round(amt, 2),
                    "payment_method": pmethod,
                    "device_id": dev,
                    "ip_address": ip,
                    "card_id": card,
                    "city": customer_city[c_idx],
                    "is_fraud": 0,
                    "fraud_scenario": "legitimate",
                }
            )

        # ==========================================
        # Generate Pattern A: Individual Suspicious Transactions
        # ==========================================
        high_risk_mcats = [
            "crypto_exchange",
            "digital_goods",
            "luxury_goods",
            "electronics",
            "gaming",
        ]
        for _ in range(n_pattern_a):
            c_idx = int(self.rng.integers(0, cfg.num_customers))
            cid = customer_ids[c_idx]
            base_amt = float(customer_base_amount_mean[c_idx])

            amt = float(
                base_amt * self.rng.uniform(4.0, 12.0) + self.rng.uniform(5000, 25000)
            )
            amt = min(amt, 350000.0)

            day_offset = int(self.rng.integers(0, cfg.days_duration))
            hour = int(self.rng.choice([1, 2, 3, 4, 5, 23]))
            minute = int(self.rng.integers(0, 60))
            second = int(self.rng.integers(0, 60))
            tx_time = cfg.start_date + timedelta(
                days=day_offset, hours=hour, minutes=minute, seconds=second
            )

            mid = self.rng.choice(merchant_ids)
            mcat = str(self.rng.choice(high_risk_mcats))

            dev = f"dev_anom_{self.rng.integers(1000, 9999)}"
            ip = f"203.0.113.{self.rng.integers(1, 254)}"
            card = self.rng.choice(card_pool)

            records.append(
                {
                    "transaction_id": f"tx_{len(records):07d}",
                    "timestamp": tx_time,
                    "customer_id": cid,
                    "customer_account_age_days": max(
                        5, int(customer_account_age_days[c_idx]) - 100
                    ),
                    "merchant_id": mid,
                    "merchant_category": mcat,
                    "amount": round(amt, 2),
                    "payment_method": "credit_card",
                    "device_id": dev,
                    "ip_address": ip,
                    "card_id": card,
                    "city": self.rng.choice(CITIES),
                    "is_fraud": 1,
                    "fraud_scenario": "individual_anomaly",
                }
            )

        # ==========================================
        # Generate Pattern B: Coordinated Abuse Networks (FraudDNA Core)
        # Distributed across 4 campaigns over the 60-day timeline
        # ==========================================
        campaign_windows = [
            (5, 12),  # Early period
            (18, 25),  # Mid-early period
            (33, 42),  # Validation window period
            (48, 57),  # Held-out test period
        ]

        n_dev_ring = int(n_pattern_b * 0.45)
        n_ip_ring = int(n_pattern_b * 0.35)
        n_card_ring = n_pattern_b - n_dev_ring - n_ip_ring

        # 1. Coordinated Device-Sharing Rings
        dev_ring_devices = [
            "dev_syndicate_alpha_01",
            "dev_syndicate_alpha_02",
            "dev_syndicate_alpha_03",
            "dev_syndicate_alpha_04",
        ]
        dev_ring_customers = [f"cust_synth_d_{k:03d}" for k in range(40)]
        dev_ring_cards = [f"card_synth_d_{k:03d}" for k in range(25)]

        for k in range(n_dev_ring):
            cid = str(self.rng.choice(dev_ring_customers))
            card = str(self.rng.choice(dev_ring_cards))
            amt = float(self.rng.uniform(2500.0, 9500.0))

            camp_idx = k % len(campaign_windows)
            camp_start, camp_end = campaign_windows[camp_idx]
            day_offset = int(self.rng.integers(camp_start, camp_end))
            hour = int(self.rng.integers(0, 24))
            minute = int(self.rng.integers(0, 60))
            second = int(self.rng.integers(0, 60))
            tx_time = cfg.start_date + timedelta(
                days=day_offset, hours=hour, minutes=minute, seconds=second
            )

            m_idx = int(self.rng.integers(0, cfg.num_merchants))
            mid = merchant_ids[m_idx]
            mcat = merchant_cats[m_idx]
            dev = dev_ring_devices[camp_idx]

            records.append(
                {
                    "transaction_id": f"tx_{len(records):07d}",
                    "timestamp": tx_time,
                    "customer_id": cid,
                    "customer_account_age_days": int(self.rng.integers(2, 30)),
                    "merchant_id": mid,
                    "merchant_category": mcat,
                    "amount": round(amt, 2),
                    "payment_method": "credit_card",
                    "device_id": dev,
                    "ip_address": f"198.51.100.{self.rng.integers(1, 50)}",
                    "card_id": card,
                    "city": "Bengaluru",
                    "is_fraud": 1,
                    "fraud_scenario": "coordinated_device_ring",
                }
            )

        # 2. Coordinated IP Proxy Farm Rings
        ip_farm_ips = ["198.51.44.77", "198.51.44.88", "198.51.44.99", "198.51.44.111"]
        ip_farm_customers = [f"cust_synth_ip_{k:03d}" for k in range(50)]
        ip_farm_devices = [f"dev_synth_ip_{k:03d}" for k in range(40)]

        for k in range(n_ip_ring):
            cid = str(self.rng.choice(ip_farm_customers))
            dev = str(self.rng.choice(ip_farm_devices))
            amt = float(self.rng.uniform(1800.0, 7500.0))

            camp_idx = k % len(campaign_windows)
            camp_start, camp_end = campaign_windows[camp_idx]
            day_offset = int(self.rng.integers(camp_start, camp_end))
            hour = int(self.rng.integers(0, 24))
            minute = int(self.rng.integers(0, 60))
            second = int(self.rng.integers(0, 60))
            tx_time = cfg.start_date + timedelta(
                days=day_offset, hours=hour, minutes=minute, seconds=second
            )

            mid = str(self.rng.choice(merchant_ids))
            mcat = str(
                self.rng.choice(["digital_goods", "gaming", "electronics", "fashion"])
            )
            ip = ip_farm_ips[camp_idx]

            records.append(
                {
                    "transaction_id": f"tx_{len(records):07d}",
                    "timestamp": tx_time,
                    "customer_id": cid,
                    "customer_account_age_days": int(self.rng.integers(1, 20)),
                    "merchant_id": mid,
                    "merchant_category": mcat,
                    "amount": round(amt, 2),
                    "payment_method": "upi",
                    "device_id": dev,
                    "ip_address": ip,
                    "card_id": f"card_synth_ip_{k % 20:03d}",
                    "city": "Delhi NCR",
                    "is_fraud": 1,
                    "fraud_scenario": "coordinated_ip_farm",
                }
            )

        # 3. Coordinated Card Testing Rings
        card_testing_cards = [
            "card_stolen_sigma_01",
            "card_stolen_sigma_02",
            "card_stolen_sigma_03",
            "card_stolen_sigma_04",
        ]
        card_ring_customers = [f"cust_synth_c_{k:03d}" for k in range(35)]

        for k in range(n_card_ring):
            cid = str(self.rng.choice(card_ring_customers))
            camp_idx = k % len(campaign_windows)
            card = card_testing_cards[camp_idx]
            dev = f"dev_c_test_{k % 12:03d}"
            amt = float(self.rng.uniform(150.0, 4500.0))

            camp_start, camp_end = campaign_windows[camp_idx]
            day_offset = int(self.rng.integers(camp_start, camp_end))
            hour = int(self.rng.integers(0, 24))
            minute = int(self.rng.integers(0, 60))
            second = int(self.rng.integers(0, 60))
            tx_time = cfg.start_date + timedelta(
                days=day_offset, hours=hour, minutes=minute, seconds=second
            )

            mid = str(self.rng.choice(merchant_ids))
            mcat = str(self.rng.choice(["digital_goods", "groceries", "utility"]))

            records.append(
                {
                    "transaction_id": f"tx_{len(records):07d}",
                    "timestamp": tx_time,
                    "customer_id": cid,
                    "customer_account_age_days": int(self.rng.integers(3, 40)),
                    "merchant_id": mid,
                    "merchant_category": mcat,
                    "amount": round(amt, 2),
                    "payment_method": "credit_card",
                    "device_id": dev,
                    "ip_address": f"198.51.88.{self.rng.integers(1, 100)}",
                    "card_id": card,
                    "city": "Mumbai",
                    "is_fraud": 1,
                    "fraud_scenario": "coordinated_card_cycle",
                }
            )

        df = pd.DataFrame(records)
        df = df.sort_values(by="timestamp").reset_index(drop=True)
        df["transaction_id"] = [f"tx_{idx:07d}" for idx in range(len(df))]

        return df


def generate_and_save_dataset(
    output_path: str = "ml/data/transactions.csv",
    seed: int = 42,
    num_transactions: int = 25000,
) -> pd.DataFrame:
    """Generate dataset and save to disk."""
    config = DatasetConfig(seed=seed, num_transactions=num_transactions)
    generator = SyntheticDataGenerator(config)
    df = generator.generate()
    df.to_csv(output_path, index=False)
    return df


if __name__ == "__main__":
    df_gen = generate_and_save_dataset()
    print(f"Generated {len(df_gen)} transactions.")
    print(f"Fraud Rate: {df_gen['is_fraud'].mean():.4f}")
    print("Fraud Pattern Distribution:")
    print(df_gen["fraud_scenario"].value_counts())
