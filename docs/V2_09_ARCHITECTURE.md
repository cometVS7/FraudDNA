# FraudDNA V2-09 — Technical System Architecture
## Case + Decision Intelligence / Investigation Workbench

---

## 1. Document Control & Metadata

- **Document Version**: 2.0.0-PROD-SPEC
- **Status**: APPROVED ARCHITECTURAL SPECIFICATION (DESIGN PHASE ONLY)
- **Phase Target**: Phase V2-09 (System Architecture)
- **Author**: Lead Product Architect + Principal Engineer
- **Integration Target**: PR #15 (`v2/production-platform` $\to$ `main`)
- **Core Reference Baseline**: `docs/V2_09_PRD.md`, `docs/V2_08_ARCHITECTURE.md`, `backend/app/api/v1/endpoints/`

---

## 2. System Architecture Overview

The FraudDNA V2-09 system integrates Next.js 16 (React 19), Tailwind CSS, Lucide icons, Recharts, and `@xyflow/react` with the FastAPI asynchronous backend, PostgreSQL persistence layer, and LangGraph intelligence engine:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FRAUDDNA V2-09 ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND LAYER (Next.js 16 / React 19 / TypeScript 5.8)                    │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │  Case Queue  │  │ Investigation│  │ Network Graph│  │ Audit Explorer  │ │
│  │  (/cases)    │  │ Workbench    │  │ (React Flow) │  │ (/audit)        │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────────┬────────┘ │
│         │                 │                 │                   │           │
│  ┌──────┴─────────────────┴─────────────────┴───────────────────┴────────┐ │
│  │                    Unified API Client (`lib/api.ts`)                  │ │
│  │              (Typed Async Fetchers, URL State Hooks, Error Handling)  │ │
│  └───────────────────────────────────┬───────────────────────────────────┘ │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ REST API GATEWAY (FastAPI / Pydantic v2)                                     │
│                                                                             │
│  • /api/v1/cases (CRUD & Status Transitions)                                │
│  • /api/v1/agent/investigate (LangGraph AI Dossier)                         │
│  • /api/v1/decisions/evaluate (Deterministic Policy Engine)                 │
│  • /api/v1/networks (V2-07 Intelligence, Graph, Paths, Syndicate Patterns)  │
│  • /api/v1/entities (Customer, Account, Device, Card, IP, Merchant Profiles)│
│  • /api/v1/audit (Immutable Event Stream & SHA-256 Chain Verification)      │
│  • /api/v1/rag/search (Vector Store Typology Citations)                     │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ BACKEND INTELLIGENCE & PERSISTENCE                                          │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │ Policy Engine│  │ LangGraph    │  │ NetworkX &   │  │ PostgreSQL 16   │ │
│  │ (ALLOW/REVIEW│  │ Agent        │  │ Graph Engine │  │ (19 Domain      │ │
│  │  /HOLD)      │  │ (Advisory)   │  │ (Syndicates) │  │  Models)        │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Frontend Component Hierarchy & Module Boundaries

The frontend follows a modular, atomic component hierarchy designed for high testability and isolation:

```
frontend/
├── app/
│   ├── cases/
│   │   ├── page.tsx                      # Case Queue & Triage Table
│   │   └── [case_id]/page.tsx            # Case Detail View
│   ├── investigate/
│   │   └── page.tsx                      # Core 3-Column Investigation Workbench
│   ├── audit/
│   │   └── page.tsx                      # Cryptographic Audit Explorer
│   ├── frauddna/
│   │   └── page.tsx                      # Risk Network & Cluster Explorer
│   ├── transactions/
│   │   └── page.tsx                      # Transaction Explorer Table
│   ├── layout.tsx                        # Root layout with Top Nav & Sidebar
│   └── globals.css                       # Dark theme CSS variables & fonts
├── components/
│   ├── layout.tsx                        # Sidebar, Header, Breadcrumbs
│   ├── fraud-graph.tsx                   # Enhanced React Flow Network Visualizer
│   ├── ui.tsx                            # Badges, Cards, Skeletons, Metrics
│   ├── workbench/
│   │   ├── hero-header.tsx               # Primary Score & Decision Hero Header
│   │   ├── decision-intelligence.tsx     # Authoritative Decision vs AI Advisory Card
│   │   ├── transaction-ledger.tsx        # Facts & Metadata Ledger
│   │   ├── entity-profile-drawer.tsx     # Slide-over Entity Drilldown Drawer
│   │   ├── shap-waterfall.tsx            # Tree SHAP Local Attributions
│   │   ├── syndicate-pattern-badges.tsx  # Detected Ring Badges & Explanations
│   │   ├── evidence-explorer.tsx         # Traceable Evidence Items List
│   │   ├── ai-dossier-card.tsx           # Grounded AI Hypothesis & Tool Trace
│   │   ├── rag-citations-card.tsx        # External AML & Typology Citations
│   │   ├── case-action-toolbar.tsx       # Safe Case Status & Note Mutator
│   │   ├── audit-events-timeline.tsx     # Chronological Event Timeline
│   │   └── path-search-dialog.tsx        # Bounded Pathfinding Search Dialog
│   └── cases/
│       ├── case-table.tsx                # Filterable Case Management Table
│       ├── case-create-modal.tsx         # New Case Creation Dialog
│       └── case-status-badge.tsx         # Colored & Icon-Decorated Case Status
├── hooks/
│   ├── use-async.ts                      # Promise lifecycle hook (data/loading/error)
│   ├── use-workbench-params.ts           # Synchronized URL query params hook
│   └── use-keyboard-shortcuts.ts         # Analyst hotkeys (Esc, 1-4 tabs, / search)
├── lib/
│   ├── api.ts                            # Strongly typed API client functions & interfaces
│   └── utils.ts                          # Formatting (INR currency, dates, class merging)
└── types/
    ├── case.ts                           # Case & Workflow TypeScript interfaces
    ├── agent.ts                          # AI Findings & Tool Trace interfaces
    ├── network.ts                        # Cluster & Syndicate Pattern interfaces
    └── graph.ts                          # Node & Edge visual types
```

---

## 4. Exact API Contracts & Integration Mapping

### 4.1 Case Management Endpoints (Workflow Mutations)

| Method | Endpoint | Purpose | Request Body / Query | Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/cases` | Paginated case queue query | `status`, `priority`, `owner`, `limit`, `offset` | `CaseListResponse` (`items: CaseResponse[]`, `total_count: int`) |
| `POST` | `/api/v1/cases` | Create operational case | `CaseCreateRequest` (`title`, `priority`, `owner`, `notes`, `investigation_id`) | `CaseResponse` (`id`, `status: "NEW"`, `created_at`, `investigation_ids`) |
| `GET` | `/api/v1/cases/{case_id}` | Fetch single case details | Route param `case_id` | `CaseResponse` |
| `PATCH` | `/api/v1/cases/{case_id}/status` | Safe state machine transition | `CaseStatusUpdateRequest` (`status: CaseStatus`, `notes`, `owner`) | `CaseResponse` |

### 4.2 Investigation & Decision Intelligence Endpoints (Read & Execution)

| Method | Endpoint | Purpose | Request Body / Query | Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/decisions/evaluate` | Authoritative Policy Evaluation | `{"transaction_id": "tx_0001991"}` | `PolicyDecision` (`action: "HOLD"`, `reason_codes`, `policy_version`, `is_deterministic: true`) |
| `POST` | `/api/v1/agent/investigate` | Autonomous LangGraph Agent | `{"transaction_id": "tx_0001991", "max_steps": 8}` | `AgentInvestigationResponse` (`findings: AgentFindings`, `is_persisted: bool`, `is_degraded: bool`) |
| `GET` | `/api/v1/investigations/{id}` | Retrieve cached risk investigation | Route param `investigation_id` | `InvestigationResponse` (`risk_score`, `risk_factors`, `evidence`, `cluster`) |

### 4.3 Network & Entity Intelligence Endpoints (Read & Pathfinding)

| Method | Endpoint | Purpose | Request Body / Query | Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/networks/{id}/intelligence` | Full V2-07 Syndicate Assessment | `max_nodes=100`, `as_of` | `NetworkIntelligenceResponse` (`exposure`, `patterns`, `timeline`, `findings`) |
| `GET` | `/api/v1/networks/{id}/graph` | Cluster React Flow Subgraph | `max_nodes=100` | `GraphData` (`nodes: GraphNode[]`, `edges: GraphEdge[]`) |
| `POST` | `/api/v1/networks/paths/search` | Bounded Multi-Hop Pathfinding | `PathSearchRequest` (`source_id`, `target_id`, `max_depth: 3`, `max_paths: 5`) | `PathSearchResponse` (`paths: NetworkPath[]`) |
| `GET` | `/api/v1/entities/{type}/{id}` | Entity Profile & Velocity | Route params `entity_type`, `entity_id` | `EntityProfileResponse` |
| `GET` | `/api/v1/entities/{type}/{id}/graph` | Entity Ego-Graph Subgraph | `depth=2`, `max_nodes=50` | `GraphData` |

### 4.4 Audit Trail & Compliance Endpoints (Read & Cryptographic Proof)

| Method | Endpoint | Purpose | Request Body / Query | Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/audit` | Query immutable audit log | `entity_id`, `entity_type`, `event_type`, `limit`, `offset` | `AuditEventListResponse` (`items: AuditEventResponse[]`, `total_count: int`) |
| `GET` | `/api/v1/audit/verify/chain` | Cryptographic SHA-256 Check | None | `AuditChainVerifyResponse` (`is_valid: bool`, `total_verified: int`, `head_event_hash: str`) |

---

## 5. Network Graph Visualization Architecture (React Flow)

The network visualizer (`components/fraud-graph.tsx`) is built on `@xyflow/react` and renders a multi-entity topology with strict performance bounds:

```
                  ┌──────────────────────┐
                  │ Customer (cust_00843)│
                  └──────────┬───────────┘
                             │ OWNS
                  ┌──────────▼───────────┐
                  │ Account (acc_a0912)  │
                  └──────────┬───────────┘
                             │ DEBITS
                  ┌──────────▼───────────┐
                  │ Transaction          │
                  │ (tx_0001991) [CENTER]│
                  └────┬──────┬─────────┬┘
       USING_CARD      │      │ ON_DEVICE│     FROM_IP
 ┌─────────────────────┘      │          └─────────────────────┐
 ▼                            ▼                                ▼
┌───────────────┐     ┌───────────────┐               ┌───────────────┐
│ Card (c_0912) │     │ Device (d_339)│               │ IP (192.0.2.1)│
└───────┬───────┘     └───────┬───────┘               └───────┬───────┘
        │ SHARES_CARD         │ SHARES_DEVICE                 │ SHARES_IP
        └──────────────┬──────┴───────────────┬───────────────┘
                       ▼                      ▼
                 ┌─────────────────────────────────┐
                 │ Connected Fraud Ring Entity     │
                 │ (tx_0001992 / cust_00844)       │
                 └─────────────────────────────────┘
```

### 5.1 Graph Rendering & Interaction Mechanics
1. **Layout Strategy**:
   - **Radial Concentric Layout** centered on the focus transaction (`tx_0001991`), distributing direct 1-hop entities (card, device, IP, merchant, customer) at radius $R_1 = 220\text{px}$, and secondary 2-hop shared infrastructure entities at radius $R_2 = 380\text{px}$.
2. **Node Visual Encoding**:
   - **Node Shapes**: Rounded hex-cards with high-contrast icon badges (`TX`, `CU`, `AC`, `CD`, `DV`, `IP`, `ME`).
   - **Risk Borders**: Normal (`#2E3038`), Medium (`#C47A63`), Critical (`#D05B5B` with animated glow pulsing).
   - **Selected State**: Warm Copper highlight (`#CC9166`) with $16\text{px}$ drop shadow.
3. **Edge Styling & Interaction**:
   - Bezier curved links labeled with semantic relationships (`OWNS`, `DEBITS`, `ON_DEVICE`, `FROM_IP`, `USING_CARD`, `SHARES_DEVICE`, `SHARES_CARD`).
   - Edges participating in detected syndicate rings are colored with high-visibility accent (`#E06C75`) and animated dash strokes.
4. **Bounds Enforcement**:
   - Graph queries are hard-capped to $N \le 100$ nodes and depth $d \le 3$ to eliminate canvas rendering lag.

---

## 6. Decision Intelligence & Visual Separation Model

To uphold the core architectural invariant, the workbench renders a dedicated **Decision Intelligence Comparison Card**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DECISION INTELLIGENCE COMPARISON                      │
├──────────────────────────────────────┬──────────────────────────────────────┤
│ 🛡️ AUTHORITATIVE FINANCIAL DECISION   │ 🤖 AI ADVISORY INVESTIGATION         │
│ (Pure Deterministic Policy Engine)   │ (LangGraph Autonomous Agent)         │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ Decision Action:                     │ Advisory Recommendation:             │
│ [ HOLD ] (Critical Risk Policy)      │ [ MANUAL_REVIEW_ESCALATION ]         │
│                                      │                                      │
│ Triggered Reason Codes:              │ Investigation Confidence:            │
│ • CRITICAL_RISK_SCORE (0.9994)       │ 95.0% (High Confidence)              │
│ • SUSPICIOUS_FRAUD_CLUSTER           │                                      │
│ • DEVICE_REUSE_DETECTED              │ Grounded Evidence Backing:           │
│ • CARD_SHARING_RING_DETECTED         │ 10 Verifiable Grounded Items         │
│                                      │                                      │
│ Policy Matrix Version:               │ Model & Agent Version:               │
│ policy_matrix_v2.0                   │ agent_v2.0 (rule_fallback_v2)        │
│                                      │                                      │
│ Financial State:                     │ Operational Scope:                   │
│ TRANSACTION SETTLEMENT BLOCKED       │ ADVISORY ONLY (ZERO FINANCIAL AUTH) │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

---

## 7. Security, Threat Modeling, & Guardrails

| Threat Vector | Mitigation Mechanism | Verification Test |
| :--- | :--- | :--- |
| **XSS via Analyst Notes** | All note strings are sanitized on submission and rendered via React escaped text nodes. | Inject `<script>alert(1)</script>` into note submission; verify text renders as literal characters. |
| **XSS / Prompt Injection via AI Output** | AI hypotheses and RAG citations are parsed into structured JSON and rendered with strict markdown DOM sanitization (`rehype-sanitize`). | Inject malicious HTML in transaction metadata; verify AI findings card renders harmless text. |
| **IDOR in Case Transitions** | All `PATCH /api/v1/cases/{id}/status` endpoints validate case existence, enforce allowed state transitions, and record actor ID in the audit log. | Attempt invalid transition (`CLOSED` $\to$ `NEW`); verify 400 Bad Request domain error. |
| **Client-Side Financial Authority Spoofing** | The UI client contains zero endpoints or code paths capable of setting transaction settlement states directly. | Inspect client bundle; confirm absence of financial mutation mutations. |
| **DoS via Graph Flooding** | Network graph endpoints strictly enforce $N \le 100$ nodes, $d \le 3$ depth, and rate-limiting. | Query `/api/v1/networks/{id}/graph?max_nodes=10000`; verify parameter rejection or automatic clamping. |

---

## 8. Performance Budget & Optimizations

- **Dynamic Subgraph Caching**: Graph topologies and entity profiles are memoized in-memory via SWR / TanStack Query patterns with 60-second TTLs.
- **Virtualized Tables**: The Case Queue and Transaction Explorer utilize CSS-bounded virtual scrolling or strict 25/50 item pagination.
- **SVG & WebGL Hybrid Rendering**: Node cards render via lightweight DOM overlays while high-density edge lines render via optimized SVG markers.
- **Bundle Optimization**: Tree-shake Lucide icons and Recharts modules to keep frontend bundle size under $180\text{KB}$ gzipped.
