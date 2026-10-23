# Multiple environments: cloud + on-prem

> **Status (M1)**: design document. The cloud reference sample runs
> on the sample workload (`examples/payments-sample/*/infra/` —
> static Terraform AWS files at M1; a real `terraform apply` is out
> of scope for M1).

## 1. Principle

**The same policy pack applies to every environment.** Differences
between cloud and on-prem are declared in per-environment values
files — no policy forks, no rules edited per environment. If a
control cannot be enforced in an environment, that is an *exception
recorded in the evidence*, not a silently weaker copy of the policy.

## 2. Cloud (reference: AWS)

- Infrastructure declared in Terraform (in the sample workload: VPC,
  ECS Fargate, ALB, IAM roles via OIDC federation — see
  `identity-and-access.md`).
- Pipelines run on GitHub-hosted runners or self-hosted runners
  inside the organisation's VPC; workloads receive their identity
  via OIDC, not via access keys.
- The evidence store sits in the organisation's infrastructure (for
  example an S3 bucket with versioning + encryption keys + Object
  Lock if the organisation requires immutability).

## 3. On-prem

- Self-managed Kubernetes + **self-hosted runners** are the phase-1
  on-prem deployment path: the gate suite runs as it does on cloud,
  only the place of execution differs.
- Admission via Kyverno on the self-managed cluster, using the same
  policies compiled from the pack (see the sample
  `docs/examples/kyverno-verify-images.yaml`).
- Air-gapped environments: scanning tools and data feeds (CISA KEV,
  EPSS) must be mirrored in (feeds updated on a schedule through a
  controlled relay point) — this is a design requirement recorded
  at M1; the concrete mirroring mechanism belongs to the gates
  milestone (M3) and its limits will be stated there.

## 4. Permitted differences (values), example

| Item | Cloud (AWS) | On-prem |
|---|---|---|
| Where the gates run | GitHub-hosted or self-hosted runner | Self-hosted runner in the DC |
| Workload identity | GitHub OIDC → IAM role | Cluster OIDC / SPIFFE (later-phase design) |
| Registry | The organisation's ECR | Internal registry (Harbor…) |
| Evidence store | S3 (versioning + SSE) | Equivalent internal object storage |
| KEV/EPSS feeds | Downloaded directly from CISA/FIRST | Via an internal mirror |

Items that must **not** differ by environment: the enabled gate
catalogue, the calibrated blocking thresholds, the evidence format
and the integrity requirement (SHA-256 manifest).
