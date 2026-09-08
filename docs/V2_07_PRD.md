# FraudDNA V2 — Phase V2-07 Product Requirements Document (PRD)
## Risk Network Intelligence & Coordinated Syndicate Analytics

---

## 1. Executive Summary & Problem Statement

Fraud detection systems historically operate on an isolated transaction or isolated entity basis:
- An isolated transaction evaluation asks: *"Does this payment of INR 45,000 look anomalous for this card/merchant?"*
- An isolated entity evaluation asks: *"Has this customer exhibited velocity anomalies in the last 24 hours?"*

However, modern financial crime—particularly payment fraud, authorized push payment (APP) scams, account takeover (ATO), and synthetic identity mule operations—is inherently **coordinated across networks of shared infrastructure**. Organized fraud syndicates strategically distribute transactions across multiple customer accounts, mule cards, burner devices, and VPN/proxy IPs to evade single-point threshold detection.

**Phase V2-07 transforms FraudDNA into a production-grade Risk Network Intelligence Engine**, enabling risk analysts and downstream automated AI agents (V2-08) to answer:
1. *Is this transaction connected to a coordinated fraud network?*
2. *Which shared devices, payment instruments, or IP addresses link apparently distinct customers?*
3. *What is the shortest/strongest suspicious path between two entities in the network?*
4. *How does risk propagate across connected infrastructure?*
5. *What is the temporal progression and expansion velocity of this syndicate?*
6. *What specific attack pattern (e.g., Device Reuse Ring, Card Sharing Ring, Burst Attack, Merchant Targeting) is active?*

---

## 2. Goals & Non-Goals

### Goals
- **Deterministic Multi-Hop Traversal**: Enable bounded 1-, 2-, and 3-hop graph analytics directly from PostgreSQL domain models with strict server-side resource caps (max nodes $\le 250$, max transactions $\le 250$).
- **Structured Path Intelligence**: Discover, rank, and explain meaningful entity connection paths (e.g., `Customer -> Device -> Customer`, `Customer -> Card -> Customer`, `Transaction -> Device -> Customer -> Transaction`) using mathematically sound path relevance scoring.
- **Automated Syndicate Pattern Detection**: Implement deterministic pattern evaluators for 7 canonical fraud syndicate signatures:
  1. *Shared Device Ring*
  2. *Card Sharing Ring*
  3. *High-Density IP Subnet Cluster*
  4. *Multi-Account Infrastructure Collusion*
  5. *Merchant Targeting Cluster*
  6. *High-Velocity Burst Attack*
  7. *Layered Entity Chain*
- **Deterministic Network Risk Propagation**: Compute a bounded $[0.0, 1.0]$ network risk score derived from transaction exposure, entity risk, suspicious member density, infrastructure concentration, and temporal coordination.
- **Point-in-Time Temporal Network Analytics**: Reconstruct network timelines (first seen, last seen, burst windows, velocity progression) obeying $timestamp \le as\_of$ without future-data leakage.
- **Traceable Network Findings & Evidence**: Emit structured, audit-grade findings and machine-readable evidence items consumed by V2-08 AI Investigation Agent and investigation cases.
- **Fast, Bounded API Surface**: Expose clean REST endpoints supporting sub-50ms query latency without full-graph memory allocations.

### Non-Goals
- **No Direct Financial Decision Mutation**: Network intelligence discovers and explains risk patterns; it does NOT directly execute `ALLOW / REVIEW / HOLD` decisions. The `PolicyEngine` remains the sole authoritative financial decision authority.
- **No Unbounded Multi-Hop Graph Traversal**: Traversal beyond 3 hops is rejected by server policy to eliminate denial-of-service vulnerabilities and graph explosion.
- **No LLM Hallucinations in Analytics**: All graph metrics, paths, patterns, and timelines are pure deterministic mathematical computations.
- **No Full-Graph In-Memory Construction**: Zero loading of 35k-node graphs or full CSV datasets in persistent mode.

---

## 3. Four-Layer Risk Separation Principle

To ensure architectural integrity, V2-07 strictly maintains the separation of the four risk tiers:

| Risk Layer | Scope | Primary Signals | Bounded Range |
|---|---|---|---|
| **Transaction Risk** | Individual payment event | LightGBM probability, Tree SHAP Top-5 feature attributions | $[0.0, 1.0]$ |
| **Entity Risk** | Specific actor/infrastructure | Historical transaction volume, max risk, 24h velocity, cross-sharing count | $[0.0, 1.0]$ |
| **Network Risk** | Connected syndicate cluster | Subgraph density, member fraud ratio, infrastructure concentration, path strength | $[0.0, 1.0]$ |
| **Behavioral Risk** | Temporal velocity window | Point-in-time burst count (5m/1h/24h), hourly outflow velocity | $[0.0, 1.0]$ |

---

## 4. User Personas & Core Use Cases

### Personas
1. **Senior Fraud Analyst / Investigator**: Needs to inspect the complete syndicate structure behind a flagged transaction, visualize connection paths, and review machine-generated findings for SAR (Suspicious Activity Report) filing.
2. **Autonomous AI Investigation Agent (V2-08)**: Queries structured network intelligence, paths, and patterns via typed APIs to synthesize natural language investigation narratives and compile evidence.
3. **Risk Operations Lead / Compliance Officer**: Monitors overall network exposure, syndicate expansion rates, and merchant collusion trends.

### Core Use Cases
- **UC-1: Syndicate Discovery from Transaction**: Given a transaction ID, retrieve the parent risk network, all interconnected accounts/devices/cards/IPs, and key collusion patterns.
- **UC-2: Entity-to-Entity Path Investigation**: Given two customer IDs or an entity pair, find the shortest, highest-confidence connecting paths via shared hardware, cards, or network IPs.
- **UC-3: Automated Pattern Classification**: Evaluate a risk network against canonical fraud topologies and return active attack signatures with confidence ratings.
- **UC-4: Point-in-Time Historical Timeline**: Query how a network evolved up to a specific historical transaction timestamp $t_0$, verifying zero data leakage from $t > t_0$.
- **UC-5: Structured Evidence Compilation**: Extract verified, source-attributed evidence items linking a network's transactions to shared entities for legal/audit compliance.

---

## 5. Network Intelligence Output Specifications

A complete network intelligence response contains:
1. **Network Metadata & Exposure**: Member entity counts, total transaction volume, suspicious volume exposure, active duration.
2. **Network Topology Metrics**: Degree distribution, density, infrastructure sharing ratios ($\frac{\text{customers}}{\text{devices}}$, $\frac{\text{customers}}{\text{cards}}$).
3. **Propagated Risk Score**: Mathematical composite of member risk, density, and coordination.
4. **Detected Syndicate Patterns**: List of active patterns with severity, confidence, and triggering criteria.
5. **Key Entity Connection Paths**: Top ranked paths connecting member entities.
6. **Temporal Progression**: Chronological sequence of network activity windows.
7. **Structured Findings**: Human- and agent-readable findings with severity and traceable evidence IDs.

---

## 6. Functional & Non-Functional Requirements

### Functional Requirements
- **FR-1 (Multi-Hop Traversal)**: Support 1, 2, and 3 hop bounded neighborhood queries from PostgreSQL. Reject depth $< 1$ or depth $> 3$ with `ValidationDomainError`.
- **FR-2 (Cap Enforcement)**: Enforce $5 \le max\_nodes \le 250$ and $5 \le max\_transactions \le 250$ on all network queries.
- **FR-3 (Deterministic Path Search)**: Implement BFS/Dijkstra bounded path-finding between source and target entities up to depth 4, ranking paths by strength score:
  $$S_{path} = \prod_{e \in path} w_e \cdot \frac{1}{1 + \text{hop\_count}}$$
- **FR-4 (Pattern Engine)**: Deterministically evaluate all 7 syndicate patterns with explicit mathematical conditions.
- **FR-5 (Temporal Correctness)**: All repository and service queries must accept an optional `as_of: datetime` parameter and apply $timestamp \le as\_of$.

### Non-Functional Requirements
- **NFR-1 (Latency)**: Multi-hop graph retrieval and network intelligence evaluation must execute in $\le 50\text{ ms}$ on standard database indexes.
- **NFR-2 (Memory Safety)**: Memory footprint for any network analysis request must remain $< 10\text{ MB}$, with zero construction of global 35k-node graphs.
- **NFR-3 (Auditability)**: All findings and risk evaluations must reference valid primary keys in PostgreSQL.
- **NFR-4 (Backward Compatibility)**: 100% test compatibility with all existing V1 and V2-01 through V2-06 test suites.
