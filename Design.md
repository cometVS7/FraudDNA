# FraudDNA — Design System
> Midnight fraud intelligence — a premium fintech investigation console.

## 1. Design Direction

**Theme:** dark, editorial, forensic fintech.

FraudDNA should preserve the reference's defining visual language: near-black canvas, white typography, warm copper punctuation, serif/sans contrast, hairline borders, pill controls, compact data density, subtle elevation, restrained gilded analytics, and motion that communicates state.

Translate the reference from a fintech spending product into a **fraud-risk intelligence terminal**.

Core principle:

> **Premium fintech analytics on the surface. Serious fraud intelligence underneath.**

The UI must communicate this architecture visually:

**ML predicts → FraudDNA graph discovers → SHAP explains → RAG grounds → AI agent investigates → deterministic policy decides → audit records.**

Never imply that an LLM directly controls payments.

---

## 2. Brand

**Product:** FraudDNA

**Tagline:** Detect the fraud hiding between the transactions.

**Tone:** precise, quiet, forensic, financial, technical, trustworthy.

Avoid generic cybersecurity styling. No neon cyberpunk, hacker imagery, glowing grids, giant shields, or Matrix effects.

---

## 3. Color Tokens

### Core

| Name | Value | Token | Role |
|---|---|---|---|
| Obsidian | `#08080A` | `--color-obsidian` | Page canvas |
| Onyx | `#040406` | `--color-onyx` | Cards |
| Carbon | `#121317` | `--color-carbon` | Panels / inputs |
| Graphite | `#1C1D22` | `--color-graphite` | Primary borders |
| Slate | `#2E3038` | `--color-slate` | Secondary borders |
| Smoke | `#464853` | `--color-smoke` | Muted structure |
| Ash | `#5E616E` | `--color-ash` | Tertiary text |
| Steel | `#777A88` | `--color-steel` | Icons / controls |
| Fog | `#9194A1` | `--color-fog` | Nav / helper text |
| Mist | `#ACAEB9` | `--color-mist` | Secondary copy |
| Silver | `#C7C9D1` | `--color-silver` | Medium emphasis |
| Bone | `#E2E3E9` | `--color-bone` | Body/data text |
| Paper White | `#FFFFFF` | `--color-paper-white` | Headings / primary CTA |
| Copper | `#CC9166` | `--color-copper` | Brand accent |
| Gilded | `#AE9357` | `--color-gilded` | Analytics |

### Semantic risk colors

| State | Value | Usage |
|---|---|---|
| Low / Allow | `#8FAF9B` | Safe / ALLOW |
| Review | `#C7A66B` | REVIEW |
| High | `#C47A63` | High risk |
| Critical / Hold | `#D05B5B` | HOLD |
| Info | `#A6A9B3` | Neutral |

Semantic colors are operational only. Copper remains the brand color.

### Gilded chart gradient

```css
--gradient-gilded:
  linear-gradient(
    103deg,
    rgb(174,147,87),
    rgb(255,240,204) 40%,
    rgb(174,147,87) 70%,
    rgba(189,157,79,0)
  );
```

Use for important risk/exposure curves, selected relationships, and analytical deltas. Never use it as a general page gradient.

---

## 4. Typography

### Display

Use Ivy Presto where available.

Fallback:

`Playfair Display → DM Serif Display → Libre Caslon Display → Georgia`

```css
--font-display: "Ivy Presto", "Playfair Display", "DM Serif Display", Georgia, serif;
```

Use only for:
- page titles
- major section titles
- hero/product statement
- major metric numbers

Weights: 400/500.

### UI

**Inter**

Use for:
- navigation
- buttons
- forms
- tables
- labels
- charts
- tooltips
- agent findings
- evidence
- metadata

### Machine evidence

**JetBrains Mono**

Use for:
- transaction IDs
- cluster IDs
- investigation IDs
- hashes
- API paths
- timestamps
- model scores

The typographic hierarchy is intentional:

**Serif = intelligence**
**Inter = operations**
**Mono = machine evidence**

---

## 5. Type Scale

| Role | Size | Line Height |
|---|---:|---:|
| Eyebrow | 11–13px | 1 |
| Data XS | 12px | 1.3 |
| Body XS | 13px | 1.45 |
| Body | 14–16px | 1.5 |
| Body Large | 18px | 1.4 |
| Subheading | 24px | 1.05 |
| Heading SM | 36–44px | 1.1 |
| Heading | 48–56px | 1.08 |
| Heading LG | 64px | 1.05 |
| Display | 80–88px | 1 |

Do not use large serif text inside dense operational tables.

---

## 6. Shape, Spacing, Elevation

```css
--radius-card: 10px;
--radius-full: 9999px;
--border-primary: #1C1D22;
--border-secondary: #2E3038;
--sidebar-width: 240px;
--page-max-width: 1440px;
```

Cards: 10px radius.

Buttons, inputs, tags, badges, icon wells: 9999px.

Use hairline borders and surface contrast. Avoid drop shadows and excessive glassmorphism.

Default card:

```text
background: #040406
border: 1px solid #1C1D22
border-radius: 10px
box-shadow: none
```

---

## 7. Application Shell

FraudDNA is an operational product, so use a persistent application shell.

### Desktop

- fixed left sidebar, approximately 240px
- Onyx sidebar
- Obsidian content canvas
- hairline divider
- independent content scrolling
- compact top utility bar

### Sidebar

```text
FraudDNA
FRAUD INTELLIGENCE

OVERVIEW
Transactions
FraudDNA Network
Investigate
Simulation
Evaluation

SYSTEM
Audit
```

Active navigation:
- white text
- tiny copper indicator
- subtle transition

Bottom:

```text
SYSTEM STATUS
● Operational
```

Only show status values actually available from the backend.

### Top utility bar

Quiet pills:

```text
Synthetic Dataset
Model v1
Agent: Deterministic / LLM
● API Healthy
```

Never fabricate status.

---

## 8. Overview — Risk Command Center

The root route should feel like the executive risk terminal.

Header:

**RISK INTELLIGENCE**

**See the risk before it becomes a loss.**

`A live view of transaction risk, coordinated fraud networks, investigation activity, and financial exposure.`

### KPI row

Four cards:

1. Transactions
2. Fraud Exposure
3. Suspicious Transactions
4. Suspicious Clusters

Use actual API values only.

### Main analytics

Large:

**Risk Distribution**

Show Low / Medium / High / Critical.

Secondary:

**Fraud Exposure**

Show:
- total amount
- fraud exposure
- prevented amount where supported
- trend

### Lower intelligence grid

- Recent High-Risk Activity
- FraudDNA Networks
- Investigation Activity

Rows show actual transaction IDs, amounts, scores, clusters, findings, and decisions.

---

## 9. Transactions — Financial Ledger

Header:

**Transaction Intelligence**

Controls:
- search
- risk level
- suspicious only
- sort
- pagination

Columns:

```text
TRANSACTION
AMOUNT
CUSTOMER
DEVICE
RISK
CLUSTER
DECISION
```

Rows use:
- 1px bottom borders
- 12–14px vertical padding
- subtle hover
- no zebra striping

Transaction IDs and technical fields use JetBrains Mono.

Clicking a row opens investigation/detail.

---

## 10. Investigation — Signature Experience

This is the most important screen.

Header:

```text
TRANSACTION / tx_0001991
CRITICAL RISK
```

Large serif risk score:

```text
1.000
```

Decision:

```text
HOLD
```

### Three-column desktop layout

#### Left — Transaction Facts

- amount
- timestamp
- customer
- merchant
- device
- IP
- card
- transaction ID

#### Center — FraudDNA Graph

React Flow is the visual signature.

Node types:
- Transaction
- Customer
- Device
- IP
- Card
- Merchant

Style:
- Onyx graph surface
- graphite edges
- muted monochrome nodes
- copper selected transaction
- semantic risk color only where necessary
- subtle highlighted relationships
- smooth zoom/pan
- no permanent animation

The graph must look like an intelligence map, not sci-fi.

#### Right — Risk Intelligence

Stack:

**Risk Score**
- model score
- risk level

**Why flagged**
- SHAP contribution bars
- feature names
- positive/negative contribution

**FraudDNA**
- cluster ID
- coordination evidence
- related entities

**Decision**
- ALLOW / REVIEW / HOLD
- deterministic policy reasons

---

## 11. AI Investigation

Treat the agent as a case-file analyst, not a chatbot.

Header:

**AI Investigation**

Small label:

`BOUNDED READ-ONLY AGENT`

Vertical timeline:

```text
01  Transaction context loaded
02  Risk explanation inspected
03  Related entities queried
04  FraudDNA cluster analyzed
05  Historical policy evidence retrieved
06  Findings synthesized
```

Each step may show:
- tool
- concise result
- duration
- provenance

Use real backend state. Never fake streaming.

### Finding card

Example structure:

**Coordinated fraud pattern detected.**

Then evidence returned by the backend.

The evidence should visually distinguish:
- observation
- model signal
- graph relationship
- retrieved policy
- agent conclusion

---

## 12. Grounded RAG Evidence

Use an evidence card/drawer, not a chat window.

Header:

**Grounded Evidence**

Each item:

```text
GDL-001
Fraud Defense Guideline

Relevant evidence...
```

Metadata:

```text
SOURCE
RETRIEVAL SCORE
DOCUMENT TYPE
```

Source IDs use Copper.

If RAG is degraded, show the real degraded state and do not invent citations.

---

## 13. Deterministic Policy Decision

This component must visually separate AI reasoning from financial control.

Card:

**Policy Decision**

Large:

```text
HOLD
```

Reasons:

```text
HIGH_RISK_THRESHOLD
SUSPICIOUS_FRAUD_CLUSTER
```

Footer:

```text
Decision authority
Deterministic policy engine
```

Visual hierarchy:

**AI investigates → deterministic policy decides.**

Never create an AI button that implies direct payment mutation.

---

## 14. FraudDNA Network

Header:

**FraudDNA**

`Find the relationships that individual transactions hide.`

Main composition:
- large React Flow canvas
- cluster inspector

Cluster cards:
- cluster ID
- risk score
- suspicious status
- transaction count
- customer count
- device count
- IP count
- card count
- merchant count
- total amount
- primary reason

Selected cluster gets a restrained copper outline.

Controls:
- zoom
- pan
- reset
- focus
- inspect

---

## 15. Simulation — Risk Laboratory

Header:

**Risk Simulation**

`Change the policy threshold. See what it would have cost.`

Controls:
- fraud threshold
- review threshold
- cost per false positive
- review capacity

Primary analytical view:

**Risk / Loss Tradeoff**

Metrics:
- fraud prevented
- fraud missed
- false positives
- false-positive cost
- expected loss
- net benefit
- precision
- recall
- F1
- FPR

Comparison table:

```text
SCENARIO
THRESHOLD
PRECISION
RECALL
FALSE POSITIVES
FRAUD PREVENTED
EXPECTED LOSS
NET BENEFIT
```

The page should feel like a financial risk laboratory.

---

## 16. Evaluation

Header:

**Model Evaluation**

Eyebrow:

`HELD-OUT TEST SET`

Large metric should use the actual persisted evaluation value.

Supporting metrics:
- Precision
- Recall
- F1
- PR-AUC
- FPR
- False-positive cost
- Fraud prevented
- Fraud missed

Visuals:
- confusion matrix
- precision/recall
- risk distribution
- threshold comparison

Always show:

`Synthetic dataset • deterministic seed • held-out evaluation`

Never hide synthetic-data provenance.

---

## 17. Audit

Header:

**Audit Trail**

Dense ledger.

Columns:

```text
TIMESTAMP
TRANSACTION
INVESTIGATION
FINDINGS
POLICY
DECISION
HASH
```

Hashes use JetBrains Mono.

Expandable details:
- evidence
- tool provenance
- policy version
- immutable audit hash
- fallback/degraded state

The audit experience should feel forensic and trustworthy.

---

## 18. Buttons

### Primary

White pill:

```text
background: #FFFFFF
color: #08080A
border-radius: 9999px
```

One primary action per section.

Examples:
- Investigate
- Run Simulation
- View Cluster

### Secondary

Transparent with graphite/slate border.

### Ghost

No border until hover.

---

## 19. Inputs and Filters

Pill-shaped:

```text
background: #121317
border: 1px solid #2E3038
color: #E2E3E9
```

Focus:

```text
border-color: #CC9166
box-shadow: none
```

Filter pills should be compact and calm.

---

## 20. Charts

Charts must disappear into the product instead of looking like default Recharts.

Rules:
- minimal gridlines
- thin strokes
- small labels
- no rainbow palette
- no 3D
- no unnecessary gradients
- dark Carbon/Onyx tooltips
- actual backend values
- gilded gradient only for the primary analytical curve
- semantic colors only where meaning requires

---

## 21. Graph Styling

Default node:

```text
background: #121317
border: 1px solid #2E3038
color: #E2E3E9
border-radius: 9999px
```

Selected transaction:

```text
border: 1px solid #CC9166
```

Critical:

```text
border: 1px solid #D05B5B
```

Edges:
- normal: #2E3038
- selected: copper/gilded
- suspicious: muted critical color

Animate only:
- selected relationship
- active investigation transition

Never continuously animate the entire graph.

---

## 22. Motion

Motion is explanatory.

Use:
- 150–220ms hover transitions
- 250–400ms panel transitions
- chart entrance
- skeleton transitions
- investigation timeline progression
- graph focus transition

Do not use:
- particles
- perpetual background animation
- bouncing cards
- neon glow
- fake terminal typing
- excessive parallax
- fake streaming

Respect `prefers-reduced-motion`.

---

## 23. Loading / Error / Empty States

### Loading

Use layout-matching skeletons with Carbon/Graphite surfaces.

Never display fake numbers while loading.

### Empty

Example:

**No suspicious clusters found.**

`No clusters currently meet the selected risk criteria.`

### Error

Example:

**Risk intelligence unavailable**

`The graph service could not load the transaction dataset.`

Action:

`Retry`

### Degraded RAG

**Evidence retrieval degraded**

`Grounded document retrieval is temporarily unavailable. Investigation remains available without unsupported evidence.`

---

## 24. Responsive

### Desktop
Full sidebar + analytical canvas.

### Tablet
Collapsible sidebar; stack intelligence panels as needed.

### Mobile
Priority:
1. risk score
2. transaction facts
3. policy decision
4. graph
5. evidence
6. SHAP
7. audit

Tables become horizontal-scroll or card lists.

---

## 25. Accessibility

- strong contrast
- keyboard navigation
- visible focus
- semantic buttons
- accessible graph labels
- status not conveyed by color alone
- semantic table headers
- keyboard-accessible tooltips
- reduced-motion support

---

## 26. Imagery

The operational application should use almost no photography.

If a landing/intro treatment exists, imagery should be:
- editorial
- muted
- financial/intelligence oriented
- human rather than hacker cliché

The product UI itself is the hero.

---

## 27. Component Inventory

Build/reuse:

- AppShell
- Sidebar
- TopBar
- PageHeader
- MetricCard
- RiskBadge
- DecisionBadge
- StatusPill
- DataTable
- TransactionRow
- RiskDistributionChart
- ExposureChart
- RiskScore
- TransactionFacts
- FraudGraph
- GraphLegend
- ClusterCard
- ClusterInspector
- ShapExplanation
- InvestigationTimeline
- AgentFinding
- EvidenceCard
- PolicyDecisionCard
- SimulationControls
- SimulationChart
- SimulationComparisonTable
- EvaluationMetricCard
- ConfusionMatrix
- AuditTable
- AuditDetail
- LoadingSkeleton
- ErrorState
- EmptyState
- SearchInput
- FilterPill
- Tooltip
- Drawer
- Modal

Prefer reusable components over route-specific duplicated styling.

---

## 28. Data Integrity Rules

This is a fraud product. Visual polish must never compromise trust.

- Use actual backend responses.
- Never hard-code demo metrics into production UI.
- Clearly label synthetic data.
- Never fabricate agent steps.
- Never fabricate RAG citations.
- Never imply historical/synthetic results are live payment actions.
- Preserve degraded states.
- Preserve deterministic policy authority.
- Preserve all existing API contracts.

---

## 29. Do

- dark editorial fintech aesthetic
- serif for intelligence and major numbers
- Inter for operations
- JetBrains Mono for evidence
- copper sparingly
- semantic risk colors only where needed
- hairline borders
- generous whitespace around major concepts
- compact tables
- FraudDNA graph as signature visual
- investigation as a case-file experience
- deterministic policy as a distinct control layer
- subtle meaningful motion
- real data

## 30. Don't

- generic blue SaaS dashboard
- neon cyberpunk
- glowing green Matrix styling
- giant cybersecurity shields
- excessive glassmorphism
- heavy shadows
- rainbow charts
- fake live metrics
- fake agent reasoning
- fabricated evidence
- giant chatbot UI
- continuous graph animation
- decorative particles
- misleading payment-blocking claims

---

## 31. CSS Tokens

```css
:root {
  --color-obsidian: #08080A;
  --color-onyx: #040406;
  --color-carbon: #121317;
  --color-graphite: #1C1D22;
  --color-slate: #2E3038;
  --color-smoke: #464853;
  --color-ash: #5E616E;
  --color-steel: #777A88;
  --color-fog: #9194A1;
  --color-mist: #ACAEB9;
  --color-silver: #C7C9D1;
  --color-bone: #E2E3E9;
  --color-paper-white: #FFFFFF;
  --color-copper: #CC9166;
  --color-gilded: #AE9357;

  --risk-low: #8FAF9B;
  --risk-review: #C7A66B;
  --risk-high: #C47A63;
  --risk-critical: #D05B5B;
  --risk-info: #A6A9B3;

  --font-display: "Ivy Presto", "Playfair Display", "DM Serif Display", Georgia, serif;
  --font-inter: "Inter", ui-sans-serif, system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;

  --radius-card: 10px;
  --radius-full: 9999px;
  --border-primary: #1C1D22;
  --border-secondary: #2E3038;

  --page-max-width: 1440px;
  --sidebar-width: 240px;
}
```

---

## 32. Implementation Principle

The reference's strongest identity is the collision between **editorial luxury and dense financial data**.

For FraudDNA, recreate that collision as:

**Editorial serif + operational sans + machine monospace**

and:

**Obsidian + Onyx + hairline borders + copper punctuation + restrained gilded analytics**

The result should feel closer to a premium financial intelligence terminal than to a conventional cybersecurity dashboard.

> **Make the interface calm enough for a financial analyst to trust, and sharp enough for a fraud investigator to believe.**
