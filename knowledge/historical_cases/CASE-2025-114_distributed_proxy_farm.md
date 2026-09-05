# CASE-2025-114: Distributed Residential Proxy Farm Executing Coordinated Micro-Transactions

> **DISCLAIMER**: This document is synthetic demonstration data generated solely for the FraudDNA project buildathon. It does not represent real Razorpay customer records, merchant transactions, or real-world fraud incidents.

## 1. Case Metadata
- **Case ID**: CASE-2025-114
- **Incident Period**: November 2025
- **Syndicate Type**: IP Proxy Farm / Distributed Network Abuse
- **Impacted Verticals**: Quick-Commerce & Utility Bill Payments
- **Outcome**: Confirmed Distributed Syndicate (Resolution: Subnet Containment)

## 2. Summary of Incident
A distributed syndicate deployed 49 synthetic customer profiles executing 256 transactions across multiple utility merchants. The perpetrators used a residential proxy network to cycle IP addresses, routing hundreds of requests through a concentrated set of 4 egress IP nodes while spoofing diverse customer identities.

## 3. FraudDNA Detection & Evidence
- **ML Model Score**: ML risk score was elevated across member transactions (average 0.78), driven by extreme network velocity (`ip_velocity_24h` and `ip_prior_customers`).
- **XAI Explanation**: Tree SHAP attributions highlighted `ip_prior_customers` (+0.38) and `ip_velocity_24h` (+0.31) as the primary factors elevating risk.
- **Graph Topology**: 49 customer accounts transacted through 4 common IP addresses. While device identifiers were randomized, the graph revealed a dense bipartite structure connecting all transactions through the proxy IPs.
- **Cluster Classification**: Cluster `cluster_23d785e3a58b` containing 256 transactions was isolated with `cluster_risk_score=1.0` and `is_suspicious=true`. Primary reason: *"49 customer accounts operating via 4 shared IP address(es)"*.

## 4. Key Lessons & Precedent
- Proxy farm syndicates attempt to conceal device identifiers, but shared IP bottlenecks expose the coordinated network.
- When `ip_prior_customers` exceeds 10 with high 24-hour transaction velocity, automated investigations must cross-reference IP subnet ownership.
