# FraudDNA V2 — Phase V2-07 Architecture Specification
## Risk Network Intelligence & Coordinated Syndicate Engine

---

## 1. System Architecture Overview

The V2-07 Risk Network Intelligence layer sits directly on top of the V2 PostgreSQL domain models and provides high-performance, deterministic network analytics to the API layer, the Risk Orchestrator (V2-06), and the downstream AI Investigation Agent (V2-08).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        API Layer (FastAPI)                             │
│  GET /networks/{id}/intelligence     GET /networks/{id}/paths          │
│  GET /networks/{id}/timeline         GET /networks/{id}/exposure       │
│  GET /networks/{id}/patterns         GET /networks/{id}/findings       │
│  GET /entities/{type}/{id}/network-intelligence                        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    NetworkIntelligenceService                          │
│  Coordinates network analytics, pathfinding, exposure, and findings    │
└──────────┬───────────────────────┬──────────────────────┬──────────────┘
           │                       │                      │
           ▼                       ▼                      ▼
┌─────────────────────┐ ┌─────────────────────┐ ┌────────────────────────┐
│ NetworkAnalysisEngine│ │SyndicateDetector    │ │PathIntelligenceEngine  │
│ - Topology Metrics  │ │ - 7 Attack Patterns │ │ - Bounded Multi-Hop    │
│ - Risk Propagation  │ │ - Confidence Scoring│ │ - Path Ranking Formula │
│ - Temporal Timeline │ │ - Rule Matrix       │ │ - Edge Semantic Weight │
└──────────┬──────────┘ └──────────┬──────────┘ └──────────┬─────────────┘
           │                       │                      │
           └───────────────────────┼──────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     NetworkRepository & EntityRepository               │
│  Bounded SQL queries, indexed foreign key lookups, zero full-graph load │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     PostgreSQL / SQLite Database                       │
│  transactions, risk_networks, customers, devices, cards, ip_addresses   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Mathematical Formulations

### 2.1 Network Risk Propagation Model

The network risk score $R_{network} \in [0.0, 1.0]$ represents the aggregate threat level of a connected syndicate. It is deterministically derived from 5 normalized components:

$$R_{network} = \min\left(1.0, w_{tx} \cdot R_{tx} + w_{ent} \cdot R_{ent} + w_{den} \cdot D_{susp} + w_{inf} \cdot C_{inf} + w_{time} \cdot T_{burst}\right)$$

Where:
- **Transaction Risk Exposure ($R_{tx}$)**:
  $$R_{tx} = 0.6 \cdot \max_{t \in T}(r_t) + 0.4 \cdot \text{avg}_{\text{top3}}(r_t)$$
- **Entity Risk Exposure ($R_{ent}$)**:
  Average risk score of connected customer accounts and infrastructure.
- **Suspicious Member Density ($D_{susp}$)**:
  $$D_{susp} = \frac{|T_{suspicious}|}{|T_{total}|} = \frac{|\{t \in T \mid r_t \ge 0.37\}|}{|T|}$$
- **Infrastructure Concentration Ratio ($C_{inf}$)**:
  Measures the degree to which multiple customer accounts share constrained infrastructure:
  $$C_{inf} = \min\left(1.0, \max\left(0.0, 1.0 - \frac{|Devices| + |Cards|}{|Customers| \cdot 2}\right) \times 1.5\right)$$
  *(If 5 customers share only 1 device and 1 card, $C_{inf}$ approaches 1.0)*
- **Temporal Coordination Burst ($T_{burst}$)**:
  Measures transaction concentration over time. If $> 50\%$ of member transactions occurred within a 1-hour window:
  $$T_{burst} = \min\left(1.0, \frac{\text{max\_hourly\_tx\_count}}{|T_{total}|} \times 1.2\right)$$

**Component Weights**:
- $w_{tx} = 0.30$
- $w_{ent} = 0.20$
- $w_{den} = 0.25$
- $w_{inf} = 0.15$
- $w_{time} = 0.10$
*(Weights sum strictly to $1.00$)*

---

### 2.2 Path Intelligence & Ranking Formulation

When analyzing connections between entities (e.g., Customer $A$ and Customer $B$), paths are discovered up to depth 4 using bounded Breadth-First Search (BFS).

Each discovered path $P = (v_0, e_1, v_1, \dots, e_k, v_k)$ is assigned a deterministic **Path Strength Score** $S(P) \in [0.0, 1.0]$:

$$S(P) = \left( \prod_{i=1}^k W(e_i) \right) \cdot \left( \frac{1}{1 + 0.25 \cdot (k - 1)} \right) \cdot \max_{v \in P}(R_v)$$

Where:
- $W(e)$ is the **Semantic Edge Weight**:
  - `SHARES_DEVICE`: $0.95$ (Strong physical collusion signal)
  - `SHARES_CARD`: $0.90$ (Direct financial instrument sharing)
  - `SHARES_IP`: $0.60$ (Network co-location; common on public Wi-Fi)
  - `EXECUTED`: $0.85$ (Customer executed transaction)
  - `MEMBER_OF_NETWORK`: $0.80$ (Syndicate cluster membership)
- $k$ is the hop count ($1 \le k \le 4$).
- $R_v$ is the risk score of the highest-risk node along the path.

Paths are sorted by $S(P)$ descending and deduplicated.

---

## 3. The 7 Canonical Syndicate Attack Patterns

The `SyndicateDetector` evaluates the network against 7 formalized fraud topologies:

### Pattern 1: Shared Device Ring (`DEVICE_REUSE_RING`)
- **Definition**: Multiple distinct customer accounts operating from the same hardware device.
- **Criteria**: $|Customers| \ge 2$ AND $|Devices| < |Customers|$ AND $\text{any}(device.shared\_count \ge 2)$.
- **Severity**: `HIGH` (or `CRITICAL` if $R_{tx} \ge 0.70$).

### Pattern 2: Payment Instrument Sharing Ring (`CARD_SHARING_RING`)
- **Definition**: Multiple customer accounts executing transactions using the same credit/debit card.
- **Criteria**: $|Customers| \ge 2$ AND $|Cards| < |Customers|$ AND $\text{any}(card.shared\_count \ge 2)$.
- **Severity**: `CRITICAL` (indicates stolen card testing or mule account network).

### Pattern 3: High-Density IP Subnet Cluster (`IP_CONCENTRATION_CLUSTER`)
- **Definition**: Abnormally high volume of distinct accounts originating from a single IP address.
- **Criteria**: $\ge 3$ customer accounts active on a single IP address.
- **Severity**: `MEDIUM` (elevated to `HIGH` if combined with high velocity).

### Pattern 4: Multi-Account Infrastructure Collusion (`MULTI_INFRASTRUCTURE_COLLUSION`)
- **Definition**: Co-occurrence of shared hardware devices AND shared payment cards across customer accounts.
- **Criteria**: `DEVICE_REUSE_RING` is True AND `CARD_SHARING_RING` is True.
- **Severity**: `CRITICAL` (high-confidence organized fraud ring).

### Pattern 5: Targeted Merchant Abuse (`MERCHANT_TARGETING_CLUSTER`)
- **Definition**: Syndicate focused disproportionately on a single merchant (e.g. cashout point or digital gift card merchant).
- **Criteria**: $\ge 70\%$ of network transaction volume directed to a single `merchant_id`.
- **Severity**: `HIGH`.

### Pattern 6: High-Velocity Burst Attack (`HIGH_VELOCITY_BURST_ATTACK`)
- **Definition**: Coordinated spike where $\ge 4$ transactions occur within a 5-minute window or $\ge 10$ transactions in 1 hour across the network.
- **Criteria**: $\text{tx\_count\_5m} \ge 4$ OR $\text{tx\_count\_1h} \ge 10$.
- **Severity**: `HIGH`.

### Pattern 7: Layered Entity Chain (`LAYERED_ENTITY_CHAIN`)
- **Definition**: Multi-hop proxy chain connecting a transaction to suspicious actors across $\ge 3$ hops.
- **Criteria**: Shortest path to a high-risk entity ($\ge 0.70$) is $\ge 3$ hops.
- **Severity**: `MEDIUM`.

---

## 4. Structured Network Findings & Evidence Model

Every execution of `NetworkIntelligenceService` produces deterministic, machine-readable findings formatted for V2-08 AI Agent consumption:

```python
class NetworkFinding(BaseModel):
    id: str  # fnd_<sha256>
    finding_type: str  # e.g., "SYNDICATE_PATTERN_DETECTED", "HIGH_RISK_CONCENTRATION"
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    confidence: float  # [0.0, 1.0]
    title: str
    description: str
    affected_entities: list[str]
    affected_transactions: list[str]
    evidence_items: list[dict[str, Any]]
    pattern_name: str | None = None
    created_at: datetime
```

---

## 5. Performance & Resource Bounds

| Metric | Target / Limit | Implementation Enforcement |
|---|---|---|
| **Max Traversal Depth** | $3$ hops | Validated at API query parameter and Service layer (`ValidationDomainError`) |
| **Max Nodes Per Query** | $250$ | Capped and validated (`5 <= max_nodes <= 250`) |
| **Max Transactions Per Query** | $250$ | Capped and validated (`5 <= max_transactions <= 250`) |
| **Path Search Depth** | $4$ | BFS queue bounded to depth 4; stops on target discovery |
| **Query Latency** | $< 50\text{ ms}$ | Uses compound indexes on `(network_id, timestamp)`, `(customer_id, timestamp)` |
| **Memory Allocation** | $< 10\text{ MB}$ | Local ego-subgraphs only; zero global graph construction |
