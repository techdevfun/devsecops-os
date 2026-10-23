# drift_control — material drift past its remediation deadline blocks the reporting period

- **Code**: `devsecops.drift_control` · **Mechanism**: OPA/Rego over a drift
  report (a job comparing declared IaC with actual state, run on a schedule) ·
  **Consuming gate**: Gate 4 (IaC scanning) extended as a scheduled job
  (scheduled drift check) · **Evidence**: `drift-report`.

**Which control** (reference mapping): SOC 2 CC7.1 (standard configuration)
and CC7.2 (detection of unauthorised/undeclared changes); ISO 27001
A.8.9 (configuration management) at reference level.

**Why**: IaC being correct at merge time is not enough — manual changes on the
console gradually move the system away from the approved state, and precisely
deviations of the security group/IAM type are the gateway to incidents. Drift must have an owner, a
ticket, and a deadline — not a list to look at.

**How to fix a violation**: either return the actual state to match the IaC
(re-apply the approved plan), or declare the change into IaC via a PR as a
normal change; acknowledgement must be accompanied by a ticket and is still blocked if
it exceeds the configured SLA (default 7 days for the network/iam/storage groups).
