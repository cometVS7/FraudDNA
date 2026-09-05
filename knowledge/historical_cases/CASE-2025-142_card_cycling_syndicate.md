# CASE-2025-142: Multi-Account Card Cycling and BIN Attack Syndicate

> **DISCLAIMER**: This document is synthetic demonstration data generated solely for the FraudDNA project buildathon. It does not represent real Razorpay payment records, bank relationships, or actual fraud cases.

## 1. Case Metadata
- **Case ID**: CASE-2025-142
- **Incident Period**: December 2025
- **Syndicate Type**: Payment Card Cycling & Multi-Account Collusion
- **Impacted Verticals**: Online Electronics & High-End Retail
- **Outcome**: Confirmed Financial Syndicate (Resolution: Card Tokens Blocked)

## 2. Summary of Incident
A fraud syndicate utilized batches of compromised virtual credit cards, cycling them rapidly across newly created customer accounts. Individual cards were transacted 1 to 2 times per account to stay below single-card velocity alerts, but were repeatedly linked to multiple distinct customer accounts within hours.

## 3. FraudDNA Detection & Evidence
- **ML Model Score**: High risk (0.84 to 0.98) driven by `card_prior_customers` and `card_velocity_24h`.
- **XAI Explanation**: `card_prior_customers` contributed +0.45 to log-odds risk, with `cust_amount_ratio` indicating abnormal spending relative to customer account history.
- **Graph Topology**: Relationship graph demonstrated bipartite customer-to-card bridges where single cards linked up to 6 different customer IDs.
- **Cluster Classification**: Distinct multi-card component isolated with `CARD_CYCLING` factor flagged in cluster risk analysis.

## 4. Key Lessons & Precedent
- Shared payment instruments across unrelated customer accounts constitute deterministic collusion evidence.
- Card cycling often accompanies credential stuffing; investigation must immediately expand to all transactions sharing the instrument.
