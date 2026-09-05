# POL-002: Risk Escalation Protocol and Analyst SLA Policy

> **DISCLAIMER**: This document is synthetic demonstration data generated solely for the FraudDNA project buildathon. It does not represent real Razorpay operational procedures or escalation guidelines.

## 1. Purpose
This policy establishes deterministic escalation pathways and Service Level Agreements (SLAs) for suspicious transactions, coordinated fraud clusters, and synthetic syndicates.

## 2. Severity Tiers & Escalation Matrix

### Tier 1: Critical Risk (SLA: 15 minutes)
- **Condition**: Transaction ML risk score >= 0.90 OR membership in a confirmed suspicious FraudDNA cluster (`is_suspicious=true` and cluster risk >= 0.90).
- **Escalation Path**: Immediate routing to Level 3 Senior Fraud Specialist and On-call Risk Engineering.
- **Protocol**: Synthesize comprehensive investigation packet (ML risk, Tree SHAP attributions, 2-hop graph neighborhood). Automated systems must flag related accounts sharing identical hardware or payment tokens.

### Tier 2: Elevated Risk (SLA: 1 hour)
- **Condition**: ML risk score between 0.70 and 0.89 OR relationship-level coordination evidence (shared device across >= 3 customers or shared IP across >= 5 customers).
- **Escalation Path**: Assigned to Level 2 Risk Analyst.
- **Protocol**: Analyst reviews XAI top drivers and checks merchant category alignment before policy action.

### Tier 3: Moderate Risk (SLA: 4 hours)
- **Condition**: ML risk score between 0.37 (operating threshold) and 0.69 without syndicate cluster membership.
- **Escalation Path**: Standard queue for routine verification.

## 3. Mandatory Investigation Evidence
Every escalated case must include:
1. Deterministic Investigation ID.
2. Verified Tree SHAP primary feature attributions.
3. Graph coordination indicators (hardware device sharing, proxy subnet flags, card cycling).
4. Relevant historical syndicate precedents retrieved via RAG.
