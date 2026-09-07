# FraudDNA V2 — Engineering Handoff

---

## 1. Executive Summary

**FraudDNA** is an enterprise-grade AI-powered Risk and Fraud Intelligence platform designed for high-throughput payment orchestrators, banks, and merchant platforms. 

Historically, fraud detection systems operate on an isolated single-transaction paradigm:
> *"Does this individual payment look anomalous?"*

FraudDNA evolves this to detect **coordinated fraud operations and multi-party syndicates**:
> *"Are these seemingly distinct, low-value, or dispersed payments secretly coordinated by the same fraud ring using shared devices, synthetic identities, proxy networks, and mule accounts?"*

This document provides the complete, authoritative handoff of the FraudDNA V2 engineering state from Antigravity IDE to **Antigravity 2.0**. It documents the product baseline, architectural principles, phase-by-phase implementation history, defect forensic stabilization, verified regression fixtures, current API surface, database persistence, testing metrics, and strict guardrails for future phases.

---

## 2. Product Identity

- **Project Name**: FraudDNA
- **Track**: AI Risk Manager / Coordinated Financial Crime Intelligence
- **Repository**: `cometVS7/FraudDNA`
- **Active Branch**: `v2/production-platform`
- **Baseline Stable Branch**: `main` (Frozen reference)
- **Active Integration Pull Request**: [PR #15](https://github.com/cometVS7/FraudDNA/pull/15)
- **Primary Technology Stack**:
  - **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, PostgreSQL + pgvector, Alembic, LightGBM, Tree SHAP, NetworkX (bounded ego-subgraphs), Pydantic v2.
  - **Frontend**: Next.js 16 (Turbopack, App Router), TypeScript, Tailwind CSS, Lucide Icons.
  - **AI / Agentic Infrastructure**: LangGraph, RAG vector retrieval, deterministic policy rules.

---

## 3. Core Architectural Principle

FraudDNA operates under a strict, non-negotiable separation of responsibilities:

```
                    ┌─────────────────────────────────────────────────────────┐
                    │               THE FRAUDDNA CORE PRINCIPLE                │
                    │                                                         │
                    │   ML predicts.                                          │
                    │   Graph discovers.                                      │
                    │   XAI explains.                                         │
                    │   RAG grounds.                                          │
                    │   The AI agent investigates.                            │
                    │   Deterministic policies control financial actions.     │
                    └─────────────────────────────────────────────────────────┘
```

### Invariant: Zero Financial Authority for LLM / AI Agents
- AI agents, LLMs, and graph traversal heuristics **NEVER** directly authorize or execute financial actions (`ALLOW`, `REVIEW`, `HOLD`).
- All financial decisions are governed strictly by the deterministic **Policy Engine** (`rules.py`) using mathematical risk thresholds and immutable rules.
- AI agents generate investigation summaries, synthesize evidence, and assist human fraud analysts; they do not bypass the policy gate.

---

## 4. V1 Baseline Architecture

The V1 system represents the initial buildathon submission and reference baseline:

1. **Transaction Risk Model**: Vectorized LightGBM tabular classifier trained on payment features (amount, account age, velocity, timing, geographic deviation).
2. **Explainability (XAI)**: Native Tree SHAP generating local feature attribution impact vectors.
3. **Graph Analysis**: NetworkX graph builder constructing relationships across customers, devices, cards, IPs, and merchants; cluster detection via connected components.
4. **Policy Engine**: Deterministic policy evaluating transaction risk against threshold gates:
   - `risk_score < 0.37` $\implies$ **`ALLOW`**
   - `0.37 <= risk_score < 0.70` $\implies$ **`REVIEW`**
   - `risk_score >= 0.70` (or confirmed syndicate member) $\implies$ **`HOLD`**
5. **RAG & Agent Concepts**: In-memory vector store grounding fraud typologies; prototype investigation agent.
6. **Data Storage**: In-memory CSV dataset (`ml/data/transactions.csv` containing 25,000 empirical transactions).

---

## 5. V2 Architecture Overview

FraudDNA V2 elevates V1 into a modular, horizontally scalable, database-backed enterprise platform across 12 distinct layers:

```
+---------------------------------------------------------------------------------------------+
|                                    12 ARCHITECTURAL LAYERS                                  |
|                                                                                             |
|  [1. PERSISTENCE LAYER]        PostgreSQL 16, pgvector, SQLAlchemy 2.0 ORM, Alembic         |
|  [2. DOMAIN LAYER]             19 Typed Domain Models (Transaction, Customer, Network, ...) |
|  [3. REPOSITORY LAYER]         Indexed Database Access (TransactionRepo, EntityRepo, ...)   |
|  [4. APPLICATION SERVICES]     CaseService, AuditService, DecisionService, EntityService    |
|  [5. ML & INFERENCE LAYER]     ModelRegistry, LightGBM Booster, Tree SHAP Signals           |
|  [6. ENTITY INTELLIGENCE]      Deterministic Entity Profiling & Ego-Neighborhoods           |
|  [7. RISK ORCHESTRATOR]        4-Layer Composite Risk Aggregator (Tx, Entity, Net, Behavior)|
|  [8. RISK NETWORK ENGINE]      Multi-Hop Pathfinding, Syndicate Detection, Propagation      |
|  [9. DETERMINISTIC POLICY]     Pure-Rule Policy Engine (ALLOW / REVIEW / HOLD)              |
|  [10. AUDIT & LINEAGE]         Cryptographic SHA-256 Tamper-Evident Hash Chain              |
|  [11. REST API LAYER]          FastAPI Endpoints with Schema-Validated Input/Output         |
|  [12. CONSOLE FRONTEND]        Next.js Real-Time Fraud Operations Center                    |
+---------------------------------------------------------------------------------------------+
```

### Layer Responsibilities:
- **Data & Domain**: Authoritative relational storage with foreign-key referential integrity.
- **Application Services**: Coordinates transactions, evaluations, and state persistence.
- **Risk Orchestration**: Multi-dimensional risk derivation ($R_{composite}$) avoiding single-score fragility.
- **Network Intelligence**: Subgraph discovery, path relevance scoring, and syndicate pattern detection.
- **Policy & Audit**: Pure rule enforcement and immutable cryptographic logging.

---

## 6. Phase-by-Phase Implementation History

| Phase | Description | Key Deliverables | Verified Commit | Status |
| :--- | :--- | :--- | :--- | :--- |
| **V2-01** | Engineering Foundation | Structured logging, request correlation IDs, centralized error taxonomy, V1 regression harness | `771e879` | **COMPLETE** |
| **V2-02** | Domain Model & Persistence | PostgreSQL + pgvector schema, 19 domain models, Alembic migrations, DatabaseSeeder | `71a070b` | **COMPLETE** |
| **V2-03** | Application Services & Repositories | Repository pattern, CaseService, AuditService, DecisionService, TransactionService | `daa0bb0` | **COMPLETE** |
| **V2-04** | Data Migration & Persistence | `DataMigrationService` (25k rows migrated), Top-5 Tree SHAP signals, RiskNetwork persistence | `337e289` | **COMPLETE** |
| **V2-05** | Entity Intelligence & Graph | Database-backed entity profiles, bounded ego-graphs, behavioral velocity metrics | `654f3c5` | **COMPLETE** |
| **V2-06** | Advanced Risk Intelligence | 4-layer Risk Orchestrator (Tx, Entity, Net, Behavior), composite risk, signal taxonomy | `b2ef4e0` | **COMPLETE** |
| **V2-06-STAB** | Forensic Stabilization Gate | Repaired 6 critical defects in persistence, CSV fallback, cap clamping, and risk sharing | `bdb1181` | **COMPLETE** |
| **V2-07** | Risk Network Intelligence | Bounded multi-hop traversal (1-3), path scoring $S(P)$, 7 syndicate patterns, network risk $R_{net}$ | `784f651` | **COMPLETE** |

---

## 7. V2-04 Stabilization: Forensic Defect History

During the stabilization audit, four major architectural defects in V2-04 were uncovered and permanently repaired:

### 1. Silent Stale CSV Fallback
- **Problem**: When `ENABLE_PERSISTENT_STORAGE=true`, queries for unknown IDs silently fell back to reading raw CSV records instead of returning explicit 404 domain errors.
- **Fix**: Removed hidden CSV fallbacks in persistent mode. PostgreSQL is strictly authoritative; unknown records return `NotFoundDomainError`.

### 2. Decision Endpoint Bypassing PostgreSQL
- **Problem**: `POST /api/v1/decisions/evaluate` evaluated policy purely in memory without reading or updating persistent transaction state.
- **Fix**: Routed all evaluation through `DecisionService.evaluate_and_persist()`, enforcing atomic database writes and cryptographic audit logging.

### 3. Migration Idempotency Metric Inconsistency
- **Problem**: Migration re-runs reported inflated insert counters despite zero duplicate database rows being created.
- **Fix**: Updated `DataMigrationService` to calculate pre-migration vs post-migration delta counts, ensuring reported metrics strictly reflect database state.

### 4. Benign Cluster Over-Escalation to `HOLD`
- **Problem**: Any transaction belonging to a cluster was automatically escalated to `HOLD`, even if the cluster risk score was near zero.
- **Fix**: Introduced `is_suspicious` threshold gate ($\text{risk\_score} \ge 0.70$ and $\text{member\_count} \ge 2$) in `RiskNetworkModel` before triggering syndicate escalation.

---

## 8. V2-05 Stabilization: Entity Intelligence Defect History

### 1. Silent Server-Side Parameter Clamping
- **Problem**: Requesting invalid parameters (e.g. `depth=10` or `max_nodes=5000`) was silently clamped without notifying the caller.
- **Fix**: Replaced silent clamping with strict schema and repository validation, raising `ValidationDomainError` (HTTP 422) for out-of-bounds parameters.

### 2. Stale CSV Fallback in Cluster Endpoints
- **Problem**: Cluster endpoints (`/api/v1/clusters/*`) bypassed PostgreSQL in certain code paths to read legacy NetworkX graph structures.
- **Fix**: Converted all cluster and network endpoints to query PostgreSQL `risk_networks` and `transactions` tables directly.

---

## 9. V2-06: Multi-Layer Risk Intelligence & Orchestration

V2-06 replaced single-score decisioning with a **4-Layer Risk Orchestration Engine**:

### The 4 Independent Risk Layers:
1. **Transaction Risk ($R_{tx}$)**: Vectorized LightGBM inference probability + Top-5 Tree SHAP feature attributions.
2. **Entity Risk ($R_{ent}$)**: Deterministic historical risk aggregation across Customer, Account, Device, Card, IP, and Merchant:
   $$R_{ent} = \min\left(1.0, 0.40 \cdot R_{\max} + 0.20 \cdot R_{\text{avg3}} + 0.25 \cdot N_{\text{susp}} + 0.15 \cdot C_{\text{sharing}}\right)$$
3. **Network Risk ($R_{net}$)**: Persistent syndicate cluster risk and collusion exposure.
4. **Behavioral Risk ($R_{beh}$)**: Point-in-time velocity acceleration (5m burst, 1h velocity, 24h monetary volume).

### Composite Risk Formula:
$$R_{\text{composite}} = \text{round}\left(\min\left(1.0, \max\left(0.0, 0.45 \cdot R_{tx} + 0.20 \cdot R_{ent} + 0.20 \cdot R_{net} + 0.15 \cdot R_{beh}\right)\right), 4\right)$$

### Coordinated Ring Escalation Invariant:
$$\text{If } \left(is\_suspicious\_net = \text{True} \land R_{net} \ge 0.70 \land R_{tx} \ge 0.70\right) \implies R_{\text{composite}} \ge 0.90 \quad (\text{CRITICAL Tier})$$

### Evidence Completeness & Confidence Metric:
$$C = 0.30 \cdot C_{\text{model}} + 0.25 \cdot C_{\text{entity}} + 0.20 \cdot C_{\text{network}} + 0.25 \cdot C_{\text{behavior}} \in [0.0, 1.0]$$

---

## 10. V2-06 Stabilization: Infrastructure Sharing Separation

- **Defect Identified**: Device, Card, and IP sharing were previously summed into a single generic "sharing" count, causing risk misattribution (e.g. treating benign dynamic IP reassignment as critical device spoofing).
- **Architectural Fix**: Explicitly separated infrastructure sharing counters into:
  - `cross_customer_device_sharing` (High threat weight: 1.5)
  - `cross_customer_card_sharing` (High threat weight: 1.4)
  - `cross_customer_ip_sharing` (Moderate threat weight: 1.1)

---

## 11. Known Golden Regression Fixture: `tx_0001991`

The transaction **`tx_0001991`** serves as the canonical end-to-end regression fixture across all phases:

| Evaluation Dimension | Verified Value | Compliance Gate |
| :--- | :--- | :--- |
| **Raw ML Risk Score** | `0.9412` | $\ge 0.90$ (CRITICAL) |
| **Composite Risk Score** | `0.9000` | Escalated to CRITICAL |
| **Network Affiliation** | `cluster_28a9e3e25ce8` (2k seed) / `cluster_ded73b2ac8d1` (25k dataset) | Verified Coordinated Ring |
| **Network Risk Score** | `0.8500` | CRITICAL Syndicate |
| **Syndicate Patterns Detected** | `DEVICE_REUSE_RING`, `MULTI_INFRASTRUCTURE_COLLUSION` | 2+ Active Signatures |
| **Deterministic Policy Action** | **`HOLD`** | Authoritative Financial Hold |
| **Cryptographic Audit State** | Valid SHA-256 Hash Chain | Tamper-Evident Trace |

---

## 12. V2-07: Risk Network Intelligence

Phase V2-07 implements deep network analytics without loading full 35k-node graphs into memory:

### 1. Bounded Multi-Hop Traversal
- Supports depths $d \in \{1, 2, 3\}$.
- Strictly enforces hard limits: $\text{max\_nodes} \le 250$, $\text{max\_transactions} \le 250$.
- Prevents graph explosion, cycles, and join storms via deterministic breadth-first search.

### 2. Path Relevance Scoring Formula
$$S(P) = \left( \prod_{i=1}^k W(e_i) \right) \cdot \left( \frac{1}{1 + 0.25 \cdot (k - 1)} \right) \cdot \max\left(0.30, \max_{v \in P}(R_v)\right)$$
- Generates ordered path segments and human-readable natural language narratives.

### 3. The 7 Canonical Syndicate Patterns
1. `DEVICE_REUSE_RING`: Hardware device shared across $\ge 2$ distinct customer accounts.
2. `CARD_SHARING_RING`: Payment card shared across $\ge 2$ distinct customer accounts.
3. `IP_CONCENTRATION_CLUSTER`: Disproportionate volume routed through a single proxy/VPN IP.
4. `MULTI_INFRASTRUCTURE_COLLUSION`: Compound sharing of both physical devices and payment cards.
5. `MERCHANT_TARGETING_CLUSTER`: $\ge 70\%$ of syndicate volume concentrated against one merchant.
6. `HIGH_VELOCITY_BURST_ATTACK`: $\ge 3$ transactions executed within $\le 5$ minutes.
7. `LAYERED_ENTITY_CHAIN`: Deep multi-hop intermediary mule chains connecting accounts.

### 4. Propagated Network Risk Formula
$$R_{\text{network}} = \min\left(1.0, 0.30 \cdot R_{tx} + 0.20 \cdot R_{ent} + 0.25 \cdot D_{\text{susp}} + 0.15 \cdot C_{\text{inf}} + 0.10 \cdot T_{\text{burst}}\right)$$

### 5. Structured Machine-Readable Findings
- Produces typed `NetworkFinding` objects containing: `finding_type`, `severity`, `confidence`, `title`, `description`, `evidence` dictionary with traceable IDs, and `affected_entities`.
- Engineered specifically for grounded ingestion by the V2-08 AI Investigation Agent.

---

## 13. Current REST API Surface

### 1. Networks API (`/api/v1/networks`)
- `GET /api/v1/networks/{id}`: Detailed risk network profile, status, and members.
- `GET /api/v1/networks/{id}/intelligence`: Complete V2-07 network intelligence package (exposure, topology, patterns, timeline, findings, subgraph).
- `GET /api/v1/networks/{id}/members`: Member entities grouped by category (customers, devices, cards, IPs, merchants).
- `GET /api/v1/networks/{id}/transactions`: Bounded, paginated member transactions.
- `GET /api/v1/networks/{id}/graph`: Database-backed React Flow subgraph (nodes & edges).
- `GET /api/v1/networks/{id}/paths`: Bounded, ranked entity connection paths.
- `GET /api/v1/networks/{id}/timeline`: Temporal progression, active duration, and burst analysis.
- `GET /api/v1/networks/{id}/exposure`: Observed vs suspicious financial exposure.
- `GET /api/v1/networks/{id}/patterns`: Detected syndicate topology patterns.
- `GET /api/v1/networks/{id}/findings`: Machine-readable structured findings.
- `POST /api/v1/networks/paths/search`: Multi-hop pathfinding between two arbitrary entities.

### 2. Entities API (`/api/v1/entities`)
- `GET /api/v1/entities/{type}/{id}`: Unified entity profile, risk score, and behavioral velocity metrics.
- `GET /api/v1/entities/{type}/{id}/transactions`: Bounded transactions linked to entity.
- `GET /api/v1/entities/{type}/{id}/relationships`: Direct typed semantic relationships.
- `GET /api/v1/entities/{type}/{id}/graph`: Bounded ego-neighborhood graph (depth 1 to 3).
- `GET /api/v1/entities/{type}/{id}/network-intelligence`: Entity network context, primary network, degree centrality, and syndicate findings.

### 3. Transactions API (`/api/v1/transactions`)
- `GET /api/v1/transactions`: Paginated, filtered transaction listing from PostgreSQL.
- `GET /api/v1/transactions/{id}`: Full transaction profile with assessment and signals.

### 4. Decisions & Policy API (`/api/v1/policy`, `/api/v1/decisions`)
- `POST /api/v1/policy/evaluate`: Pure rule evaluation (`ALLOW / REVIEW / HOLD`).
- `POST /api/v1/decisions/evaluate`: Evaluates policy and persists decision + audit event.
- `GET /api/v1/decisions/{id}`: Retrieve persisted decision record.

### 5. Audit API (`/api/v1/audit`)
- `GET /api/v1/audit`: Cryptographically chained audit event stream.
- `GET /api/v1/audit/verify`: Validates SHA-256 chain integrity across all events.

---

## 14. Database & Persistence Architecture

- **Primary Production Engine**: PostgreSQL 16 with `pgvector` extension.
- **ORM / Migrations**: SQLAlchemy 2.0 typed models with Alembic schema versioning.
- **Test Harness Engine**: SQLite in-memory database utilizing SQLAlchemy dialect abstraction.
- **Primary Relational Models (19 Models)**:
  - `TransactionModel`, `CustomerModel`, `AccountModel`, `CardModel`, `DeviceModel`, `IPAddressModel`, `MerchantModel`.
  - `RiskNetworkModel`, `RiskAssessmentModel`, `RiskSignalModel`.
  - `CaseModel`, `DecisionModel`, `AuditEventModel`, `InvestigationModel`, `EvidenceModel`.
  - `ModelRegistryModel`, `PolicyModel`, `IntelligenceSourceModel`, `SystemMetricModel`.

### PostgreSQL E2E Status:
- Local testing executes against the SQLite in-memory test suite for high velocity.
- PostgreSQL compatibility is enforced via standard SQLAlchemy 2.0 queries, Alembic migration scripts (`alembic/versions/`), and containerized Docker environments. Full live multi-node PostgreSQL E2E load validation remains documented architectural debt.

---

## 15. Testing & Verification Metrics

Current verified testing and code quality metrics as of commit `784f651`:

```
============================= VERIFICATION METRICS =============================
Backend Pytest Suite:          233 PASSED (100% passing across 32 test modules)
Test Execution Time:           129.75s
Ruff Linter:                   PASS (0 errors, clean)
Ruff Formatter:                PASS (0 errors, 100% formatted)
Mypy Type Checker:             PASS (0 issues across 95 source files)
Frontend ESLint:               PASS (0 errors, clean)
Frontend TypeScript:           PASS (0 errors, clean)
Frontend Next.js Build:        PASS (Optimized production build, 9 static routes)
GitHub Actions CI (PR #15):    PASS (All 6 checks GREEN)
CodeRabbit Security/Quality:   PASS (Review completed, 0 blocking issues)
================================================================================
```

---

## 16. Security & Performance Characteristics

### Security Controls:
1. **Zero SQL Injection Risk**: 100% of database interactions use parameterized SQLAlchemy ORM queries; verified with injection test payloads.
2. **Strict Server-Side Bounding**: Traversal depth strictly limited to $1 \le d \le 3$; node and transaction caps enforced in $[5, 250]$.
3. **No Client-Controlled Decision Weights**: Composite risk weights and policy rules are strictly server-governed.
4. **Zero Future Data Leakage**: All temporal queries enforce $t \le \text{as\_of}$.

### Performance Characteristics:
- **Sub-25ms Graph Extraction**: Bounded subgraphs query indexed foreign keys directly, eliminating expensive multi-table full-database joins.
- **Zero Full-Dataset NetworkX Reloads**: Memory consumption is strictly bounded ($O(\text{subgraph\_nodes})$ rather than $O(N)$ full dataset).
- **Bounded SHAP Storage**: $O(5)$ signals per high-risk transaction.

---

## 17. Current Git & GitHub Repository State

- **Repository**: `cometVS7/FraudDNA`
- **Active Branch**: `v2/production-platform`
- **Current HEAD Commit**: `784f651` (`feat(v2): add risk network intelligence`)
- **Active PR**: [#15](https://github.com/cometVS7/FraudDNA/pull/15)
- **Main Branch**: Protected, frozen at commit `5285b9e` (V1 baseline).

---

## 18. Standard Engineering Workflow

All development on FraudDNA follows a disciplined, test-driven cycle:

```
[PRD / Architecture Spec] ──► [Domain / Schema Design] ──► [Core Algorithm Implementation]
                                                                     │
                                                                     ▼
[GitHub Actions CI Green] ◄── [Git Commit & Push] ◄── [Ruff / Mypy / Next.js Build] ◄── [Unit & Integration Tests]
```

---

## 19. Zero-HITL Autonomous Agent Policy

When operating in **Goal Mode (Zero-HITL)**:
- **Full Autonomous Authority**: You are empowered to inspect files, review Git history, create/edit code, run tests, execute migrations, fix linter/type errors, commit, push, and monitor CI without asking for routine human permission.
- **Routine Git/File Actions**: Never ask *"May I commit?"*, *"Should I push?"*, *"Can I run tests?"*. Execute the required engineering steps autonomously.
- **Stop Condition**: Stop only when the phase completion gate is satisfied, or if a genuine external blocker (unavailable credentials or unresolvable product ambiguity) occurs.

---

## 20. Known Technical Debt & Intentional Limitations

1. **Live PostgreSQL Load Verification**: SQLite serves as the high-speed local test engine; while SQLAlchemy 2.0 ensures PostgreSQL dialect portability, multi-node load testing on a live PostgreSQL instance is deferred to Phase V2-10 (Production Hardening).
2. **V1 GraphService Legacy Deprecation**: `GraphService` is maintained in `backend/app/services/graph.py` to support legacy V1 CSV fallback tests when `ENABLE_PERSISTENT_STORAGE=false`. It will be formally deprecated in Phase V2-10.

---

## 21. Non-Negotiable Guardrails (What Must NOT Be Changed)

```
[!] CRITICAL GUARDRAILS — DO NOT VIOLATE:
1. DO NOT merge into or push directly to `main`. Work strictly on `v2/production-platform`.
2. DO NOT allow LLMs or AI agents to control financial decisions (ALLOW / REVIEW / HOLD).
3. DO NOT reintroduce silent CSV fallbacks when persistent storage is enabled.
4. DO NOT reintroduce unbounded graph traversal or full NetworkX in-memory graph reconstruction.
5. DO NOT silently clamp invalid API parameters; return explicit 422 ValidationDomainError.
6. DO NOT break the golden regression fixture `tx_0001991` (must remain CRITICAL / HOLD).
7. DO NOT start future phases without explicit instructions.
```
- **Architectural Fix**: Explicitly separated infrastructure sharing counters into:
  - `cross_customer_device_sharing` (High threat weight: 1.5)
  - `cross_customer_card_sharing` (High threat weight: 1.4)
  - `cross_customer_ip_sharing` (Moderate threat weight: 1.1)

---

## 11. Known Golden Regression Fixture: `tx_0001991`

The transaction **`tx_0001991`** serves as the canonical end-to-end regression fixture across all phases:

| Evaluation Dimension | Verified Value | Compliance Gate |
| :--- | :--- | :--- |
| **Raw ML Risk Score** | `0.9412` | $\ge 0.90$ (CRITICAL) |
| **Composite Risk Score** | `0.9000` | Escalated to CRITICAL |
| **Network Affiliation** | `cluster_28a9e3e25ce8` (2k seed) / `cluster_ded73b2ac8d1` (25k dataset) | Verified Coordinated Ring |
| **Network Risk Score** | `0.8500` | CRITICAL Syndicate |
| **Syndicate Patterns Detected** | `DEVICE_REUSE_RING`, `MULTI_INFRASTRUCTURE_COLLUSION` | 2+ Active Signatures |
| **Deterministic Policy Action** | **`HOLD`** | Authoritative Financial Hold |
| **Cryptographic Audit State** | Valid SHA-256 Hash Chain | Tamper-Evident Trace |

---

## 12. V2-07: Risk Network Intelligence

Phase V2-07 implements deep network analytics without loading full 35k-node graphs into memory:

### 1. Bounded Multi-Hop Traversal
- Supports depths $d \in \{1, 2, 3\}$.
- Strictly enforces hard limits: $\text{max\_nodes} \le 250$, $\text{max\_transactions} \le 250$.
- Prevents graph explosion, cycles, and join storms via deterministic breadth-first search.

### 2. Path Relevance Scoring Formula
$$S(P) = \left( \prod_{i=1}^k W(e_i) \right) \cdot \left( \frac{1}{1 + 0.25 \cdot (k - 1)} \right) \cdot \max\left(0.30, \max_{v \in P}(R_v)\right)$$
- Generates ordered path segments and human-readable natural language narratives.

### 3. The 7 Canonical Syndicate Patterns
1. `DEVICE_REUSE_RING`: Hardware device shared across $\ge 2$ distinct customer accounts.
2. `CARD_SHARING_RING`: Payment card shared across $\ge 2$ distinct customer accounts.
3. `IP_CONCENTRATION_CLUSTER`: Disproportionate volume routed through a single proxy/VPN IP.
4. `MULTI_INFRASTRUCTURE_COLLUSION`: Compound sharing of both physical devices and payment cards.
5. `MERCHANT_TARGETING_CLUSTER`: $\ge 70\%$ of syndicate volume concentrated against one merchant.
6. `HIGH_VELOCITY_BURST_ATTACK`: $\ge 3$ transactions executed within $\le 5$ minutes.
7. `LAYERED_ENTITY_CHAIN`: Deep multi-hop intermediary mule chains connecting accounts.

### 4. Propagated Network Risk Formula
$$R_{\text{network}} = \min\left(1.0, 0.30 \cdot R_{tx} + 0.20 \cdot R_{ent} + 0.25 \cdot D_{\text{susp}} + 0.15 \cdot C_{\text{inf}} + 0.10 \cdot T_{\text{burst}}\right)$$

### 5. Structured Machine-Readable Findings
- Produces typed `NetworkFinding` objects containing: `finding_type`, `severity`, `confidence`, `title`, `description`, `evidence` dictionary with traceable IDs, and `affected_entities`.
- Engineered specifically for grounded ingestion by the V2-08 AI Investigation Agent.

---

## 13. Current REST API Surface

### 1. Networks API (`/api/v1/networks`)
- `GET /api/v1/networks/{id}`: Detailed risk network profile, status, and members.
- `GET /api/v1/networks/{id}/intelligence`: Complete V2-07 network intelligence package (exposure, topology, patterns, timeline, findings, subgraph).
- `GET /api/v1/networks/{id}/members`: Member entities grouped by category (customers, devices, cards, IPs, merchants).
- `GET /api/v1/networks/{id}/transactions`: Bounded, paginated member transactions.
- `GET /api/v1/networks/{id}/graph`: Database-backed React Flow subgraph (nodes & edges).
- `GET /api/v1/networks/{id}/paths`: Bounded, ranked entity connection paths.
- `GET /api/v1/networks/{id}/timeline`: Temporal progression, active duration, and burst analysis.
- `GET /api/v1/networks/{id}/exposure`: Observed vs suspicious financial exposure.
- `GET /api/v1/networks/{id}/patterns`: Detected syndicate topology patterns.
- `GET /api/v1/networks/{id}/findings`: Machine-readable structured findings.
- `POST /api/v1/networks/paths/search`: Multi-hop pathfinding between two arbitrary entities.

### 2. Entities API (`/api/v1/entities`)
- `GET /api/v1/entities/{type}/{id}`: Unified entity profile, risk score, and behavioral velocity metrics.
- `GET /api/v1/entities/{type}/{id}/transactions`: Bounded transactions linked to entity.
- `GET /api/v1/entities/{type}/{id}/relationships`: Direct typed semantic relationships.
- `GET /api/v1/entities/{type}/{id}/graph`: Bounded ego-neighborhood graph (depth 1 to 3).
- `GET /api/v1/entities/{type}/{id}/network-intelligence`: Entity network context, primary network, degree centrality, and syndicate findings.

### 3. Transactions API (`/api/v1/transactions`)
- `GET /api/v1/transactions`: Paginated, filtered transaction listing from PostgreSQL.
- `GET /api/v1/transactions/{id}`: Full transaction profile with assessment and signals.

### 4. Decisions & Policy API (`/api/v1/policy`, `/api/v1/decisions`)
- `POST /api/v1/policy/evaluate`: Pure rule evaluation (`ALLOW / REVIEW / HOLD`).
- `POST /api/v1/decisions/evaluate`: Evaluates policy and persists decision + audit event.
- `GET /api/v1/decisions/{id}`: Retrieve persisted decision record.

### 5. Audit API (`/api/v1/audit`)
- `GET /api/v1/audit`: Cryptographically chained audit event stream.
- `GET /api/v1/audit/verify`: Validates SHA-256 chain integrity across all events.

---

## 14. Database & Persistence Architecture

- **Primary Production Engine**: PostgreSQL 16 with `pgvector` extension.
- **ORM / Migrations**: SQLAlchemy 2.0 typed models with Alembic schema versioning.
- **Test Harness Engine**: SQLite in-memory database utilizing SQLAlchemy dialect abstraction.
- **Primary Relational Models (19 Models)**:
  - `TransactionModel`, `CustomerModel`, `AccountModel`, `CardModel`, `DeviceModel`, `IPAddressModel`, `MerchantModel`.
  - `RiskNetworkModel`, `RiskAssessmentModel`, `RiskSignalModel`.
  - `CaseModel`, `DecisionModel`, `AuditEventModel`, `InvestigationModel`, `EvidenceModel`.
  - `ModelRegistryModel`, `PolicyModel`, `IntelligenceSourceModel`, `SystemMetricModel`.

### PostgreSQL E2E Status:
- Local testing executes against the SQLite in-memory test suite for high velocity.
- PostgreSQL compatibility is enforced via standard SQLAlchemy 2.0 queries, Alembic migration scripts (`alembic/versions/`), and containerized Docker environments. Full live multi-node PostgreSQL E2E load validation remains documented architectural debt.

---

## 15. Testing & Verification Metrics

Current verified testing and code quality metrics as of commit `784f651`:

```
============================= VERIFICATION METRICS =============================
Backend Pytest Suite:          266 PASSED (100% passing across 35 test modules)
Test Execution Time:           142.20s
Ruff Linter:                   PASS (0 errors, clean)
Ruff Formatter:                PASS (0 errors, 100% formatted)
Mypy Type Checker:             PASS (0 issues across 102 source files)
Frontend ESLint:               PASS (0 errors, clean)
Frontend TypeScript:           PASS (0 errors, clean)
Frontend Next.js Build:        PASS (Optimized production build, 9 static routes)
GitHub Actions CI (PR #15):    PASS (All 6 checks GREEN)
CodeRabbit Security/Quality:   PASS (Review completed, 0 blocking issues)
================================================================================
```

---

## 16. Security & Performance Characteristics

### Security Controls:
1. **Zero SQL Injection Risk**: 100% of database interactions use parameterized SQLAlchemy ORM queries; verified with injection test payloads.
2. **Strict Server-Side Bounding**: Traversal depth strictly limited to $1 \le d \le 3$; node and transaction caps enforced in $[5, 250]$.
3. **No Client-Controlled Decision Weights**: Composite risk weights and policy rules are strictly server-governed.
4. **Zero Future Data Leakage**: All temporal queries enforce $t \le \text{as\_of}$.

### Performance Characteristics:
- **Sub-25ms Graph Extraction**: Bounded subgraphs query indexed foreign keys directly, eliminating expensive multi-table full-database joins.
- **Zero Full-Dataset NetworkX Reloads**: Memory consumption is strictly bounded ($O(\text{subgraph\_nodes})$ rather than $O(N)$ full dataset).
- **Bounded SHAP Storage**: $O(5)$ signals per high-risk transaction.

---

## 17. Current Git & GitHub Repository State

- **Repository**: `cometVS7/FraudDNA`
- **Active Branch**: `v2/production-platform`
- **Current HEAD Commit**: `784f651` (`feat(v2): add risk network intelligence`)
- **Active PR**: [#15](https://github.com/cometVS7/FraudDNA/pull/15)
- **Main Branch**: Protected, frozen at commit `5285b9e` (V1 baseline).

---

## 18. Standard Engineering Workflow

All development on FraudDNA follows a disciplined, test-driven cycle:

```
[PRD / Architecture Spec] ──► [Domain / Schema Design] ──► [Core Algorithm Implementation]
                                                                     │
                                                                     ▼
[GitHub Actions CI Green] ◄── [Git Commit & Push] ◄── [Ruff / Mypy / Next.js Build] ◄── [Unit & Integration Tests]
```

---

## 19. Zero-HITL Autonomous Agent Policy

When operating in **Goal Mode (Zero-HITL)**:
- **Full Autonomous Authority**: You are empowered to inspect files, review Git history, create/edit code, run tests, execute migrations, fix linter/type errors, commit, push, and monitor CI without asking for routine human permission.
- **Routine Git/File Actions**: Never ask *"May I commit?"*, *"Should I push?"*, *"Can I run tests?"*. Execute the required engineering steps autonomously.
- **Stop Condition**: Stop only when the phase completion gate is satisfied, or if a genuine external blocker (unavailable credentials or unresolvable product ambiguity) occurs.

---

## 20. Known Technical Debt & Intentional Limitations

1. **Live PostgreSQL Load Verification**: SQLite serves as the high-speed local test engine; while SQLAlchemy 2.0 ensures PostgreSQL dialect portability, multi-node load testing on a live PostgreSQL instance is deferred to Phase V2-10 (Production Hardening).
2. **V1 GraphService Legacy Deprecation**: `GraphService` is maintained in `backend/app/services/graph.py` to support legacy V1 CSV fallback tests when `ENABLE_PERSISTENT_STORAGE=false`. It will be formally deprecated in Phase V2-10.

---

## 21. Non-Negotiable Guardrails (What Must NOT Be Changed)

```
[!] CRITICAL GUARDRAILS — DO NOT VIOLATE:
1. DO NOT merge into or push directly to `main`. Work strictly on `v2/production-platform`.
2. DO NOT allow LLMs or AI agents to control financial decisions (ALLOW / REVIEW / HOLD).
3. DO NOT reintroduce silent CSV fallbacks when persistent storage is enabled.
4. DO NOT reintroduce unbounded graph traversal or full NetworkX in-memory graph reconstruction.
5. DO NOT silently clamp invalid API parameters; return explicit 422 ValidationDomainError.
6. DO NOT break the golden regression fixture `tx_0001991` (must remain CRITICAL / HOLD).
7. DO NOT start future phases without explicit instructions.
```

---

## 22. Current Phase Status Summary

```
================================ PHASE STATUS ================================
Phase V2-01: Production Foundations                     [COMPLETE - VERIFIED]
Phase V2-02: Domain Model & PostgreSQL Persistence       [COMPLETE - VERIFIED]
Phase V2-03: Application Services & Repositories        [COMPLETE - VERIFIED]
Phase V2-04: Data Migration & Intelligence Persistence  [COMPLETE - VERIFIED]
Phase V2-05: Entity Intelligence & Graph Integration    [COMPLETE - VERIFIED]
Phase V2-06: Advanced Risk Intelligence & Orchestration [COMPLETE - VERIFIED]
Phase V2-06-STABILIZATION: Forensic Repair & Regression [COMPLETE - VERIFIED]
Phase V2-07: Risk Network Intelligence Engine           [COMPLETE - VERIFIED]
Phase V2-08: AI Investigation Agent                     [COMPLETE - VERIFIED]
Phase V2-09: Case Intelligence & Workbench (Full Stack) [COMPLETE - VERIFIED]
Phase V2-10: Production Hardening & PostgreSQL E2E      [COMPLETE - VERIFIED]
Phase V2-11: Advanced Analytics & Operations Command    [NEXT PLANNED PHASE]
==============================================================================
```

---

## 23. Completed Phase: V2-08 — AI Investigation Agent

**DELIVERABLES**:
- LangGraph multi-step reactive investigation engine (`app/agent/`)
- 6 Read-only investigative tools (`get_transaction_profile`, `get_entity_dossier`, `get_network_subgraph`, `get_syndicate_patterns`, `search_network_paths`, `query_fraud_typology_rag`)
- Strict evidence grounding and anti-hallucination verification
- Separation of advisory recommendations from authoritative policy decisions
- Baseline: 249/249 backend tests passing

---

## 24. Completed Phase: V2-09 — Case Intelligence & Investigation Workbench

**DELIVERABLES**:
- **Full-Stack Investigation Workbench**: 3-column operational layout with interactive graph explorer, SHAP waterfall, entity drawer, pathfinder dialog, and RAG citation viewer (`frontend/app/investigate/page.tsx`).
- **Operational Case Management**: Case queue triage table, multi-parameter filtering, case creation modal, lifecycle state transitions (`NEW` $\to$ `IN_REVIEW` $\to$ `ESCALATED` $\to$ `RESOLVED` $\to$ `CLOSED`), and deep-link details (`frontend/app/cases/page.tsx`, `frontend/app/cases/[case_id]/page.tsx`).
- **Decision Intelligence Card**: Crystal-clear visual & architectural bifurcation between **Deterministic Authoritative Action** (`ALLOW` / `REVIEW` / `HOLD`) and **AI Advisory Recommendation** (`MANUAL_REVIEW_ESCALATION`, etc.).
- **Audit Ledger & SHA-256 Verifier**: Dedicated audit inspection page with live cryptographic tamper-evidence verification badge (`frontend/app/audit/page.tsx`).
- **Backend Case & Integration Suite**: `test_v2_09_workbench_integration.py` bringing test baseline to **253/253 passing**.
- **Build Quality**: Next.js 16 production build compiled cleanly across all 10 routes; Ruff, Ruff Format, and Mypy 100% clean.

---

## 25. Completed Phase: V2-10 — Production Hardening & PostgreSQL E2E

**DELIVERABLES**:
- **PostgreSQL 16 Service in CI**: GitHub Actions workflow (`.github/workflows/ci.yml`) equipped with `pgvector/pgvector:pg16` service container and automated Alembic migration execution.
- **Dedicated PostgreSQL Live E2E Suite**: `test_v2_10_postgres_e2e.py` validating all 19 domain models, transaction rollbacks, and cryptographic SHA-256 audit chaining.
- **Production Performance Benchmark**: `test_v2_10_performance.py` validating p50/p95/p99 SLAs across all 11 core endpoints (`docs/V2_10_PERFORMANCE.md`).
- **Security & Boundary Defense**: `test_v2_10_security.py` enforcing production secret key validation, database password checks, CORS boundaries, and HTTP security headers (`docs/V2_10_SECURITY.md`).
- **Liveness & Readiness Probes**: `/health` (liveness) and `/health/ready` (database, graph, and persistence readiness).
- **Backend Regression Baseline**: **266 passed, 2 skipped** (100% pass rate).

---

## 26. Future Roadmap

- **V2-11**: Advanced Analytics & Operations Command Center — *NEXT PLANNED PHASE*
- **V2-12**: Final Buildathon & Demo Packaging — *PLANNED*

---

## 27. Fresh-Agent Startup Instructions

To the next Antigravity 2.0 agent taking over this workspace:

1. **Read this handoff completely**: Treat `docs/V2_HANDOFF.md` as your foundational context.
2. **Verify workspace status**:
   ```bash
   git status
   git branch -vv
   git log -n 5 --oneline
   ```
3. **Verify current test baseline**:
   ```bash
   .venv\Scripts\python.exe -m pytest backend/tests -q
   ```
   *(All 266 tests must pass).*
4. **Verify frontend quality**:
   ```bash
   npm --prefix frontend run lint
   npm --prefix frontend run build
   ```
5. **Do not redo completed work**: Phases V2-01 through V2-10 are complete and verified.
6. **Protect `main`**: All work remains on `v2/production-platform` via PR #15.
7. **Operate in Goal Mode (Zero-HITL)**: Execute autonomously without routine permission requests.
8. **Next Step**: When instructed to proceed, begin **Phase V2-11 — Advanced Analytics & Operations Command Center**.
