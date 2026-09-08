# FraudDNA V2-08 — Product Requirements Document (PRD)
## Autonomous AI Investigation Agent & Grounded Evidence Synthesis

---

## 1. Document Control & Metadata

- **Document Version**: 2.0.0-PROD-SPEC
- **Status**: APPROVED ARCHITECTURAL SPECIFICATION
- **Phase Target**: Phase V2-08 (AI Investigation Agent)
- **Author**: FraudDNA Autonomous Lead Engineer
- **Integration Target**: PR #15 (`v2/production-platform` $\to$ `main`)
- **Core Reference Baseline**: `docs/V2_HANDOFF.md`, `docs/V2_07_ARCHITECTURE.md`, `backend/app/models/domain.py`

---

## 2. Executive Summary & Problem Statement

Historically, financial fraud investigation platforms rely on disjointed consoles: human investigators must manually jump across tabular transaction viewers, graph visualizers, explainability (XAI) dashboards, and regulatory compliance playbooks to build a case. In high-throughput orchestrators processing tens of thousands of transactions per minute, this manual synthesis creates severe operational bottlenecks, delays triage of coordinated syndicates, and leads to inconsistent evidence documentation.

**FraudDNA V2-08** introduces the **Autonomous AI Investigation Agent**—an enterprise-grade, bounded, evidence-grounded investigative intelligence system built on **LangGraph**. The AI Investigation Agent autonomously coordinates transaction risk profiling, entity ego-neighborhood inspection, syndicate pattern discovery, multi-hop connection path analysis, Tree SHAP feature attributions, and regulatory fraud typology grounding (RAG) into structured, audit-persisted investigation dossiers.

---

## 3. The Core Architectural Invariant

FraudDNA enforces a strict, immutable separation of concerns across the intelligence stack:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE FRAUDDNA CORE INVARIANT                         │
│                                                                             │
│   ML predicts.                                                              │
│   Graph discovers.                                                          │
│   XAI explains.                                                             │
│   RAG grounds.                                                              │
│   The AI agent investigates.                                                │
│   Deterministic policies control financial actions.                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Invariant Non-Negotiables:
1. **Zero Financial Authority for AI/LLM**: The AI agent **NEVER** has authority to approve a transaction, block a transaction, change decision states (`ALLOW`, `REVIEW`, `HOLD`), alter numerical risk scores, or mutate financial state.
2. **Purely Advisory & Evidentiary**: The agent generates analytical hypotheses, synthesizes verifiable evidence traces, calculates investigation confidence, and recommends operational case next-steps for human fraud analysts.
3. **Deterministic Policy Gate**: All financial enforcement is governed exclusively by the pure-rule Policy Engine (`app.policy.rules`) and persisted via `DecisionService`.

---

## 4. Goals & Non-Goals

### 4.1 Primary Goals (In-Scope)
- **Autonomous Multi-Layer Investigation**: Automatically synthesize data across Transaction ML ($R_{tx}$), Entity Intelligence ($R_{ent}$), Network Syndicate Analytics ($R_{net}$), Behavioral Velocity ($R_{beh}$), Tree SHAP XAI vectors, and Typology RAG documents.
- **Bounded LangGraph State Machine**: Orchestrate investigations via a deterministic, bounded state graph with strict node budgets (max 10 tool calls, max 8 reasoning steps), explicit loop termination, and degraded fallback modes.
- **Evidence Hierarchy & Strict Grounding**: Require every finding, hypothesis, and severity rating to cite verifiable entity IDs, transaction IDs, network cluster IDs, path IDs, SHAP signal names, or typology document IDs.
- **Read-Only Tool Registry**: Provide 9 allowlisted, deterministic, read-only tools querying PostgreSQL repositories and vector stores with zero risk of state corruption.
- **Dual-Engine Model Abstraction**: Decouple the reasoning engine via a multi-provider LLM abstraction (`BaseLLMProvider`) supporting Cloud LLMs (Gemini, OpenAI, Anthropic) alongside an offline, zero-dependency `DeterministicFallbackEngine` for CI and air-gapped deployments.
- **PostgreSQL & Cryptographic Audit Persistence**: Persist investigation dossiers, evidence items, and AI findings into existing `InvestigationModel`, `EvidenceModel`, `AIFindingModel` tables, linked to `AuditEventModel` with SHA-256 tamper-evident hash chaining.
- **Golden Regression Compliance**: Verify end-to-end investigation fidelity against canonical syndicate transaction `tx_0001991`.

### 4.2 Non-Goals (Strictly Out-of-Scope)
- **Direct Financial Action Execution**: The agent will not invoke settlement APIs, block cards, freeze accounts, or override `DecisionModel`.
- **Unconstrained Autonomous Tool Calling**: The agent will not have access to arbitrary bash execution, unvalidated Python REPL, raw SQL queries, or network egress outside allowlisted services.
- **Dynamic Database Schema Expansions**: No new database tables will be introduced; V2-08 maps directly into the 19 domain models established in V2-02.
- **Full Case Management UI**: Interactive multi-tab investigation UI is scheduled for Phase V2-11; V2-08 delivers complete, schema-validated REST APIs.

---

## 5. User Personas & User Stories

### 5.1 Personas
- **Tier-2 Fraud Operations Analyst**: Investigates escalated `REVIEW` and `HOLD` transactions, needing complete context, syndicate graphs, and playbook justification within seconds.
- **Risk Compliance & Audit Officer**: Validates that all automated fraud decisions and investigator notes are cryptographically traceable to empirical evidence without hallucination.
- **Engineering / ML Platform Lead**: Monitors agent latency, token usage, tool invocation reliability, grounding completeness, and degraded fallback rates.

### 5.2 User Stories
1. **US-01 (Automated Transaction Investigation)**: *As a fraud analyst, when a high-risk transaction (`tx_0001991`) is flagged, I want an AI agent to automatically pull the 4-layer risk score, inspect linked device/card sharing, identify any affiliated fraud syndicate, and retrieve matching fraud playbooks so I can understand the threat immediately.*
2. **US-02 (Verifiable Evidence Grounding)**: *As a compliance officer, I want every claim in the investigation summary to cite specific transaction IDs, device IDs, or RAG playbook sections so that unsupported LLM hallucinations are strictly prevented.*
3. **US-03 (Offline / Resilient Execution)**: *As an infrastructure engineer, I want the system to cleanly fall back to a deterministic rule-based investigation if the external LLM provider experiences latency spikes or network outages, guaranteeing zero downtime.*
4. **US-04 (Cryptographic Audit Lineage)**: *As a risk auditor, I want every investigation report and its tool execution trace to be hashed and appended to the SHA-256 audit ledger.*

---

## 6. Detailed Functional Requirements

### 6.1 Bounded State Machine (LangGraph)
- **FR-01**: The agent must execute as a compiled LangGraph `StateGraph` using a typed `InvestigationState` schema.
- **FR-02**: The workflow must enforce a hard upper bound of $N \le 10$ tool calls and $S \le 8$ reasoning transitions.
- **FR-03**: The graph must include deterministic entry setup (`initialize`), structured context extraction (`extract_context`), risk orchestration (`orchestrate_risk`), network syndicate discovery (`investigate_network`), typology retrieval (`retrieve_typology`), evidence evaluation (`evaluate_evidence`), structured synthesis (`synthesize_findings`), and persistence validation (`validate_and_persist`).
- **FR-04**: If an external LLM call fails, times out (> 15.0s), or returns unparseable JSON, the graph must route to `degraded_deterministic_synthesis` without raising unhandled 500 exceptions.

### 6.2 Read-Only Tool Registry
- **FR-05**: All agent tools must be strictly read-only and execute against the SQLAlchemy 2.0 repository layer.
- **FR-06**: Tool parameter schemas must be validated via Pydantic with strict bounds (e.g., depth $1 \le d \le 3$, limits $1 \le k \le 100$).
- **FR-07**: Allowlisted tools:
  1. `get_transaction_profile(transaction_id: str)`
  2. `get_risk_orchestration(transaction_id: str)`
  3. `get_shap_signals(transaction_id: str)`
  4. `get_entity_profile(entity_type: str, entity_id: str)`
  5. `get_entity_ego_graph(entity_type: str, entity_id: str, depth: int, max_nodes: int)`
  6. `get_network_intelligence(network_id: str, max_transactions: int)`
  7. `search_network_paths(source_id: str, target_id: str, max_depth: int)`
  8. `search_typology_rag(query: str, top_k: int, category: str | None)`
  9. `get_audit_history(entity_id: str, limit: int)`

### 6.3 Evidence Hierarchy & Provenance
- **FR-08**: Every synthesized evidence item must be typed into an explicit hierarchy:
  - `TRANSACTION_EVIDENCE`: Direct payment attributes (amount, currency, merchant category).
  - `XAI_EVIDENCE`: Local feature attribution (Tree SHAP impact, direction, rank).
  - `ENTITY_EVIDENCE`: Cross-account device, card, or IP sharing metrics and velocity bursts.
  - `NETWORK_EVIDENCE`: Syndicate cluster membership, multi-hop connection paths, and detected `SyndicatePatternType` signatures.
  - `TYPOLOGY_EVIDENCE`: Regulatory playbooks, historical cases, and escalation criteria retrieved from RAG.
  - `AUDIT_EVIDENCE`: Historical decision events and previous investigation outcomes.
- **FR-09**: Every evidence item must contain an explicit `source_id`, `source_subsystem`, `severity`, and `confidence`.

### 6.4 Typology Knowledge Grounding (RAG)
- **FR-10**: The agent must ground its modus operandi hypotheses in synthetic fraud playbooks (`knowledge/guidelines/`, `knowledge/historical_cases/`, `knowledge/policies/`).
- **FR-11**: RAG retrieval must pass similarity score thresholds ($\ge 0.55$) and cite document IDs (e.g., `GDL-001`, `CASE-2025-089`, `POL-002`).
- **FR-12**: LLM synthesis prompts must explicitly separate *Observed Empirical Evidence* from *Retrieved Domain Knowledge* and *Hypothesized Modus Operandi*.

### 6.5 Persistence & Database Integration
- **FR-13**: Persist the completed investigation record into PostgreSQL `investigations` table (`InvestigationModel`).
- **FR-14**: Persist individual verified evidence items into `evidence` table (`EvidenceModel`).
- **FR-15**: Persist structured AI findings into `ai_findings` table (`AIFindingModel`).
- **FR-16**: Emit a cryptographically chained `AuditEventModel` with event type `INVESTIGATION_COMPLETED` containing the SHA-256 hash of the investigation findings.

---

## 7. Non-Functional Requirements (NFRs)

| Dimension | Target Specification | Enforcement Mechanism |
| :--- | :--- | :--- |
| **P95 Latency (Local / Degraded)** | $\le 250\text{ ms}$ | In-memory deterministic synthesis engine |
| **P95 Latency (Cloud LLM)** | $\le 4.5\text{ s}$ | Async HTTP client, strict 15s timeout, bounded prompt context ($\le 4\text{k}$ tokens) |
| **Memory Footprint** | $O(\text{subgraph\_nodes}) \le 2\text{ MB}$ per execution | Bounded BFS traversals ($d \le 3, N \le 100$), zero full-graph loading |
| **Security / SQL Injection** | Zero SQL Injection Risk | 100% parameterized SQLAlchemy ORM queries |
| **Prompt Injection Defense** | Zero System Prompt Hijacking | Delimiter isolation (`<<<DATA>>>`), strict regex sanitization, structured output enforcement |
| **Reliability & Availability** | 99.99% investigation success rate | Automatic failover to deterministic synthesis on LLM timeout or validation error |
| **Type Safety & Linting** | 100% Clean (0 errors) | Mypy strict type checking, Ruff linter and formatter |

---

## 8. Success Metrics & Acceptance Gates

```
============================== V2-08 ACCEPTANCE CRITERIA ==============================
1. 100% Passing Tests: All existing 233 backend tests + minimum 25 new V2-08 tests pass.
2. Code Quality: 0 Ruff lint errors, 0 format discrepancies, 0 Mypy type issues across all files.
3. Strict Invariant Verification: Agent output contains NO financial mutations; policy actions stay pure.
4. Golden Regression: tx_0001991 investigation successfully synthesizes DEVICE_REUSE_RING,
   MULTI_INFRASTRUCTURE_COLLUSION, Tree SHAP velocity signals, and GDL-001 playbooks into a CRITICAL dossier.
5. Deterministic Fallback: Agent completes 100% of investigations even when LLM_PROVIDER="deterministic".
6. Audit Chain Integrity: Verification endpoint GET /api/v1/audit/verify returns valid SHA-256 chain.
=======================================================================================
```
