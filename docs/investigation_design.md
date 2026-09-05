# FraudDNA Risk Investigation API Design

## 1. Overview & Architecture

The **Risk Investigation API** (Phase 3) unifies FraudDNA's predictive, structural, and explainability capabilities into a structured, defense-only investigation service.

```text
                               +----------------------------+
                               |  POST /api/v1/investigations |
                               +--------------+-------------+
                                              |
                                              v
                              +-------------------------------+
                              |     InvestigationService      |
                              +---------------+---------------+
                                              |
        +-----------------------+-------------+-------------+-----------------------+
        |                       |                           |                       |
        v                       v                           v                       v
+---------------+       +---------------+           +---------------+       +---------------+
| Phase 1 ML    |       | LightGBM      |           | Phase 2       |       | Phase 2       |
| Risk Scoring  |       | Tree SHAP XAI |           | FraudDNA Graph|       | Cluster Engine|
+-------+-------+       +-------+-------+           +-------+-------+       +-------+-------+
        |                       |                           |                       |
        | [Risk Level]          | [Top Feature Drivers]     | [Shared Entities]     | [Syndicate ID]
        |                       |                           | [Connected Txs]       | [Risk Reason]
        +-----------------------+-------------+-------------+-----------------------+
                                              |
                                              v
                              +-------------------------------+
                              | Deterministic Evidence        |
                              | Synthesis Engine              |
                              +---------------+---------------+
                                              |
                                              v
                              +-------------------------------+
                              |    InvestigationResponse      |
                              +-------------------------------+
```

---

## 2. Core Principles

1. **ML predicts** transaction-level risk.
2. **Graph discovers** hidden multi-account relationships and coordinated collusion.
3. **XAI explains** exact feature attributions via Tree SHAP.
4. **Investigation Service synthesizes** verified evidence without hallucinations or LLMs.
5. **Defense-Only Scope**: The service does not make autonomous financial decisions (no blocking, no refunds).

---

## 3. Request & Response Lifecycle

### Request Flow
1. Client issues `POST /api/v1/investigations` with `{"transaction_id": "<txn_id>"}`.
2. `InvestigationService.investigate(transaction_id)` resolves the transaction record.
3. If the transaction does not exist, raises `TransactionNotFoundError` → HTTP 404.
4. **Deterministic Investigation ID**: Computes `inv_{sha256(transaction_id + ':v1')[:16]}` ensuring full reproducibility.
5. **Risk Level Mapping**: Categorizes raw numerical risk into standard operational tiers:
   - `< 0.30` → `low`
   - `0.30 <= score < 0.70` → `medium`
   - `0.70 <= score < 0.90` → `high`
   - `>= 0.90` → `critical`
6. **XAI / Tree SHAP**: Uses native LightGBM `booster_.predict(X, pred_contrib=True)` to extract exact SHAP values across all 18 model features, ranking top drivers by absolute contribution.
7. **Graph Traversal**:
   - Queries direct neighbors of `transaction:{transaction_id}` (customer, device, IP, card, merchant).
   - Inspects cross-customer sharing on bridge nodes (e.g. device shared across $N > 1$ accounts).
   - Traverses 2 hops to discover connected transactions sharing the same hardware, network, or card.
8. **Cluster Integration**: Retrieves FraudDNA cluster metadata (cluster ID, cluster risk score, suspicious status, primary reason).
9. **Evidence Synthesis**: Builds verified evidence items categorized by source (`risk_model`, `shap`, `frauddna_graph`, `frauddna_cluster`).
10. The result is cached in-memory and returned as `InvestigationResponse`.

---

## 4. API Contract

### POST `/api/v1/investigations`
**Request Payload**:
```json
{
  "transaction_id": "txn_00123"
}
```

**Response Payload (200 OK)**:
```json
{
  "investigation_id": "inv_3a9f81d4e02bc567",
  "transaction_id": "txn_00123",
  "risk_score": 0.9421,
  "risk_level": "critical",
  "risk_factors": [
    {
      "feature": "dev_prior_customers",
      "value": 10,
      "impact": 0.4125,
      "direction": "increases_risk",
      "rank": 1
    },
    {
      "feature": "dev_velocity_24h",
      "value": 14,
      "impact": 0.2814,
      "direction": "increases_risk",
      "rank": 2
    }
  ],
  "related_entities": [
    {
      "entity_type": "device",
      "entity_id": "device:dev_004",
      "relationship": "shared_device_across_customers",
      "metadata": {
        "degree": 40,
        "connected_customers_count": 10,
        "is_shared_across_customers": true
      }
    },
    {
      "entity_type": "customer",
      "entity_id": "customer:cust_0102",
      "relationship": "transacted_by",
      "metadata": {
        "degree": 8,
        "connected_customers_count": 1
      }
    }
  ],
  "related_transactions": [
    {
      "transaction_id": "txn_00119",
      "timestamp": "2026-03-01T12:04:15",
      "amount": 4820.0,
      "risk_score": 0.938,
      "relationship": "shared_device"
    }
  ],
  "cluster": {
    "cluster_id": "cluster_ded73b2ac8d1",
    "cluster_risk_score": 1.0,
    "is_suspicious": true,
    "transaction_count": 329,
    "customer_count": 40,
    "device_count": 4,
    "ip_count": 28,
    "card_count": 42,
    "suspicious_transaction_count": 329,
    "primary_reason": "40 customer accounts sharing 4 device(s) (ratio: 10.0x)."
  },
  "evidence": [
    {
      "evidence_type": "critical_ml_risk",
      "description": "Transaction-level ML fraud risk score is critical (0.9421 >= 0.90).",
      "severity": "critical",
      "source": "risk_model"
    },
    {
      "evidence_type": "xai_primary_risk_driver",
      "description": "Model feature 'dev_prior_customers' significantly increased risk (impact: +0.4125, observed value: 10).",
      "severity": "high",
      "source": "shap"
    },
    {
      "evidence_type": "shared_device_collusion",
      "description": "Hardware device 'device:dev_004' is shared across 10 distinct customer accounts.",
      "severity": "high",
      "source": "frauddna_graph"
    },
    {
      "evidence_type": "suspicious_cluster_membership",
      "description": "Transaction is a member of suspicious FraudDNA cluster 'cluster_ded73b2ac8d1' (score: 1.0000, 329 txs, 40 accounts). Reason: 40 customer accounts sharing 4 device(s) (ratio: 10.0x).",
      "severity": "critical",
      "source": "frauddna_cluster"
    }
  ],
  "status": "completed",
  "generated_at": "2026-09-05T04:54:30.123456"
}
```

### GET `/api/v1/investigations/{investigation_id}`
Retrieves a previously computed investigation by ID. Returns HTTP 404 if not found.

---

## 5. Graceful Degradation & Resilience

| Scenario | Behavior | Status |
| :--- | :--- | :--- |
| **Unknown Transaction** | Returns HTTP 404 (`TransactionNotFoundError`) | N/A |
| **Model/XAI Unavailable** | Omits SHAP factors (`risk_factors = []`), synthesizes remaining graph & cluster evidence | `degraded` |
| **Isolated Transaction (No Cluster)** | Returns `cluster = null`, generates standard baseline evidence | `completed` |
| **Graph Node Missing** | Relies on ML inference with empty related entities | `completed` |

---

## 6. Boundary with Future AI Agent (Phase 5)

- **Phase 3 (This Phase)**: Deterministic, factual risk aggregation. Emits structured evidence objects grounded strictly in ML and graph outputs.
- **Phase 5 (Future LangGraph Agent)**: Will consume this API as a tool to reason over evidence, synthesize narrative explanations, and coordinate policy checks. Phase 3 guarantees clean, typed inputs for the agent without hallucinated data.
