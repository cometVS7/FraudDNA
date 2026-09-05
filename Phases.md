# FraudDNA — Implementation Phases

## Phase 0 — Foundation
Create a clean runnable foundation.

Tasks:
- repository structure
- frontend setup
- backend setup
- Python/ML environment
- linting/type checking/testing
- Docker/Docker Compose foundation
- environment configuration
- basic health endpoint
- README/developer setup

Do not implement fraud detection yet.

## Phase 1 — Dataset and Risk Model
- realistic synthetic transaction data
- known ground truth
- feature engineering
- train/validation/held-out test split
- LightGBM
- threshold selection on validation
- held-out evaluation
- precision/recall/F1/PR-AUC/confusion matrix/FPR
- false-positive monetary cost
- persisted model/evaluation artifacts

## Phase 2 — FraudDNA Graph
- NetworkX graph
- entity relationships
- suspicious cluster detection
- cluster API
- graph-ready frontend data

## Phase 3 — Risk Investigation API [COMPLETED]
- transaction risk endpoint (`POST /api/v1/investigations`)
- deterministic investigation retrieval (`GET /api/v1/investigations/{investigation_id}`)
- LightGBM native Tree SHAP feature attribution (XAI)
- FraudDNA graph relationship extraction (direct entities & 2-hop connected transactions)
- fraud cluster context lookup & integration
- deterministic, verifiable evidence synthesis across risk model, SHAP, graph, and clusters
- graceful degradation for missing components / isolated transactions
- comprehensive automated test suite (35/35 passing)

## Phase 4 — RAG [COMPLETED]
- curated synthetic knowledge base (policies, guidelines, and historical cases)
- deterministic document ingestion and section-aware chunking pipeline
- pluggable embedding provider abstraction (deterministic local provider + external API adapter)
- PostgreSQL + pgvector storage models with offline in-memory fallback
- semantic retrieval service with top-k cosine similarity, metadata filtering, and deterministic tie-breaking
- REST API endpoints (`POST /api/v1/rag/ingest`, `POST /api/v1/rag/search`, `GET /api/v1/rag/documents`, `GET /api/v1/rag/status`)
- failure handling & graceful degradation without hallucinated evidence
- comprehensive automated test suite (49/49 passing across entire backend)

## Phase 5 — AI Investigation Agent & Policy Engine [COMPLETED]
- bounded LangGraph investigation workflow with structured state machine
- strict allowlist of 7 read-only investigation tools (zero SQL/code execution/mutation)
- max-step budget cap and step-level execution time observability
- structured Pydantic findings output (`AgentInvestigationOutput`)
- grounding across ML risk model, XAI Tree SHAP, FraudDNA graph, clusters, and RAG knowledge
- deterministic safety fallbacks on missing dependencies or LLM unavailability
- deterministic policy engine producing `ALLOW`, `REVIEW`, `HOLD` actions
- auditable reason codes and reproducible decision hashes
- REST API endpoints (`POST /api/v1/agent/investigate`, `POST /api/v1/decisions/evaluate`, `GET /api/v1/decisions/{transaction_id}`)
- comprehensive automated unit and integration tests

## Phase 6 — Risk Simulation & Financial Impact [COMPLETED]
- configurable risk and review thresholds (`fraud_threshold`, `review_threshold`)
- realistic financial parameters (`cost_per_false_positive`, `avg_fraud_loss`, `review_capacity`)
- empirical replay dataset with deterministic evaluations
- comprehensive classification metrics: TP, FP, TN, FN, precision, recall, F1, FPR, detection rate
- exact financial modeling: `fraud_prevented_amount`, `fraud_missed_amount`, `false_positive_cost`, `expected_loss`, `net_benefit`
- multi-threshold comparison engine with deterministic `comparison_id`
- operational review capacity overflow detection
- REST API endpoints (`POST /api/v1/simulations/run`, `POST /api/v1/simulations/compare`, `GET /api/v1/dashboard/summary`)
- automated unit & integration test coverage (105/105 backend tests passing)

## Phase 8 — Complete Fraud Intelligence Dashboard [COMPLETED]
Fully integrated Next.js application backed by actual live backend endpoints:
- **Overview (`/`)**: High-level KPIs, decision distributions (ALLOW / REVIEW / HOLD), recent transactions, quick actions
- **Transactions (`/transactions`)**: Searchable, filterable transaction ledger with real amounts, risk scores, and level badges
- **FraudDNA Graph (`/frauddna`)**: Interactive React Flow graph visualization of entity rings, shared devices/cards/IPs, and syndicate clusters
- **Investigation (`/investigate`)**: End-to-end multi-layer pipeline inspection: ML risk score, Tree SHAP top factors, graph ring context, RAG policy evidence, AI agent audit trail, and deterministic decision card
- **Simulation (`/simulation`)**: Interactive threshold sliders, dynamic financial impact projections, precision/recall curves, and threshold comparison grid
- **Evaluation (`/evaluation`)**: Held-out test performance (AUC-ROC, AP, F1), confusion matrix, scenario catch rates, and transparent synthetic data disclosures
- **Audit Trail (`/audit`)**: Verifiable investigation timeline, evidence verification, and deterministic decision hash inspection

## Phase 7 — Final Hardening, End-to-End Validation & Submission Readiness [COMPLETED]
- **Full Chain E2E Validation**: Transaction → LightGBM ML Risk → Tree SHAP → FraudDNA Graph → Cluster Context → RAG Grounding → Bounded LangGraph Agent → Deterministic Policy Engine → Immutable Audit Trail → Dashboard APIs → Simulation Engine
- **7 E2E Case Scenarios**:
  - Case A: Known legitimate transaction (`tx_0000000`) travels cleanly to `ALLOW`
  - Case B: Individual anomaly (`tx_0000006`) elevated to `REVIEW`/`HOLD`
  - Case C: Coordinated device syndicate (`tx_0001991`) with shared entity clustering, grounded RAG evidence, and deterministic `HOLD`
  - Case D: AI agent offline / missing API credentials fallback to deterministic reasoning
  - Case E: RAG database unreachable fallback to in-memory store without hallucinating citations
  - Case F: Malformed / nonexistent transaction IDs rejected cleanly (404 / 422)
  - Case G: Deterministic policy idempotency & reproducibility
- **Failure Recovery & Degradation Safety**:
  - LLM unavailable → structured offline deterministic fallback
  - RAG unavailable → in-memory cosine fallback with degraded status logging
  - Agent step timeout → bounded step limit ceiling strictly enforced
  - Malformed inputs → Pydantic v2 strict request validation
- **Deployment & Docker Hardening**:
  - Root `Dockerfile` updated to copy ML models, feature pipelines, and curated knowledge base
  - `docker-compose.yml` updated with correct build context
  - GitHub Actions CI updated with ESLint, TypeScript, and full backend test gates
- **Final Quality Gate**:
  - 117/117 backend tests passing (pytest)
  - Ruff linter & format: 0 errors
  - Mypy static typing: 0 errors across 54 source files
  - ESLint: 0 errors
  - TypeScript: 0 type errors
  - Next.js production build: 9/9 static routes compiled cleanly
