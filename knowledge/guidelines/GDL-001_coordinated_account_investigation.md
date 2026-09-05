# GDL-001: Coordinated Account and Syndicate Investigation Playbook

> **DISCLAIMER**: This document is synthetic demonstration data generated solely for the FraudDNA project buildathon. It does not represent real Razorpay operational guidelines or proprietary fraud playbooks.

## 1. Introduction
Coordinated fraud syndicates deliberately keep individual transactions below conventional fraud thresholds to evade legacy rule engines. This guideline outlines techniques for uncovering organized collusion across devices, networks, and payment instruments using FraudDNA graph intelligence.

## 2. Syndicate Patterns & Signatures

### Pattern A: Shared Hardware Collusion (Device Rings)
- **Signature**: Multiple distinct customer accounts (e.g. 10 to 50 accounts) authenticating and transacting through a very small cluster of hardware identifiers (1 to 4 devices).
- **Modus Operandi**: Fraudsters use automated device emulators or physical device farms to cycle through stolen identities.
- **Graph Indicator**: Device node degree >= 5 with `connected_customers_count` >= 3.
- **Investigation Step**: Inspect the ego-network around the device node up to radius 2. Identify all connected transactions and examine if timestamps suggest automated batch script execution.

### Pattern B: Distributed Proxy / VPN Farms
- **Signature**: Dozens of accounts operating through a narrow IP subnet or a shared residential proxy pool.
- **Modus Operandi**: Masking geographic origin while testing stolen credit cards or running coordinated promotional abuse.
- **Graph Indicator**: Elevated `ip_prior_customers` and `ip_velocity_24h` combined with diverse customer accounts.

### Pattern C: Card Cycling Networks
- **Signature**: A cluster of virtual or physical payment cards shared across unrelated customer accounts.
- **Graph Indicator**: Card node linked to > 1 distinct customer ID in the FraudDNA graph.

## 3. Investigation Protocol
1. Retrieve transaction details and ML risk score.
2. Examine Tree SHAP attributions: check if network/velocity features (`dev_velocity_24h`, `ip_velocity_24h`, `card_prior_customers`) dominate.
3. Traverse graph relationships: extract 2-hop connected entities and determine cluster membership.
4. If cluster risk score is >= 0.50 and relationship collusion exists, flag as a coordinated syndicate.
