# POL-003: Transaction Review and Manual Evaluation Policy

> **DISCLAIMER**: This document is synthetic demonstration data generated solely for the FraudDNA project buildathon. It does not represent real Razorpay transaction review policies.

## 1. Overview
This policy defines the standards for conducting manual reviews of flagged payment transactions within the FraudDNA risk intelligence platform.

## 2. Review Trigger Thresholds
Transactions are submitted to manual review under the following deterministic conditions:
1. **Uncertain ML Prediction**: Model risk score falls in the boundary region (0.35 to 0.55) with conflicting feature drivers.
2. **Velocity Deviation**: Customer transaction velocity in 24 hours exceeds 5x their 30-day historical mean, but single transaction amount is within typical range.
3. **New Entity Linkage**: Established customer transacting from a previously unseen device fingerprint that has an elevated device-velocity score.

## 3. Evaluation Criteria
Analysts conducting reviews must evaluate:
- **Device Fingerprint Authenticity**: Check whether the device ID exhibits signs of emulation or multi-account pooling.
- **Geographic and IP Consistency**: Verify if the IP geolocation aligns with the customer's prior transaction history or indicates proxy/VPN usage.
- **Coordinated Entity Network**: Query the FraudDNA relationship graph up to 2 hops. If the transaction shares an instrument with an account in review, both cases must be consolidated.

## 4. Permitted Decisions
Under deterministic review, analysts can recommend:
- **ALLOW**: Legitimate transaction with transient anomaly explained by verified customer history.
- **REVIEW**: Extended verification required, triggering secondary authentication or document request.
- **HOLD**: Strong coordination evidence or critical risk requiring risk containment.
