# POL-001: Merchant Risk and Transaction Volume Policy

> **DISCLAIMER**: This document is synthetic demonstration data generated solely for the FraudDNA project buildathon. It does not represent real Razorpay policies, operational thresholds, or merchant agreements.

## 1. Purpose & Scope
This policy governs transaction volume thresholds, high-risk merchant categorization, and mandatory verification triggers across all merchants onboarded to the FraudDNA platform.

## 2. Risk Classification Tiers
Merchants are categorized based on their historical dispute ratios, transaction velocity, and business vertical:

* **Tier 1 (Standard Low Risk)**: Established digital goods, utilities, and grocery merchants. Standard automated fraud monitoring applies.
* **Tier 2 (Moderate Risk)**: Electronics, travel, and ticketing. Subject to dynamic velocity checks and card-velocity monitoring.
* **Tier 3 (Elevated Risk)**: Gaming credits, digital gift cards, crypto on-ramps, and high-value jewelry.
  - Transactions above INR 15,000 require enhanced device and IP scrutiny.
  - New customer accounts transacting on Tier 3 merchants are restricted to a maximum 24-hour velocity of 3 transactions.

## 3. High-Risk Merchant Category Triggers
Any transaction meeting the following criteria triggers an automated risk flag:
1. **Category Mismatch**: Transaction amount exceeds 300% of the category average ticket size.
2. **Velocity Spike**: Merchant experiences > 500% increase in hourly transaction count compared to its 30-day baseline.
3. **Cross-Account Device Sharing**: A single device ID initiates transactions across multiple distinct customer accounts at the same merchant within 1 hour.

## 4. Policy Action Requirements
- When ML risk score is >= 0.70 on a Tier 3 merchant transaction, the system records an elevated risk signal and cross-checks the FraudDNA graph for cluster membership.
- If the merchant is flagged as part of an active syndicate, all connected transactions are queued for coordinated review.
