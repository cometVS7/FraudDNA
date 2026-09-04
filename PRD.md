# FraudDNA — Product Requirements Document

## 1. Product
**FraudDNA** is an AI-powered fraud defense and risk-intelligence platform that detects coordinated fraud and abuse that can look normal at the individual transaction level.

### Core question
> Are these seemingly normal payments actually connected to the same fraud or abuse operation?

FraudDNA combines:
- transaction-level ML risk scoring
- relationship-graph analysis
- explainable AI
- grounded RAG
- a bounded AI investigation agent
- deterministic risk policies
- auditability
- risk simulation

## 2. Problem
A transaction can look legitimate in isolation while being part of a larger coordinated attack. FraudDNA connects customers, transactions, devices, IPs, payment instruments, and merchants to expose these hidden relationships.

## 3. Users
### Primary
Merchant Risk Analyst

### Secondary
- Risk Manager
- ML/Engineering team

## 4. Core Journey
Transaction Data → Risk Detection → Relationship Analysis → Fraud Cluster → AI Investigation → Evidence + XAI → Deterministic Policy Decision → Audit → Risk Simulation

## 5. Core Features

### 5.1 Transaction Risk Detection
- Realistic synthetic payment dataset with ground truth.
- Train/validation/held-out test split.
- Leakage prevention.
- LightGBM risk model.
- Precision, recall, F1, PR-AUC, confusion matrix, FPR.
- False-positive monetary cost.
- Honest metrics only.

### 5.2 FraudDNA Relationship Graph
Model:
- Customer
- Transaction
- Device
- IP address
- Card/payment instrument
- Merchant

Use NetworkX for the MVP.

### 5.3 Coordinated Abuse Detection
Find suspicious connected clusters using relationship and risk signals.

Example demo narrative:
> 20 transactions. Individually: NORMAL. Together: one coordinated attack.

Only display this narrative when the generated ground truth/data actually supports it.

### 5.4 Explainable AI
Use SHAP on the actual risk model.

Display:
- risk score
- top contributing features
- positive/negative contribution
- human-readable explanation

### 5.5 AI Investigation Agent
Use LangGraph + an LLM for bounded evidence gathering and synthesis.

Allowlisted read-only tools:
- get_transaction_history()
- get_customer_profile()
- get_related_entities()
- get_cluster_analysis()
- get_risk_explanation()
- search_historical_cases()
- retrieve_policy()

Controls:
- maximum steps
- timeouts
- structured output validation
- safe termination
- human-review fallback

### 5.6 RAG
Use PostgreSQL + pgvector and curated:
- merchant risk policies
- fraud policies
- historical cases
- escalation rules

Never fabricate retrieved evidence.

### 5.7 Deterministic Policy Engine
Actions:
- ALLOW
- REVIEW
- HOLD

The LLM must not directly control money, payment state, refunds, or policy enforcement.

> AI investigates uncertainty. Deterministic policies control financial decisions.

### 5.8 Risk Simulation
Allow configurable thresholds/policies and replay historical/synthetic transactions.

Show:
- fraud prevented
- false positives
- false-positive cost
- expected loss
- net benefit
- precision/recall trade-off

### 5.9 Audit
Record:
- risk score
- graph findings
- investigation
- evidence
- agent/tool events
- policy decision
- simulation configuration
- failure events

### 5.10 Failure Recovery
- LLM unavailable → continue detection/XAI and escalate.
- RAG unavailable → do not invent evidence; escalate.
- Agent timeout → terminate and escalate.
- External call failure → bounded retry.
- Duplicate request → idempotent behavior.

## 6. Evaluation
Use realistic synthetic data with known labels.

Required:
- Precision
- Recall
- F1
- PR-AUC
- Confusion matrix
- FPR
- False-positive monetary cost
- Held-out test-set size

Threshold selection uses validation data only. Final metrics use held-out data.

## 7. Non-Goals
Do not build:
- real money movement
- real payment processing
- offensive fraud tooling
- autonomous refunds
- LLM-controlled payment blocking
- Kafka
- Kubernetes
- unnecessary microservices
- Neo4j
- GNN/GraphSAGE unless later justified
- custom LLM training
- fine-tuning

## 8. Success Criteria
A strong MVP demonstrates:
1. Transaction-level fraud detection.
2. Honest held-out evaluation.
3. False-positive cost.
4. Hidden relationship discovery.
5. Actual XAI.
6. Working investigation.
7. Grounded evidence.
8. Deterministic action.
9. Risk simulation.
10. Auditability and failure recovery.

## 9. Engineering Principle
**ML predicts. Graph discovers. XAI explains. RAG grounds. The AI agent investigates. Deterministic policies control financial actions.**
