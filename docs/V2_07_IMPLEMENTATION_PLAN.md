# FraudDNA V2 — Phase V2-07 Implementation Plan
## Risk Network Intelligence & Coordinated Syndicate Engine

---

## 1. Objectives & Overview

Phase V2-07 builds the foundational **Risk Network Intelligence Engine** that powers deep syndicate discovery, multi-hop pathfinding, risk propagation, attack pattern detection, and structured findings.

---

## 2. Milestones & Work Breakdown

### Milestone 1: Pydantic Schema Contracts
- **File**: `backend/app/schemas/network_intelligence.py`
- **Contents**:
  - `NetworkIntelligenceResponse`: Full intelligence payload for a network.
  - `NetworkPath`: Represents a typed, scored connection path between entities.
  - `SyndicatePattern`: Formal structure for detected attack signatures.
  - `NetworkTimelinePoint` & `NetworkTimeline`: Temporal activity distribution.
  - `NetworkExposure`: Observed vs. inferred financial exposure.
  - `NetworkFinding`: Structured findings with evidence links.
  - `EntityNetworkIntelligenceResponse`: Network intelligence for a single entity.

### Milestone 2: Path Intelligence Engine
- **File**: `backend/app/graph/paths.py`
- **Class**: `PathIntelligenceEngine`
- **Capabilities**:
  - Bounded multi-hop traversal (1 to 3 hops).
  - Entity-to-entity shortest path and strongest path discovery (up to depth 4).
  - Mathematical path ranking formula using semantic edge weights (`SHARES_DEVICE` 0.95, `SHARES_CARD` 0.90, `SHARES_IP` 0.60).
  - Node and edge deduplication, cycle detection.

### Milestone 3: Syndicate Pattern Detection Engine
- **File**: `backend/app/graph/syndicate.py`
- **Class**: `SyndicateDetector`
- **Capabilities**:
  - Implementation of all 7 canonical fraud syndicate patterns:
    1. `DEVICE_REUSE_RING`
    2. `CARD_SHARING_RING`
    3. `IP_CONCENTRATION_CLUSTER`
    4. `MULTI_INFRASTRUCTURE_COLLUSION`
    5. `MERCHANT_TARGETING_CLUSTER`
    6. `HIGH_VELOCITY_BURST_ATTACK`
    7. `LAYERED_ENTITY_CHAIN`
  - Explicit triggering criteria, confidence scoring $[0.0, 1.0]$, and structured explanations.

### Milestone 4: Network Analytics Engine
- **File**: `backend/app/graph/network_analytics.py`
- **Class**: `NetworkAnalyticsEngine`
- **Capabilities**:
  - Deterministic 5-component Network Risk Propagation formula ($R_{tx}$, $R_{ent}$, $D_{susp}$, $C_{inf}$, $T_{burst}$).
  - Point-in-time temporal timeline analysis ($timestamp \le as\_of$).
  - Observed vs. inferred exposure metrics calculation.
  - Structured findings synthesis for V2-08 agent consumption.

### Milestone 5: Network Intelligence Application Service
- **File**: `backend/app/services/network_intelligence.py`
- **Class**: `NetworkIntelligenceService`
- **Capabilities**:
  - Coordinates database queries, analytics engine, syndicate detector, and path engine.
  - Generates full network intelligence, path searches, timelines, exposure profiles, and entity network context.
  - Registered in `app.services.__init__`.

### Milestone 6: Repository Extensions & Multi-Hop Traversal
- **Files**:
  - `backend/app/repositories/network_repository.py`
  - `backend/app/repositories/entity_repository.py`
- **Capabilities**:
  - Bounded multi-hop ego-graph expansion (depth 1, 2, and 3).
  - Optimized SQL queries for member transactions, shared entity links, and temporal bounds.

### Milestone 7: API Endpoints & Routing
- **Files**:
  - `backend/app/api/v1/endpoints/networks.py` (enhanced)
  - `backend/app/api/v1/endpoints/network_intelligence.py` (new)
- **Endpoints**:
  - `GET /api/v1/networks/{id}/intelligence`
  - `GET /api/v1/networks/{id}/paths`
  - `GET /api/v1/networks/{id}/timeline`
  - `GET /api/v1/networks/{id}/exposure`
  - `GET /api/v1/networks/{id}/patterns`
  - `GET /api/v1/networks/{id}/findings`
  - `GET /api/v1/entities/{type}/{id}/network-intelligence`
  - `POST /api/v1/network-analysis/paths`

### Milestone 8: Golden Synthetic Fixtures & Unit Tests
- **Files**:
  - `backend/tests/fixtures/synthetic_networks.py`
  - `backend/tests/test_v2_network_intelligence.py`
- **Test Categories**:
  - Unit tests for all 7 patterns and path ranking.
  - Integration tests for database queries and service orchestration.
  - Boundary tests (depth 1, 2, 3, 4 rejection; node caps; empty networks).
  - Temporal correctness tests ($timestamp \le as\_of$).
  - Full regression on V2-04, V2-05, V2-06 (`tx_0001991`).

### Milestone 9: Static Analysis & Validation
- Run Ruff linter and formatter.
- Run Mypy type checker.
- Run frontend lint, type-check, and build.
- Run full pytest test suite.

### Milestone 10: Git Operations & PR Update
- Commit: `feat(v2): add risk network intelligence`
- Push to `v2/production-platform`.
- Verify CI passes.
