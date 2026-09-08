"""FraudDNA Multi-Hop Path Intelligence Engine.

Implements bounded pathfinding between entities, semantic edge weighting,
cycle prevention, path strength scoring, and deterministic path explanation.
"""

import hashlib
from collections import deque

from app.core.errors import ValidationDomainError
from app.schemas.graph import GraphData, GraphEdge, GraphNode
from app.schemas.network_intelligence import NetworkPath, PathSegment

# Semantic Edge Weights representing collusion strength
SEMANTIC_EDGE_WEIGHTS: dict[str, float] = {
    "SHARES_DEVICE": 0.95,
    "ON_DEVICE": 0.95,
    "SHARES_CARD": 0.90,
    "USING_CARD": 0.90,
    "SHARES_IP": 0.60,
    "FROM_IP": 0.60,
    "EXECUTED": 0.85,
    "OWNS": 0.80,
    "AT_MERCHANT": 0.50,
    "MEMBER_OF_NETWORK": 0.75,
}
DEFAULT_EDGE_WEIGHT = 0.70


class PathIntelligenceEngine:
    """Discovers, scores, and explains bounded multi-hop paths between entities."""

    def __init__(self, max_depth: int = 4, max_paths: int = 20) -> None:
        self.max_depth = max_depth
        self.max_paths = max_paths

    def find_paths_between_entities(
        self,
        graph_data: GraphData,
        source_id: str,
        target_id: str,
        max_depth: int = 3,
        max_paths: int = 10,
    ) -> list[NetworkPath]:
        """Find ranked, deterministic connection paths between source and target nodes."""
        if max_depth < 1 or max_depth > 4:
            raise ValidationDomainError(
                f"Path search depth must be between 1 and 4. Requested: {max_depth}",
                details={"max_depth": max_depth},
            )

        # Normalize node IDs (support raw or namespaced)
        src = source_id if ":" in source_id else source_id
        tgt = target_id if ":" in target_id else target_id

        # Build adjacency graph
        nodes_by_id: dict[str, GraphNode] = {n.id: n for n in graph_data.nodes}
        # Fallback matching by raw_id
        raw_to_id: dict[str, str] = {n.raw_id: n.id for n in graph_data.nodes}

        real_src = nodes_by_id.get(src) or (
            nodes_by_id.get(raw_to_id.get(src, "")) if src in raw_to_id else None
        )
        real_tgt = nodes_by_id.get(tgt) or (
            nodes_by_id.get(raw_to_id.get(tgt, "")) if tgt in raw_to_id else None
        )

        if not real_src or not real_tgt:
            return []

        src_node_id = real_src.id
        tgt_node_id = real_tgt.id

        if src_node_id == tgt_node_id:
            return []

        adj: dict[str, list[GraphEdge]] = {}
        for edge in graph_data.edges:
            adj.setdefault(edge.source, []).append(edge)
            # Add reverse edge for undirected connectivity analysis
            rev_edge = GraphEdge(
                id=f"{edge.target}->{edge.source}:{edge.relation}",
                source=edge.target,
                target=edge.source,
                relation=edge.relation,
                weight=edge.weight,
                metadata=edge.metadata,
            )
            adj.setdefault(edge.target, []).append(rev_edge)

        # Bounded BFS Path Finding with cycle prevention
        # Queue item: (current_node_id, list_of_edges, visited_node_set)
        queue: deque[tuple[str, list[GraphEdge], set[str]]] = deque()
        queue.append((src_node_id, [], {src_node_id}))

        discovered_paths: list[list[GraphEdge]] = []

        while queue and len(discovered_paths) < max_paths * 3:
            curr_id, path_edges, visited = queue.popleft()

            if len(path_edges) >= max_depth:
                continue

            for edge in adj.get(curr_id, []):
                next_node = edge.target
                if next_node == tgt_node_id:
                    discovered_paths.append(path_edges + [edge])
                elif next_node not in visited and len(path_edges) + 1 < max_depth:
                    new_visited = set(visited)
                    new_visited.add(next_node)
                    queue.append((next_node, path_edges + [edge], new_visited))

        # Convert and score paths
        scored_paths: list[NetworkPath] = []
        seen_signatures: set[str] = set()

        for edges in discovered_paths:
            sig = "->".join(e.id for e in edges)
            if sig in seen_signatures:
                continue
            seen_signatures.add(sig)

            net_path = self._build_network_path(edges, nodes_by_id)
            if net_path:
                scored_paths.append(net_path)

        # Sort paths by strength descending, hop count ascending
        scored_paths.sort(key=lambda p: (-p.path_strength, p.hop_count, p.path_id))
        return scored_paths[:max_paths]

    def extract_key_network_paths(
        self, graph_data: GraphData, max_paths: int = 5
    ) -> list[NetworkPath]:
        """Discover the most critical collusion and risk-propagation paths across the network."""
        nodes = graph_data.nodes
        if len(nodes) < 2:
            return []

        # Find customer nodes and high-risk nodes
        customers = [n for n in nodes if n.entity_type == "customer"]
        high_risk_nodes = [n for n in nodes if n.risk_score >= 0.70]

        all_paths: list[NetworkPath] = []
        evaluated_pairs: set[tuple[str, str]] = set()

        # 1. Customer-to-Customer collusion paths
        for i in range(len(customers)):
            for j in range(i + 1, min(len(customers), i + 6)):
                pair = (customers[i].id, customers[j].id)
                if pair not in evaluated_pairs:
                    evaluated_pairs.add(pair)
                    paths = self.find_paths_between_entities(
                        graph_data=graph_data,
                        source_id=customers[i].id,
                        target_id=customers[j].id,
                        max_depth=3,
                        max_paths=2,
                    )
                    all_paths.extend(paths)

        # 2. Paths connecting high-risk nodes to other members
        for hr_node in high_risk_nodes[:4]:
            for other_node in customers[:4]:
                if hr_node.id != other_node.id:
                    pair = (hr_node.id, other_node.id)
                    if pair not in evaluated_pairs:
                        evaluated_pairs.add(pair)
                        paths = self.find_paths_between_entities(
                            graph_data=graph_data,
                            source_id=hr_node.id,
                            target_id=other_node.id,
                            max_depth=3,
                            max_paths=2,
                        )
                        all_paths.extend(paths)

        # Deduplicate and rank
        unique_paths: dict[str, NetworkPath] = {}
        for p in all_paths:
            if p.path_id not in unique_paths:
                unique_paths[p.path_id] = p
            elif p.path_strength > unique_paths[p.path_id].path_strength:
                unique_paths[p.path_id] = p

        ranked = sorted(
            unique_paths.values(),
            key=lambda p: (-p.path_strength, p.hop_count, p.path_id),
        )
        return ranked[:max_paths]

    def _build_network_path(
        self, edges: list[GraphEdge], nodes_by_id: dict[str, GraphNode]
    ) -> NetworkPath | None:
        """Construct and score a single NetworkPath from an edge sequence."""
        if not edges:
            return None

        segments: list[PathSegment] = []
        product_weight = 1.0
        max_node_risk = 0.0

        for edge in edges:
            src_node = nodes_by_id.get(edge.source)
            tgt_node = nodes_by_id.get(edge.target)

            src_type = src_node.entity_type if src_node else "unknown"
            tgt_type = tgt_node.entity_type if tgt_node else "unknown"

            if src_node:
                max_node_risk = max(max_node_risk, src_node.risk_score)
            if tgt_node:
                max_node_risk = max(max_node_risk, tgt_node.risk_score)

            edge_weight = SEMANTIC_EDGE_WEIGHTS.get(edge.relation, DEFAULT_EDGE_WEIGHT)
            product_weight *= edge_weight

            segments.append(
                PathSegment(
                    source_id=edge.source,
                    source_type=src_type,
                    relation=edge.relation,
                    target_id=edge.target,
                    target_type=tgt_type,
                    weight=edge_weight,
                )
            )

        hop_count = len(segments)
        # Mathematical Path Strength Score:
        # S(P) = (product of edge weights) * (1 / (1 + 0.25*(hop_count - 1))) * max(0.20, max_node_risk)
        decay_factor = 1.0 / (1.0 + 0.25 * (hop_count - 1))
        risk_amplifier = max(0.30, max_node_risk)
        path_strength = round(min(1.0, product_weight * decay_factor * risk_amplifier), 4)

        first_src = edges[0].source
        last_tgt = edges[-1].target

        # Deterministic Path ID: pth_<sha256>
        path_key = f"{first_src}->" + "->".join(f"{e.relation}->{e.target}" for e in edges)
        path_id = f"pth_{hashlib.sha256(path_key.encode('utf-8')).hexdigest()[:12]}"

        # Synthesize explanatory narrative
        summary = self._generate_path_narrative(segments, path_strength, hop_count)

        return NetworkPath(
            path_id=path_id,
            source_id=first_src,
            target_id=last_tgt,
            hop_count=hop_count,
            path_strength=path_strength,
            segments=segments,
            summary=summary,
        )

    def _generate_path_narrative(
        self, segments: list[PathSegment], strength: float, hop_count: int
    ) -> str:
        """Synthesize natural, human-understandable explanation for an entity path."""
        if not segments:
            return "Empty connection path."

        src = segments[0].source_id
        tgt = segments[-1].target_id

        parts: list[str] = []
        for seg in segments:
            parts.append(f"{seg.source_id} -[{seg.relation}]-> {seg.target_id}")

        chain_str = " -> ".join(parts)
        return (
            f"Path of {hop_count} hop(s) connecting {src} to {tgt} "
            f"(strength: {strength:.4f}): {chain_str}."
        )
