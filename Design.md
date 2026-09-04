# FraudDNA — Product & Visual Design System

## 1. Design Direction

FraudDNA should feel like a **premium fintech analytics product combined with a fraud investigation console**.

The visual reference is the clean, interactive analytics language of the supplied Dribbble dashboard reference:
- spacious card-based composition
- sophisticated financial analytics
- interactive charts
- heat maps
- trend visualizations
- restrained color palette
- subtle motion
- strong information hierarchy

Reference:
https://dribbble.com/shots/26573812-Interactive-Analytics-Dashboard-Concept

Do **not** copy the reference literally. Use its design language and adapt it into a unique FraudDNA product.

Avoid a generic dark cybersecurity/SOC dashboard.

## 2. Visual Personality
FraudDNA should feel:
- premium
- intelligent
- precise
- investigative
- calm
- trustworthy
- data-rich
- operational

Avoid:
- excessive gradients
- neon cyberpunk styling
- hacker imagery
- decorative AI animations
- fake live activity
- meaningless glowing effects
- excessive glassmorphism
- generic SaaS dashboard templates

## 3. Theme

### Primary direction
Light-first.

Use:
- warm off-white/light-gray page background
- white or slightly tinted cards
- deep charcoal text
- muted gray secondary text
- soft borders
- subtle shadows
- restrained mint/green accent

The interface should feel closer to a high-end financial analytics product than a cybersecurity terminal.

### Semantic risk colors
- Green → ALLOW / low risk
- Amber → REVIEW / elevated risk
- Red → HOLD / high risk
- Mint/green → FraudDNA primary accent
- Blue/cyan → AI/informational signals

Risk colors must communicate state, not decorate the UI.

## 4. Typography
Primary:
- Inter

Technical/data:
- JetBrains Mono

Use monospaced typography for:
- transaction IDs
- entity IDs
- risk scores
- timestamps
- technical metadata

## 5. Layout

Desktop-first because the primary user is a risk analyst.

Recommended shell:

```text
┌─────────────────────────────────────────────────────────────────┐
│ FraudDNA                                      Search   Profile   │
├───────────────┬─────────────────────────────────────────────────┤
│               │                                                 │
│ Overview      │              Main Content                       │
│ Transactions  │                                                 │
│ FraudDNA      │                                                 │
│ Investigate   │                                                 │
│ Simulation    │                                                 │
│ Evaluation    │                                                 │
│ Audit         │                                                 │
│               │                                                 │
└───────────────┴─────────────────────────────────────────────────┘
```

Use generous whitespace and clear visual grouping.

## 6. Overview Dashboard

The homepage should resemble a sophisticated analytics dashboard.

Top-level cards:
- Fraud Exposure
- Fraud Prevented
- Suspicious Transactions
- Active Clusters
- False-Positive Cost

Secondary analytics:
- risk activity trend
- fraud rate trend
- suspicious cluster distribution
- transaction volume
- risk heatmap
- recent investigations

Only use actual calculated values.

## 7. Hero Analytics Section

The main analytical area should contain an interactive trend visualization.

Example:
**Risk Activity**
- transaction volume
- suspicious volume
- risk score distribution
- time range controls

Use Recharts.

Charts should have:
- minimal grid lines
- strong typography
- clear hover states
- meaningful tooltips
- restrained animation
- no chart junk

## 8. Risk Heatmap

Create a compact heatmap for patterns such as:
- hour vs risk
- geography vs risk
- merchant segment vs risk
- device/IP concentration

Only show dimensions supported by actual data.

The heatmap should immediately answer:
> Where is risk concentrating?

## 9. FraudDNA Graph

This is the signature feature.

Use React Flow.

The graph should feel like a premium data visualization rather than a cybersecurity attack map.

Entities:
- Customer
- Transaction
- Device
- IP
- Card
- Merchant

Visual behavior:
- normal entities → muted
- suspicious entities → emphasized
- selected entity → strong focus
- relationships → subtle lines
- suspicious relationships → stronger visual weight

Interaction:
- click node → inspect entity
- hover → relationship metadata
- zoom/pan
- focus cluster
- open investigation

### Signature moment

```text
20 transactions
        ↓
individually normal
        ↓
shared relationships discovered
        ↓
coordinated fraud cluster
        ↓
₹ exposure revealed
```

Never hard-code this narrative unless the underlying dataset produces it.

## 10. Transaction Detail

Use a clean two-column analytical layout.

### Left
Transaction information:
- amount
- timestamp
- customer
- merchant
- device
- IP
- payment instrument

### Right
Risk intelligence:
- risk score
- risk band
- model explanation
- cluster membership
- connected entities
- investigation status
- policy decision

The risk score should be visually prominent without becoming a giant gimmick.

## 11. XAI Panel

Display:
- model risk score
- top SHAP features
- contribution direction
- contribution magnitude
- concise explanation

Recommended visual:
horizontal contribution bars with clear positive/negative semantics.

Do not create explanations manually if the model's SHAP output is available.

## 12. Investigation Console

The investigation page should feel like an analyst workspace.

Structure:

```text
Case Header
↓
Risk Summary
↓
FraudDNA Cluster
↓
Evidence Timeline
↓
AI Investigation
↓
RAG Evidence
↓
Policy Decision
↓
Audit Trail
```

The user should always understand:
- what was detected
- what relationships were found
- what evidence was gathered
- what the AI concluded
- what policy decided
- why the final action happened

## 13. Investigation Timeline

Timeline events:
1. Detection
2. Graph discovery
3. Tool call
4. Retrieved evidence
5. AI synthesis
6. Policy evaluation
7. Final action
8. Audit event

Use subtle motion when events appear.

Motion should communicate progression, not simulate intelligence.

## 14. RAG Evidence

Show evidence as clean source cards.

Each card:
- document title
- source type
- relevant evidence
- relevance score if useful
- retrieval timestamp

Make provenance obvious.

Never display hallucinated citations or invented policy.

## 15. Deterministic Decision Card

Make the final decision visually clear:

```text
RISK DECISION

HOLD

Reason
High transaction risk + coordinated cluster evidence
+ applicable merchant policy.

Decision source
Deterministic Policy Engine
```

Make it obvious that the LLM did not directly make the financial decision.

## 16. Risk Simulation

Design this as an interactive analytics workspace.

Controls:
- risk threshold
- policy configuration
- cost assumptions where appropriate

Results:
- fraud caught
- false positives
- FP cost
- expected loss
- net benefit
- precision
- recall

Use before/after charts and a clear summary such as:

> Lower threshold catches more fraud but increases customer friction.

The simulation should help a risk manager make a decision.

## 17. Evaluation Page

Display:
- Precision
- Recall
- F1
- PR-AUC
- FPR
- confusion matrix
- false-positive monetary cost
- held-out test-set size

Clearly label:
**Synthetic evaluation data** when applicable.

Use a polished analytics layout rather than a raw notebook-style presentation.

## 18. Audit Page

Show:
- investigation ID
- transaction ID
- model version
- risk score
- graph evidence
- retrieved evidence
- policy version
- final action
- timestamps
- agent/tool events
- failure events

Audit should look authoritative and easy to inspect.

## 19. Motion Design

Use subtle motion:
- card hover
- chart transitions
- graph focus
- timeline progression
- number transitions
- panel expansion

Avoid:
- constant pulsing
- fake scanning
- random particles
- excessive spring animations
- animation that implies an action actually happened when it did not

Motion should improve comprehension.

## 20. Responsive Design
Desktop-first, but support tablet/mobile gracefully.

Prioritize:
1. readability
2. investigation flow
3. graph interaction
4. critical risk information

## 21. Empty / Loading / Failure States

### Loading
Use skeletons that match the final layout.

### Empty
Explain what the analyst can do next.

### Failure
Be explicit.

Example:

> AI investigation unavailable.
> Risk detection and graph analysis completed.
> Case escalated to human review.

Never replace missing data with fake values.

## 22. Product Signature

The visual story should move from:

**Clean analytics → suspicious pattern → relationship discovery → fraud cluster → investigation → evidence → deterministic decision → financial impact**

The user should feel that FraudDNA discovered something hidden in the data.

## 23. Design Principle

**Premium fintech analytics on the surface. Serious fraud intelligence underneath.**
