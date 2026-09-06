# FraudDNA V2 — Implementation Plan

## 1. Implementation Philosophy

FraudDNA V2 will be built incrementally on top of the stable V1 foundation.

V1 remains untouched while V2 is developed on:

`v2/production-platform`

Implementation order must follow dependency order rather than visual priority.

The sequence is:

```text
Foundation
    ↓
Data & Domain Layer
    ↓
Backend Architecture
    ↓
Intelligence Services
    ↓
Investigation & Case Management
    ↓
Frontend Application Shell
    ↓
Advanced Intelligence
    ↓
Security & Reliability
    ↓
Testing
    ↓
Performance
    ↓
Deployment
    ↓
Production Validation
2. Phase V2-01 — Repository & Engineering Foundation

Objectives:

establish V2 development structure
preserve V1
standardize development conventions
establish configuration boundaries
establish environment handling
establish service boundaries
establish testing strategy

Tasks:

inspect current V1 architecture
identify reusable components
identify technical debt
define V2 application modules
define backend service boundaries
define frontend route structure
define shared domain contracts
define configuration model
define environment variables
define logging conventions
define error handling conventions

Deliverables:

V2 module structure
configuration architecture
environment template
engineering conventions
initial V2 tests

Exit criteria:

V1 remains functional
V2 branch remains isolated
application starts successfully
tests pass
no secrets committed
3. Phase V2-02 — Domain & Data Layer

Objectives:

Build the persistent domain model described in V2_DOMAIN_MODEL.md.

Core entities:

Transaction
Customer
Account
Card
Device
IP
Merchant
Risk Network
Risk Assessment
Risk Signal
Investigation
Evidence
AI Finding
Case
Decision
Policy
Model
Intelligence Source
Audit Event

Tasks:

database schema
SQLAlchemy models
Alembic migrations
indexes
constraints
relationships
timestamps
point-in-time fields
entity identifiers
audit fields

PostgreSQL remains the primary relational store.

pgvector remains available for intelligence retrieval.

Exit criteria:

migrations reproducible
schema constraints tested
entity relationships validated
no destructive migration of V1 data without explicit reason
point-in-time fields preserved
4. Phase V2-03 — Data Access & Application Services

Objectives:

Introduce a clean application/service layer.

Services:

TransactionService
CustomerService
AccountService
CardService
DeviceService
IPService
MerchantService
NetworkService
RiskService
InvestigationService
CaseService
EvidenceService
DecisionService
AuditService
ModelService
IntelligenceService

Rules:

routers remain thin
business logic belongs in services
database access belongs in repositories/data-access components where appropriate
domain rules must be testable independently
no frontend-specific business logic in backend services

Exit criteria:

service boundaries documented
unit tests exist
API handlers remain small
domain logic independently testable
5. Phase V2-04 — Transaction Intelligence

Objectives:

Expand V1 transaction intelligence into a production-grade transaction domain.

Capabilities:

transaction search
pagination
filtering
sorting
risk filtering
decision filtering
customer filtering
merchant filtering
device filtering
IP filtering
card filtering
time filtering
amount filtering

Transaction detail:

transaction context
risk assessment
risk signals
SHAP
behavioral context
network context
related entities
investigation
decision
audit

Performance requirements:

indexed queries
bounded result sets
no unbounded database scans
predictable pagination

Exit criteria:

large transaction datasets remain responsive
filters are deterministic
pagination is stable
API contracts tested
6. Phase V2-05 — Entity Intelligence

Objectives:

Create entity-centric intelligence.

Entity types:

Customer
Account
Card
Device
IP
Merchant

Capabilities:

entity search
entity profile
behavioral statistics
risk history
transaction history
velocity analysis
relationship discovery
anomaly history
investigation history
case history

Exit criteria:

entity pages are backed by real data
statistics are dynamically calculated
point-in-time correctness preserved
relationships traceable to source records
7. Phase V2-06 — Advanced Risk Intelligence

Objectives:

Evolve the V1 risk system into a layered risk intelligence engine.

Risk layers:

Transaction Risk
       +
Behavioral Risk
       +
Graph Risk
       +
Network Risk
       ↓
Risk Intelligence

Capabilities:

model prediction
behavioral anomaly detection
network risk
graph-derived signals
risk aggregation
confidence
signal attribution
historical risk

Every risk assessment must preserve:

model version
feature version
timestamp
input context
score
risk tier

Exit criteria:

risk calculations reproducible
no hardcoded analytical results
model lineage visible
explanations traceable
8. Phase V2-07 — Risk Network Intelligence

Objectives:

Expand FraudDNA graph intelligence substantially.

Capabilities:

multi-hop graph traversal
suspicious subgraph detection
community detection
temporal coordination
shared infrastructure analysis
attack signatures
network scoring
network exposure
network timeline

Graph rules:

traversal depth bounded
result size bounded
merchant relationships must not collapse unrelated activity
suspiciousness requires evidence
graph computations must be measurable

Exit criteria:

large graphs remain responsive
suspicious networks are explainable
network evidence is traceable
graph results are deterministic where expected
9. Phase V2-08 — Investigation Intelligence

Objectives:

Build the complete investigation lifecycle.

Flow:

Trigger
  ↓
Risk Assessment
  ↓
Evidence Collection
  ↓
Graph Analysis
  ↓
Historical Intelligence
  ↓
AI Investigation
  ↓
Structured Findings
  ↓
Policy Evaluation
  ↓
Decision
  ↓
Case
  ↓
Audit

Capabilities:

investigation creation
investigation queue
priority
status
assignment
evidence collection
timeline
investigation history
linked entities
linked networks
linked transactions

Exit criteria:

investigation can be reproduced
evidence is traceable
state transitions are validated
failed dependencies do not corrupt state
10. Phase V2-09 — AI Investigation Platform

Objectives:

Upgrade the existing bounded LangGraph agent.

Architecture:

Planner
   ↓
Allowlisted Tools
   ↓
Evidence
   ↓
RAG
   ↓
Structured Findings
   ↓
Deterministic Policy

Capabilities:

multi-step investigation
tool selection
evidence correlation
historical case retrieval
policy retrieval
graph analysis
structured findings
confidence
evidence references

Security requirements:

allowlisted tools
bounded steps
bounded output
schema validation
prompt injection resistance
no unrestricted filesystem
no arbitrary SQL
no direct financial actions
no policy modification

Failure modes:

LLM unavailable
RAG unavailable
tool unavailable
timeout
malformed output
invalid evidence

All failures must degrade safely.

11. Phase V2-10 — RAG & Intelligence Layer

Objectives:

Build production-grade grounded intelligence retrieval.

Pipeline:

Source
  ↓
Ingestion
  ↓
Validation
  ↓
Chunking
  ↓
Metadata
  ↓
Embedding
  ↓
Vector Store
  ↓
Hybrid Retrieval
  ↓
Reranking
  ↓
Evidence

Capabilities:

policy retrieval
historical case retrieval
fraud guideline retrieval
investigation intelligence
source provenance
document versioning
content hashing

Requirements:

retrieval must return provenance
poisoned content must not bypass validation
ingestion paths must be constrained
retrieval failures must degrade safely
12. Phase V2-11 — Case Management

Objectives:

Introduce persistent operational case management.

Capabilities:

case creation
assignment
priority
status
linked investigations
linked transactions
linked entities
linked networks
evidence
notes
AI findings
decisions
timeline
audit

Case lifecycle:

NEW
 ↓
TRIAGED
 ↓
INVESTIGATING
 ↓
ESCALATED
 ↓
RESOLVED
 ↓
CLOSED

Human investigators remain authoritative over case workflow.

13. Phase V2-12 — Deterministic Decision Intelligence

Objectives:

Expand the existing policy engine.

Decision outcomes:

ALLOW
REVIEW
HOLD

Policy evaluation must consider:

risk
behavioral signals
network signals
investigation findings
operational constraints

Requirements:

policy versioning
effective dates
deterministic evaluation
decision reasons
reproducibility
auditability

The LLM must never directly produce the final financial decision.

14. Phase V2-13 — Simulation Lab

Objectives:

Build a sophisticated counterfactual policy environment.

Capabilities:

threshold simulation
review capacity simulation
cost assumptions
fraud-loss assumptions
policy comparison
scenario comparison
precision/recall tradeoffs
net benefit
expected loss
operational cost

Advanced capabilities may include:

threshold optimization
segment analysis
network-aware simulation
policy sensitivity
cost curves

All simulation results must be generated from actual underlying data.

15. Phase V2-14 — Model Intelligence

Objectives:

Turn model evaluation into a real model-operations surface.

Capabilities:

model registry
model version
feature version
performance metrics
score distribution
calibration
drift
feature drift
data quality
explainability
evaluation history

Metrics:

precision
recall
F1
PR-AUC
ROC-AUC
FPR
confusion matrix

No metric may be manually hardcoded into the frontend.

16. Phase V2-15 — Audit & Governance

Objectives:

Create complete decision traceability.

Audit events must cover:

model prediction
investigation creation
evidence collection
AI investigation
policy evaluation
decision generation
case updates
policy changes
model deployment
simulation execution
administrative changes

Audit records should support:

timestamp
actor
source
entity
payload hash
previous hash
event hash

Audit history must be append-only from the application perspective.

17. Phase V2-16 — Frontend Application Shell

Objectives:

Build the V2 enterprise application shell after backend contracts stabilize.

Structure:

Application Shell
├── Sidebar
├── Global Header
├── Global Search
├── Command Interface
├── Workspace
├── Context Panel
└── Detail Drawer

Primary routes:

/
 /transactions
 /transactions/[id]
 /entities
 /entities/[type]/[id]
 /networks
 /networks/[id]
 /investigations
 /investigations/[id]
 /cases
 /cases/[id]
 /simulation
 /models
 /audit
 /system

Requirements:

responsive
keyboard accessible
fast navigation
loading states
empty states
error states
permission-aware UI
no fake data
18. Phase V2-17 — Design System Implementation

Objectives:

Implement the finalized visual system consistently.

Principles:

premium fintech
forensic analytics
editorial typography
dense information hierarchy
restrained color
meaningful motion
high signal-to-noise ratio

Components:

cards
tables
filters
command palette
graph canvas
timelines
evidence blocks
risk indicators
decision panels
audit ledger
charts
drawers
modals
alerts

Every component must support real application states.

19. Phase V2-18 — Security Hardening

Security must be built into every layer.

Requirements:

authentication
authorization
RBAC
input validation
request size limits
rate limiting
query bounds
graph traversal bounds
agent step limits
RAG ingestion restrictions
prompt injection defenses
XSS protection
CSRF strategy where applicable
security headers
secret management
dependency scanning
audit logging

Threat model:

unauthorized access
BOLA/IDOR
injection
prompt injection
RAG poisoning
resource exhaustion
graph abuse
model abuse
data leakage
privilege escalation
20. Phase V2-19 — Observability

Implement structured observability.

Metrics:

request latency
error rate
throughput
model latency
graph latency
RAG latency
agent latency
database latency
cache behavior
memory usage
CPU usage

Logs:

structured
contextual
correlation ID
request ID
investigation ID
case ID where applicable

Never log secrets or sensitive payment information unnecessarily.

21. Phase V2-20 — Reliability

Requirements:

graceful degradation
timeouts
bounded retries
idempotency
safe fallbacks
dependency isolation
startup validation
health checks
readiness checks
failure recovery

Critical principle:

Failure of AI
    ≠
Failure of fraud detection
Failure of RAG
    ≠
Unsafe financial decision
Failure of frontend
    ≠
Corruption of backend state
22. Phase V2-21 — Performance Engineering

Measure before optimizing.

Targets should be established from real workloads.

Focus areas:

database indexes
pagination
graph traversal
model inference
SHAP
RAG retrieval
agent execution
serialization
frontend rendering
bundle size

Requirements:

no unbounded operations
no accidental O(N²) request paths
bounded graph queries
bounded agent execution
bounded cache growth
predictable memory usage
23. Phase V2-22 — Automated Testing

Testing layers:

Unit

Domain logic and services.

Integration

Database, graph, model, RAG, and service boundaries.

API

Request validation and response contracts.

Security

Injection and abuse cases.

AI

Agent tool restrictions, structured outputs, failure recovery.

E2E

Complete investigative workflow.

Performance

Latency and resource tests.

Regression

V1 behavior that must remain stable.

Required principle:

Every important production bug becomes a regression test.

24. Phase V2-23 — Deployment Architecture

Initial production architecture:

Browser
   |
   v
Frontend
   |
   v
API
   |
   +---- PostgreSQL
   |
   +---- pgvector
   |
   +---- ML
   |
   +---- Graph
   |
   +---- RAG
   |
   +---- Agent

Avoid premature microservices.

The initial architecture should remain a modular monolith unless measured requirements justify service extraction.

25. Phase V2-24 — Production Validation

Before merging V2 into main, perform:

Functional validation
all routes
all APIs
all workflows
all decisions
Data validation
real backend data
no fabricated analytics
no hardcoded metrics
correct relationships
Security validation
authentication
authorization
injection
abuse
resource exhaustion
prompt injection
RAG poisoning
Performance validation
latency
throughput
memory
graph scaling
database behavior
AI validation
grounded responses
evidence attribution
structured outputs
safe fallback
deterministic decision authority
Browser validation
desktop
mobile
console
network
accessibility
Deployment validation
production startup
health checks
environment configuration
database connectivity
model loading
RAG
agent
26. Merge Gate

V2 may not merge into main until:

all planned capabilities are implemented
all critical tests pass
security review passes
performance review passes
production deployment passes
browser QA passes
data integrity is verified
AI safety boundaries are verified
auditability is verified
documentation is complete
no known P0/P1 defects remain
27. Implementation Rule

Do not optimize for the number of features.

Optimize for:

Depth
+
Correctness
+
Traceability
+
Reliability
+
Security
+
Performance
+
User Experience

A smaller subsystem implemented to production quality is preferable to a large collection of shallow features.

28. Final V2 Engineering Principle

FraudDNA V2 should feel like a real financial-risk platform because its architecture behaves like one.

Real Data
   +
Real Models
   +
Real Relationships
   +
Real Evidence
   +
Bounded AI
   +
Deterministic Decisions
   +
Persistent Cases
   +
Complete Auditability
   +
Measured Performance
   =
Production-Grade Fraud Intelligence Platform