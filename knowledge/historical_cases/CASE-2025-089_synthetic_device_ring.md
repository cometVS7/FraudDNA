# CASE-2025-089: Synthetic Device Ring with Multi-Account Emulator Collusion

> **DISCLAIMER**: This document is synthetic demonstration data generated solely for the FraudDNA project buildathon. It does not represent real Razorpay customer data, merchant records, or actual fraud incidents.

## 1. Case Metadata
- **Case ID**: CASE-2025-089
- **Incident Period**: October 2025
- **Syndicate Type**: Hardware Device Farm / Device Fingerprint Collusion
- **Impacted Verticals**: Digital Gaming & Prepaid Gift Cards
- **Outcome**: Confirmed Coordinated Syndicate (Resolution: Network Suspended)

## 2. Summary of Incident
A coordinated fraud network operated 40 distinct synthetic customer profiles transacting across digital goods merchants. When evaluated individually, each transaction was kept moderate (INR 2,000 to INR 6,500) and spread over a 72-hour window. Legacy rule engines failed to detect the attacks because individual account velocity remained below standard velocity thresholds.

## 3. FraudDNA Detection & Evidence
- **ML Model Score**: Transactions scored between 0.72 and 0.96 due to elevated 24-hour device velocity (`dev_velocity_24h`).
- **XAI Explanation**: Top SHAP driver was `dev_prior_customers` (impact: +0.42), indicating anomalous multi-customer device sharing.
- **Graph Topology**: All 40 accounts converged onto exactly 4 shared hardware device IDs. The ratio of accounts per device was 10.0x (far exceeding the normal 1:1 or 1:2 ratio).
- **Cluster Classification**: NetworkX connected component identified a 329-transaction cluster with a cluster risk score of 1.0. Flagged as `is_suspicious=true` with primary reason: *"40 customer accounts sharing 4 device(s) (ratio: 10.0x)"*.

## 4. Key Lessons & Precedent
- Device sharing across >= 5 customer accounts is a primary indicator of automated emulator farms.
- Coordinated syndicates can appear benign when looking at customer account age and single amounts; relationship graph clustering is essential to expose the underlying syndicate topology.
