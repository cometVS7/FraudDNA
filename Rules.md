# FraudDNA — Engineering Rules

## 1. Core Rule
FraudDNA is a reliable fraud-defense product, not an AI demo.

Every feature must be useful, testable, observable, and honest.

## 2. AI Boundaries
### ML
Transaction risk prediction and useful anomaly signals.

### Graph
Relationship discovery and coordinated-abuse detection.

### SHAP
Actual model explainability.

### LLM
Investigation and evidence synthesis only.

### RAG
Ground LLM output in real curated documents/cases/policies.

### Agent
Controlled investigation workflow only.

## 3. Financial Decision Boundary
The LLM must never:
- determine final fraud probability
- calculate authoritative financial loss
- enforce policy
- modify payment state
- issue refunds
- execute payment actions

The deterministic policy engine controls the final risk action.

## 4. Deterministic Actions
Supported actions:
- ALLOW
- REVIEW
- HOLD

Financial calculations must be deterministic and reproducible.

## 5. Evaluation
- Train/validation/test separation.
- No label leakage.
- No future-information leakage.
- Threshold selection only on validation.
- Final performance on held-out test.
- Report false positives honestly.
- Include monetary FP cost.
- Never cherry-pick metrics.

## 6. Failure Handling
- LLM failure → continue where possible and escalate.
- RAG failure → no fabricated evidence.
- Agent timeout → terminate safely.
- External failure → bounded retries.
- Duplicate requests → idempotent handling.
- Missing evidence → explicit uncertainty.

## 7. Quality
Backend:
- Ruff
- mypy
- pytest

Frontend:
- ESLint
- strict TypeScript
- Zod for uncertain/external data

## 8. Secrets
Use `.env` locally.
Commit `.env.example`.
Never commit credentials or API keys.

## 9. Dependency Rule
Add a dependency only if it solves a concrete requirement and materially reduces risk/time.

## 10. Scope Rule
If time is constrained, preserve:
1. ML detector
2. held-out evaluation
3. false-positive cost
4. FraudDNA graph
5. XAI
6. investigation
7. policy decision
8. risk simulation

Cut polish before correctness.

## 11. Testing
Test:
- feature generation
- model inference
- graph construction
- cluster detection
- policy logic
- simulation calculations
- API validation
- failure paths
- agent boundaries

## 12. Git
Before committing:
1. inspect diff
2. run relevant checks
3. inspect changed files
4. verify no secrets
5. ensure commit scope is intentional

Use:
- feat:
- fix:
- test:
- refactor:
- docs:
- chore:

Do not blindly commit/push.

## 13. Frontend Rules
- Premium fintech analytics aesthetic.
- No fake metrics.
- No fake real-time activity.
- Clear loading/error/empty states.
- Motion should explain state changes, not decorate them.

## 14. Defense-Only
Do not implement offensive fraud techniques, evasion, credential theft, attack automation, or payment-abuse instructions.

## 15. Final Principle
**Use AI where uncertainty benefits from reasoning. Use deterministic engineering where money, policy, safety, reproducibility, or auditability is involved.**
