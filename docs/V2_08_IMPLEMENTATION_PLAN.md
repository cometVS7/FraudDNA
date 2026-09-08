# FraudDNA V2-08 — Implementation Plan
## Step-by-Step Execution Plan for Autonomous AI Investigation Agent

---

## 1. Implementation Principles & Strategy

Phase **V2-08** will be executed in disciplined, incremental steps adhering strictly to the FraudDNA Zero-HITL Engineering Policy:

```
[PRD & Arch Spec] ──► [Schemas & Interfaces] ──► [Provider Abstraction] ──► [Read-Only Tools]
                                                                                   │
                                                                                   ▼
[CI Verification] ◄── [REST API & Audit] ◄── [Service & Persistence] ◄── [LangGraph State Machine]
```

### Critical Implementation Guardrails:
1. **Zero Production Mutation During Design**: No implementation code is created or modified until the design artifacts are reviewed.
2. **Zero Modification of V2-01 Through V2-07**: Existing risk orchestrators, network intelligence services, entity repositories, and database migration scripts remain untouched.
3. **Strict Invariant Adherence**: AI agent outputs are purely advisory; all financial controls remain in `rules.py` and `DecisionService`.
4. **Zero Schema Migration**: Uses existing `InvestigationModel`, `EvidenceModel`, `AIFindingModel`, and `AuditEventModel` tables.

---

## 2. Work Breakdown Structure (WBS)

### Phase 1: Schemas & Domain Typing
- **Task 1.1**: Update `app.schemas.investigation` and `app.agent.schemas` with strict Pydantic v2 schemas:
  - `EvidenceCategory`, `EvidenceItem`, `AgentFindingOutput`, `AgentInvestigationOutput`, `AgentInvestigationRequest`, `AgentInvestigationResponse`.
  - Enforce `extra="forbid"` and bounded numeric constraints across all models.

### Phase 2: Model & Provider Abstraction Layer
- **Task 2.1**: Implement `app.agent.providers.BaseLLMProvider` abstract interface.
- **Task 2.2**: Implement `DeterministicFallbackEngine` supporting offline, zero-token, fully grounded rule-based synthesis for CI and test environments.
- **Task 2.3**: Implement `GeminiProvider`, `OpenAIProvider`, and `AnthropicProvider` with strict 15s timeouts, JSON mode parsing, and error-handling wrappers.
- **Task 2.4**: Implement provider factory `get_llm_provider()` reading `settings.LLM_PROVIDER`.

### Phase 3: Read-Only Investigation Tool Registry
- **Task 3.1**: Implement `app.agent.tools.AgentTools` integrating with V2 PostgreSQL repositories:
  1. `get_transaction_profile`: Queries `TransactionRepository.get_by_id()`.
  2. `get_risk_orchestration`: Queries `RiskOrchestrator.orchestrate_transaction_risk()`.
  3. `get_shap_signals`: Queries `RiskAssessmentModel` and `RiskSignalModel`.
  4. `get_entity_profile`: Queries `EntityRepository.get_entity_profile()`.
  5. `get_entity_ego_graph`: Queries `EntityRepository.get_ego_graph()`.
  6. `get_network_intelligence`: Queries `NetworkIntelligenceService.get_network_intelligence()`.
  7. `search_network_paths`: Queries `NetworkIntelligenceService.search_paths()`.
  8. `search_typology_rag`: Queries `RAGService.search()` with similarity score $\ge 0.55$.
  9. `get_audit_history`: Queries `AuditRepository.get_events_for_entity()`.
- **Task 3.2**: Add execution timing, parameter sanitization, and structured error catching to every tool.

### Phase 4: LangGraph State Machine & Workflow Nodes
- **Task 4.1**: Define `app.agent.state.InvestigationState` TypedDict.
- **Task 4.2**: Implement state graph nodes in `app.agent.graph`:
  - `initialize_node`
  - `extract_primary_context_node`
  - `orchestrate_risk_context_node`
  - `investigate_network_node`
  - `retrieve_typology_rag_node`
  - `evaluate_evidence_node` (conditional edge router)
  - `synthesize_findings_node` (invokes provider with prompt isolation)
  - `validate_and_persist_node` (validates schema, persists to DB, logs audit hash)
- **Task 4.3**: Author robust system prompt and XML-delimited context synthesis templates in `app.agent.prompts`.

### Phase 5: Application Service & Persistence Coordination
- **Task 5.1**: Implement `app.agent.service.AgentInvestigationService` facade:
  - Validates transaction existence in PostgreSQL before launching graph.
  - Manages database sessions and atomic transaction flushes.
  - Persists `InvestigationModel`, `EvidenceModel`, `AIFindingModel`.
  - Records SHA-256 audit event `INVESTIGATION_COMPLETED` via `AuditService`.
- **Task 5.2**: Update dependency injection providers in `app.agent.service` and `app.services.investigation`.

### Phase 6: REST API Layer
- **Task 6.1**: Wire endpoints in `app.api.v1.endpoints.agent` and `app.api.v1.endpoints.investigations`:
  - `POST /api/v1/investigations/run`: Trigger bounded AI investigation.
  - `GET /api/v1/investigations/{id}`: Retrieve persisted investigation dossier.
  - `GET /api/v1/investigations`: List investigations with status/priority filtering.
  - `GET /api/v1/investigations/{id}/evidence`: List verified evidence items.
  - `GET /api/v1/investigations/{id}/findings`: List structured AI findings.
- **Task 6.2**: Add comprehensive OpenAPI documentation, schemas, and error responses.

### Phase 7: Automated Verification & Golden Regression Suite
- **Task 7.1**: Implement comprehensive test suite `backend/tests/test_v2_agent_investigation.py` (minimum 25 tests).
- **Task 7.2**: Verify canonical golden fixture `tx_0001991` end-to-end.
- **Task 7.3**: Execute full test suite (233 existing + 25 new tests = 258 passing).
- **Task 7.4**: Run Ruff linter, Ruff formatter, and Mypy type checker across backend source files.

---

## 3. Test Matrix & Validation Specifications

```
+---------------------------------+---------------------------------------------------------------+
| Test Category                   | Specific Assertions & Scenarios                               |
+---------------------------------+---------------------------------------------------------------+
| Read-Only Tool Unit Tests       | - Parameter boundary validation (depth, limits).              |
|                                 | - Read-only guarantee: zero database mutations during calls.  |
|                                 | - Graceful handling of missing entities (404 / empty payload).|
|                                                                                                 |
| LangGraph Workflow Tests        | - Complete execution across all 8 nodes.                      |
|                                 | - Hard tool budget enforcement (fails if > 10 tool calls).    |
|                                 | - Evidence evaluation conditional branch routing.             |
|                                 |                                                               |
| Provider & Fallback Tests       | - DeterministicFallbackEngine produces valid schema JSON.     |
|                                 | - Timeout / error simulation triggers degraded fallback.      |
|                                 | - Prompt injection strings neutralized in context blocks.     |
|                                 |                                                               |
| Persistence & Audit Tests       | - InvestigationModel created with status="COMPLETED".         |
|                                 | - EvidenceModel records inserted with correct foreign keys.   |
|                                 | - AIFindingModel records contain valid tool traces.           |
|                                 | - AuditEventModel appended with valid SHA-256 hash chain.     |
|                                 |                                                               |
| Golden Regression (tx_0001991)  | - Identifies DEVICE_REUSE_RING and MULTI_INFRASTRUCTURE.      |
|                                 | - Matches GDL-001 playbooks in RAG retrieval.                 |
|                                 | - Assigns CRITICAL risk level without changing policy HOLD.   |
|                                 |                                                               |
| Regression Protection           | - 100% of existing 233 backend tests remain green.            |
+---------------------------------+---------------------------------------------------------------+
```

---

## 4. Verification Commands

```powershell
# 1. Run full backend pytest suite
& ".venv/Scripts/python.exe" -m pytest backend/tests -v --tb=short

# 2. Run Ruff linter and formatter checks
& ".venv/Scripts/python.exe" -m ruff check --config backend/pyproject.toml backend
& ".venv/Scripts/python.exe" -m ruff format --check --config backend/pyproject.toml backend

# 3. Run Mypy strict type checking
& ".venv/Scripts/python.exe" -m mypy --config-file backend/pyproject.toml backend/app

# 4. Verify PR #15 status
gh pr view 15 --json number,title,state,statusCheckRollup
```

---

## 5. Rollout & Handover Checklist

- [x] Document Control & PRD completed (`docs/V2_08_PRD.md`)
- [x] Technical Architecture completed (`docs/V2_08_ARCHITECTURE.md`)
- [x] Implementation Plan completed (`docs/V2_08_IMPLEMENTATION_PLAN.md`)
- [ ] User Review & Approval of Design Artifacts
- [ ] Phase V2-08 Code Implementation
- [ ] 258+ Tests Passing Locally & in GitHub Actions CI
- [ ] PR #15 Ready for Phase V2-09
