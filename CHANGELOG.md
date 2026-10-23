# Changelog

All notable changes to devsecops-os are recorded here. The format
follows [Keep a Changelog](https://keepachangelog.com/), and versions
follow [SemVer](https://semver.org/). The project was **publicly
released on 2026-10-23** — phase 1 is available as prerelease
`v1.0.0-phase1` at
[github.com/techdevfun/devsecops-os](https://github.com/techdevfun/devsecops-os).
The milestone entries below record how phase 1 was built, serving
the release dossier (`release/RELEASE-DOSSIER.md`).

## [1.0.0-phase1] — 2026-10-23

Phase 1 **publicly released**: the repository is public at
[github.com/techdevfun/devsecops-os](https://github.com/techdevfun/devsecops-os),
with the phase-1 tree published as prerelease `v1.0.0-phase1`.

### Changed

- Policy pack 1.1.0: all Rego deny messages translated to English; policy-decision evidence records now carry English violations text (decisions, violation counts and schemas unchanged). Evidence bundle tool 1.3.0: all bundle data text (manifest note, ci-log record fields, control-index completeness basis, summary.md) and collect/verify output translated to English. Demo re-recorded raw with fully English output; the previous Vietnamese-output capture was replaced, never edited.

### Added

- **Gate 11 — runtime version floor** (policy pack 1.2.0, new policy `devsecops.runtime_version`): blocks workloads whose declared runtime is below the security floor for its branch. Floors live in pack data (`policies/data/runtime_floors.json`) — first entry: PHP floors for PHP2Shell (CVE-2026-109618 / CVE-2026-109619): 8.2 >= 8.2.35, 8.3 >= 8.3.36, 8.4 >= 8.4.27, 8.5 >= 8.5.12; older branches are denied as end-of-life with no fixed upstream release, and unpinned tags (`latest`, partial versions) are denied as unverifiable. The check reads the Dockerfile `FROM` declaration only, needs neither a KEV listing nor package matching, and passes as not-applicable for runtimes without floor data. Measured gap it closes (2026-10-23): neither gate 5 (Trivy cannot match interpreter CVEs in the source-compiled PHP image) nor gate 8 (the CVEs were absent from CISA KEV catalog 2026.10.21) detected a vulnerable `php:8.3.0` workload; gate 11 denies it and passes `php:8.4.27`.

## [Unreleased] — local completion round M5-A3 (2026-10-22)

### Added

- **Decision/periodic evidence generator set** `evidence/generators.py`
  (standard library only): generates the 4 record types still missing
  from the phase-1 map from real data — `change-record` (from the gate
  results of a run, together with the `change_record` policy decision
  run for real with OPA), `drift-report` (IaC configuration drift
  against the declared baseline, together with the `drift_control`
  decision), `access-review-report` (a review of the permissions of
  the workflows in the tree themselves) and
  `config-baseline-report` (evaluation of the IaC policies against
  the current configuration). The drift baseline is declared at
  `evidence/baselines/payments-sample.tf-normalized.json`.
- Collector (`evidence/bundle_tool.py` 1.2.0): also scans the run's
  `supplementary-records/` directory (schema-checked like a gate
  record) and **self-issues a `ci-log` record** — packaging the run's
  entire log into a deterministic zip artefact with SHA-256; the
  verify step cross-checks the hash declared in the record against
  the artefact in the bundle. Phase-1 map traceability reaches
  **13/14 full rows** (`row-05` remains partial because gate 10 is
  off by design).
- Tests: `evidence/tests/test_generators.py` (15 tests: the
  generators + the collector extension) and
  `gates/local/tests/test_adapters.py` (13 tests for the gate
  adapters, including a real SBOM chain + Cosign signing on a
  minimal workload).
- `CONTRIBUTING.md`, the issue templates in `.github/ISSUE_TEMPLATE/`,
  and the secret-exposure incident handling section in `SECURITY.md`.
- A draft of the dev.to introductory article (`release/devto-article-draft.md`)
  — not yet posted, awaiting the release gate.

### Fixed

- `examples/checkout-sample/.github/workflows/ci.yml`: fixed the
  reusable workflow reference for gate 10 to the correct file name
  `gate-10-ai-pr-review.yml`.
- Traceability in `evidence/README.md` and the landing content updated
  to the 13/14 status.

## [M5-A2] — 2026-10-22

### Added

- Cosign signing for evidence bundles (`collect --sign`): a signature
  over `bundle.sha256`, with verification mandatory when the manifest
  declares a signature (fail-closed, even when the cosign binary is
  missing on the verifying machine).
- Unit tests for `bundle_tool.py` (`evidence/tests/`, 8 tests
  including tampering cases: editing a record + recomputing the hash
  is still caught at the signature layer).

## [M5-A] — 2026-10-22

### Added

- Golden path: `templates/api-service/` and the dogfood workload
  `examples/checkout-sample/` built from the template itself — ran
  the full local pipeline (10 gates + bundle + verify) green on the
  first run.
- Demo (`release/demo/`), landing content, a pre-release risk scan,
  and the release dossier `release/RELEASE-DOSSIER.md`.

### Fixed

- Sample Terraform workload: split the security group's inline rules
  into separate `aws_vpc_security_group_*_rule` resources — no more
  reference cycle, `terraform validate` passes on both variants.
- Removed the artefact collection job using `merge-multiple: true` in
  the CI workflow (it overwrote records with the same name across
  gates).

## [M4] — 2026-10-22

### Added

- Evidence automation: `evidence/bundle_tool.py` — collects records
  from a run, checks the M2 schemas, packages a bundle with a
  SHA-256 manifest, and verifies it with a single command
  (`evidence/verify_bundle.py`).

## [M3] — 2026-10-22

### Added

- 10 CI gates as reusable workflows, sharing the same scripts as the
  local run (`gates/local/gate-NN.sh`) — CI and local are the same
  code. Gate 10 (AI PR review) is OFF by default; the main pipeline
  completes while gate 10 is off.

## [M2] — 2026-10-22

### Added

- Policy pack v1: 14 policies (12 Rego + 2 Kyverno) and 14 evidence
  schemas covering all 14 rows of the phase-1 control map; the
  verification suite `opa test` with 48 tests and the harness that
  checks against the sample workload.

## [M1] — 2026-10-22

### Added

- Repository skeleton: reference architecture documents, static
  sample configuration, and the demo workload
  `examples/payments-sample/` (a clean variant + a variant with 4
  deliberately planted faults, each fault mapping to the gate that
  will block it).
