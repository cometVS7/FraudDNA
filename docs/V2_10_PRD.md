# FraudDNA V2-10 — Product Requirements Document (PRD)
## Production Hardening & PostgreSQL E2E Platform Architecture

---

## 1. Executive Summary

Phase **V2-10 (Production Hardening & PostgreSQL E2E)** elevates the FraudDNA platform from an integration-ready system to an enterprise-grade, PostgreSQL-backed, secure, observable, and concurrency-hardened production platform.

Historically, prototype fraud detection architectures rely on fragile in-memory caches or permissive developer defaults. V2-10 establishes immutable persistence, strict configuration enforcement, database connection pooling, cryptographic audit verification, bounded graph memory safety, adversarial prompt injection isolation, and automated CI PostgreSQL validation.

---

## 2. Core Architectural Invariant

```
ML predicts. Graph discovers. XAI explains. RAG grounds. The AI agent investigates. Deterministic policies control financial actions.
```

- **Zero Financial Authority for AI**: AI agents produce structured advisory findings (`AdvisoryAction`) and never mutate financial state (`PolicyAction`).
- **Zero In-Memory Fallback in Production**: When persistent storage mode is active, all writes and authoritative queries must execute against PostgreSQL with transactional integrity.

---

## 3. Key Requirements & Capabilities

### B1. PostgreSQL Live End-to-End Persistence
- Full relational persistence across all 19 domain models (`customers`, `accounts`, `cards`, `devices`, `ip_addresses`, `merchants`, `risk_networks`, `transactions`, `risk_assessments`, `decisions`, `cases`, `investigations`, `evidence`, `ai_findings`, `audit_events`).
- Transaction rollback safety guaranteeing atomicity.
- `pgvector` vector store support for typology embedding similarity lookups.

### B2. Database Connection Pooling & Concurrency
- Configurable SQLAlchemy async and sync connection pool settings (`DB_POOL_SIZE=10`, `DB_MAX_OVERFLOW=20`, `DB_POOL_TIMEOUT=30.0`).
- Guaranteed session lifecycle (automatic commit on success, rollback on exception, close in `finally`).
- Zero shared mutable sessions across concurrent asynchronous requests.

### B3. Production Configuration Hardening & Security
- Explicit production mode validation (`settings.validate_production_configuration()`):
  - Rejection of default/insecure `SECRET_KEY` (minimum 32 characters required).
  - Rejection of default `frauddna_password` in production `DATABASE_URL`.
  - Rejection of wildcard CORS (`*`).
- Standard HTTP security response headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`).

### B4. Bounded Graph & Memory Safety
- Traversal depth strictly bounded ($d \in [1, 4]$).
- Maximum node count strictly bounded ($\le 250$).
- Out-of-bounds queries rejected with HTTP 422 rather than silently clamped.
- Zero whole-graph downloads to browser.

### B5. AI Agent Production Hardening
- Hard reasoning limits: $\le 8$ reasoning steps, $\le 10$ tool calls.
- Timeout bounding: 30s per investigation request.
- Adversarial prompt injection isolation: Untrusted transaction notes and metadata are processed through strict delimiters and validated schemas.

### B6. Cryptographic Audit Integrity
- SHA-256 tamper-evident hash chaining.
- Live verification probe `/api/v1/audit/verify/chain`.
- Immediate detection of payload or signature tampering.

---

## 4. Acceptance Criteria

1. **Backend Test Suite**: 266+ tests passing with zero regressions.
2. **Code Quality**: Ruff clean, Ruff format clean, Mypy clean with zero type errors across all source files.
3. **Frontend Production Build**: Next.js 16 compiled cleanly across all 10 routes.
4. **CI Integration**: GitHub Actions workflow running PostgreSQL 16 service with migrations and live E2E test execution.
