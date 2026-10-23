# dependency_kev — block dependencies affected by CISA KEV / high EPSS

- **Code**: `devsecops.dependency_kev` · **Mechanism**: OPA/Rego over the
  dependency list + vulnerability data (OSV) merged with the CISA KEV feed and
  EPSS scores (FIRST) · **Consuming gate**: Gate 3 (SCA) generates the data,
  Gate 8 (KEV/EPSS) consumes this policy to decide blocking · **Evidence**:
  `vuln-risk-ranking` + `policy-decision`.

**Which control** (reference mapping): SSDF RV.1/RV.2 (identify and
analyse vulnerabilities); PCI DSS 4.0 Requirement 11 (periodic vulnerability scanning) and
6.3 (keep software supported/patched); ISO 27001 A.8.8 (technical vulnerability
management); CPS 234 (lifecycle vulnerability management).

**Why**: blocking on raw CVSS creates alert fatigue that leads teams to turn off
the gate (lesson from flagship #1). KEV is evidence of real exploitation, EPSS is
the probability of exploitation — blocking on these two signals keeps the true-block rate
high. Planted fault #2 (starlette 1.0.0 / CVE-2026-48710 in KEV) is blocked
by this policy itself.

**How to fix a violation**: upgrade the dependency to the first patched version recorded
in the vulnerability data (starlette ≥ 1.0.1); if an upgrade is not yet possible, open an issue
with a remediation deadline according to the KEV/EPSS level — pack v1 has no silent allowlist
for CVEs that belong to KEV.
