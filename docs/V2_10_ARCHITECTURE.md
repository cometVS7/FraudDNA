# FraudDNA V2-10 — Technical Architecture Document
## Production Hardening, Concurrency & PostgreSQL Integration

---

## 1. Architectural Topology

```
                                  [ CLIENTS ]
             (Next.js 16 Console / External Payment Orchestrator)
                                      │
                                      ▼
                        [ REQUEST CORRELATION LAYER ]
              ├── Request ID (X-Request-ID) & Correlation ID Injection
              └── Security Headers (HSTS, CSP/Frame, NoSniff, XSS)
                                      │
                                      ▼
                           [ FASTAPI ROUTER & REST ]
              ├── /api/v1/decisions  ──> Deterministic Policy Engine (Pure Logic)
              ├── /api/v1/agent      ──> LangGraph Grounded AI Investigator (Advisory)
              ├── /api/v1/cases      ──> Case Lifecycle Service
              ├── /api/v1/networks   ──> Bounded Graph Traversal & Syndicate Engine
              └── /api/v1/audit      ──> SHA-256 Tamper-Evident Ledger
                                      │
                                      ▼
                     [ APPLICATION & REPOSITORY LAYER ]
              ├── DecisionService, CaseService, EntityService, AuditService
              └── Bounded Engine & Pool Manager (SQLAlchemy 2.0)
                                      │
                                      ▼
                     [ POSTGRESQL 16 + PGVECTOR STORAGE ]
              ├── 19 Relational Domain Tables (Foreign-Key Cascades)
              ├── Composite Indexes on (transaction_id, timestamp, risk_score)
              ├── Cryptographic Audit Hash Chaining (previous_hash -> event_hash)
              └── Typology Embeddings Vector Space (Cosine Similarity)
```

---

## 2. Database Connection Pooling & Concurrency Architecture

### Engine Configuration
```python
create_engine(
    settings.DATABASE_URL_SYNC,
    echo=False,
    future=True,
    pool_pre_ping=True,      # Health check connections before checkout
    pool_size=10,            # Bounded active connection pool
    max_overflow=20,         # Burst capacity for high-throughput spikes
    pool_timeout=30.0,       # Fail fast rather than deadlocking callers
)
```

### Session Lifecycle Management
```python
def get_sync_db() -> Generator[Session, None, None]:
    factory = get_sync_session_factory()
    with factory() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
```
- **Atomicity**: Any unhandled domain exception automatically triggers a database rollback before bubbling up.
- **Leak Prevention**: The `finally: session.close()` guarantee ensures connection fairy returns to pool immediately.

---

## 3. Bounded Graph & Memory Safety Controls

To eliminate memory spikes in production container environments:
1. **Depth Bounding**: BFS traversal is hard-capped at depth $d \le 4$.
2. **Node Bounding**: Ego-neighborhood queries are capped at $\le 250$ entities.
3. **Path Bounding**: Pathfinding returns at most 50 ranked paths.
4. **Reject Malformed Queries**: Out-of-bounds parameters reject with HTTP 422 immediately at the schema level.

---

## 4. Adversarial Prompt Injection Defense

AI investigation input fields (customer city, device fingerprint, transaction notes, merchant category) are treated as strictly untrusted user data:
- Wrapped inside structured XML/JSON delimiters in prompt templates.
- Explicit system prompt instructions forbid executing user commands found inside transaction attributes.
- Output validation enforces Pydantic schema deserialization.
