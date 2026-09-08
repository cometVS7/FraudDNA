"""FraudDNA Syndicate Pattern Detection Engine.

Evaluates risk networks and entity neighborhoods against 7 canonical fraud topologies:
1. DEVICE_REUSE_RING
2. CARD_SHARING_RING
3. IP_CONCENTRATION_CLUSTER
4. MULTI_INFRASTRUCTURE_COLLUSION
5. MERCHANT_TARGETING_CLUSTER
6. HIGH_VELOCITY_BURST_ATTACK
7. LAYERED_ENTITY_CHAIN
"""

from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from app.schemas.graph import GraphData
from app.schemas.network_intelligence import (
    PatternSeverity,
    SyndicatePattern,
    SyndicatePatternType,
)


class SyndicateDetector:
    """Evaluates graph topology, member entities, and transactions to detect attack signatures."""

    def evaluate_syndicate_patterns(
        self,
        transactions: list[Any],
        member_entities: dict[str, list[str]],
        graph_data: GraphData | None = None,
        as_of: datetime | None = None,
    ) -> list[SyndicatePattern]:
        """Run all 7 syndicate pattern evaluators and return detected patterns."""
        patterns: list[SyndicatePattern] = []

        if as_of is not None:
            filtered_txs = []
            for tx in transactions:
                ts = getattr(tx, "timestamp", None) or (
                    tx.get("timestamp") if isinstance(tx, dict) else None
                )
                if ts is None or ts <= as_of:
                    filtered_txs.append(tx)
            transactions = filtered_txs

        customers = member_entities.get("customers", [])
        n_cust = len(customers)
        n_tx = len(transactions)

        # ----------------------------------------------------------------------
        # Pattern 1: DEVICE_REUSE_RING
        # ----------------------------------------------------------------------
        dev_to_cust: dict[str, set[str]] = {}
        for tx in transactions:
            dev_id = getattr(tx, "device_id", None) or (
                tx.get("device_id") if isinstance(tx, dict) else None
            )
            cust_id = getattr(tx, "customer_id", None) or (
                tx.get("customer_id") if isinstance(tx, dict) else None
            )
            if dev_id and cust_id:
                dev_to_cust.setdefault(str(dev_id), set()).add(str(cust_id))

        shared_devices = {d: custs for d, custs in dev_to_cust.items() if len(custs) >= 2}
        has_device_ring = len(shared_devices) > 0 and n_cust >= 2

        max_dev_shared = max((len(c) for c in shared_devices.values()), default=0)
        dev_confidence = (
            round(min(1.0, 0.70 + 0.10 * (max_dev_shared - 1)), 2) if has_device_ring else 0.0
        )
        dev_severity = (
            PatternSeverity.CRITICAL
            if max_dev_shared >= 3
            else (PatternSeverity.HIGH if has_device_ring else PatternSeverity.LOW)
        )

        patterns.append(
            SyndicatePattern(
                pattern_type=SyndicatePatternType.DEVICE_REUSE_RING,
                name="Hardware Device Reuse Ring",
                severity=dev_severity,
                confidence=dev_confidence,
                triggered=has_device_ring,
                description=(
                    f"Coordinated device reuse: {len(shared_devices)} hardware device(s) shared "
                    f"across {n_cust} customer accounts (max {max_dev_shared} accounts/device)."
                    if has_device_ring
                    else "No suspicious multi-customer device sharing detected."
                ),
                evidence={
                    "shared_device_count": len(shared_devices),
                    "shared_devices": list(shared_devices.keys()),
                    "max_accounts_per_device": max_dev_shared,
                },
            )
        )

        # ----------------------------------------------------------------------
        # Pattern 2: CARD_SHARING_RING
        # ----------------------------------------------------------------------
        card_to_cust: dict[str, set[str]] = {}
        for tx in transactions:
            card_id = getattr(tx, "card_id", None) or (
                tx.get("card_id") if isinstance(tx, dict) else None
            )
            cust_id = getattr(tx, "customer_id", None) or (
                tx.get("customer_id") if isinstance(tx, dict) else None
            )
            if card_id and cust_id:
                card_to_cust.setdefault(str(card_id), set()).add(str(cust_id))

        shared_cards = {k: custs for k, custs in card_to_cust.items() if len(custs) >= 2}
        has_card_ring = len(shared_cards) > 0 and n_cust >= 2

        max_card_shared = max((len(c) for c in shared_cards.values()), default=0)
        card_confidence = (
            round(min(1.0, 0.80 + 0.10 * (max_card_shared - 1)), 2) if has_card_ring else 0.0
        )

        patterns.append(
            SyndicatePattern(
                pattern_type=SyndicatePatternType.CARD_SHARING_RING,
                name="Payment Card Sharing Ring",
                severity=PatternSeverity.CRITICAL if has_card_ring else PatternSeverity.LOW,
                confidence=card_confidence,
                triggered=has_card_ring,
                description=(
                    f"Payment instrument collusion: {len(shared_cards)} payment card(s) used "
                    f"across {n_cust} distinct customer accounts."
                    if has_card_ring
                    else "No multi-customer payment instrument sharing detected."
                ),
                evidence={
                    "shared_card_count": len(shared_cards),
                    "shared_cards": list(shared_cards.keys()),
                    "max_accounts_per_card": max_card_shared,
                },
            )
        )

        # ----------------------------------------------------------------------
        # Pattern 3: IP_CONCENTRATION_CLUSTER
        # ----------------------------------------------------------------------
        ip_to_cust: dict[str, set[str]] = {}
        for tx in transactions:
            ip_id = getattr(tx, "ip_id", None) or (
                tx.get("ip_id") if isinstance(tx, dict) else None
            )
            cust_id = getattr(tx, "customer_id", None) or (
                tx.get("customer_id") if isinstance(tx, dict) else None
            )
            if ip_id and cust_id:
                ip_to_cust.setdefault(str(ip_id), set()).add(str(cust_id))

        concentrated_ips = {i: custs for i, custs in ip_to_cust.items() if len(custs) >= 3}
        has_ip_cluster = len(concentrated_ips) > 0

        max_ip_shared = max((len(c) for c in concentrated_ips.values()), default=0)
        ip_confidence = (
            round(min(1.0, 0.60 + 0.08 * (max_ip_shared - 2)), 2) if has_ip_cluster else 0.0
        )
        ip_severity = (
            PatternSeverity.HIGH
            if max_ip_shared >= 5
            else (PatternSeverity.MEDIUM if has_ip_cluster else PatternSeverity.LOW)
        )

        patterns.append(
            SyndicatePattern(
                pattern_type=SyndicatePatternType.IP_CONCENTRATION_CLUSTER,
                name="High-Density IP Address Concentration",
                severity=ip_severity,
                confidence=ip_confidence,
                triggered=has_ip_cluster,
                description=(
                    f"IP address proxy concentration: {len(concentrated_ips)} IP address(es) each "
                    f"shared across 3+ distinct accounts (max {max_ip_shared} accounts/IP)."
                    if has_ip_cluster
                    else "No high-density IP concentration detected."
                ),
                evidence={
                    "concentrated_ip_count": len(concentrated_ips),
                    "concentrated_ips": list(concentrated_ips.keys()),
                    "max_accounts_per_ip": max_ip_shared,
                },
            )
        )

        # ----------------------------------------------------------------------
        # Pattern 4: MULTI_INFRASTRUCTURE_COLLUSION
        # ----------------------------------------------------------------------
        has_multi_collusion = has_device_ring and has_card_ring
        multi_confidence = 0.95 if has_multi_collusion else 0.0

        patterns.append(
            SyndicatePattern(
                pattern_type=SyndicatePatternType.MULTI_INFRASTRUCTURE_COLLUSION,
                name="Multi-Layer Infrastructure Collusion",
                severity=PatternSeverity.CRITICAL if has_multi_collusion else PatternSeverity.LOW,
                confidence=multi_confidence,
                triggered=has_multi_collusion,
                description=(
                    f"High-confidence syndicate collusion: Accounts share both physical devices ({len(shared_devices)}) "
                    f"and payment cards ({len(shared_cards)}), confirming coordinated operation."
                    if has_multi_collusion
                    else "No multi-layer infrastructure collusion detected."
                ),
                evidence={
                    "shared_devices": list(shared_devices.keys()),
                    "shared_cards": list(shared_cards.keys()),
                },
            )
        )

        # ----------------------------------------------------------------------
        # Pattern 5: MERCHANT_TARGETING_CLUSTER
        # ----------------------------------------------------------------------
        merch_counter: Counter[str] = Counter()
        for tx in transactions:
            m_id = getattr(tx, "merchant_id", None) or (
                tx.get("merchant_id") if isinstance(tx, dict) else None
            )
            if m_id:
                merch_counter[str(m_id)] += 1

        top_merch_id = merch_counter.most_common(1)[0][0] if merch_counter else None
        top_merch_count = merch_counter.most_common(1)[0][1] if merch_counter else 0
        merch_ratio = top_merch_count / n_tx if n_tx > 0 else 0.0

        has_merch_targeting = merch_ratio >= 0.70 and n_tx >= 3 and top_merch_id is not None

        patterns.append(
            SyndicatePattern(
                pattern_type=SyndicatePatternType.MERCHANT_TARGETING_CLUSTER,
                name="Disproportionate Merchant Targeting",
                severity=PatternSeverity.HIGH if has_merch_targeting else PatternSeverity.LOW,
                confidence=round(merch_ratio, 2) if has_merch_targeting else 0.0,
                triggered=has_merch_targeting,
                description=(
                    f"Targeted merchant abuse: {merch_ratio * 100:.1f}% ({top_merch_count}/{n_tx}) of network transactions "
                    f"are concentrated on merchant '{top_merch_id}'."
                    if has_merch_targeting
                    else "Transaction volume is distributed across multiple merchants."
                ),
                evidence={
                    "targeted_merchant_id": top_merch_id,
                    "merchant_transaction_count": top_merch_count,
                    "merchant_volume_ratio": round(merch_ratio, 4),
                },
            )
        )

        # ----------------------------------------------------------------------
        # Pattern 6: HIGH_VELOCITY_BURST_ATTACK
        # ----------------------------------------------------------------------
        timestamps: list[datetime] = []
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
                timestamps.append(ts)

        timestamps.sort()
        max_5m_burst = 0
        max_1h_burst = 0

        for i in range(len(timestamps)):
            t0 = timestamps[i]
            t_5m = t0 + timedelta(minutes=5)
            t_1h = t0 + timedelta(hours=1)

            c_5m = sum(1 for t in timestamps if t0 <= t <= t_5m)
            c_1h = sum(1 for t in timestamps if t0 <= t <= t_1h)

            max_5m_burst = max(max_5m_burst, c_5m)
            max_1h_burst = max(max_1h_burst, c_1h)

        has_burst = (max_5m_burst >= 4) or (max_1h_burst >= 8)
        burst_confidence = round(min(1.0, 0.75 + 0.05 * max_5m_burst), 2) if has_burst else 0.0

        patterns.append(
            SyndicatePattern(
                pattern_type=SyndicatePatternType.HIGH_VELOCITY_BURST_ATTACK,
                name="High-Velocity Coordinated Burst Attack",
                severity=PatternSeverity.HIGH if has_burst else PatternSeverity.LOW,
                confidence=burst_confidence,
                triggered=has_burst,
                description=(
                    f"Automated / scripted burst activity: {max_5m_burst} transactions executed in 5 minutes "
                    f"({max_1h_burst} in 1 hour) across member entities."
                    if has_burst
                    else "No coordinated velocity burst detected."
                ),
                evidence={
                    "max_transactions_5m": max_5m_burst,
                    "max_transactions_1h": max_1h_burst,
                },
            )
        )

        # ----------------------------------------------------------------------
        # Pattern 7: LAYERED_ENTITY_CHAIN
        # ----------------------------------------------------------------------
        has_layered_chain = False
        if graph_data and len(graph_data.nodes) >= 5:
            # Check for paths with hop count >= 3
            if n_cust >= 3 and (has_device_ring or has_card_ring) and len(graph_data.edges) >= 4:
                has_layered_chain = True

        patterns.append(
            SyndicatePattern(
                pattern_type=SyndicatePatternType.LAYERED_ENTITY_CHAIN,
                name="Layered Multi-Hop Entity Chain",
                severity=PatternSeverity.MEDIUM if has_layered_chain else PatternSeverity.LOW,
                confidence=0.70 if has_layered_chain else 0.0,
                triggered=has_layered_chain,
                description=(
                    f"Layered proxy chain: {n_cust} accounts interact across interconnected multi-hop infrastructure."
                    if has_layered_chain
                    else "No multi-hop layered proxy chain detected."
                ),
                evidence={"total_nodes": len(graph_data.nodes) if graph_data else 0},
            )
        )

        return patterns
