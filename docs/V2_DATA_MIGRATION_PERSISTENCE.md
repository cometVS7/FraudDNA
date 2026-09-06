# FraudDNA V2 — Data Migration & Persistence Architecture

## 1. Overview

Phase V2-04 establishes **PostgreSQL as the authoritative data path** for FraudDNA while guaranteeing 100% backward compatibility for all existing V1 ML, Tree SHAP, Graph, Cluster, and Agent pipelines.

The architecture shifts runtime from CSV-in-memory reliance to relational persistence:

```
[ ml/data/transactions.csv (25k txs) ]
  ├── ml/models/lightgbm_model.joblib
  ├── ml/models/feature_pipeline.joblib
  └── knowledge/ (guidelines, policies, historical cases)
               │
               ▼
   [ DataMigrationService ] (scripts/migrate_v1_to_v2.py)
   ├── ModelRegistryModel (mdl_lightgbm_v010)
   ├── PolicyModel (pol_2025_1)
   ├── IntelligenceSourceModel (markdown docs)
   ├── Core Entities (Customers, Accounts, Cards, Devices, IPs, Merchants)
   ├── RiskNetworkModel (Coordinated fraud syndicate clusters)
   ├── TransactionModel (25k rows, Decimal amount, UTC timestamps, FKs)
   ├── RiskAssessmentModel (Point-in-time LightGBM inference)
   └── RiskSignalModel (Top-5 Tree SHAP feature attributions)
               │
               ▼
[ PostgreSQL Relational Domain Store ]
   ├── Indexed Multi-Dimensional Lookups
   ├── Cryptographic SHA-256 Audit Trail
   └── Foreign-Key Referential Integrity
```

---

## 2. V2 Authoritative Data Path vs. V1 Compatibility Path

The system is governed by the feature flag `ENABLE_PERSISTENT_STORAGE` in `app.core.config.settings`:

- **`ENABLE_PERSISTENT_STORAGE=true`** (Authoritative V2 Mode):
  - `GET /api/v1/transactions` queries PostgreSQL via `TransactionRepository` with bounded pagination (1–200 items), sorting, and multi-dimensional filters.
  - `GET /api/v1/transactions/{id}` queries PostgreSQL directly.
  - `POST /api/v1/investigations` executes deterministic ML/SHAP/Graph investigation and persists the record and evidence via `InvestigationService.persist_investigation()`.
  - `GET /api/v1/investigations/{id}` checks in-memory cache and falls back to persistent database retrieval.
  - `POST /api/v1/decisions/evaluate` evaluates deterministic policy rules (`ALLOW / REVIEW / HOLD`) and persists the decision record and cryptographic audit log via `DecisionService.evaluate_and_persist()`.

- **`ENABLE_PERSISTENT_STORAGE=false`** (V1 In-Memory Baseline Mode):
  - Standard development and testing mode preserving full compatibility with V1 tests without external database dependencies, utilizing `GraphService` and CSV.
  - When `ENABLE_PERSISTENT_STORAGE=true`, PostgreSQL is authoritative and unknown IDs return explicit 404s without silent fallback to stale CSV.

---

## 3. Migration Procedure & CLI Utility

The migration engine is implemented in `app.services.migration.DataMigrationService` and exposed via `scripts/migrate_v1_to_v2.py`.

### Migration Execution
```bash
# Standard batch migration with default chunk size 5,000
python scripts/migrate_v1_to_v2.py --batch-size 5000

# Dry-run or test migration with row limit
python scripts/migrate_v1_to_v2.py --limit 2000

# Referential integrity verification only
python scripts/migrate_v1_to_v2.py --verify-only
```

### Process Stages
1. **Source Artifact Validation**: Verifies `transactions.csv`, `lightgbm_model.joblib`, `feature_pipeline.joblib`, and `knowledge/` exist.
2. **Model Registry & Policy Setup**: Upserts `mdl_lightgbm_v010` and `pol_2025_1`.
3. **Entity Extraction**: Deduplicates and inserts `CustomerModel`, `AccountModel`, `CardModel`, `DeviceModel`, `IPAddressModel`, and `MerchantModel`.
4. **Network Detection**: Runs `ClusterDetector` on graph neighborhood to discover coordinated fraud syndicates and persist `RiskNetworkModel`.
5. **Vectorized Risk Scoring**: Computes inference probabilities across the dataset using native LightGBM booster.
6. **Transaction Ingestion**: Batch inserts `TransactionModel` with `network_id` linkage, `risk_score`, `risk_tier`, and aligned `decision_action`.
7. **Risk Assessments**: Records immutable point-in-time evaluation records (`RiskAssessmentModel`).
8. **Tree SHAP Risk Signals**: Calculates and persists Top-5 feature attribution factors for policy-targeted transactions.
9. **Referential Integrity Audit**: Executes 11 automated constraint checks.

---

## 4. Idempotency & Restartability

The migration service is **100% idempotent and restartable**:
- Checks existing primary keys (`existing_ids = set(...)`) prior to staging records.
- Re-running the migration against an already populated database executes in zero inserts, zero duplicate key conflicts, and verifies clean referential integrity.
- Transactions are committed atomically at the conclusion of migration, ensuring partial failures roll back cleanly.

---

## 5. Intelligence Persistence Strategies

### Risk Assessments
- Stored in `RiskAssessmentModel` with `id = ras_{tx_id}_v010`.
- Retains `model_id`, `model_version`, `risk_score` in [0.0, 1.0], `risk_tier`, and timestamp.
- Supports multiple model versions evaluating the same transaction over time.

### Tree SHAP Risk Signals
- Stored in `RiskSignalModel` with `id = sig_{assessment_id}_{rank}`.
- **Bounded Deterministic Top-5 Policy**:
  - Targets transactions with elevated risk (`risk_score >= 0.37`), cluster members, or confirmed fraud.
  - Sorts all 18 feature attributions by absolute impact `|impact|` descending.
  - Retains Top-5 features: `feature_name`, `feature_value`, `impact`, `direction` (`INCREASES_RISK`, `DECREASES_RISK`, `NEUTRAL`), and `rank` (1 to 5).
  - Storage is strictly bounded ($O(5)$ per evaluated transaction).

### Graph & Risk Network Persistence
- Coordinated fraud syndicates detected by `ClusterDetector` are persisted into `RiskNetworkModel`.
- Individual member transactions record `transaction.network_id = cluster_id` as an indexed foreign key.
- Avoids storing raw NetworkX edges in the database while preserving full network membership and aggregate risk scores.

---

## 6. Investigation & Decision Lineage

The complete decision lineage is connected via relational foreign keys:
```
Transaction (tx_0001991)
    │
    ├── RiskAssessment (ras_tx_0001991_v010)
    │     └── RiskSignal (sig_ras_tx_0001991_v010_1..5) [Tree SHAP Top-5]
    │
    ├── RiskNetwork (cluster_ded73b2ac8d1) [Coordinated Ring]
    │
    ├── Investigation (inv_tx_0001991)
    │     └── Evidence (ev_*) [Graph collusion, velocity burst, SHAP signals]
    │
    ├── Decision (dec_*) [Deterministic action: HOLD]
    │
    └── AuditEvent (aud_*) [Tamper-evident cryptographic SHA-256 chain]
```

An investigator or regulator can query any decision and trace exact point-in-time evidence, model attributions, and cluster relationships without re-running ML models.

---

## 7. Remaining CSV Dependencies

As of Phase V2-04:
- `ml/data/transactions.csv` serves as the initial source for database migration.
- Used as fallback dataset when `ENABLE_PERSISTENT_STORAGE=false` (e.g. lightweight isolated unit tests).
- Analytical graph construction in `GraphService` initializes from CSV when database persistence is disabled.
- Full retirement of runtime CSV loading for analytical graphs will occur in Phase V2-05 (Transaction & Network Intelligence).
