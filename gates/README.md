# CI security gates — M3 (installed, locally verified)

The blueprint section 5 suite of 10 gates was installed at M3 and verified
with real tools on both sample workload variants. Measured results:
`gates/verification/results.md` (raw logs: `gates/verification/logs/`).
Gate 11 (runtime version floor) was added on 2026-10-23 with policy pack
1.2.0 — it closes a measured blind spot of gates 5/8 (see the gate 11 row
below and `policies/docs/runtime_version.md`).

## Structure — why the gates live in two places

GitHub only loads reusable workflows from the repo's `.github/workflows/`,
so the 12 YAML files (11 gates + `all-gates.yml`) live there. But the real
runnable code of each gate is a SINGLE script `gates/local/gate-NN.sh` — the workflow
only checks out, downloads the pinned tools (version + sha256 in
`gates/local/fetch_tools.sh`), then calls exactly that script. That way the run
on GitHub and the locally verified run are **the same code**, with
no "CI one way, dev machine another".

| Directory/file | Role |
|---|---|
| `.github/workflows/gate-NN-*.yml` | Reusable workflow (`workflow_call`) for each gate |
| `.github/workflows/all-gates.yml` | Umbrella workflow: runs all 11 gates on one workload variant + collects artefacts (the real collector is M4) |
| `gates/local/gate-NN.sh` | The gate's real runnable code (shared by CI + local runs) |
| `gates/local/lib.sh` | Shared library: run identification, evidence record writing, OPA invocation |
| `gates/local/adapters/*.py` | Converters from scanner output → policy pack input / evidence records |
| `gates/local/fetch_tools.sh` | Downloads version-pinned tools + verifies sha256 |
| `gates/verification/` | M3 local verification runner + results |

## The 11 gates ↔ tools ↔ policies ↔ evidence

| # | Gate | Real tool (version at verification time) | Pack policy (M2) | Evidence produced |
|---|---|---|---|---|
| 1 | Secret scanning | gitleaks 8.30.1 | `devsecops.secret_findings` | SARIF + `policy-decision` |
| 2 | SAST | Semgrep 1.182.1 (p/security-audit, p/python) — report-only | — (no policy yet in phase 1) | SARIF + summary by severity |
| 3 | SCA | osv-scanner 2.7.0 | (detection; the decision is at gate 8) | SARIF + normalized vulnerability list |
| 4 | IaC scanning | Terraform 1.17.0 (validate) + Trivy 0.76.1 (config) + OPA 1.21.3 over conftest 0.71.1's HCL2 parse | `network_exposure`, `storage_encryption`, `iam_least_privilege` | SARIF + `policy-decision` ×3 + `iac-assessment` |
| 5 | Container scanning | Trivy 0.76.1 (image) + KEV cross-check | `devsecops.base_image` | SARIF + `policy-decision` + CVE summary |
| 6 | SBOM + attestation | Syft 1.55.0 + Cosign 3.1.4 | `devsecops.provenance` | `sbom` (CycloneDX, signed bundle) + `provenance-attestation` + `policy-decision` |
| 7 | License compliance | Read from the CycloneDX SBOM | `devsecops.license_policy` | `policy-decision` |
| 8 | EPSS/CISA KEV | CISA KEV feed + FIRST EPSS downloaded at run time | `devsecops.dependency_kev` | `vuln-risk-ranking` + `policy-decision` |
| 9 | Pipeline hygiene | Scans the repo's own `.github/workflows/` | `devsecops.pipeline_policy` | `pipeline-config-verification` + `policy-decision` |
| 10 | AI PR Review Gate | Flagship #1 — **not published yet** | (when enabled: `pr-review-report`) | Off: only records the state, produces no evidence |
| 11 | Runtime version floor | Declared-version check (no scanner): Dockerfile `FROM` versions vs the pack floor data | `devsecops.runtime_version` | `policy-decision` |

Gate 10 is **OFF by default** in phase 1 (the `enabled`/`enable_ai_pr_review` inputs
default to `false`, and the `ENABLE_AI_PR_REVIEW` variable for local runs): the wiring at
the PR layer is in place, the umbrella workflow runs end to end while it is off, and phase-1
acceptance does not depend on it. It is only enabled once flagship #1 passes its own
publish gate.

## Running locally

```bash
# run the full verification (both variants, with timing):
bash gates/verification/run_verification.sh

# run a single gate:
REPO_ROOT=$PWD WORKLOAD=$PWD/examples/payments-sample/planted \
OUT_ROOT=$PWD/evidence/output/thu COMMIT_SHA=thu-1 \
  bash gates/local/gate-01.sh
```

Gate exit codes: `0` = pass (does not block), `1` = **blocked** under the blueprint's
default blocking conditions, `2` = infrastructure error / incomplete scan
(with `scan-error.json` — never disguised as "clean").
Each run's evidence lives in `evidence/output/<run>/gate-NN-*/`
per M4's directory contract (see `evidence/README.md`); the M4 collector
will gather the `*.record.json` files + artefacts there.

## Operating principles (inheriting flagship #1's lessons)

- **Report-only by default when first installed** at an adopting organization (the
  `gates.<id>.mode` setting in `docs/examples/devsecops-os.sample.yml`);
  switching to blocking only happens after calibration runs over that repo's own
  history. The M3 verification run itself used the blueprint's default blocking conditions
  to prove the blocking capability.
- Every truncated scan / data error must **fail loudly** — gate 3 retries
  when osv-scanner hits a resolution error and exits 2 if it still cannot scan
  any dependency; gate 5 writes `scan-error.json` when trivy errors.
- Each gate has a controlled bypass, and every use of a bypass is recorded
  in the evidence (gate 1's allowlist has an expiry; pack exceptions
  have an expiry date in the `change_record` policy).
- The evidence collector is the "final gate" (M4): missing mandatory evidence
  from enabled gates → the run is flagged `evidence incomplete`.

## Known limitations (measured at M3, not hidden)

- **Terraform plan JSON could not be generated yet**: the sample workload has a real circular
  reference error between two security groups (`aws_security_group.alb` ↔
  `aws_security_group.app` referencing each other in inline rules), so
  both `terraform validate` and `plan` fail on BOTH variants.
  Gate 4 therefore uses the standard HCL2 parse (`conftest parse`) as the input
  for the 3 infrastructure policies — replacing the M2 harness's regex extractor —
  and records the validate result separately in the evidence. Getting plan JSON
  requires refactoring the workload to separate `aws_vpc_security_group_*_rule` resources:
  left for M5 to decide (see `gates/verification/results.md`).
- On GitHub Actions each job runs independently: gates 7/8 regenerate the
  SBOM / rescan dependencies when they do not find gate 6/3's output in
  the same job (chained local runs reuse the existing output).
- Gate 6 locally reaches SLSA Build L1 (regular builder + temporary signing
  key); higher levels via `slsa-github-generator` are only available when running on
  GitHub Actions — deployed at M5.
- Kyverno (the pack's 2 cluster-side policies) is not part of these 10 CI gates;
  they apply at the cluster admission layer per the architecture documentation.
