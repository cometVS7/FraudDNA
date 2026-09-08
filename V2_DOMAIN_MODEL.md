# FraudDNA V2 — Domain Model

## 1. Purpose

FraudDNA V2 is built around a connected financial-risk domain model.

The system must treat fraud intelligence as relationships between:

- Transactions
- Customers
- Accounts
- Cards
- Devices
- IP Addresses
- Merchants
- Risk Networks
- Investigations
- Cases
- Evidence
- Decisions
- Policies
- Models
- Intelligence Sources
- Audit Events

The domain model must support point-in-time analysis, explainability, investigation, deterministic decisions, and complete auditability.

---

# 2. Core Domain Entities

## 2.1 Transaction

Represents a financial transaction evaluated by FraudDNA.

Core fields:

- transaction_id
- timestamp
- amount
- currency
- customer_id
- account_id
- card_id
- device_id
- ip_id
- merchant_id
- payment_method
- transaction_status
- risk_score
- risk_tier
- decision
- investigation_id
- network_id
- created_at

Rules:

- transaction_id is globally unique.
- Transaction data must be immutable after creation except for explicitly auditable state changes.
- Risk predictions must reference the model version that produced them.
- Decisions must reference the policy version that produced them.

---

# 3. Customer

Represents a customer associated with financial activity.

Core fields:

- customer_id
- account_ids
- created_at
- account_age
- status
- risk_score
- risk_tier

Derived intelligence:

- transaction_count
- transaction_volume
- average_transaction_amount
- transaction_velocity
- historical_risk
- behavioral_anomalies
- linked_devices
- linked_ips
- linked_cards
- linked_merchants
- linked_networks
- linked_cases

---

# 4. Account

Represents a financial account.

Core fields:

- account_id
- customer_id
- created_at
- status
- risk_score
- risk_tier

Derived intelligence:

- transaction activity
- velocity
- amount distribution
- historical risk
- linked devices
- linked IPs
- linked cards
- linked merchants
- linked networks
- investigations
- cases

A customer may have one or more accounts.

---

# 5. Card

Represents a payment instrument.

Core fields:

- card_id
- created_at
- status
- risk_score
- risk_tier

Derived intelligence:

- customer count
- transaction count
- velocity
- amount distribution
- geographic activity where available
- linked devices
- linked IPs
- linked merchants
- linked networks

Card relationships are important fraud signals.

A payment instrument shared across unrelated customers may indicate coordinated activity.

---

# 6. Device

Represents a device fingerprint.

Core fields:

- device_id
- first_seen
- last_seen
- risk_score
- risk_tier

Derived intelligence:

- customer count
- account count
- transaction count
- transaction velocity
- linked cards
- linked IPs
- linked merchants
- linked networks

Shared device relationships must be analyzed carefully because legitimate shared-device behavior exists.

---

# 7. IP Address

Represents an originating network address.

Core fields:

- ip_id
- first_seen
- last_seen
- risk_score
- risk_tier

Derived intelligence:

- customer count
- account count
- transaction count
- velocity
- linked devices
- linked cards
- linked merchants
- linked networks

IP relationships are supporting evidence rather than automatic proof of fraud.

---

# 8. Merchant

Represents a merchant receiving transactions.

Core fields:

- merchant_id
- merchant_category
- status
- risk_score
- risk_tier

Derived intelligence:

- transaction volume
- transaction value
- customer count
- fraud rate
- risk distribution
- linked networks

Merchant relationships must not automatically connect every transaction into one giant fraud network.

Graph construction must preserve meaningful investigative relationships.

---

# 9. Risk Network

Represents a connected set of entities and transactions exhibiting meaningful risk or coordination signals.

Core fields:

- network_id
- status
- risk_score
- confidence
- created_at
- first_activity
- last_activity

Derived fields:

- transaction_count
- customer_count
- account_count
- device_count
- card_count
- ip_count
- merchant_count
- transaction_value
- suspicious_transaction_value
- estimated_exposure

Network intelligence:

- shared infrastructure
- shared payment instruments
- behavioral similarity
- temporal coordination
- transaction concentration
- attack signatures
- suspicious subgraphs

A connected graph component is not automatically a suspicious network.

Suspicion requires evidence.

---

# 10. Investigation

Represents an analytical investigation into suspicious activity.

Core fields:

- investigation_id
- status
- priority
- trigger_type
- primary_transaction_id
- primary_network_id
- risk_score
- created_at
- updated_at
- assigned_to

Investigation states:

- OPEN
- ANALYZING
- REVIEW
- ESCALATED
- RESOLVED
- CLOSED

Investigation evidence may include:

- model signals
- SHAP explanations
- behavioral anomalies
- graph relationships
- network evidence
- historical cases
- policy evidence
- retrieved intelligence
- agent findings

---

# 11. Case

Represents the operational record of a fraud investigation.

Core fields:

- case_id
- status
- priority
- owner
- created_at
- updated_at
- closed_at

Case states:

- NEW
- TRIAGED
- INVESTIGATING
- ESCALATED
- RESOLVED
- CLOSED

A case can contain:

- multiple transactions
- multiple entities
- multiple networks
- multiple investigations
- evidence
- investigator notes
- AI findings
- decisions
- timeline events
- audit events

---

# 12. Evidence

Represents a traceable fact supporting an investigation or decision.

Core fields:

- evidence_id
- evidence_type
- source
- source_id
- description
- confidence
- timestamp
- investigation_id
- case_id

Evidence types may include:

- MODEL_SIGNAL
- SHAP_SIGNAL
- BEHAVIORAL_ANOMALY
- GRAPH_RELATIONSHIP
- NETWORK_PATTERN
- HISTORICAL_CASE
- POLICY_RULE
- RAG_DOCUMENT
- AGENT_FINDING
- HUMAN_OBSERVATION

Evidence must be attributable to a source.

The system must never represent an unsupported AI statement as verified evidence.

---

# 13. Risk Assessment

Represents a model-generated assessment of risk.

Core fields:

- assessment_id
- subject_type
- subject_id
- model_id
- model_version
- score
- risk_tier
- generated_at
- feature_version

Risk assessment must preserve:

- input context
- model version
- feature version
- prediction timestamp
- score
- risk tier

Risk scores must not be hardcoded into the frontend.

---

# 14. Model

Represents a deployed risk model.

Core fields:

- model_id
- model_name
- version
- status
- feature_version
- trained_at
- deployed_at

Performance metadata:

- precision
- recall
- f1
- pr_auc
- roc_auc
- fpr

Operational metadata:

- artifact location
- checksum
- training dataset identifier
- evaluation dataset identifier

---

# 15. Risk Signal

Represents a measurable factor contributing to risk.

Core fields:

- signal_id
- signal_type
- feature_name
- value
- contribution
- direction
- generated_at

Examples:

- high transaction velocity
- unusual transaction amount
- new account
- shared device
- shared card
- suspicious network membership
- unusual activity hour

Risk signals must remain distinguishable from final decisions.

---

# 16. Policy

Represents a deterministic decision policy.

Core fields:

- policy_id
- policy_name
- version
- status
- effective_from
- effective_until

A policy evaluates:

- risk score
- risk tier
- network risk
- behavioral signals
- investigation findings
- operational constraints

Possible outcomes:

- ALLOW
- REVIEW
- HOLD

The policy engine is authoritative for financial decisions.

LLM output cannot directly override policy.

---

# 17. Decision

Represents the final deterministic system decision.

Core fields:

- decision_id
- transaction_id
- investigation_id
- policy_id
- policy_version
- decision
- reasons
- generated_at

Decision values:

- ALLOW
- REVIEW
- HOLD

A decision must be reproducible from its recorded inputs and policy version.

---

# 18. Intelligence Source

Represents information available to the investigation system.

Source types:

- POLICY
- HISTORICAL_CASE
- FRAUD_GUIDELINE
- INVESTIGATION_RECORD
- SYSTEM_DOCUMENT

Core fields:

- source_id
- source_type
- title
- version
- content_hash
- created_at
- updated_at

RAG retrieval must preserve source provenance.

---

# 19. AI Investigation Finding

Represents a structured output produced by the investigation agent.

Core fields:

- finding_id
- investigation_id
- finding_type
- statement
- confidence
- supporting_evidence_ids
- generated_at
- agent_version

Finding types may include:

- RISK_ASSESSMENT
- COORDINATION_PATTERN
- BEHAVIORAL_PATTERN
- NETWORK_PATTERN
- POLICY_CONTEXT
- HISTORICAL_CONTEXT
- RECOMMENDATION

AI findings are investigative intelligence.

They are not financial decisions.

---

# 20. Audit Event

Represents an immutable event in the system's audit history.

Core fields:

- audit_event_id
- timestamp
- actor
- actor_type
- event_type
- entity_type
- entity_id
- payload_hash
- previous_hash
- event_hash

Audit events should support hash chaining where appropriate.

Examples:

- transaction_scored
- investigation_created
- evidence_added
- agent_completed
- decision_generated
- policy_updated
- case_updated
- simulation_run
- model_deployed

---

# 21. Relationship Model

Primary relationships:

```text
Customer
   |
   +---- Account
   |
   +---- Card
   |
   +---- Device
   |
   +---- IP
   |
   +---- Transaction
             |
             +---- Merchant
             |
             +---- Card
             |
             +---- Device
             |
             +---- IP
             |
             +---- Risk Assessment
             |
             +---- Investigation
                       |
                       +---- Evidence
                       |
                       +---- AI Findings
                       |
                       +---- Decision
                       |
                       +---- Case

Network relationships:

Transaction
    |
    +---- Customer
    +---- Account
    +---- Card
    +---- Device
    +---- IP
    +---- Merchant
    |
    v
Risk Network
    |
    +---- Related Transactions
    +---- Related Customers
    +---- Shared Infrastructure
    +---- Attack Signatures
22. Investigation Lifecycle
Transaction / Network Trigger
            |
            v
      Risk Assessment
            |
            v
     Evidence Collection
            |
            v
      Graph Analysis
            |
            v
       RAG Retrieval
            |
            v
      AI Investigation
            |
            v
    Structured Findings
            |
            v
    Deterministic Policy
            |
            v
      ALLOW / REVIEW / HOLD
            |
            v
       Case Creation
            |
            v
        Audit Event
23. Point-in-Time Integrity

FraudDNA must preserve temporal correctness.

Any derived intelligence must respect:

information_available_at_time_T

when evaluating an event at time T.

The system must prevent future information from influencing historical predictions.

This applies to:

transaction features
customer statistics
device statistics
IP statistics
card statistics
network intelligence
model evaluation
simulation
24. Identity Rules

IDs must be:

unique
stable
deterministic where required
namespaced by entity type where graph representation requires it

Examples:

txn:tx_0001991
customer:cust_0042
account:acct_0102
device:dev_0198
ip:ip_0081
card:card_0044
merchant:merchant_0021
network:cluster_ded73b2ac8d1
investigation:inv_xxxxxxxxxxxxxxxx
case:case_xxxxxxxxxxxxxxxx

Graph node identifiers must never rely on ambiguous raw IDs alone.

25. Domain Ownership

Each domain has a clear authority.

Domain	Authority
Transaction state	Transaction service
Risk score	Risk intelligence
Explainability	Explainability service
Relationships	Graph intelligence
Retrieved knowledge	RAG layer
AI findings	Investigation agent
Financial decision	Deterministic policy engine
Case state	Case management
Audit history	Audit service
Model performance	Model intelligence
Simulation outputs	Simulation engine

No domain should silently overwrite another domain's authoritative state.

26. AI Boundary

AI may:

investigate
summarize
correlate
retrieve
classify evidence
identify patterns
generate structured findings
recommend investigative actions

AI may not:

directly authorize payments
directly block payments
modify policy
modify model thresholds
fabricate evidence
bypass deterministic controls
delete audit history
execute arbitrary tools
access unrestricted filesystem or database resources
27. Domain Integrity Principle

The most important rule of the V2 domain model is:

FraudDNA must distinguish what happened, what the model predicted, what the graph discovered, what the AI inferred, and what the policy decided.

These are separate concepts.

They must remain separately represented throughout the system.