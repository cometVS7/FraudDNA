# FraudDNA — Machine Learning Risk Model Design & Methodology

## 1. Overview
The **FraudDNA Risk Detection Engine** provides transaction-level ML scoring designed specifically to detect both isolated fraud anomalies and coordinated abuse networks where individual payments appear benign in isolation.

---

## 2. Synthetic Dataset Generation (`ml/data/generator.py`)

### Parameters
* **Transactions**: 25,000 records
* **Entities**: 2,000 Customers, 150 Merchants, 3,000 Devices, 3,500 IP Addresses, 2,500 Payment Cards
* **Duration**: 60 days
* **Overall Fraud Rate**: ~4.5%
* **Seed**: `42` (fully reproducible)

### Fraud Ground Truth Typologies
1. **Pattern A — Individual Anomalous Transactions (~35% of fraud)**:
   * Drastic amount deviation (4x–12x customer baseline).
   * High-risk merchant categories (`digital_goods`, `crypto_exchange`, `luxury_goods`, `gaming`).
   * Off-hour execution (01:00 AM – 05:00 AM).
   * Unrecognized device / IP combinations.

2. **Pattern B — Coordinated Abuse Networks (~65% of fraud — Foundation of FraudDNA)**:
   * **Device-Sharing Collusion Rings**: A syndicate operating across 25+ synthetic customer accounts cycling through shared emulator/fraud devices. Individual amounts are modest (₹2,500 – ₹9,500) and appear normal in isolation, but reveal high shared device concentration.
   * **IP Proxy Farm / Velocity Bursts**: Coordinated burst transactions originating from a concentrated proxy IP subnet across multiple accounts within 24–48 hour windows.
   * **Card Testing / Multi-Account Instrument Cycling**: Rapid velocity testing of stolen payment instruments cycled across multiple synthetic customer accounts before high-value checkouts.

3. **Legitimate Traffic (~95.5%)**:
   * Log-normal spending distributions centered around individual customer baselines.
   * Realistic diurnal transaction curves (diurnal peaks at 12–2 PM and 7–10 PM).
   * Stable device, IP, and card associations.

---

## 3. Temporal & Leakage-Free Feature Engineering (`ml/features/engineering.py`)

### Leakage Prevention Invariant
All features are calculated point-in-time using **only information available strictly before or at the current transaction timestamp ($t \le T_{\text{current}}$)**:
* Modifying future records does NOT alter past feature values.
* Categorical encoders and global baseline parameters are fit **strictly on the Training set**.
* Historical state is updated sequentially in chronological order across the timeline.

### Engineered Feature Sets
* **Transaction & Temporal**:
  * `amount`, `log_amount`: Raw and log-transformed transaction value.
  * `customer_account_age_days`: Account maturity.
  * `hour_of_day`, `day_of_week`, `is_night`: Diurnal and weekend signals.
  * `merchant_cat_code`, `payment_method_code`: Encoded transaction metadata.
* **Customer Baseline & Velocity**:
  * `cust_prior_tx_count`: Number of prior transactions by this customer.
  * `cust_prior_mean_amt`: Historical running average amount for this customer.
  * `cust_amount_ratio`: Current amount relative to customer baseline.
  * `cust_hours_since_last`: Elapsed hours since prior customer transaction.
* **Entity Concentration & Multi-Account Velocity**:
  * `dev_prior_customers`: Distinct customer accounts previously observed on this device.
  * `dev_velocity_24h`: Transaction count on this device in the preceding 24 hours.
  * `ip_prior_customers`: Distinct customer accounts previously observed on this IP.
  * `ip_velocity_24h`: Transaction count on this IP in the preceding 24 hours.
  * `card_prior_customers`: Distinct customer accounts previously observed using this card.
  * `card_velocity_24h`: Transaction count on this card in the preceding 24 hours.

---

## 4. Dataset Splitting & Threshold Tuning

### Strict Chronological Split
* **Training Set**: Earliest 70% of chronological transactions.
* **Validation Set**: Next 15% of chronological transactions.
* **Held-Out Test Set**: Final 15% of chronological transactions (strictly untouched during modeling/tuning).

### Threshold Selection
* The decision threshold $\tau^*$ is selected **strictly on the Validation set** by sweeping $\tau \in [0.10, 0.90]$ to maximize the validation $F_1$ score and balance precision against false-positive customer friction.
* The held-out test set is evaluated exactly once using the frozen model and frozen threshold $\tau^*$.

---

## 5. False-Positive Monetary Cost Model

False positives introduce operational overhead, analyst review time, and customer friction.
* **Cost per False Positive**: Configurable baseline assumption ($\text{Cost}_{\text{FP}} = \text{₹}350$).
* **False-Positive Monetary Cost**: $\text{FP Count} \times \text{Cost}_{\text{FP}}$.
* **Net Business Benefit**:
  $$\text{Net Benefit} = \text{Fraud Loss Prevented (₹)} - \text{False-Positive Monetary Cost (₹)}$$
