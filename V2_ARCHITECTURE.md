# FraudDNA V2 — Architecture

## Architectural Goal

FraudDNA V2 will evolve into a production-grade, AI-native fraud intelligence and financial crime operations platform.

The architecture must remain modular, explainable, secure, observable, and auditable while allowing ML, graph intelligence, RAG, agentic AI, simulation, and investigation capabilities to evolve independently.

---

## High-Level Architecture

```text
                         FRAUDDNA V2
                              |
        +---------------------+---------------------+
        |                     |                     |
   EXPERIENCE            INTELLIGENCE           PLATFORM
        |                     |                     |
        v                     v                     v
  Web Application       Risk Intelligence      API Layer
  Investigation UI      Entity Intelligence    Auth / RBAC
  Analytics             Network Intelligence   Security
  Case Management       Investigation AI       Observability
                        Simulation              Audit
                        Model Intelligence      Configuration
                              |
                              v
                       Decision Layer
                              |
                       Deterministic
                       Policy Engine
                              |
                    +---------+---------+
                    |         |         |
                  ALLOW     REVIEW     HOLD

1. Experience Layer

The frontend will evolve from a dashboard into an investigator-oriented operating environment.

Primary areas:

Command Center
Transaction Intelligence
Entity Intelligence
Risk Networks
Investigation Workspace
Case Management
Simulation
Model Intelligence
Decision Audit
System Administration

The frontend must consume backend APIs and must never become the source of analytical truth.

2. API / Application Layer

FastAPI remains the primary application API.

Responsibilities:

request validation
authentication and authorization
API versioning
domain orchestration
response schemas
rate limiting
error handling
audit integration

Domain boundaries should be organized around capabilities rather than individual frontend pages.

Core domains:

transactions
entities
risk
networks
investigations
cases
intelligence
simulation
models
decisions
audit
administration
3. Risk Intelligence Layer

The risk engine should become modular.

Transaction Risk

Predict transaction-level fraud probability.

Behavioral Anomaly Detection

Identify behavior that deviates from an entity's historical baseline.

Graph Risk

Use relationship structure and network behavior as fraud signals.

Ensemble Risk

Combine independent risk signals into a final risk assessment.

Every prediction must be traceable to:

model version
feature version
timestamp
input context
prediction
confidence/probability where applicable
4. Entity Intelligence Layer

Maintain behavioral intelligence for:

customers
accounts
cards
devices
IP addresses
merchants
transactions

Entity profiles should expose:

historical activity
behavioral statistics
velocity
risk history
relationships
anomalies
linked investigations
previous decisions

Historical reasoning must remain point-in-time aware.

5. Network Intelligence Layer

The graph subsystem should evolve beyond simple connected-component discovery.

Capabilities may include:

relationship graphs
shared-device detection
shared-IP detection
shared-card detection
multi-hop analysis
suspicious subgraph discovery
community detection
temporal network analysis
coordinated attack signatures
network-level risk scoring

Graph traversal must remain bounded and resource-controlled.

6. Investigation Intelligence Layer

Investigation becomes a first-class domain.

An investigation may contain:

triggering activity
entities involved
network context
risk signals
model explanations
retrieved intelligence
historical cases
hypotheses
evidence
investigator notes
AI findings
policy outcome
audit trail

Investigations should be reproducible.

7. Agentic Intelligence Layer

The AI investigation system must remain bounded, tool-driven, and observable.

Investigation Request
        |
        v
   Agent Planner
        |
        v
  Allowlisted Tools
        |
        +---- Risk Intelligence
        +---- Graph Intelligence
        +---- Entity Intelligence
        +---- Historical Cases
        +---- RAG
        +---- Policy Context
        |
        v
  Evidence Collection
        |
        v
 Structured Findings
        |
        v
 Deterministic Policy Engine

The agent must never directly execute financial actions.

AI outputs must be structured.

AI conclusions must be grounded in available evidence.

The agent must never directly execute financial actions.

AI outputs must be structured.

8. Intelligence / RAG Layer

The knowledge system should support:

fraud policies
merchant policies
investigation procedures
historical cases
escalation guidelines
relevant regulatory/internal guidance

Target pipeline:
Documents
    |
Ingestion
    |
Chunking
    |
Metadata
    |
Embeddings
    |
Vector Index
    |
Hybrid Retrieval
    |
Reranking
    |
Evidence
    |
Investigation Agent

Retrieved evidence must include provenance.

9. Decision Layer

The decision layer remains deterministic.

ML Risk
   +
Graph Risk
   +
Behavioral Signals
   +
Investigation Evidence
   +
Policy
   |
   v
Decision Engine
   |
   +---- ALLOW
   +---- REVIEW
   +---- HOLD

The LLM cannot override policy controls.

Every decision must record:

decision
policy version
risk signals
reasons
timestamp
transaction/investigation reference
audit record

10. Simulation Layer

Simulation should become a genuine counterfactual risk laboratory.

It should support:

threshold experiments
policy experiments
review-capacity experiments
fraud-loss assumptions
false-positive cost
operational cost
expected fraud prevented
expected false-positive cost
net benefit
precision / recall tradeoffs

Simulation results must be calculated from actual model predictions and historical data.

No fabricated analytical values.

11. Model Intelligence / MLOps

The long-term platform should support:

model registry
model versions
training metadata
feature versions
experiment tracking
evaluation reports
model monitoring
prediction monitoring
drift detection
data-quality monitoring
calibration monitoring
threshold optimization
rollback capability

These capabilities should be introduced incrementally based on actual requirements.

12. Data Layer

Initial architecture:

PostgreSQL
    |
    +-- transactions
    +-- entities
    +-- investigations
    +-- cases
    +-- decisions
    +-- audit
    +-- simulations
    +-- model metadata
    +-- knowledge
    |
    +-- pgvector

Specialized databases or storage systems should only be introduced when justified by measurable requirements.

13. Processing Layer

Long-running operations should eventually be separated from synchronous API requests.

Potential asynchronous workloads:

large graph analysis
batch inference
document ingestion
embedding generation
large simulations
model evaluation
drift analysis

Do not introduce distributed infrastructure until workload or reliability requirements justify it.

14. Security Layer

Security is a platform capability.

Required areas:

authentication
RBAC
API authorization
input validation
rate limiting
secrets management
secure headers
CORS
audit logging
prompt-injection defense
RAG-poisoning defense
data isolation
resource limits
dependency security
15. Observability Layer

The platform should eventually expose:

structured logs
request metrics
latency
error rates
model latency
agent latency
tool execution
RAG retrieval behavior
decision counts
investigation duration
system health

Critical workflows should be traceable end-to-end.

16. Deployment Architecture

Target architecture:

                    Internet
                       |
                  CDN / Edge
                       |
                Web Application
                       |
                   API Layer
                       |
        +--------------+--------------+
        |              |              |
   Risk Services   AI Services    Data Services
        |              |              |
        +--------------+--------------+
                       |
                  PostgreSQL
                    + pgvector

Containerization remains the baseline.

The deployment architecture should remain cloud-agnostic where practical.

17. Architectural Principles
Domain boundaries before microservices.
Modular monolith before unnecessary distributed systems.
Measure before scaling.
Real data before visual polish.
Deterministic controls around financial decisions.
AI is bounded by tools and policies.
Every important output must be traceable.
Every model prediction must be reproducible.
Every decision must be auditable.
Security is part of architecture, not a final patch.
Avoid infrastructure complexity without demonstrated need.
Preserve V1 capabilities while V2 evolves.
No hardcoded analytical results.
No fabricated product behavior.
Every major capability must have automated tests.

