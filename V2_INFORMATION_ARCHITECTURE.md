# FraudDNA V2 — Information Architecture

## 1. Product Navigation Model

FraudDNA V2 should use a persistent application shell designed around the fraud analyst's workflow.

Primary navigation:

1. Command Center
2. Transactions
3. Entities
4. Risk Networks
5. Investigations
6. Cases
7. Simulation
8. Model Intelligence
9. Decision Audit
10. System

The navigation should communicate that FraudDNA is an operational intelligence platform rather than a conventional analytics dashboard.

---

## 2. Command Center

Route:

`/`

Purpose:

Provide the operational overview of the entire fraud environment.

Primary sections:

- Risk Exposure
- Transaction Activity
- Risk Distribution
- Priority Activity
- Active Risk Networks
- Investigation Workload
- Decision Activity
- Model Health
- System Health

Primary actions:

- Open transaction
- Investigate transaction
- Explore risk network
- Open case
- Run simulation
- Inspect model performance

The Command Center must remain a summary layer.

Detailed investigation belongs in the appropriate domain workspace.

---

## 3. Transactions

Route:

`/transactions`

Purpose:

Provide the operational transaction intelligence ledger.

Primary capabilities:

- transaction search
- filtering
- sorting
- pagination
- risk filtering
- amount filtering
- time filtering
- decision filtering
- cluster filtering
- customer filtering
- merchant filtering
- device filtering
- IP filtering
- payment instrument filtering

Transaction row should expose:

- transaction ID
- timestamp
- amount
- customer
- merchant
- device
- risk score
- risk tier
- cluster
- decision
- investigation state

Primary actions:

- Open transaction
- Investigate
- View customer
- View device
- View IP
- View card
- View merchant
- View risk network

---

## 4. Transaction Detail

Route:

`/transactions/[transaction_id]`

Purpose:

Provide a focused view of one transaction.

Information hierarchy:

### Header

- transaction ID
- amount
- timestamp
- risk score
- risk tier
- decision

### Transaction Context

- customer
- merchant
- payment instrument
- device
- IP
- location where available

### Risk Intelligence

- model signals
- behavioral signals
- SHAP explanation
- anomaly indicators

### Network Context

- connected entities
- related transactions
- suspicious cluster
- network exposure

### Decision

- policy outcome
- reasons
- policy version

### Investigation

- investigation status
- linked case
- investigation entry point

---

## 5. Entities

Route:

`/entities`

Purpose:

Provide entity-centric intelligence.

Entity types:

- customers
- accounts
- cards
- devices
- IP addresses
- merchants
- transactions

The entity interface should support:

- entity search
- entity type filtering
- risk filtering
- relationship discovery
- activity history

---

## 6. Entity Detail

Route:

`/entities/[type]/[id]`

Purpose:

Provide the behavioral and relational profile of an entity.

Primary sections:

### Identity

Relevant entity metadata.

### Behavioral Profile

- transaction volume
- transaction value
- frequency
- velocity
- typical amounts
- typical activity times
- behavioral deviations

### Risk Profile

- current risk
- historical risk
- risk events
- linked decisions

### Relationships

- customers
- devices
- IPs
- cards
- merchants
- transactions
- networks

### Investigations

Linked investigations and cases.

### Activity Timeline

Chronological activity.

The entity page should act as the bridge between transaction intelligence and network intelligence.

---

## 7. Risk Networks

Route:

`/networks`

Purpose:

Provide graph-native fraud intelligence.

Primary capabilities:

- graph exploration
- suspicious cluster discovery
- entity relationship analysis
- multi-hop exploration
- risk filtering
- network exposure analysis
- temporal filtering

Network overview should show:

- active networks
- suspicious networks
- transaction volume
- financial exposure
- affected customers
- affected devices
- affected cards
- affected IPs

---

## 8. Network Detail

Route:

`/networks/[network_id]`

Purpose:

Provide a focused forensic view of a risk network.

Primary sections:

### Network Header

- network ID
- network risk
- confidence
- status
- exposure

### Graph

Interactive relationship graph.

### Network Composition

- transactions
- customers
- devices
- cards
- IPs
- merchants

### Attack Signatures

Detected coordination patterns.

### Financial Exposure

- total transaction value
- suspicious transaction value
- estimated exposure
- transaction count

### Timeline

Chronological network activity.

### Investigations

Linked investigations.

### Cases

Linked cases.

---

## 9. Investigations

Route:

`/investigations`

Purpose:

Provide the investigation queue and operational workload.

Capabilities:

- investigation search
- risk filtering
- status filtering
- priority filtering
- assignment
- sorting
- pagination

Investigation row should expose:

- investigation ID
- triggering activity
- risk
- network
- status
- priority
- assigned investigator
- created time
- latest activity

---

## 10. Investigation Workspace

Route:

`/investigations/[investigation_id]`

Purpose:

Provide the primary fraud investigation workstation.

This is one of the most important V2 screens.

Information hierarchy:

### Case Header

- investigation ID
- transaction/activity
- risk score
- risk tier
- decision
- status
- priority

### Risk Summary

- transaction risk
- behavioral risk
- graph risk
- overall assessment

### Evidence

- SHAP evidence
- behavioral anomalies
- graph evidence
- cluster evidence
- historical cases
- retrieved intelligence

### Entity Graph

Interactive network context.

### Timeline

Chronological investigation events.

### AI Investigation

Structured findings from the investigation agent.

Each AI finding must show supporting evidence.

### Intelligence Sources

Retrieved policies, cases, and knowledge.

### Decision Engine

Display:

- policy
- signals
- reasons
- decision
- policy version

### Audit

Traceable decision history.

---

## 11. Cases

Route:

`/cases`

Purpose:

Provide operational case management.

Case list should support:

- search
- filtering
- sorting
- assignment
- priority
- status

Case states:

- NEW
- TRIAGED
- INVESTIGATING
- ESCALATED
- RESOLVED
- CLOSED

---

## 12. Case Detail

Route:

`/cases/[case_id]`

Purpose:

Provide the long-lived operational record of a fraud investigation.

Sections:

### Case Header

- case ID
- status
- priority
- owner
- created time
- updated time

### Linked Activity

- transactions
- entities
- networks
- investigations

### Evidence

Supporting intelligence.

### Investigator Notes

Human-entered notes.

### AI Findings

Structured AI findings.

### Decisions

Decision history.

### Timeline

All important case events.

### Audit

Complete traceability.

---

## 13. Simulation

Route:

`/simulation`

Purpose:

Provide a counterfactual risk laboratory.

Primary controls:

- fraud threshold
- review threshold
- review capacity
- false-positive cost
- estimated fraud loss
- operational assumptions

Primary outputs:

- precision
- recall
- F1
- FPR
- TP
- FP
- TN
- FN
- fraud prevented
- fraud missed
- false-positive cost
- operational cost
- expected loss
- net benefit

Visualizations should support:

- threshold curves
- precision/recall tradeoffs
- net-benefit curves
- confusion matrices
- scenario comparison

All outputs must be dynamically calculated.

---

## 14. Model Intelligence

Route:

`/models`

Purpose:

Provide the ML operations and model-performance view.

Primary sections:

### Model Overview

- active model
- version
- status
- deployment time
- feature version

### Performance

- precision
- recall
- F1
- PR-AUC
- ROC-AUC
- FPR
- confusion matrix

### Prediction Behavior

- score distribution
- risk distribution
- threshold behavior

### Explainability

- feature importance
- SHAP behavior
- dominant signals

### Data Quality

- missing values
- schema consistency
- feature ranges
- data drift

### Model Monitoring

- drift
- calibration
- performance changes
- prediction distribution changes

---

## 15. Decision Audit

Route:

`/audit`

Purpose:

Provide complete decision traceability.

Audit ledger should support:

- filtering
- searching
- sorting
- transaction lookup
- investigation lookup
- decision filtering
- policy filtering
- time filtering

Each record should expose:

- timestamp
- actor/system
- transaction
- investigation
- model version
- risk signals
- evidence
- policy version
- decision
- rationale
- audit hash

---

## 16. System

Route:

`/system`

Purpose:

Provide platform administration and health.

Sections:

### System Health

- API
- database
- model services
- graph services
- RAG
- agent

### Configuration

- thresholds
- policies
- feature configuration

### Access

- users
- roles
- permissions

### Models

- model versions
- deployment status

### Knowledge

- knowledge sources
- ingestion status
- indexing status

### Audit

Administrative activity.

---

## 17. Global Search

FraudDNA V2 should eventually provide global search.

Search across:

- transactions
- customers
- accounts
- devices
- IPs
- cards
- merchants
- networks
- investigations
- cases

Search results should indicate entity type and risk context.

---

## 18. Global Command Interface

A keyboard-accessible command interface should eventually provide rapid navigation.

Examples:

- Search transaction
- Search customer
- Open investigation
- Open network
- Create case
- Run simulation
- Open model
- Search audit

Suggested shortcut:

`⌘K` / `Ctrl+K`

The command interface must respect authorization.

---

## 19. Cross-Domain Navigation

The user should be able to move naturally through the intelligence graph.

Expected workflow:

```text
Command Center
      |
      v
Priority Transaction
      |
      v
Transaction Detail
      |
      v
Entity
      |
      v
Risk Network
      |
      v
Investigation
      |
      v
Evidence
      |
      v
AI Findings
      |
      v
Decision
      |
      v
Case
      |
      v
Audit

This flow should require minimal context switching.

20. Context Preservation

Navigation between domains should preserve relevant context.

Examples:

Transaction → Investigation should preserve transaction ID.

Entity → Network should preserve entity ID.

Network → Investigation should preserve network ID.

Investigation → Case should preserve investigation ID.

Audit → Investigation should preserve investigation context.

Users should never have to manually reconstruct context.

21. Global UI Structure

The application should use:

Persistent Sidebar

Primary domain navigation.

Global Header
global search
command interface
notifications
user context
system status
Workspace

Primary domain content.

Context Panel

Contextual information where useful.

Detail Drawer

Fast inspection without losing the current workspace.

22. Responsive Strategy

Desktop is the primary operational environment.

Mobile should support:

monitoring
alert review
transaction inspection
basic investigation
decision inspection

Mobile should not attempt to reproduce the full desktop graph workstation.

23. Information Hierarchy

Every screen should follow:

WHAT IS HAPPENING?
        ↓
WHY IS IT HAPPENING?
        ↓
WHAT IS CONNECTED?
        ↓
WHAT EVIDENCE SUPPORTS IT?
        ↓
WHAT SHOULD HAPPEN?
        ↓
WHY WAS THAT DECISION MADE?

The UI should make this progression obvious.

24. V2 Navigation Principle

FraudDNA V2 navigation must mirror the user's investigative mental model:

Activity → Entity → Network → Investigation → Evidence → Decision → Case → Audit

The navigation system is therefore part of the product's intelligence architecture, not merely a visual menu.