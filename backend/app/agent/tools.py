"""FraudDNA AI Investigation Agent Tools.

Provides a strictly allowlisted, bounded, read-only set of 7 investigation tools:
1. get_transaction_history
2. get_customer_profile
3. get_related_entities
4. get_cluster_analysis
5. get_risk_explanation
6. search_historical_cases
7. retrieve_policy

All tools are read-only, deterministic where possible, bounded in execution,
and completely incapable of executing arbitrary code, arbitrary SQL, mutating data,
or invoking financial transaction actions.
"""

import time
from typing import Any

from app.graph.models import EntityType, make_node_id, parse_node_id
from app.graph.service import GraphService, get_graph_service
from app.rag.retrieval import RAGService
from app.schemas.investigation import InvestigationResponse
from app.services.investigation import InvestigationService, get_investigation_service


class AgentTools:
    """Bounded, read-only investigation tool registry for FraudDNA agents."""

    ALLOWLISTED_TOOLS: set[str] = {
        "get_transaction_history",
        "get_customer_profile",
        "get_related_entities",
        "get_cluster_analysis",
        "get_risk_explanation",
        "search_historical_cases",
        "retrieve_policy",
    }

    def __init__(
        self,
        investigation_service: InvestigationService | None = None,
        graph_service: GraphService | None = None,
        rag_service: RAGService | None = None,
    ) -> None:
        self.investigation_service = investigation_service or get_investigation_service()
        self.graph_service = graph_service or get_graph_service()
        self.rag_service = rag_service or RAGService()

    def execute_tool(self, tool_name: str, **kwargs: Any) -> tuple[dict[str, Any], float]:
        """Safely execute an allowlisted tool with timing and error isolation."""
        if tool_name not in self.ALLOWLISTED_TOOLS:
            raise ValueError(
                f"Disallowed or unknown tool '{tool_name}'. Allowed tools: {sorted(self.ALLOWLISTED_TOOLS)}"
            )

        start_t = time.perf_counter()
        func = getattr(self, tool_name)
        result = func(**kwargs)
        duration_ms = (time.perf_counter() - start_t) * 1000.0
        return result, round(duration_ms, 2)

    def get_transaction_history(self, transaction_id: str) -> dict[str, Any]:
        """Fetch transaction attributes and recent historical transactions for the customer."""
        self.graph_service.initialize()
        row = self.graph_service.get_transaction_row(transaction_id)
        if row is None:
            return {
                "found": False,
                "transaction_id": transaction_id,
                "error": "Transaction not found",
            }

        cust_id = str(row.get("customer_id", ""))
        # Look up other transactions by this customer in the graph
        cust_node = make_node_id(EntityType.CUSTOMER, cust_id)
        other_txs: list[dict[str, Any]] = []
        if cust_node in self.graph_service.graph:
            for neighbor in self.graph_service.graph.neighbors(cust_node):
                n_type, tx_id = parse_node_id(neighbor)
                if n_type == EntityType.TRANSACTION.value and tx_id != transaction_id:
                    attrs = self.graph_service.graph.nodes[neighbor]
                    other_txs.append(
                        {
                            "transaction_id": tx_id,
                            "amount": float(attrs.get("amount", 0.0)),
                            "risk_score": float(attrs.get("risk_score", 0.0)),
                            "timestamp": str(attrs.get("timestamp", "")),
                        }
                    )

        # Sort historical transactions by timestamp descending
        other_txs.sort(key=lambda x: str(x["timestamp"]), reverse=True)

        return {
            "found": True,
            "transaction_id": transaction_id,
            "customer_id": cust_id,
            "amount": float(row.get("amount", 0.0)),
            "currency": str(row.get("currency", "INR")),
            "merchant_id": str(row.get("merchant_id", "")),
            "merchant_category": str(row.get("merchant_category", "")),
            "timestamp": str(row.get("timestamp", "")),
            "customer_prior_transaction_count": len(other_txs),
            "recent_transactions": other_txs[:10],
        }

    def get_customer_profile(self, customer_id: str) -> dict[str, Any]:
        """Fetch customer profile, account tenure, velocity indicators, and linked entities."""
        self.graph_service.initialize()
        cust_node = make_node_id(EntityType.CUSTOMER, customer_id)
        if cust_node not in self.graph_service.graph:
            return {"found": False, "customer_id": customer_id, "error": "Customer not found"}

        # Extract linked devices, IPs, and cards
        devices: set[str] = set()
        ips: set[str] = set()
        cards: set[str] = set()
        tx_count = 0

        for neighbor in self.graph_service.graph.neighbors(cust_node):
            n_type, _ = parse_node_id(neighbor)
            if n_type == EntityType.TRANSACTION.value:
                tx_count += 1
                for sub_neighbor in self.graph_service.graph.neighbors(neighbor):
                    sn_type, sn_id = parse_node_id(sub_neighbor)
                    if sn_type == "device":
                        devices.add(sn_id)
                    elif sn_type == "ip":
                        ips.add(sn_id)
                    elif sn_type == "card":
                        cards.add(sn_id)

        return {
            "found": True,
            "customer_id": customer_id,
            "total_transactions_in_graph": tx_count,
            "linked_device_count": len(devices),
            "linked_ip_count": len(ips),
            "linked_card_count": len(cards),
            "devices": list(devices)[:5],
            "ips": list(ips)[:5],
            "cards": list(cards)[:5],
        }

    def get_related_entities(self, transaction_id: str) -> dict[str, Any]:
        """Fetch direct graph entities and cross-account sharing indicators."""
        self.graph_service.initialize()
        tx_node = make_node_id(EntityType.TRANSACTION, transaction_id)
        if tx_node not in self.graph_service.graph:
            return {
                "found": False,
                "transaction_id": transaction_id,
                "error": "Transaction not found",
            }

        entities: list[dict[str, Any]] = []
        shared_entities: list[dict[str, Any]] = []

        for neighbor in self.graph_service.graph.neighbors(tx_node):
            n_type, raw_id = parse_node_id(neighbor)
            connected_customers = [
                n
                for n in self.graph_service.graph.neighbors(neighbor)
                if parse_node_id(n)[0] == EntityType.CUSTOMER.value
            ]
            cust_count = len(connected_customers)
            item = {
                "entity_type": n_type,
                "entity_id": raw_id,
                "namespaced_id": neighbor,
                "connected_customers_count": cust_count,
                "is_shared": cust_count > 1,
            }
            entities.append(item)
            if cust_count > 1 and n_type in {"device", "ip", "card"}:
                shared_entities.append(item)

        return {
            "found": True,
            "transaction_id": transaction_id,
            "total_entities": len(entities),
            "entities": entities,
            "shared_cross_account_entities": shared_entities,
            "has_shared_collusion_evidence": len(shared_entities) > 0,
        }

    def get_cluster_analysis(self, transaction_id: str) -> dict[str, Any]:
        """Fetch FraudDNA cluster metrics, size, risk score, and suspiciousness."""
        self.graph_service.initialize()
        cluster_id = self.graph_service.get_cluster_id_for_transaction(transaction_id)
        if not cluster_id:
            return {
                "in_cluster": False,
                "transaction_id": transaction_id,
                "message": "Transaction does not belong to any multi-entity cluster.",
            }

        cluster = self.graph_service.get_cluster_by_id(cluster_id)
        if cluster is None:
            return {
                "in_cluster": False,
                "cluster_id": cluster_id,
                "error": "Cluster data unavailable",
            }

        return {
            "in_cluster": True,
            "cluster_id": cluster.cluster_id,
            "cluster_risk_score": cluster.cluster_risk_score,
            "is_suspicious": cluster.is_suspicious,
            "transaction_count": cluster.transaction_count,
            "customer_count": cluster.customer_count,
            "device_count": cluster.device_count,
            "ip_count": cluster.ip_count,
            "card_count": cluster.card_count,
            "suspicious_transaction_count": cluster.suspicious_transaction_count,
            "primary_reason": cluster.primary_reason,
        }

    def get_risk_explanation(self, transaction_id: str) -> dict[str, Any]:
        """Fetch Tree SHAP feature attributions and ML risk scores."""
        try:
            inv: InvestigationResponse = self.investigation_service.investigate(transaction_id)
            return {
                "transaction_id": transaction_id,
                "risk_score": inv.risk_score,
                "risk_level": inv.risk_level.value,
                "top_risk_factors": [
                    {
                        "feature": f.feature,
                        "value": f.value,
                        "impact": f.impact,
                        "direction": f.direction.value,
                        "rank": f.rank,
                    }
                    for f in inv.risk_factors
                ],
                "synthesized_evidence": [
                    {
                        "type": e.evidence_type,
                        "description": e.description,
                        "severity": e.severity.value,
                        "source": e.source.value,
                    }
                    for e in inv.evidence
                ],
            }
        except Exception as e:
            return {
                "transaction_id": transaction_id,
                "error": f"Failed to compute risk explanation: {e}",
            }

    def search_historical_cases(self, query: str, top_k: int = 3) -> dict[str, Any]:
        """Query Phase 4 RAG knowledge base for historical fraud syndicates and cases."""
        try:
            self.rag_service.initialize()
            resp = self.rag_service.search(
                query=query,
                top_k=top_k,
                filters={"doc_type": "historical_case"},
            )
            return {
                "query": query,
                "total_matches": resp.total_results,
                "store_status": resp.store_status,
                "cases": [
                    {
                        "document_id": r.source_id,
                        "title": r.document_title,
                        "similarity": round(r.similarity, 4),
                        "snippet": r.content[:300],
                        "source_path": str(r.metadata.get("source_path", "")),
                    }
                    for r in resp.results
                ],
            }
        except Exception as e:
            return {
                "query": query,
                "total_matches": 0,
                "store_status": "unavailable",
                "error": f"RAG retrieval failed: {e}",
                "cases": [],
            }

    def retrieve_policy(self, query: str, top_k: int = 3) -> dict[str, Any]:
        """Query Phase 4 RAG knowledge base for fraud policies, escalation SLAs, and review thresholds."""
        try:
            self.rag_service.initialize()
            resp = self.rag_service.search(
                query=query,
                top_k=top_k,
                filters={"doc_type": "policy"},
            )
            return {
                "query": query,
                "total_matches": resp.total_results,
                "store_status": resp.store_status,
                "policies": [
                    {
                        "document_id": r.source_id,
                        "title": r.document_title,
                        "similarity": round(r.similarity, 4),
                        "snippet": r.content[:300],
                        "source_path": str(r.metadata.get("source_path", "")),
                    }
                    for r in resp.results
                ],
            }
        except Exception as e:
            return {
                "query": query,
                "total_matches": 0,
                "store_status": "unavailable",
                "error": f"Policy retrieval failed: {e}",
                "policies": [],
            }
