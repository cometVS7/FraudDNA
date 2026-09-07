# FraudDNA V2-10 — Implementation Plan & Verification Strategy

---

## 1. Work Breakdown Structure

| Task ID | Component / Milestone | Primary Files | Verification Method |
| :--- | :--- | :--- | :--- |
| **V2-10.1** | Production Config Hardening | `backend/app/core/config.py`, `.env.example` | Pytest validation against insecure settings |
| **V2-10.2** | Security Headers & Error Sanitization | `backend/app/core/middleware.py`, `backend/app/main.py` | Pytest HTTP header assertion |
| **V2-10.3** | Readiness & Liveness Probes | `backend/app/api/v1/endpoints/health.py`, `backend/app/schemas/health.py` | Live `/health` and `/ready` response tests |
| **V2-10.4** | PostgreSQL Live E2E Suite | `backend/tests/test_v2_10_postgres_e2e.py` | Real PostgreSQL model & rollback tests |
| **V2-10.5** | Production Performance Benchmark | `backend/tests/test_v2_10_performance.py`, `docs/V2_10_PERFORMANCE.md` | Statistical percentile latency measurements |
| **V2-10.6** | Boundary & Security Suite | `backend/tests/test_v2_10_security.py` | Out-of-bounds rejection (HTTP 422) tests |
| **V2-10.7** | CI Workflow Hardening | `.github/workflows/ci.yml` | PostgreSQL 16 service integration in GitHub Actions |

---

## 2. Verification Protocol

1. **Step 1: Code Quality & Static Analysis**:
   - `ruff check --config backend/pyproject.toml backend`
   - `ruff format --check --config backend/pyproject.toml backend`
   - `mypy --config-file backend/pyproject.toml backend/app`
2. **Step 2: Backend Regression**:
   - `pytest backend/tests/ -v --tb=short` (Target: 266+ passing)
3. **Step 3: Frontend Quality**:
   - `npm --prefix frontend run lint`
   - `npm --prefix frontend run type-check`
   - `npm --prefix frontend run build`
4. **Step 4: Golden Demo Invariants (`tx_0001991`)**:
   - Verify deterministic `HOLD` vs advisory `MANUAL_REVIEW_ESCALATION` separation.
