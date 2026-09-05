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

## Phase 4 — RAG
- curated policies/cases
- document ingestion
- embeddings
- pgvector retrieval
- source metadata

## Phase 5 — AI Investigation Agent
- bounded LangGraph workflow
- allowlisted tools
- max steps
- timeouts
- structured output
- evidence synthesis
- safe fallback

## Phase 6 — Deterministic Policy Engine
- ALLOW/REVIEW/HOLD
- model/graph/evidence signals
- deterministic logic
- policy reasoning
- audit record

## Phase 7 — Risk Simulation
- configurable thresholds
- replay dataset
- fraud caught
- false positives
- FP cost
- expected loss
- net benefit
- precision/recall trade-off

## Phase 8 — Dashboard
Build:
- Overview
- Transactions
- FraudDNA
- Investigations
- Simulation
- Evaluation
- Audit

Key views:
- analytics overview
- transaction detail
- interactive FraudDNA graph
- investigation timeline
- XAI
- RAG evidence
- deterministic decision
- simulation
- evaluation

## Phase 9 — Failure Recovery
Demonstrate:
- LLM unavailable
- RAG unavailable
- agent timeout
- duplicate request
- partial evidence

## Phase 10 — Testing and Hardening
- backend tests
- ML evaluation checks
- graph tests
- policy tests
- simulation tests
- API tests
- frontend checks
- lint/type checks
- dependency/security checks

## Phase 11 — Deployment
- production environment variables
- Docker build
- backend deployment
- database deployment
- frontend deployment
- GitHub Actions

## Phase 12 — Final Demo
Demo sequence:
1. Start with normal-looking transactions.
2. Show transaction-level risk.
3. Reveal hidden relationships.
4. Show suspicious cluster.
5. Show XAI.
6. Run AI investigation.
7. Show grounded evidence.
8. Show deterministic decision.
9. Show audit trail.
10. Change threshold in simulation and show business impact.

## Scope Rule
If time is limited, the minimum vertical slice is:

**ML detector + held-out evaluation + false-positive cost + FraudDNA graph + XAI + working investigation + policy decision + risk simulation.**
