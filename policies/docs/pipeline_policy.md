# pipeline_policy — pipeline hygiene + secure build + OIDC

- **Code**: `devsecops.pipeline_policy` · **Mechanism**: OPA/Rego over a
  normalised workflow (from GitHub Actions YAML) · **Consuming
  gate**: Gate 9 (pipeline hygiene) for the permissions/SHA pinning/OIDC part; Gate 2
  (SAST) + the entire gate suite for the "required gates present" part (ISO rows
  A.8.25–A.8.28 / SSDF PW.7–PW.9) · **Evidence**:
  `pipeline-config-verification` + `policy-decision` (+ `pr-review-report`
  when gate 10 is enabled).

**Which control** (reference mapping): SSDF PW.9 (secure build environment
configuration) and PW.7 (code review — via the requirement that review/SAST gates are
present); ISO 27001 A.8.25–A.8.28 (secure development lifecycle); SOC 2
CC6.1/CC7.1; PCI DSS 4.0 Requirements 6/8 (no static credentials in CI);
CPS 234 (proportionate controls).

**Why**: the pipeline is the highest-value supply-chain attack target
(lesson R9 from flagship #1 about actions being taken over): a third-party action
not pinned by SHA can have its code replaced under the same tag; `write-all` and
long-lived cloud secrets turn a faulty workflow into full infrastructure
privileges. OIDC federation replaces static credentials with short-lived tokens scoped to the
exact repo/branch — the identity-first principle of the architecture.

**How to fix a violation**: declare minimal `permissions` for each
job; pin every third-party action by full commit SHA (with a comment recording the
version); jobs that touch the cloud move to `id-token: write` + a role ARN
via OIDC; enable all gates in the pack's `required_gates`.
