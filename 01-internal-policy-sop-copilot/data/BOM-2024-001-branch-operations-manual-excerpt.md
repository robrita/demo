# BOM-2024-001: Branch Operations Manual – Excerpt

**Document Title:** Branch Operations Manual  
**Policy ID:** BOM-2024-001  
**Owner:** Retail Banking Operations – Head of Branch Operations  
**Version:** 6.0  
**Effective Date:** 2024-01-01  
**Review Date:** 2025-01-01  
**Confidentiality:** Internal Use Only  
**Domain:** Branch Operations

---

*Note: This is an excerpt covering sections relevant to the POC. The full manual is 200+ pages.*

---

## 5. Branch Service Channels and Authority Boundaries

### 5.1 Branch Staff Authority

Branch staff (Tellers, Service Associates, Branch Operations Officers, Branch Managers) are authorized to perform in-person transactions, account servicing, and fee adjustments within their respective authority levels as defined by applicable policies (e.g., POL-2024-001 Fee Waiver Policy).

### 5.2 Contact Center Agent Restrictions

Contact center agents are **not authorized** to process fee waivers or reversals directly in the core banking system. Contact center agents may:

- Acknowledge the customer's request and log the fee waiver request in the Complaint Management System (CMS).
- Escalate the request to the customer's home branch for processing.
- Provide the customer with the branch contact information and expected turnaround time (2 business days).

**Rationale:** Fee waivers require access to the core banking Fee Reversal module (Transaction Code FW-01), which is restricted to branch-based roles with the appropriate system access profile.

### 5.3 Contact Center Agent – Permitted Actions

| Action | Permitted | System |
|---|---|---|
| Account balance inquiry (verified customer) | Yes | CRM |
| Transaction history inquiry (verified customer) | Yes | CRM |
| Card block / temporary hold | Yes | Card Management System |
| Fee waiver / reversal processing | **No** | Core Banking (restricted) |
| Complaint logging | Yes | CMS |
| Fraud escalation | Yes | CMS + Fraud Queue |
| Account information update (address, email) | Yes (Level 2 verification required) | CRM |
| Account closure | **No** | Core Banking (restricted) |

---

*End of Excerpt – BOM-2024-001 v6.0*
