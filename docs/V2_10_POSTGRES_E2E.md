# FraudDNA V2-10 — PostgreSQL Live E2E Verification Report

---

## 1. Environment & Architecture Overview

- **Database Engine**: PostgreSQL 16 with `pgvector` extension.
- **ORM / Driver**: SQLAlchemy 2.0 (asyncpg for async paths, psycopg2 for sync migrations and repositories).
- **Alembic Migration Chain**:
  1. `0001_rag_tables`: Vector embeddings, documents, typology indexes.
  2. `0002_v2_domain_schema`: 19 domain models (`customers`, `transactions`, `devices`, `decisions`, `cases`, `audit_events`, etc.).
  3. `0003_network_temporal_fields`: Temporal network metrics.
  4. `0004_risk_orchestration_fields`: 4-layer multi-composite risk columns.

---

## 2. Test Execution & Coverage

The dedicated test suite `backend/tests/test_v2_10_postgres_e2e.py` validates:

1. **Domain Model Relational Integrity**:
   - Creates Customer, Device, Merchant, Card, and Transaction with real foreign-key dependencies.
   - Queries through SQLAlchemy relationships (`tx.customer.city`, `tx.device.device_fingerprint`).
2. **Transaction Rollback & Isolation**:
   - Asserts that when a transaction is rolled back on error, zero phantom rows persist in the database.
3. **Cryptographic SHA-256 Audit Trail Chaining**:
   - Asserts sequential chaining of `previous_hash` linking to predecessor's `event_hash`.
   - Executes `AuditService.verify_audit_chain()` against live database rows.
4. **Clean Skip Semantics**:
   - When executed in environments without active PostgreSQL daemon, tests cleanly skip (`pytestmark = skipif`) with informative skip messages, while executing in full during GitHub Actions CI where PostgreSQL 16 is provisioned as a service container.
