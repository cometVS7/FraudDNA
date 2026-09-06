"""FraudDNA Database Seeding and Ingestion Engine.

Provides an idempotent, batch-optimized mechanism to seed the V2 relational schema
from empirical repository artifacts:
1. Core transactions dataset: ml/data/transactions.csv
2. Model metadata: ml/models/model_metadata.json
3. Policy engine configuration: Phase 5 rule matrix
4. Knowledge intelligence sources: knowledge/
"""

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import (
    AccountModel,
    CardModel,
    CustomerModel,
    DeviceModel,
    IntelligenceSourceModel,
    IPAddressModel,
    MerchantModel,
    ModelRegistryModel,
    PolicyModel,
    TransactionModel,
)

logger = logging.getLogger(__name__)


@dataclass
class SeedResult:
    """Detailed summary of database seeding execution."""

    customers_inserted: int = 0
    accounts_inserted: int = 0
    cards_inserted: int = 0
    devices_inserted: int = 0
    ips_inserted: int = 0
    merchants_inserted: int = 0
    transactions_inserted: int = 0
    models_inserted: int = 0
    policies_inserted: int = 0
    sources_inserted: int = 0
    total_records_processed: int = 0
    is_idempotent: bool = True
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DatabaseSeeder:
    """Manages deterministic and idempotent ingestion into the V2 relational database."""

    def __init__(
        self,
        data_path: str | Path = "ml/data/transactions.csv",
        models_dir: str | Path = "ml/models",
        knowledge_dir: str | Path = "knowledge",
    ) -> None:
        self.data_path = Path(data_path)
        self.models_dir = Path(models_dir)
        self.knowledge_dir = Path(knowledge_dir)

    def _resolve_paths(self) -> None:
        """Resolve candidate relative paths when running from root or backend/."""
        if not self.data_path.exists():
            alt = Path("..") / self.data_path
            if alt.exists():
                self.data_path = alt

        if not self.models_dir.exists():
            alt = Path("..") / self.models_dir
            if alt.exists():
                self.models_dir = alt

        if not self.knowledge_dir.exists():
            alt = Path("..") / self.knowledge_dir
            if alt.exists():
                self.knowledge_dir = alt

    def seed_sync(self, session: Session, batch_size: int = 5000) -> SeedResult:
        """Execute synchronous database seeding."""
        import time

        self._resolve_paths()
        t0 = time.perf_counter()
        result = SeedResult()

        logger.info("Beginning FraudDNA V2 synchronous database seeding...")

        # 1. Seed Model Registry from model_metadata.json
        result.models_inserted = self._seed_model_registry(session)

        # 2. Seed Policy Matrix
        result.policies_inserted = self._seed_policy(session)

        # 3. Seed Intelligence Sources from knowledge/
        result.sources_inserted = self._seed_intelligence_sources(session)

        # 4. Ingest Transactions & Core Entities
        if self.data_path.exists():
            df = pd.read_csv(self.data_path)
            result.total_records_processed = len(df)

            # Ingest entities
            result.customers_inserted = self._seed_customers(session, df)
            result.accounts_inserted = self._seed_accounts(session, df)
            result.cards_inserted = self._seed_cards(session, df)
            result.devices_inserted = self._seed_devices(session, df)
            result.ips_inserted = self._seed_ips(session, df)
            result.merchants_inserted = self._seed_merchants(session, df)

            # Ingest transactions
            result.transactions_inserted = self._seed_transactions(
                session, df, batch_size=batch_size
            )
            del df

        session.commit()
        result.elapsed_seconds = round(time.perf_counter() - t0, 3)
        logger.info(
            f"Seeding completed in {result.elapsed_seconds}s. "
            f"Txs={result.transactions_inserted}, Custs={result.customers_inserted}, "
            f"Cards={result.cards_inserted}, Devs={result.devices_inserted}, IPs={result.ips_inserted}"
        )
        return result

    def _seed_model_registry(self, session: Session) -> int:
        metadata_file = self.models_dir / "model_metadata.json"
        model_id = "mdl_lightgbm_v010"

        existing = session.execute(
            select(ModelRegistryModel).where(ModelRegistryModel.id == model_id)
        ).scalar_one_or_none()
        if existing is not None:
            return 0

        metadata: dict[str, Any] = {}
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)

        entry = ModelRegistryModel(
            id=model_id,
            model_name="LightGBM Binary Fraud Classifier",
            version=metadata.get("version", "0.1.0"),
            model_type=metadata.get("algorithm", "lightgbm.LGBMClassifier"),
            status="ACTIVE",
            operating_threshold=float(metadata.get("selected_validation_threshold", 0.37)),
            feature_names=metadata.get("feature_names", []),
            feature_count=int(metadata.get("feature_count", 18)),
            metrics={
                "validation_f1": metadata.get("validation_f1_at_threshold", 0.9872),
                "cost_per_fp_inr": metadata.get("cost_per_fp_inr", 350.0),
            },
            artifact_path=str(self.models_dir / "lightgbm_model.joblib"),
            created_at=datetime.now(UTC),
        )
        session.add(entry)
        session.flush()
        return 1

    def _seed_policy(self, session: Session) -> int:
        policy_id = "pol_2025_1"
        existing = session.execute(
            select(PolicyModel).where(PolicyModel.id == policy_id)
        ).scalar_one_or_none()
        if existing is not None:
            return 0

        policy = PolicyModel(
            id=policy_id,
            policy_name="FraudDNA Standard Deterministic Policy Matrix",
            version="2025.1",
            status="ACTIVE",
            rules_config={
                "hold_risk_threshold": 0.90,
                "allow_risk_threshold": 0.30,
                "review_risk_threshold_low": 0.30,
                "review_risk_threshold_high": 0.90,
                "cluster_hold_threshold": 0.70,
                "shared_device_hold_threshold": 1,
            },
            effective_from=datetime(2025, 1, 1, tzinfo=UTC),
            created_at=datetime.now(UTC),
        )
        session.add(policy)
        session.flush()
        return 1

    def _seed_intelligence_sources(self, session: Session) -> int:
        if not self.knowledge_dir.exists():
            return 0

        inserted = 0
        categories = {
            "policies": "POLICY",
            "historical_cases": "HISTORICAL_CASE",
            "guidelines": "FRAUD_GUIDELINE",
        }

        for subfolder, source_type in categories.items():
            folder_path = self.knowledge_dir / subfolder
            if not folder_path.exists():
                continue

            for file_path in folder_path.glob("*.md"):
                source_id = file_path.stem
                existing = session.execute(
                    select(IntelligenceSourceModel).where(IntelligenceSourceModel.id == source_id)
                ).scalar_one_or_none()
                if existing is not None:
                    continue

                content = file_path.read_text(encoding="utf-8")
                chash = hashlib.sha256(content.encode("utf-8")).hexdigest()
                title = source_id.replace("_", " ").replace("-", " ").title()

                entry = IntelligenceSourceModel(
                    id=source_id,
                    source_type=source_type,
                    title=title,
                    version="1.0",
                    content_hash=chash,
                    source_path=str(file_path),
                    created_at=datetime.now(UTC),
                )
                session.add(entry)
                inserted += 1

        session.flush()
        return inserted

    def _seed_customers(self, session: Session, df: pd.DataFrame) -> int:
        existing_ids = set(session.execute(select(CustomerModel.id)).scalars().all())
        unique_custs = df.drop_duplicates(subset=["customer_id"])

        new_customers = []
        for _, row in unique_custs.iterrows():
            cid = str(row["customer_id"])
            if cid in existing_ids:
                continue
            existing_ids.add(cid)
            new_customers.append(
                CustomerModel(
                    id=cid,
                    account_age_days=int(row.get("customer_account_age_days", 0)),
                    city=str(row["city"]) if "city" in row and pd.notna(row["city"]) else None,
                    status="ACTIVE",
                    risk_score=0.0,
                    risk_tier="LOW",
                )
            )

        if new_customers:
            session.add_all(new_customers)
            session.flush()
        return len(new_customers)

    def _seed_accounts(self, session: Session, df: pd.DataFrame) -> int:
        existing_ids = set(session.execute(select(AccountModel.id)).scalars().all())
        unique_custs = df.drop_duplicates(subset=["customer_id"])

        new_accounts = []
        for _, row in unique_custs.iterrows():
            cid = str(row["customer_id"])
            acc_id = f"acc_{cid}"
            if acc_id in existing_ids:
                continue
            existing_ids.add(acc_id)
            new_accounts.append(
                AccountModel(
                    id=acc_id,
                    customer_id=cid,
                    account_type="SAVINGS",
                    status="ACTIVE",
                    risk_score=0.0,
                    risk_tier="LOW",
                )
            )

        if new_accounts:
            session.add_all(new_accounts)
            session.flush()
        return len(new_accounts)

    def _seed_cards(self, session: Session, df: pd.DataFrame) -> int:
        existing_ids = set(session.execute(select(CardModel.id)).scalars().all())
        unique_cards = df.drop_duplicates(subset=["card_id"])

        new_cards = []
        for _, row in unique_cards.iterrows():
            crd = str(row["card_id"])
            if crd in existing_ids:
                continue
            existing_ids.add(crd)
            new_cards.append(
                CardModel(
                    id=crd,
                    card_type="CREDIT"
                    if "credit" in str(row.get("payment_method", "")).lower()
                    else "DEBIT",
                    status="ACTIVE",
                    risk_score=0.0,
                    risk_tier="LOW",
                )
            )

        if new_cards:
            session.add_all(new_cards)
            session.flush()
        return len(new_cards)

    def _seed_devices(self, session: Session, df: pd.DataFrame) -> int:
        existing_ids = set(session.execute(select(DeviceModel.id)).scalars().all())
        unique_devices = df.drop_duplicates(subset=["device_id"])

        new_devices = []
        for _, row in unique_devices.iterrows():
            dev = str(row["device_id"])
            if dev in existing_ids:
                continue
            existing_ids.add(dev)
            new_devices.append(
                DeviceModel(
                    id=dev,
                    device_fingerprint=dev,
                    status="ACTIVE",
                    risk_score=0.0,
                    risk_tier="LOW",
                )
            )

        if new_devices:
            session.add_all(new_devices)
            session.flush()
        return len(new_devices)

    def _seed_ips(self, session: Session, df: pd.DataFrame) -> int:
        existing_ids = set(session.execute(select(IPAddressModel.id)).scalars().all())
        unique_ips = df.drop_duplicates(subset=["ip_address"])

        new_ips = []
        for _, row in unique_ips.iterrows():
            raw_ip = str(row["ip_address"])
            ip_id = f"ip_{raw_ip}"
            if ip_id in existing_ids:
                continue
            existing_ids.add(ip_id)
            new_ips.append(
                IPAddressModel(
                    id=ip_id,
                    ip_address=raw_ip,
                    status="ACTIVE",
                    risk_score=0.0,
                    risk_tier="LOW",
                )
            )

        if new_ips:
            session.add_all(new_ips)
            session.flush()
        return len(new_ips)

    def _seed_merchants(self, session: Session, df: pd.DataFrame) -> int:
        existing_ids = set(session.execute(select(MerchantModel.id)).scalars().all())
        unique_merchants = df.drop_duplicates(subset=["merchant_id"])

        new_merchants = []
        for _, row in unique_merchants.iterrows():
            mid = str(row["merchant_id"])
            if mid in existing_ids:
                continue
            existing_ids.add(mid)
            new_merchants.append(
                MerchantModel(
                    id=mid,
                    merchant_category=str(row.get("merchant_category", "general")),
                    status="ACTIVE",
                    risk_score=0.0,
                    risk_tier="LOW",
                )
            )

        if new_merchants:
            session.add_all(new_merchants)
            session.flush()
        return len(new_merchants)

    def _seed_transactions(self, session: Session, df: pd.DataFrame, batch_size: int = 5000) -> int:
        existing_ids = set(session.execute(select(TransactionModel.id)).scalars().all())

        new_tx_objects = []
        for _, row in df.iterrows():
            tx_id = str(row["transaction_id"])
            if tx_id in existing_ids:
                continue
            existing_ids.add(tx_id)

            # Parse ISO timestamp
            ts_raw = row["timestamp"]
            if isinstance(ts_raw, str):
                ts = datetime.fromisoformat(ts_raw)
            else:
                ts = pd.to_datetime(ts_raw).to_pydatetime()
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)

            cid = str(row["customer_id"])
            raw_ip = str(row["ip_address"])

            new_tx_objects.append(
                TransactionModel(
                    id=tx_id,
                    timestamp=ts,
                    amount=Decimal(str(round(float(row["amount"]), 2))),
                    currency="INR",
                    payment_method=str(row.get("payment_method", "card")),
                    city=str(row["city"]) if "city" in row and pd.notna(row["city"]) else None,
                    is_fraud=bool(row.get("is_fraud", 0)),
                    fraud_scenario=str(row.get("fraud_scenario", "legitimate")),
                    risk_score=0.0,
                    risk_tier="LOW",
                    customer_id=cid,
                    account_id=f"acc_{cid}",
                    card_id=str(row["card_id"]),
                    device_id=str(row["device_id"]),
                    ip_id=f"ip_{raw_ip}",
                    merchant_id=str(row["merchant_id"]),
                    network_id=None,
                )
            )

            if len(new_tx_objects) >= batch_size:
                session.add_all(new_tx_objects)
                session.flush()
                new_tx_objects.clear()

        if new_tx_objects:
            session.add_all(new_tx_objects)
            session.flush()

        return len(existing_ids)
