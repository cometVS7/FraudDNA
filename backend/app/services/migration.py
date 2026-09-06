"""FraudDNA Authoritative Data Migration & Ingestion Engine.

Migrates the 25,000-transaction V1 dataset and empirical artifacts into the
V2 PostgreSQL relational domain schema with complete entity deduplication,
graph syndicate cluster persistence, vectorized LightGBM risk scoring,
Tree SHAP risk signal persistence, and referential integrity verification.
"""

import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import ensure_ml_on_sys_path
from app.graph.builder import GraphBuilder
from app.graph.cluster import ClusterDetector
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
    RiskAssessmentModel,
    RiskNetworkModel,
    RiskSignalModel,
    TransactionModel,
)

logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """Detailed summary of data migration execution."""

    customers_count: int = 0
    accounts_count: int = 0
    cards_count: int = 0
    devices_count: int = 0
    ips_count: int = 0
    merchants_count: int = 0
    networks_count: int = 0
    transactions_count: int = 0
    assessments_count: int = 0
    signals_count: int = 0
    models_count: int = 0
    policies_count: int = 0
    sources_count: int = 0
    total_processed: int = 0
    is_idempotent: bool = True
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntegrityReport:
    """Detailed verification report on domain data integrity."""

    is_valid: bool = True
    checks_passed: int = 0
    checks_failed: int = 0
    details: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DataMigrationService:
    """Orchestrates deterministic and idempotent migration of V1 data to V2 persistence."""

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
        """Resolve candidate paths relative to repository root or backend/."""
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

    def validate_source_artifacts(self) -> dict[str, bool]:
        """Validate existence of all required source artifacts before migration."""
        self._resolve_paths()
        status = {
            "transactions_csv": self.data_path.exists(),
            "model_metadata": (self.models_dir / "model_metadata.json").exists(),
            "lightgbm_model": (self.models_dir / "lightgbm_model.joblib").exists(),
            "feature_pipeline": (self.models_dir / "feature_pipeline.joblib").exists(),
            "knowledge_dir": self.knowledge_dir.exists(),
        }
        missing = [k for k, exists in status.items() if not exists]
        if missing:
            raise FileNotFoundError(f"Missing required source artifacts for migration: {missing}")
        return status

    def migrate_sync(
        self,
        session: Session,
        batch_size: int = 5000,
        compute_risk: bool = True,
        compute_signals: bool = True,
        limit: int | None = None,
    ) -> MigrationResult:
        """Execute full synchronous migration into PostgreSQL."""
        self.validate_source_artifacts()
        ensure_ml_on_sys_path()
        t0 = time.perf_counter()
        result = MigrationResult()

        logger.info("Beginning FraudDNA V2 Authoritative Data Migration...")

        # 1. Seed Model Registry
        result.models_count = self._seed_model_registry(session)

        # 2. Seed Policy Matrix
        result.policies_count = self._seed_policy(session)

        # 3. Seed Intelligence Sources
        result.sources_count = self._seed_intelligence_sources(session)

        # 4. Load dataset
        df = pd.read_csv(self.data_path)
        if limit is not None and limit > 0:
            df = df.head(limit)
        result.total_processed = len(df)

        # 5. Seed Core Entities
        result.customers_count = self._seed_customers(session, df)
        result.accounts_count = self._seed_accounts(session, df)
        result.cards_count = self._seed_cards(session, df)
        result.devices_count = self._seed_devices(session, df)
        result.ips_count = self._seed_ips(session, df)
        result.merchants_count = self._seed_merchants(session, df)

        # 6. Load ML artifacts & compute vectorized risk scores
        model, pipeline = self._load_ml_artifacts()
        if compute_risk and model is not None and pipeline is not None:
            logger.info("Computing vectorized LightGBM risk scores for dataset...")
            X, _ = pipeline.transform(df, update_state=False)
            probabilities = model.predict_proba(X)[:, 1]
        else:
            X = None
            probabilities = np.zeros(len(df))

        # 7. Detect and persist graph clusters (RiskNetworkModel)
        tx_to_cluster = self._seed_risk_networks(session, df, probabilities)
        result.networks_count = len(
            set(session.execute(select(RiskNetworkModel.id)).scalars().all())
        )

        # 8. Batch Insert Transactions
        result.transactions_count = self._seed_transactions(
            session=session,
            df=df,
            probabilities=probabilities,
            tx_to_cluster=tx_to_cluster,
            batch_size=batch_size,
        )

        # 9. Point-in-time Risk Assessments
        result.assessments_count = self._seed_risk_assessments(
            session=session,
            df=df,
            probabilities=probabilities,
            batch_size=batch_size,
        )

        # 10. Tree SHAP Risk Signals (Top 5 per suspicious/elevated transaction)
        if compute_signals and model is not None and pipeline is not None and X is not None:
            result.signals_count = self._seed_risk_signals(
                session=session,
                df=df,
                X=X,
                model=model,
                feature_names=pipeline.feature_columns,
                probabilities=probabilities,
                tx_to_cluster=tx_to_cluster,
                batch_size=batch_size,
            )

        session.commit()
        result.elapsed_seconds = round(time.perf_counter() - t0, 3)
        logger.info(
            f"Migration completed in {result.elapsed_seconds}s: "
            f"Txs={result.transactions_count}, Networks={result.networks_count}, "
            f"Assessments={result.assessments_count}, Signals={result.signals_count}"
        )
        return result

    def _load_ml_artifacts(self) -> tuple[Any | None, Any | None]:
        """Load LightGBM classifier and feature pipeline."""
        model_path = self.models_dir / "lightgbm_model.joblib"
        pipe_path = self.models_dir / "feature_pipeline.joblib"
        if not model_path.exists() or not pipe_path.exists():
            return None, None
        try:
            model = joblib.load(model_path)
            pipeline = joblib.load(pipe_path)
            return model, pipeline
        except Exception as exc:
            logger.warning(f"Could not load ML artifacts for scoring: {exc}")
            return None, None

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

    def _seed_risk_networks(
        self, session: Session, df: pd.DataFrame, probabilities: np.ndarray
    ) -> dict[str, str]:
        """Detect graph syndicate clusters and persist RiskNetworkModel records."""
        existing_net_ids = set(session.execute(select(RiskNetworkModel.id)).scalars().all())
        builder = GraphBuilder()
        detector = ClusterDetector(risk_threshold=0.37)

        # Build risk scores lookup
        risk_scores: dict[str, float] = {}
        for idx in range(len(df)):
            tx_id = str(df.iloc[idx]["transaction_id"])
            risk_scores[tx_id] = float(probabilities[idx])

        graph = builder.build_from_dataframe(df, risk_scores=risk_scores)
        clusters = detector.detect_clusters(graph)

        tx_to_cluster: dict[str, str] = {}
        new_networks: list[RiskNetworkModel] = []

        for cluster in clusters:
            cid = cluster.cluster_id
            for tx_id in cluster.member_transaction_ids:
                tx_to_cluster[tx_id] = cid

            if cid in existing_net_ids:
                continue
            existing_net_ids.add(cid)

            new_networks.append(
                RiskNetworkModel(
                    id=cid,
                    network_name=f"Coordinated Fraud Syndicate {cid}",
                    status="ACTIVE",
                    risk_score=round(float(cluster.cluster_risk_score), 4),
                    is_suspicious=cluster.is_suspicious,
                    primary_reason=cluster.primary_reason,
                    transaction_count=cluster.transaction_count,
                    customer_count=cluster.customer_count,
                    device_count=cluster.device_count,
                    card_count=cluster.card_count,
                    ip_count=cluster.ip_count,
                    merchant_count=cluster.merchant_count,
                    total_amount=Decimal(str(round(float(cluster.total_transaction_amount), 2))),
                    created_at=datetime.now(UTC),
                )
            )

        if new_networks:
            session.add_all(new_networks)
            session.flush()

        return tx_to_cluster

    def _seed_transactions(
        self,
        session: Session,
        df: pd.DataFrame,
        probabilities: np.ndarray,
        tx_to_cluster: dict[str, str],
        batch_size: int = 5000,
    ) -> int:
        existing_ids = set(session.execute(select(TransactionModel.id)).scalars().all())
        new_tx_objects: list[TransactionModel] = []
        inserted_count = 0

        for idx in range(len(df)):
            row = df.iloc[idx]
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
            score = round(float(probabilities[idx]), 4)

            # Derive risk tier
            if score < 0.30:
                tier = "LOW"
            elif score < 0.70:
                tier = "MEDIUM"
            elif score < 0.90:
                tier = "HIGH"
            else:
                tier = "CRITICAL"

            network_id = tx_to_cluster.get(tx_id)

            # Deterministic initial action alignment
            if score >= 0.90 or (network_id is not None and score >= 0.70):
                action = "HOLD"
            elif score >= 0.30:
                action = "REVIEW"
            else:
                action = "ALLOW"

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
                    risk_score=score,
                    risk_tier=tier,
                    decision_action=action,
                    customer_id=cid,
                    account_id=f"acc_{cid}",
                    card_id=str(row["card_id"]),
                    device_id=str(row["device_id"]),
                    ip_id=f"ip_{raw_ip}",
                    merchant_id=str(row["merchant_id"]),
                    network_id=network_id,
                    created_at=datetime.now(UTC),
                )
            )

            if len(new_tx_objects) >= batch_size:
                session.add_all(new_tx_objects)
                session.flush()
                inserted_count += len(new_tx_objects)
                new_tx_objects.clear()

        if new_tx_objects:
            session.add_all(new_tx_objects)
            session.flush()
            inserted_count += len(new_tx_objects)

        return len(existing_ids)

    def _seed_risk_assessments(
        self,
        session: Session,
        df: pd.DataFrame,
        probabilities: np.ndarray,
        batch_size: int = 5000,
    ) -> int:
        """Persist point-in-time RiskAssessmentModel entries for evaluated transactions."""
        existing_ras_ids = set(session.execute(select(RiskAssessmentModel.id)).scalars().all())
        new_assessments: list[RiskAssessmentModel] = []
        inserted_count = 0

        for idx in range(len(df)):
            row = df.iloc[idx]
            tx_id = str(row["transaction_id"])
            ras_id = f"ras_{tx_id}_v010"
            if ras_id in existing_ras_ids:
                continue
            existing_ras_ids.add(ras_id)

            score = round(float(probabilities[idx]), 4)
            if score < 0.30:
                tier = "LOW"
            elif score < 0.70:
                tier = "MEDIUM"
            elif score < 0.90:
                tier = "HIGH"
            else:
                tier = "CRITICAL"

            ts_raw = row["timestamp"]
            if isinstance(ts_raw, str):
                ts = datetime.fromisoformat(ts_raw)
            else:
                ts = pd.to_datetime(ts_raw).to_pydatetime()
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)

            new_assessments.append(
                RiskAssessmentModel(
                    id=ras_id,
                    transaction_id=tx_id,
                    model_id="mdl_lightgbm_v010",
                    model_version="0.1.0",
                    risk_score=score,
                    risk_tier=tier,
                    feature_version="v1.0",
                    generated_at=ts,
                )
            )

            if len(new_assessments) >= batch_size:
                session.add_all(new_assessments)
                session.flush()
                inserted_count += len(new_assessments)
                new_assessments.clear()

        if new_assessments:
            session.add_all(new_assessments)
            session.flush()
            inserted_count += len(new_assessments)

        return len(existing_ras_ids)

    def _seed_risk_signals(
        self,
        session: Session,
        df: pd.DataFrame,
        X: pd.DataFrame | np.ndarray,
        model: Any,
        feature_names: list[str],
        probabilities: np.ndarray,
        tx_to_cluster: dict[str, str],
        batch_size: int = 5000,
    ) -> int:
        """Persist structured Tree SHAP risk signals under bounded deterministic Top-5 policy.

        Policy:
        Persist top 5 feature contributions (sorted by absolute impact descending) for:
        1. All elevated risk transactions (risk_score >= 0.37 operating threshold)
        2. All transactions belonging to a detected cluster
        3. All transactions labeled as fraud
        """
        existing_sig_ids = set(session.execute(select(RiskSignalModel.id)).scalars().all())

        # Identify candidate indices meeting the deterministic policy
        candidate_indices: list[int] = []
        for idx in range(len(df)):
            row = df.iloc[idx]
            tx_id = str(row["transaction_id"])
            score = float(probabilities[idx])
            is_fraud = bool(row.get("is_fraud", 0))
            in_cluster = tx_id in tx_to_cluster
            if score >= 0.37 or is_fraud or in_cluster:
                candidate_indices.append(idx)

        if not candidate_indices:
            return 0

        logger.info(
            f"Computing Tree SHAP risk signals for {len(candidate_indices)} policy-targeted transactions..."
        )

        # Slice candidate feature matrix
        X_candidates: Any
        if isinstance(X, pd.DataFrame):
            X_candidates = X.iloc[candidate_indices]
        else:
            X_candidates = X[candidate_indices]

        # Batch Tree SHAP prediction via native LightGBM booster
        contribs = model.booster_.predict(X_candidates, pred_contrib=True)

        new_signals: list[RiskSignalModel] = []
        inserted_count = 0

        for idx_in_subset, global_idx in enumerate(candidate_indices):
            tx_id = str(df.iloc[global_idx]["transaction_id"])
            ras_id = f"ras_{tx_id}_v010"
            tx_contribs = contribs[idx_in_subset]

            # Pair features with contributions and raw values
            scored_features: list[tuple[str, float, float]] = []
            for feat_idx, feat_name in enumerate(feature_names):
                impact = float(tx_contribs[feat_idx])
                if isinstance(X_candidates, pd.DataFrame):
                    raw_val = float(cast(Any, X_candidates.iloc[idx_in_subset, feat_idx]))
                else:
                    raw_val = float(X_candidates[idx_in_subset][feat_idx])
                scored_features.append((feat_name, raw_val, impact))

            # Bounded deterministic Top-5 policy: sort by |impact| descending
            scored_features.sort(key=lambda it: abs(it[2]), reverse=True)

            for rank, (feat_name, raw_val, impact) in enumerate(scored_features[:5], start=1):
                sig_id = f"sig_{ras_id}_{rank}"
                if sig_id in existing_sig_ids:
                    continue
                existing_sig_ids.add(sig_id)

                if impact > 0.001:
                    direction = "INCREASES_RISK"
                elif impact < -0.001:
                    direction = "DECREASES_RISK"
                else:
                    direction = "NEUTRAL"

                new_signals.append(
                    RiskSignalModel(
                        id=sig_id,
                        assessment_id=ras_id,
                        feature_name=feat_name,
                        feature_value=round(raw_val, 4),
                        impact=round(impact, 4),
                        direction=direction,
                        rank=rank,
                    )
                )

                if len(new_signals) >= batch_size:
                    session.add_all(new_signals)
                    session.flush()
                    inserted_count += len(new_signals)
                    new_signals.clear()

        if new_signals:
            session.add_all(new_signals)
            session.flush()
            inserted_count += len(new_signals)

        return len(existing_sig_ids)

    def verify_integrity(self, session: Session) -> IntegrityReport:
        """Execute full referential integrity and consistency checks across migrated domain state."""
        report = IntegrityReport()

        def check(name: str, passed: bool, error_msg: str) -> None:
            if passed:
                report.checks_passed += 1
                report.details[name] = "PASSED"
            else:
                report.checks_failed += 1
                report.is_valid = False
                report.details[name] = f"FAILED: {error_msg}"
                report.errors.append(f"[{name}] {error_msg}")

        # 1. Total Transaction Count
        tx_count = session.execute(select(func.count(TransactionModel.id))).scalar() or 0
        check(
            "transaction_count_positive",
            tx_count > 0,
            f"Expected > 0 transactions, found {tx_count}",
        )
        report.details["total_transactions"] = tx_count

        # 2. Customer Foreign Key Integrity
        orphan_customers = (
            session.execute(
                select(func.count(TransactionModel.id)).where(
                    ~TransactionModel.customer_id.in_(select(CustomerModel.id))
                )
            ).scalar()
            or 0
        )
        check(
            "customer_fk_integrity",
            orphan_customers == 0,
            f"Found {orphan_customers} transactions referencing non-existent customers",
        )

        # 3. Merchant Foreign Key Integrity
        orphan_merchants = (
            session.execute(
                select(func.count(TransactionModel.id)).where(
                    ~TransactionModel.merchant_id.in_(select(MerchantModel.id))
                )
            ).scalar()
            or 0
        )
        check(
            "merchant_fk_integrity",
            orphan_merchants == 0,
            f"Found {orphan_merchants} transactions referencing non-existent merchants",
        )

        # 4. Card Foreign Key Integrity
        orphan_cards = (
            session.execute(
                select(func.count(TransactionModel.id)).where(
                    TransactionModel.card_id.isnot(None),
                    ~TransactionModel.card_id.in_(select(CardModel.id)),
                )
            ).scalar()
            or 0
        )
        check(
            "card_fk_integrity",
            orphan_cards == 0,
            f"Found {orphan_cards} transactions referencing non-existent cards",
        )

        # 5. Device Foreign Key Integrity
        orphan_devices = (
            session.execute(
                select(func.count(TransactionModel.id)).where(
                    TransactionModel.device_id.isnot(None),
                    ~TransactionModel.device_id.in_(select(DeviceModel.id)),
                )
            ).scalar()
            or 0
        )
        check(
            "device_fk_integrity",
            orphan_devices == 0,
            f"Found {orphan_devices} transactions referencing non-existent devices",
        )

        # 6. IP Foreign Key Integrity
        orphan_ips = (
            session.execute(
                select(func.count(TransactionModel.id)).where(
                    TransactionModel.ip_id.isnot(None),
                    ~TransactionModel.ip_id.in_(select(IPAddressModel.id)),
                )
            ).scalar()
            or 0
        )
        check(
            "ip_fk_integrity",
            orphan_ips == 0,
            f"Found {orphan_ips} transactions referencing non-existent IP addresses",
        )

        # 7. Risk Network Foreign Key Integrity
        orphan_networks = (
            session.execute(
                select(func.count(TransactionModel.id)).where(
                    TransactionModel.network_id.isnot(None),
                    ~TransactionModel.network_id.in_(select(RiskNetworkModel.id)),
                )
            ).scalar()
            or 0
        )
        check(
            "network_fk_integrity",
            orphan_networks == 0,
            f"Found {orphan_networks} transactions referencing non-existent risk networks",
        )

        # 8. Risk Assessment Foreign Key Integrity
        orphan_ras = (
            session.execute(
                select(func.count(RiskAssessmentModel.id)).where(
                    ~RiskAssessmentModel.transaction_id.in_(select(TransactionModel.id))
                )
            ).scalar()
            or 0
        )
        check(
            "assessment_fk_integrity",
            orphan_ras == 0,
            f"Found {orphan_ras} risk assessments referencing non-existent transactions",
        )

        # 9. Risk Signal Foreign Key Integrity
        orphan_signals = (
            session.execute(
                select(func.count(RiskSignalModel.id)).where(
                    ~RiskSignalModel.assessment_id.in_(select(RiskAssessmentModel.id))
                )
            ).scalar()
            or 0
        )
        check(
            "signal_fk_integrity",
            orphan_signals == 0,
            f"Found {orphan_signals} risk signals referencing non-existent assessments",
        )

        # 10. Risk Score Bounds Check [0.0, 1.0]
        invalid_tx_scores = (
            session.execute(
                select(func.count(TransactionModel.id)).where(
                    (TransactionModel.risk_score < 0.0) | (TransactionModel.risk_score > 1.0)
                )
            ).scalar()
            or 0
        )
        check(
            "transaction_risk_score_bounds",
            invalid_tx_scores == 0,
            f"Found {invalid_tx_scores} transactions with risk score out of [0.0, 1.0]",
        )

        # 11. Known High-Risk Transaction Verification (tx_0001991)
        tx_known = session.execute(
            select(TransactionModel).where(TransactionModel.id == "tx_0001991")
        ).scalar_one_or_none()
        if tx_known is not None:
            check(
                "tx_0001991_exists",
                True,
                "",
            )
            check(
                "tx_0001991_high_risk",
                tx_known.risk_score >= 0.90,
                f"tx_0001991 risk score was {tx_known.risk_score}, expected >= 0.90",
            )
            check(
                "tx_0001991_critical_tier",
                tx_known.risk_tier == "CRITICAL",
                f"tx_0001991 risk tier was {tx_known.risk_tier}, expected CRITICAL",
            )
            check(
                "tx_0001991_hold_decision",
                tx_known.decision_action == "HOLD",
                f"tx_0001991 decision action was {tx_known.decision_action}, expected HOLD",
            )
        else:
            # If migration was run with limit < 2000, tx_0001991 might not be loaded yet
            report.details["tx_0001991"] = "SKIPPED_NOT_IN_SUBSET"

        return report
