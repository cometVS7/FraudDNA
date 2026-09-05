import gc
import logging
import threading
import time
from pathlib import Path
from typing import Any

import joblib
import networkx as nx
import numpy as np
import pandas as pd

from app.core.config import ensure_ml_on_sys_path
from app.graph.builder import GraphBuilder
from app.graph.cluster import ClusterDetector
from app.graph.models import EntityType, make_node_id
from app.schemas.cluster import ClusterDetail, ClusterListResponse, ClusterSummary
from app.schemas.graph import GraphData

logger = logging.getLogger(__name__)


class GraphService:
    """Manages graph construction, clustering, and API query handling."""

    def __init__(
        self,
        data_path: str | Path = "ml/data/transactions.csv",
        models_dir: str | Path = "ml/models",
    ) -> None:
        self.data_path = Path(data_path)
        self.models_dir = Path(models_dir)
        self.builder = GraphBuilder()
        self.detector = ClusterDetector(risk_threshold=0.37)

        self.graph: nx.Graph = nx.Graph()
        self.clusters: list[ClusterDetail] = []
        self.clusters_by_id: dict[str, ClusterDetail] = {}
        self.tx_to_cluster: dict[str, str] = {}
        self.transactions_by_id: dict[str, dict[str, Any]] = {}
        self.overview_metrics: dict[str, Any] = {}
        self.all_transactions: list[dict[str, Any]] = []
        self.is_initialized: bool = False
        self._lock = threading.Lock()

    def initialize(self, force_reload: bool = False) -> None:
        """Load dataset, run ML risk inference, build graph, and detect clusters."""
        if self.is_initialized and not force_reload:
            return

        with self._lock:
            if self.is_initialized and not force_reload:
                return

            data_path = self.data_path
            if not data_path.exists():
                alt_data = Path("..") / data_path
                if alt_data.exists():
                    data_path = alt_data

            models_dir = self.models_dir
            if not models_dir.exists():
                alt_models = Path("..") / models_dir
                if alt_models.exists():
                    models_dir = alt_models

            if not data_path.exists():
                raise FileNotFoundError(f"Transactions dataset not found at {data_path}")

            # Ensure repository root is on sys.path for joblib unpickling
            ensure_ml_on_sys_path()

            logger.info("FraudDNA graph initialization started")
            print("FraudDNA graph initialization started", flush=True)
            t0 = time.perf_counter()

            # Load dataset
            df = pd.read_csv(data_path)

            # Compute transaction risk scores using Phase 1 LightGBM model
            risk_scores = self._score_transactions(df, models_dir=models_dir)

            # Build in-memory NetworkX relationship graph
            graph = self.builder.build_from_dataframe(df, risk_scores=risk_scores)

            # Detect and score clusters
            clusters = self.detector.detect_clusters(graph)
            clusters_by_id = {c.cluster_id: c for c in clusters}

            # Build transaction to cluster lookup
            tx_to_cluster: dict[str, str] = {}
            for cluster in clusters:
                for tx_id in cluster.member_transaction_ids:
                    tx_to_cluster[tx_id] = cluster.cluster_id

            # Precompute overview metrics and shared transaction memory
            all_transactions, transactions_by_id, overview_metrics = self._precompute_views(
                df, graph, tx_to_cluster, clusters
            )

            # Commit all validated state atomically
            self.data_path = data_path
            self.models_dir = models_dir
            self.graph = graph
            self.clusters = clusters
            self.clusters_by_id = clusters_by_id
            self.tx_to_cluster = tx_to_cluster
            self.all_transactions = all_transactions
            self.transactions_by_id = transactions_by_id
            self.overview_metrics = overview_metrics
            self.is_initialized = True

            del df
            gc.collect()

            elapsed = time.perf_counter() - t0

            logger.info(
                f"FraudDNA graph initialized in {elapsed:.2f}s "
                f"(transactions={len(self.transactions_by_id)}, nodes={self.graph.number_of_nodes()}, "
                f"edges={self.graph.number_of_edges()}, clusters={len(self.clusters)})"
            )
            print(f"FraudDNA graph initialized in {elapsed:.2f}s", flush=True)
            print(f"transactions={len(self.transactions_by_id)}", flush=True)
            print(f"nodes={self.graph.number_of_nodes()}", flush=True)
            print(f"edges={self.graph.number_of_edges()}", flush=True)
            print(f"clusters={len(self.clusters)}", flush=True)

    def _score_transactions(
        self, df: pd.DataFrame, models_dir: Path | None = None
    ) -> dict[str, float]:
        """Score transactions with Phase 1 LightGBM model."""
        target_models_dir = models_dir or self.models_dir
        if not target_models_dir.exists():
            alt_models = Path("..") / target_models_dir
            if alt_models.exists():
                target_models_dir = alt_models

        model_file = target_models_dir / "lightgbm_model.joblib"
        pipeline_file = target_models_dir / "feature_pipeline.joblib"

        if not model_file.exists():
            raise FileNotFoundError(f"ML model artifact not found at {model_file}")
        if not pipeline_file.exists():
            raise FileNotFoundError(f"Feature pipeline artifact not found at {pipeline_file}")

        try:
            model = joblib.load(model_file)
            pipeline = joblib.load(pipeline_file)
            X, _ = pipeline.transform(df, update_state=False)
            raw_probs = model.predict_proba(X)
            probs = np.asarray(raw_probs)[:, 1]
            scores = {
                str(tx_id): round(float(p), 4)
                for tx_id, p in zip(df["transaction_id"], probs, strict=True)
            }
            del X
            del raw_probs
            del probs
            gc.collect()
            return scores
        except Exception as e:
            logger.error(f"Failed to score transactions with ML model: {e}", exc_info=True)
            raise RuntimeError(f"ML model scoring failed: {e}") from e

    def _precompute_views(
        self,
        df: pd.DataFrame,
        graph: nx.Graph,
        tx_to_cluster: dict[str, str],
        clusters: list[ClusterDetail],
    ) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
        """Precompute dashboard metrics and structured unified transaction objects."""
        total_txns = len(df)
        fraud_count = int(df["is_fraud"].sum()) if "is_fraud" in df.columns else 0
        legit_count = total_txns - fraud_count
        fraud_rate = round(fraud_count / total_txns, 4) if total_txns > 0 else 0.0

        total_amount = round(float(df["amount"].sum()), 2) if "amount" in df.columns else 0.0
        fraud_amount = 0.0
        if "is_fraud" in df.columns and "amount" in df.columns:
            fraud_amount = round(float(df.loc[df["is_fraud"] == 1, "amount"].sum()), 2)

        distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        suspicious_count = 0
        high_risk_count = 0
        critical_count = 0

        all_transactions: list[dict[str, Any]] = []
        transactions_by_id: dict[str, dict[str, Any]] = {}

        records = df.to_dict(orient="records")
        for row in records:
            tx_id = str(row.get("transaction_id", ""))
            tx_node = f"transaction:{tx_id}"
            score = float(graph.nodes[tx_node].get("risk_score", 0.0)) if tx_node in graph else 0.0

            if score < 0.30:
                level = "low"
                distribution["low"] += 1
            elif score < 0.70:
                level = "medium"
                distribution["medium"] += 1
            elif score < 0.90:
                level = "high"
                distribution["high"] += 1
            else:
                level = "critical"
                distribution["critical"] += 1

            if score >= 0.37:
                suspicious_count += 1
            if score >= 0.70:
                high_risk_count += 1
            if score >= 0.90:
                critical_count += 1

            cluster_id = tx_to_cluster.get(tx_id)
            is_fraud = bool(row.get("is_fraud", 0))

            # Unified record preserving raw attributes and enriched scoring metadata
            tx_obj = {
                **{str(k): v for k, v in row.items()},
                "transaction_id": tx_id,
                "amount": float(row.get("amount", 0)),
                "timestamp": str(row.get("timestamp", "")),
                "customer_id": str(row.get("customer_id", "")),
                "merchant_id": str(row.get("merchant_id", "")),
                "device_id": str(row.get("device_id", "")),
                "ip_address": str(row.get("ip_address", "")),
                "card_id": str(row.get("card_id", "")),
                "risk_score": round(score, 4),
                "risk_level": level,
                "is_fraud": is_fraud,
                "cluster_id": cluster_id,
            }

            all_transactions.append(tx_obj)
            transactions_by_id[tx_id] = tx_obj

        total_clusters = len(clusters)
        suspicious_clusters = sum(1 for c in clusters if c.is_suspicious)

        overview_metrics = {
            "total_transactions": total_txns,
            "fraud_count": fraud_count,
            "legitimate_count": legit_count,
            "fraud_rate": fraud_rate,
            "total_amount": total_amount,
            "fraud_exposure": fraud_amount,
            "suspicious_transactions": suspicious_count,
            "high_risk_count": high_risk_count,
            "critical_risk_count": critical_count,
            "total_clusters": total_clusters,
            "suspicious_clusters": suspicious_clusters,
            "risk_distribution": distribution,
            "data_label": "synthetic_dataset",
        }

        return all_transactions, transactions_by_id, overview_metrics

    def get_clusters(
        self,
        min_risk: float = 0.0,
        suspicious_only: bool = False,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "risk_score",
    ) -> ClusterListResponse:
        """Query paginated list of fraud clusters with optional filters."""
        self._ensure_initialized()

        filtered = self.clusters

        if min_risk > 0.0:
            filtered = [c for c in filtered if c.cluster_risk_score >= min_risk]

        if suspicious_only:
            filtered = [c for c in filtered if c.is_suspicious]

        # Sorting
        if sort_by == "risk_score":
            filtered.sort(key=lambda c: (-c.cluster_risk_score, -c.transaction_count, c.cluster_id))
        elif sort_by == "transaction_count":
            filtered.sort(key=lambda c: (-c.transaction_count, -c.cluster_risk_score, c.cluster_id))
        elif sort_by == "amount":
            filtered.sort(
                key=lambda c: (-c.total_transaction_amount, -c.cluster_risk_score, c.cluster_id)
            )

        total = len(filtered)
        paginated = filtered[offset : offset + limit]

        summaries = [
            ClusterSummary(
                cluster_id=c.cluster_id,
                cluster_risk_score=c.cluster_risk_score,
                is_suspicious=c.is_suspicious,
                transaction_count=c.transaction_count,
                customer_count=c.customer_count,
                device_count=c.device_count,
                ip_count=c.ip_count,
                card_count=c.card_count,
                merchant_count=c.merchant_count,
                suspicious_transaction_count=c.suspicious_transaction_count,
                total_transaction_amount=c.total_transaction_amount,
                suspicious_transaction_amount=c.suspicious_transaction_amount,
                primary_reason=c.primary_reason,
            )
            for c in paginated
        ]

        return ClusterListResponse(
            total_clusters=total,
            limit=limit,
            offset=offset,
            clusters=summaries,
        )

    def get_cluster_by_id(self, cluster_id: str) -> ClusterDetail | None:
        """Retrieve full details and subgraph for a specific cluster."""
        self._ensure_initialized()
        return self.clusters_by_id.get(cluster_id)

    def get_transaction_relationships(
        self,
        transaction_id: str,
        depth: int = 2,
    ) -> GraphData:
        """Extract ego-subgraph surrounding a given transaction."""
        self._ensure_initialized()
        tx_node = make_node_id(EntityType.TRANSACTION, transaction_id)
        if tx_node not in self.graph:
            return GraphData()

        # Ego graph up to specified radius
        subgraph = nx.ego_graph(self.graph, tx_node, radius=depth)
        return GraphBuilder.subgraph_to_graph_data(subgraph)

    def get_entity_relationships(
        self,
        entity_type: EntityType | str,
        raw_id: str,
        depth: int = 2,
    ) -> GraphData:
        """Extract ego-subgraph surrounding an entity node."""
        self._ensure_initialized()
        node_id = make_node_id(entity_type, raw_id)
        if node_id not in self.graph:
            return GraphData()

        subgraph = nx.ego_graph(self.graph, node_id, radius=depth)
        return GraphBuilder.subgraph_to_graph_data(subgraph)

    def get_cluster_id_for_transaction(self, transaction_id: str) -> str | None:
        """Lookup cluster ID that contains a specific transaction."""
        self._ensure_initialized()
        return self.tx_to_cluster.get(transaction_id)

    def get_transaction_row(self, transaction_id: str) -> dict[str, Any] | None:
        """Lookup original transaction record attributes."""
        self._ensure_initialized()
        return self.transactions_by_id.get(transaction_id)

    def has_transaction(self, transaction_id: str) -> bool:
        """Check whether transaction exists in dataset/graph."""
        self._ensure_initialized()
        return transaction_id in self.transactions_by_id

    def _ensure_initialized(self) -> None:
        """Ensure in-memory graph is built."""
        if not self.is_initialized:
            self.initialize()

    def get_overview_metrics(self) -> dict[str, Any]:
        """Return precomputed dashboard overview metrics."""
        self._ensure_initialized()
        return self.overview_metrics


# Global Singleton Instance
_graph_service_instance: GraphService | None = None
_service_lock = threading.Lock()


def get_graph_service() -> GraphService:
    """Dependency provider for GraphService singleton."""
    global _graph_service_instance
    if _graph_service_instance is None:
        with _service_lock:
            if _graph_service_instance is None:
                _graph_service_instance = GraphService()
    return _graph_service_instance
