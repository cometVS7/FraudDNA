"""FraudDNA Network Analytics Engine.

Calculates deterministic network risk propagation, exposure profiles,
temporal timeline progressions, structural graph topology, and machine-readable findings.
"""

import hashlib
from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

from app.schemas.graph import GraphData
from app.schemas.network_intelligence import (
    NetworkExposure,
    NetworkFinding,
    NetworkTimeline,
    NetworkTimelinePoint,
    NetworkTopologyMetrics,
    PatternSeverity,
    SyndicatePattern,
)


class NetworkAnalyticsEngine:
    """Computes mathematical network risk, temporal dynamics, exposure, and findings."""

    def compute_network_exposure(
        self,
        network_id: str,
        transactions: list[Any],
        member_entities: dict[str, list[str]],
    ) -> NetworkExposure:
        """Compute observed financial and entity exposure metrics."""
        n_tx = len(transactions)
        total_amt = 0.0
        susp_amt = 0.0
        susp_count = 0

        merch_counts: Counter[str] = Counter()

        for tx in transactions:
            amt = float(
                getattr(tx, "amount", 0.0)
                or (tx.get("amount", 0.0) if isinstance(tx, dict) else 0.0)
            )
            score = float(
                getattr(tx, "risk_score", 0.0)
                or (tx.get("risk_score", 0.0) if isinstance(tx, dict) else 0.0)
            )
            total_amt += amt
            if score >= 0.37:
                susp_count += 1
                susp_amt += amt

            m_id = getattr(tx, "merchant_id", None) or (
                tx.get("merchant_id") if isinstance(tx, dict) else None
            )
            if m_id:
                merch_counts[str(m_id)] += 1

        top_merch_id = merch_counts.most_common(1)[0][0] if merch_counts else None
        top_merch_count = merch_counts.most_common(1)[0][1] if merch_counts else 0
        merch_ratio = round(top_merch_count / n_tx, 4) if n_tx > 0 else 0.0

        return NetworkExposure(
            network_id=network_id,
            total_transactions=n_tx,
            suspicious_transactions=susp_count,
            total_amount=round(total_amt, 2),
            suspicious_amount=round(susp_amt, 2),
            exposed_customer_count=len(member_entities.get("customers", [])),
            exposed_device_count=len(member_entities.get("devices", [])),
            exposed_card_count=len(member_entities.get("cards", [])),
            exposed_ip_count=len(member_entities.get("ips", [])),
            exposed_merchant_count=len(member_entities.get("merchants", [])),
            primary_targeted_merchant_id=top_merch_id,
            merchant_concentration_ratio=merch_ratio,
        )

    def compute_network_topology_metrics(
        self,
        graph_data: GraphData,
        member_entities: dict[str, list[str]],
    ) -> NetworkTopologyMetrics:
        """Compute structural graph metrics and infrastructure sharing ratios."""
        n_nodes = graph_data.total_nodes
        n_edges = graph_data.total_edges

        # Graph Density = 2 * |E| / (|V| * (|V| - 1))
        if n_nodes > 1:
            possible_edges = n_nodes * (n_nodes - 1)
            density = round(min(1.0, (2.0 * n_edges) / possible_edges), 4)
        else:
            density = 0.0

        n_cust = len(member_entities.get("customers", []))
        n_dev = len(member_entities.get("devices", []))
        n_crd = len(member_entities.get("cards", []))

        cust_dev_ratio = round(n_cust / max(1, n_dev), 2)
        cust_card_ratio = round(n_cust / max(1, n_crd), 2)

        # Sharing index: how concentrated infrastructure is across customers
        if n_cust >= 2:
            raw_sharing = 1.0 - (float(n_dev + n_crd) / (n_cust * 2.0))
            sharing_index = round(min(1.0, max(0.0, raw_sharing * 1.5)), 4)
        else:
            sharing_index = 0.0

        return NetworkTopologyMetrics(
            node_count=n_nodes,
            edge_count=n_edges,
            density=density,
            customer_to_device_ratio=cust_dev_ratio,
            customer_to_card_ratio=cust_card_ratio,
            infrastructure_sharing_index=sharing_index,
        )

    def compute_temporal_timeline(
        self,
        network_id: str,
        transactions: list[Any],
        as_of: datetime | None = None,
    ) -> NetworkTimeline:
        """Construct chronological activity progression obeying point-in-time boundaries."""
        parsed_txs: list[tuple[datetime, Any]] = []
        for tx in transactions:
            ts = getattr(tx, "timestamp", None) or (
                tx.get("timestamp") if isinstance(tx, dict) else None
            )
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts)
                except Exception:
                    ts = None
            if isinstance(ts, datetime):
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)
                if as_of is None or ts <= as_of:
                    parsed_txs.append((ts, tx))

        parsed_txs.sort(key=lambda t: t[0])

        if not parsed_txs:
            now_dt = as_of or datetime.now(UTC)
            return NetworkTimeline(
                network_id=network_id,
                first_seen=now_dt,
                last_seen=now_dt,
                active_duration_hours=0.0,
                is_burst_attack=False,
                timeline_points=[],
            )

        first_seen = parsed_txs[0][0]
        last_seen = parsed_txs[-1][0]
        duration_hours = round(max(0.0, (last_seen - first_seen).total_seconds() / 3600.0), 2)

        # Determine bucket size (hourly if <= 72h, daily if longer)
        bucket_delta = timedelta(hours=1) if duration_hours <= 72 else timedelta(days=1)

        buckets: dict[datetime, list[Any]] = {}
        for ts, tx in parsed_txs:
            # Round down to bucket
            if bucket_delta == timedelta(hours=1):
                b_key = ts.replace(minute=0, second=0, microsecond=0)
            else:
                b_key = ts.replace(hour=0, minute=0, second=0, microsecond=0)
            buckets.setdefault(b_key, []).append(tx)

        timeline_points: list[NetworkTimelinePoint] = []
        max_hourly_count = 0

        for b_time in sorted(buckets.keys()):
            b_txs = buckets[b_time]
            b_count = len(b_txs)
            max_hourly_count = max(max_hourly_count, b_count)

            b_total_amt = sum(
                float(
                    getattr(t, "amount", 0.0)
                    or (t.get("amount", 0.0) if isinstance(t, dict) else 0.0)
                )
                for t in b_txs
            )
            b_susp_txs = [
                t
                for t in b_txs
                if float(
                    getattr(t, "risk_score", 0.0)
                    or (t.get("risk_score", 0.0) if isinstance(t, dict) else 0.0)
                )
                >= 0.37
            ]
            b_susp_amt = sum(
                float(
                    getattr(t, "amount", 0.0)
                    or (t.get("amount", 0.0) if isinstance(t, dict) else 0.0)
                )
                for t in b_susp_txs
            )

            b_custs = {
                getattr(t, "customer_id", None)
                or (t.get("customer_id") if isinstance(t, dict) else None)
                for t in b_txs
            }
            b_devs = {
                getattr(t, "device_id", None)
                or (t.get("device_id") if isinstance(t, dict) else None)
                for t in b_txs
            }

            timeline_points.append(
                NetworkTimelinePoint(
                    time_bucket=b_time.isoformat(),
                    transaction_count=b_count,
                    suspicious_count=len(b_susp_txs),
                    total_amount=round(b_total_amt, 2),
                    suspicious_amount=round(b_susp_amt, 2),
                    active_customers=len([c for c in b_custs if c]),
                    active_devices=len([d for d in b_devs if d]),
                )
            )

        is_burst = (max_hourly_count >= 8) or (duration_hours <= 1.0 and len(parsed_txs) >= 4)

        return NetworkTimeline(
            network_id=network_id,
            first_seen=first_seen,
            last_seen=last_seen,
            active_duration_hours=duration_hours,
            is_burst_attack=is_burst,
            timeline_points=timeline_points,
        )

    def calculate_propagated_network_risk(
        self,
        exposure: NetworkExposure,
        topology: NetworkTopologyMetrics,
        timeline: NetworkTimeline,
        transactions: list[Any],
    ) -> tuple[float, str, float]:
        """Compute the deterministic 5-component network risk score and tier."""
        if not transactions:
            return 0.0, "LOW", 0.50

        scores = [
            float(
                getattr(t, "risk_score", 0.0)
                or (t.get("risk_score", 0.0) if isinstance(t, dict) else 0.0)
            )
            for t in transactions
        ]
        scores.sort(reverse=True)

        # 1. Transaction Risk Component (w = 0.30)
        max_score = scores[0] if scores else 0.0
        top3_avg = sum(scores[:3]) / len(scores[:3]) if scores else 0.0
        r_tx = 0.60 * max_score + 0.40 * top3_avg

        # 2. Entity Exposure Component (w = 0.20)
        r_ent = min(
            1.0,
            float(exposure.exposed_customer_count) * 0.15
            + (1.0 if max_score >= 0.70 else 0.0) * 0.4,
        )

        # 3. Suspicious Member Density (w = 0.25)
        d_susp = exposure.suspicious_transactions / max(1, exposure.total_transactions)

        # 4. Infrastructure Concentration (w = 0.15)
        c_inf = topology.infrastructure_sharing_index

        # 5. Temporal Burst (w = 0.10)
        t_burst = (
            1.0
            if timeline.is_burst_attack
            else (0.5 if timeline.active_duration_hours <= 24 else 0.2)
        )

        # Weighted combination
        raw_risk = 0.30 * r_tx + 0.20 * r_ent + 0.25 * d_susp + 0.15 * c_inf + 0.10 * t_burst

        # Invariant: If top transaction is critical and ring has high density, propagated risk must be >= 0.85
        if max_score >= 0.90 and d_susp >= 0.50:
            propagated_score = round(min(1.0, max(raw_risk, 0.85)), 4)
        else:
            propagated_score = round(min(1.0, max(0.0, raw_risk)), 4)

        # Tier derivation
        if propagated_score >= 0.90:
            tier = "CRITICAL"
        elif propagated_score >= 0.70:
            tier = "HIGH"
        elif propagated_score >= 0.30:
            tier = "MEDIUM"
        else:
            tier = "LOW"

        confidence = round(
            min(1.0, 0.70 + 0.05 * min(6, len(transactions)) + 0.10 * (1 if d_susp > 0 else 0)),
            2,
        )

        return propagated_score, tier, confidence

    def synthesize_network_findings(
        self,
        network_id: str,
        exposure: NetworkExposure,
        patterns: list[SyndicatePattern],
        propagated_score: float,
        tier: str,
        transactions: list[Any],
        member_entities: dict[str, list[str]],
    ) -> list[NetworkFinding]:
        """Generate structured, audit-traceable machine-readable findings."""
        findings: list[NetworkFinding] = []

        tx_ids = [
            str(getattr(t, "id", None) or (t.get("transaction_id") if isinstance(t, dict) else ""))
            for t in transactions[:10]
        ]
        cust_ids = member_entities.get("customers", [])[:10]
        dev_ids = member_entities.get("devices", [])[:5]
        card_ids = member_entities.get("cards", [])[:5]

        # 1. Finding for overall propagated network risk
        if propagated_score >= 0.70:
            fnd_key = f"{network_id}_high_network_risk_{tier}"
            fnd_id = f"fnd_{hashlib.sha256(fnd_key.encode('utf-8')).hexdigest()[:12]}"
            findings.append(
                NetworkFinding(
                    id=fnd_id,
                    finding_type="HIGH_RISK_SYNDICATE_THREAT",
                    severity=PatternSeverity.CRITICAL
                    if tier == "CRITICAL"
                    else PatternSeverity.HIGH,
                    confidence=0.90,
                    title=f"Coordinated {tier} Risk Syndicate",
                    description=(
                        f"Risk network '{network_id}' exhibits high-confidence coordinated threat "
                        f"(propagated risk: {propagated_score:.4f}, exposure: INR {exposure.total_amount:,.2f}) "
                        f"spanning {exposure.exposed_customer_count} accounts and {exposure.total_transactions} transactions."
                    ),
                    affected_entities=cust_ids + dev_ids + card_ids,
                    affected_transactions=tx_ids,
                    evidence_items=[
                        {"propagated_risk_score": propagated_score, "risk_tier": tier},
                        {"suspicious_transactions": exposure.suspicious_transactions},
                        {"total_exposure_amount": exposure.total_amount},
                    ],
                    pattern_name="NETWORK_RISK_PROPAGATION",
                )
            )

        # 2. Findings for each triggered pattern
        for pat in patterns:
            if pat.triggered:
                p_key = f"{network_id}_{pat.pattern_type.value}"
                fnd_id = f"fnd_{hashlib.sha256(p_key.encode('utf-8')).hexdigest()[:12]}"
                findings.append(
                    NetworkFinding(
                        id=fnd_id,
                        finding_type=f"SYNDICATE_PATTERN_{pat.pattern_type.value}",
                        severity=pat.severity,
                        confidence=pat.confidence,
                        title=pat.name,
                        description=pat.description,
                        affected_entities=cust_ids,
                        affected_transactions=tx_ids,
                        evidence_items=[pat.evidence],
                        pattern_name=pat.pattern_type.value,
                    )
                )

        return findings
