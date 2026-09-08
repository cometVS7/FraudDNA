# FraudDNA V2 — V1 Baseline

## Purpose

This document defines the submitted FraudDNA V1 application as the functional baseline for V2 development.

V2 development must not compromise the correctness or functionality represented by this baseline.

## V1 Status

- Submitted buildathon version: YES
- Stable branch: main
- V2 development branch: v2/production-platform
- V1 remains the reference implementation until V2 is explicitly approved for replacement.

## V1 Functional Capabilities

- Transaction risk scoring
- LightGBM fraud detection
- SHAP explanations
- FraudDNA relationship graph
- Suspicious cluster detection
- RAG-based intelligence retrieval
- LangGraph investigation agent
- Deterministic ALLOW / REVIEW / HOLD policy engine
- Risk simulation
- Model evaluation
- Decision audit
- Production API
- Production frontend

## V2 Development Rules

1. Do not modify `main` during V2 development.
2. Do not remove V1 functionality merely to simplify V2 implementation.
3. Do not replace real backend data with mock or hardcoded data.
4. Do not invent analytics or performance metrics.
5. Preserve working ML behavior unless a measured improvement is demonstrated.
6. Preserve deterministic financial decision controls.
7. Every major V2 capability must be testable independently.
8. V2 changes must remain isolated to the V2 branch until final approval.
9. V2 must be demonstrably better than V1 before replacement is considered.

## V2 Principle

V1 is the proof that FraudDNA works.

V2 is where FraudDNA becomes a production-grade product.

The objective is not to make V1 prettier.

The objective is to evolve FraudDNA into a serious fraud intelligence platform while preserving correctness, explainability, security, and operational trust.