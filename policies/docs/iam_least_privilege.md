# iam_least_privilege — no wildcard on `*`, no AdministratorAccess

- **Code**: `devsecops.iam_least_privilege` · **Mechanism**: OPA/Rego over an
  IAM policy normalised from the Terraform plan · **Consuming gate**: Gate 4
  (IaC) + Gate 9 (pipeline hygiene, for workflow token permissions) · **Evidence**:
  `access-review-report` + `policy-decision`.

**Which control** (reference mapping): SOC 2 CC6.1 (logical access according to
least privilege); PCI DSS 4.0 Requirement 7 (restrict access according to business need)
and Requirement 8 (unique identification); ISO 27001 A.5.15 (access
control); CPS 234 (security controls proportionate to the threat).

**Why**: a policy with `Action: *` on `Resource: *` turns a leaked credential
into full account privileges; this is the most exploited IAM misconfiguration
and also the easiest to catch with a policy.

**How to fix a violation**: narrow the action to exactly the APIs the workload
calls (check CloudTrail/access advisor), attach a specific resource ARN; do not
attach an administrative managed policy to a workload role — create a minimal
dedicated policy and record the reason in the IaC.
