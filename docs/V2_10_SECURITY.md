# FraudDNA V2-10 — Security & Boundary Defense Report

---

## 1. Security Architecture & Threat Modeling

FraudDNA operates under a defense-in-depth security model protecting financial orchestrators, analyst consoles, and automated risk scoring:

### 1.1 Non-Negotiable Invariant Enforcement
- **Zero Financial Mutation Authority**:
  - AI agents produce advisory recommendations (`AdvisoryAction`) only.
  - Case management actions only update operational ticket status (`NEW`, `IN_REVIEW`, `ESCALATED`, `RESOLVED`, `CLOSED`) and append analyst triage notes.
  - Only the pure, deterministic `PolicyEngine` can emit authoritative `PolicyAction` (`ALLOW`, `REVIEW`, `HOLD`).

### 1.2 Configuration Hardening & Fail-Fast Validation
- Production configuration validation (`settings.validate_production_configuration()`):
  - **Insecure Secret Key Defense**: Rejects keys shorter than 32 characters or default dev placeholders.
  - **Database Credential Defense**: Rejects default `frauddna_password` in production.
  - **CORS Defense**: Rejects wildcard `*` origins in production mode.

### 1.3 HTTP Security Headers
Every HTTP response emitted by the FastAPI backend includes standard defense headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (when `is_production` is true)

### 1.4 Bounded Graph & Denial-of-Service Defense
- Graph traversal depth bounded ($d \in [1, 4]$).
- Maximum node count bounded ($\le 250$).
- Excessive queries return HTTP 422 immediately.

### 1.5 Adversarial Prompt Injection Defense
- Transaction fields, customer metadata, and notes are encapsulated within strict structured delimiters.
- System prompt reinforces that data attributes cannot override policy rules or agent boundaries.
