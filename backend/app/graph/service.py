"""FraudDNA Graph Service Module.

Provides singleton access to the in-memory relationship graph, cluster queries,
and entity neighborhood traversals.
"""

from pathlib import Path
from typing import Any

import joblib  # type: ignore[import-untyped]
import networkx as nx
import numpy as np
import pandas as pd

from app.graph.builder import GraphBuilder
from app.graph.cluster import ClusterDetector
from app.graph.models import EntityType, make_node_id
from app.schemas.cluster import ClusterDetail, ClusterListResponse, ClusterSummary
from app.schemas.graph import GraphData


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
        self.df: pd.DataFrame | None = None
        self.transactions_by_id: dict[str, dict[str, Any]] = {}
        self.is_initialized: bool = False

    def initialize(self, force_reload: bool = False) -> None:
        """Load dataset, run ML risk inference, build graph, and detect clusters."""
        if self.is_initialized and not force_reload:
            return

        if not self.data_path.exists():
            raise FileNotFoundError(f"Transactions dataset not found at {self.data_path}")

        df = pd.read_csv(self.data_path)
        self.df = df
        self.transactions_by_id = {
            str(row["transaction_id"]): {str(k): v for k, v in row.items()}
            for _, row in df.iterrows()
        }

        # Compute or load transaction risk scores using Phase 1 model
        risk_scores = self._score_transactions(df)

        # Build in-memory NetworkX relationship graph
        self.graph = self.builder.build_from_dataframe(df, risk_scores=risk_scores)

        # Detect and score clusters
        self.clusters = self.detector.detect_clusters(self.graph)
        self.clusters_by_id = {c.cluster_id: c for c in self.clusters}

        # Build transaction to cluster lookup
        self.tx_to_cluster.clear()
        for cluster in self.clusters:
            for tx_id in cluster.member_transaction_ids:
                self.tx_to_cluster[tx_id] = cluster.cluster_id

        self.is_initialized = True

    def _score_transactions(self, df: pd.DataFrame) -> dict[str, float]:
        """Score transactions with Phase 1 LightGBM model if available."""
        model_file = self.models_dir / "lightgbm_model.joblib"
        pipeline_file = self.models_dir / "feature_pipeline.joblib"

        if model_file.exists() and pipeline_file.exists():
            try:
                model = joblib.load(model_file)
                pipeline = joblib.load(pipeline_file)
                X, _ = pipeline.transform(df, update_state=False)
                raw_probs = model.predict_proba(X)
                probs = np.asarray(raw_probs)[:, 1]
                return {
                    str(tx_id): round(float(p), 4)
                    for tx_id, p in zip(df["transaction_id"], probs, strict=False)
                }
            except Exception as e:
                print(f"Warning: Could not score transactions with ML model: {e}")

        # Fallback if model artifact not loaded
        return {str(tx_id): 0.0 for tx_id in df["transaction_id"]}

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


# Global Singleton Instance
_graph_service_instance: GraphService | None = None


def get_graph_service() -> GraphService:
    """Dependency provider for GraphService singleton."""
    global _graph_service_instance
    if _graph_service_instance is None:
        _graph_service_instance = GraphService()
        _graph_service_instance.initialize()
    return _graph_service_instance
