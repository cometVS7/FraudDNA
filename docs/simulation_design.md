# FraudDNA — Risk Simulation & Financial Impact Engine Design

## Architectural Purpose

The **Risk Simulation Engine** provides risk operations teams, finance leaders, and fraud managers with an interactive, deterministic sandbox to model the business and financial impact of threshold adjustments before deploying policy changes to production.

In high-volume payment processing, adjusting fraud thresholds creates trade-offs:
- **Lowering thresholds** captures more fraud (higher recall), but increases false positives and operational review overhead.
- **Raising thresholds** reduces customer friction and manual review costs, but permits more fraudulent losses (higher false negatives).

The Simulation Engine quantifies this precision/recall and financial trade-off using empirical replay over evaluation datasets.

---

## 1. Mathematical & Financial Impact Model

### Classification Metrics

Given a decision threshold $\tau \in (0, 1)$:

$$\hat{y}_i = \begin{cases} 1 & \text{if } \text{score}_i \ge \tau \\ 0 & \text{otherwise} \end{cases}$$

- **True Positives ($TP$)**: $\sum \mathbb{I}(\hat{y}_i = 1 \land y_i = 1)$
- **False Positives ($FP$)**: $\sum \mathbb{I}(\hat{y}_i = 1 \land y_i = 0)$
- **True Negatives ($TN$)**: $\sum \mathbb{I}(\hat{y}_i = 0 \land y_i = 0)$
- **False Negatives ($FN$)**: $\sum \mathbb{I}(\hat{y}_i = 0 \land y_i = 1)$

$$\text{Precision} = \frac{TP}{TP + FP}$$
$$\text{Recall} = \frac{TP}{TP + FN}$$
$$\text{F1} = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$
$$\text{FPR} = \frac{FP}{FP + TN}$$

### Financial Formulations

- **Fraud Prevented Amount**:
  $$\text{fraud\_prevented\_amount} = \sum_{i \in TP} \text{amount}_i$$

- **Fraud Missed Amount**:
  $$\text{fraud\_missed\_amount} = \sum_{i \in FN} \text{amount}_i$$

- **False Positive Cost**:
  $$\text{false\_positive\_cost} = FP \times \text{cost\_per\_false\_positive}$$

- **Expected Loss**:
  $$\text{expected\_loss} = \text{fraud\_missed\_amount} + \text{false\_positive\_cost}$$

- **Net Benefit**:
  $$\text{net\_benefit} = \text{fraud\_prevented\_amount} - \text{false\_positive\_cost}$$

### Operational Capacity

When a secondary `review_threshold` $\tau_r < \tau$ is configured:
- Transactions with $\tau_r \le \text{score}_i < \tau$ route to manual review.
- $\text{review\_volume} = \sum \mathbb{I}(\tau_r \le \text{score}_i < \tau)$
- $\text{capacity\_exceeded} = \text{review\_volume} > \text{review\_capacity}$

---

## 2. Pydantic Schemas

- **`SimulationConfig`**:
  - `fraud_threshold`: float (0.01 to 0.99, default 0.37)
  - `review_threshold`: float | None
  - `cost_per_false_positive`: float (default 350.0 INR)
  - `avg_fraud_loss`: float | None
  - `review_capacity`: int (default 500)

- **`SimulationResult`**:
  - Full metrics including classification counts, rates, financial amounts, review volume, and deterministic run timestamp.

- **`SimulationCompareResponse`**:
  - `comparison_id`: Deterministic hash `cmp:<sha256(configs)>`
  - `results`: Ordered list of `SimulationResult` across thresholds.

---

## 3. REST API Endpoints

- `POST /api/v1/simulations/run` — Run single simulation with custom parameters.
- `POST /api/v1/simulations/compare` — Compare multiple threshold configurations side-by-side.
- `GET /api/v1/dashboard/summary` — Aggregate overview metrics, decision breakdown, and risk distribution.

---

## 4. Frontend Dashboard Integration

1. **Simulation View (`/simulation`)**:
   - Interactive threshold slider (0.05 to 0.95)
   - Real-time recalculation of expected loss and net benefit
   - Precision/Recall/F1 curve visualization via Recharts
   - Multi-threshold comparison table

2. **Evaluation View (`/evaluation`)**:
   - Held-out test set performance (AUC-ROC, Average Precision, F1)
   - Confusion matrix visualization
   - Scenario catch rate breakdown (velocity burst, device reuse, card cycling)
   - Synthetic data transparency label

3. **Overview (`/`)**:
   - Top-level operational KPIs backed by `/api/v1/dashboard/summary`
   - Decision breakdown (ALLOW / REVIEW / HOLD)
   - High-risk transaction quick review links
