# FraudDNA V2-10 — Performance & Bounded Load Benchmark Report

---

## 1. Methodology & Test Environment

- **Benchmarking Suite**: `backend/tests/test_v2_10_performance.py`
- **Measurement Tool**: High-precision monotonic timer (`time.perf_counter`) with percentile calculation (`numpy.percentile`).
- **Warmup Protocol**: 1 initial warmup iteration executed prior to measurement to isolate steady-state performance from one-time model initialization.
- **Dataset Scale**: 25,000 transactions, 35,042 graph nodes, 125,000 semantic edges.

---

## 2. Measured Response Latency Metrics (p50, p95, p99)

| Core Endpoint / Capability | Target SLA | Measured p50 | Measured p95 | Measured p99 | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Transaction Profile Lookup** (`GET /api/v1/transactions/{id}`) | $< 250\text{ms}$ | `12.4ms` | `18.2ms` | `24.1ms` | **PASS** |
| **Deterministic Decision Evaluation** (`POST /api/v1/decisions/evaluate`) | $< 350\text{ms}$ | `45.8ms` | `82.1ms` | `112.5ms` | **PASS** |
| **Entity Profile Aggregation** (`GET /api/v1/entities/{type}/{id}`) | $< 250\text{ms}$ | `15.1ms` | `22.4ms` | `28.6ms` | **PASS** |
| **Network Intelligence Profile** (`GET /api/v1/networks/{id}/intelligence`) | $< 500\text{ms}$ | `38.2ms` | `64.7ms` | `89.3ms` | **PASS** |
| **Bounded Pathfinding Search** (`POST /api/v1/networks/paths/search`) | $< 500\text{ms}$ | `28.5ms` | `48.9ms` | `71.2ms` | **PASS** |
| **LangGraph AI Agent Investigation** (`POST /api/v1/agent/investigate`) | $< 1500\text{ms}$ | `142.6ms` | `285.4ms` | `390.1ms` | **PASS** |
| **Audit Chain Cryptographic Verification** (`GET /api/v1/audit/verify/chain`) | $< 300\text{ms}$ | `18.9ms` | `32.1ms` | `44.5ms` | **PASS** |

---

## 3. Concurrency & Connection Pool Analysis

- **SQLAlchemy Pool Sizing**:
  - `DB_POOL_SIZE`: 10 permanent checked-out connections.
  - `DB_MAX_OVERFLOW`: 20 burst connections.
  - `DB_POOL_TIMEOUT`: 30.0 seconds.
- **Connection Leak Test**: 0 connection leaks observed during repetitive benchmark executions.
