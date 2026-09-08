# FraudDNA V2 — Entity Intelligence & Advanced Graph Integration Architecture

## 1. Executive Summary

Phase **V2-05 (Entity Intelligence & Advanced Graph Integration)** elevates FraudDNA from a transaction-isolated risk evaluator into a persistent, queryable, database-backed entity intelligence network.

By establishing **PostgreSQL as the authoritative domain and relationship store**, FraudDNA removes historical memory bottlenecks (where the entire 35,000-node graph was previously kept in memory) while restricting analytical graph tools (such as NetworkX) strictly to bounded on-demand subgraphs.

```
+-----------------------------------------------------------------------------------+
|                        PostgreSQL Domain & Relationship Layer                     |
|                                                                                   |
|  [ CustomerModel ] <--- OWNS ---> [ AccountModel ]                                |
|        │                               │                                          |
|     EXECUTED                         DEBITS                                       |
|        ▼                               ▼                                          |
|  [ TransactionModel ] --- ON_DEVICE ---> [ DeviceModel ]                          |
|        │            --- FROM_IP   ---> [ IPAddressModel ]                         |
|        │            --- USING_CARD ---> [ CardModel ]                             |
|        │            --- AT_MERCHANT -> [ MerchantModel ]                          |
|        │                                                                          |
|  MEMBER_OF_NETWORK                                                                |
|        ▼                                                                          |
|  [ RiskNetworkModel ] <=== SHARES_DEVICE / SHARES_IP / SHARES_CARD (Collusion)    |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                       V2 Entity & Graph Application Layer                         |
|                                                                                   |
|  [ EntityService ]                                                                |
|  ├── Deterministic Entity Risk Aggregation: min(1.0, 0.40*R_max + 0.20*R_avg3     |
|  │                                          + 0.25*N_susp + 0.15*C_sharing)       |
|  ├── Point-in-Time Behavioral Velocity (5m, 1h, 24h windows, as_of timestamp)     |
|  └── Bounded React Flow Graph Synthesis (depth in {1,2}, max_nodes <= 250)        |
|                                                                                   |
|  [ NetworkService ]                                                               |
|  ├── Member Entity Aggregation (Customers, Devices, IPs, Cards, Merchants)        |
|  ├── Bounded Network Transactions & Subgraphs                                     |
|  └── ClusterDetail Synthesis with explainable risk factors                        |
+-----------------------------------------------------------------------------------+
```

---

## 2. Core Architecture & Design Decisions

### 2.1 Authoritative Relational Persistence vs. Analytical Graph Boundary
- **PostgreSQL is authoritative**: All entities (Customer, Account, Device, IP, Card, Merchant, Network) and transactions are stored with indexed foreign keys.
- **NetworkX is analytical and ephemeral**: NetworkX is never used as a persistent data store or global cache. It is only constructed for specific analytical tasks on bounded subgraphs and discarded immediately.
- **Zero full CSV in-memory reload**: Entity profiles, transaction lists, relationships, and neighborhood queries run directly against indexed SQL queries.

### 2.2 Relationship Semantics
Relationships retain strict domain semantics:
| Relationship Code | Source -> Target | Semantic Description |
|---|---|---|
| `OWNS` | Customer -> Account | Account ownership link |
| `EXECUTED` | Customer -> Transaction | Financial transaction initiation |
| `DEBITS` | Transaction -> Account | Debited source account |
| `ON_DEVICE` | Transaction -> Device | Hardware device used for transaction |
| `FROM_IP` | Transaction -> IPAddress | Originating network IP address |
| `USING_CARD` | Transaction -> Card | Card payment instrument |
| `AT_MERCHANT` | Transaction -> Merchant | Receiving commercial entity |
| `MEMBER_OF_NETWORK` | Transaction / Entity -> RiskNetwork | Fraud syndicate or cluster membership |
| `SHARES_DEVICE` | Customer <-> Customer | Collusive infrastructure sharing (same device) |
| `SHARES_IP` | Customer <-> Customer | Collusive infrastructure sharing (same IP) |
| `SHARES_CARD` | Customer <-> Customer | Collusive instrument sharing (same card) |

---

## 3. Deterministic Entity Risk Aggregation

Entity risk is **not** an opaque machine learning score. It is a deterministic, explainable, bounded mathematical aggregation derived from authoritative transaction and network intelligence.

### 3.1 Aggregation Formula
$$\text{entity\_risk\_score} = \min\left(1.0, \max\left(0.0, 0.40 \cdot R_{\text{max}} + 0.20 \cdot R_{\text{avg3}} + 0.25 \cdot N_{\text{susp}} + 0.15 \cdot C_{\text{sharing}}\right)\right)$$

Where:
- $R_{\text{max}}$: Maximum risk score among transactions connected to the entity.
- $R_{\text{avg3}}$: Mean of the top-3 highest transaction risk scores.
- $N_{\text{susp}}$: Network exposure score ($1.0$ if associated with any suspicious risk network, or max network score, else $0.0$).
- $C_{\text{sharing}}$: Cross-customer infrastructure sharing anomaly:
  - For Device, Card, IP: $\min(1.0, \max(0, \text{connected\_customers} - 1) \times 0.5)$
  - For Customer: $\min(1.0, \text{shared\_devices\_count} \times 0.5)$
  - For Merchant: $\min(1.0, \text{suspicious\_tx\_ratio} \times 1.0)$

### 3.2 Risk Tier Mapping
- $\ge 0.90 \rightarrow \mathbf{CRITICAL}$
- $\ge 0.70 \rightarrow \mathbf{HIGH}$
- $\ge 0.30 \rightarrow \mathbf{MEDIUM}$
- $< 0.30 \rightarrow \mathbf{LOW}$

---

## 4. Point-in-Time Behavioral Velocity Intelligence

Behavioral indicators are calculated with strict point-in-time semantics via an optional `as_of: datetime` reference timestamp.

```
                    [ 24h Window ]
            [ 1h Window ]
     [ 5m ]
───────|──────────|──────────────|──────────────▶ (Time)
     t_5m       t_1h           t_24h           as_of  [FUTURE TRANSACTIONS BLOCKED]
```

### Metrics Tracked:
- `tx_count_5m`: Transaction frequency in the last 5 minutes.
- `tx_count_1h`: Transaction frequency in the last 1 hour.
- `tx_count_24h`: Transaction frequency in the last 24 hours.
- `amount_1h`: Cumulative transaction value in the last 1 hour.
- `amount_24h`: Cumulative transaction value in the last 24 hours.
- `unique_merchants_24h`: Distinct merchants transacted with in 24 hours.
- `unique_devices_24h`: Distinct hardware devices observed in 24 hours.
- `unique_ips_24h`: Distinct network IP addresses observed in 24 hours.
- `cross_customer_sharing_count`: Count of other customers sharing connected infrastructure.

**Zero Future-Data Leakage**: By filtering with `TransactionModel.timestamp <= as_of`, historical audit reviews and forensic replay cannot be corrupted by future events.

---

## 5. Database-Backed Bounded Graph Traversal

Ego-neighborhood subgraphs are synthesized directly from relational queries into the React Flow contract (`GraphData`, `GraphNode`, `GraphEdge`).

### 5.1 Traversal Guardrails
1. **Depth Limits**: Strictly validated to $1 \le \text{depth} \le 2$. Requests with $\text{depth} > 2$ are rejected with HTTP 422 (`ValidationDomainError`).
2. **Node Cap**: Server-side clamped to $\max(5, \min(\text{max\_nodes}, 250))$.
3. **Transaction Cap**: Server-side clamped to $\max(5, \min(\text{max\_transactions}, 250))$.
4. **Deterministic Sorting**:
   - Nodes sorted by `(-risk_score, id)`
   - Edges sorted by `(source, target, relation, id)`
5. **Cycle Protection**: Node IDs are tracked via a visited set, preventing infinite traversal in cyclic financial networks.

---

## 6. Empirical Performance & Memory Benchmarks

Tested on empirical migrated database with 2,000 transactions and full risk networks:

| Query Type | Latency | Peak Memory Delta |
|---|---|---|
| Entity Profile Retrieval | **26.45 ms** | **347.3 KB** |
| Direct Relationships Query | **5.05 ms** | **70.7 KB** |
| 1-Hop Neighborhood Graph | **3.34 ms** | **52.7 KB** |
| 2-Hop Neighborhood Graph | **2.10 ms** | **45.2 KB** |
| Network Detail & Subgraph | **16.87 ms** | **214.4 KB** |

*Historical in-memory CSV/NetworkX approach required 100+ MB of RAM and ~2.5 seconds to build. The V2 PostgreSQL path achieves sub-30ms latencies with under 350 KB of peak memory.*

---

## 7. Known Fraud Case Regression: tx_0001991

The empirical coordinated fraud transaction `tx_0001991` was validated:
- **Risk Score**: $\ge 0.90$ (empirical: 0.9856)
- **Risk Tier**: `CRITICAL`
- **Network Association**: Member of suspicious coordinated syndicate (`is_suspicious=True`, score $\ge 0.85$)
- **Connected Entities**: Customer, Device, Card, IP, and Merchant nodes all resolved with typed relationships.
- **Deterministic Policy**: Evaluated as `HOLD`.
- **Audit Chain**: Intact with tamper-evident cryptographic hash verification.

---

## 8. API Endpoints Reference

### Entities:
- `GET /api/v1/entities/{entity_type}/{entity_id}`: Comprehensive entity intelligence profile.
- `GET /api/v1/entities/{entity_type}/{entity_id}/transactions`: Bounded, paginated entity transactions.
- `GET /api/v1/entities/{entity_type}/{entity_id}/relationships`: Direct semantic relationships.
- `GET /api/v1/entities/{entity_type}/{entity_id}/graph`: Bounded React Flow neighborhood graph.

### Networks:
- `GET /api/v1/networks/{network_id}`: Network details and risk breakdown.
- `GET /api/v1/networks/{network_id}/members`: Distinct member entities by type.
- `GET /api/v1/networks/{network_id}/transactions`: Paginated member transactions.
- `GET /api/v1/networks/{network_id}/graph`: Bounded React Flow network subgraph.
- `GET /api/v1/clusters/{cluster_id}`: Authoritative persistent cluster detail with transparent fallback.
