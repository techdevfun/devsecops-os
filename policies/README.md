# Policy pack v1 — pack map (M2)

This directory contains the **policy pack v1** of devsecops-os: every row
marked "phase 1" in the mapping table in section 4 of the blueprint has all
three of the following:

1. **runnable policy code** — OPA/Rego (`rego/`), Kyverno (`kyverno/`),
   or a decision policy over scanner output when the nature of the
   control is not a policy (with the reason stated clearly in that
   policy's documentation);
2. **an enforcement mechanism declaration** — which gate in section 5
   of the blueprint consumes the policy and at which step (workflow
   wiring belongs to M3);
3. **an evidence type definition** — JSON schema at
   `evidence-schemas/` (14 types), so the M4 collector can collect
   according to the exact contract in `../evidence/README.md`.

Each policy has its own document in `docs/`: which control, why,
and how to fix a violation (acceptance criterion 6 of the blueprint).

> **All mappings in the pack are reference mappings for audit
> preparation, not a compliance certification** under any framework.
> Pack metadata, cross-reference sources and review date: `pack.yaml`
> (not reviewed for more than 12 months → the pack is marked "stale",
> risk R4 of the blueprint).

## Local verification (re-runnable)

```bash
# OPA: unit test each policy + static fixtures + planted-vs-clean comparison
python3 policies/harness/run_checks.py
# Kyverno: requires the kyverno CLI (~/workspace/tools/kyverno or PATH)
bash policies/harness/kyverno_check.sh
```

- `harness/build_workload_fixtures.py` generates input from **real files**
  of `examples/payments-sample` (SG in `main.tf`, secret in
  `config.py`, pin in `requirements.txt`, FROM in `Dockerfile`)
  — the mandatory M2 comparison: the 4 planted faults of the planted
  variant must give a **deny** verdict, the clean variant must **pass**.
- Real measured results are recorded in the M2 milestone report (not
  recorded in this file to avoid documentation running ahead of
  measurements).

## Pack v1 map: phase 1 row → policy → gate → evidence

Gates are numbered according to section 5 of the blueprint: 1 secret · 2 SAST · 3 SCA ·
4 IaC · 5 container · 6 SBOM+attestation · 7 license · 8 KEV/EPSS ·
9 pipeline hygiene · 10 AI PR Review Gate (OFF by default in phase 1) ·
final: evidence collector (M4).

| # | Blueprint row (framework — control group) | Policy (code/file) | Consuming gate & step | Evidence type |
|---|---|---|---|---|
| 1 | ISO 27001 A.8.25–A.8.28 — secure development lifecycle, secure coding | `devsecops.pipeline_policy` (`rego/pipeline_policy.rego`, "required gates present" part) + `devsecops.secret_findings` | Gates 1/2/3/4 generate data at PR; pipeline_policy decides gate completeness at the aggregation step | `sarif-report`, `pipeline-config-verification`, `policy-decision` |
| 2 | ISO 27001 A.8.9 + A.8.32 — configuration management, change management | `devsecops.change_record` + Kyverno `workload-baseline` | Decision layer on merge into a protected branch; Kyverno enforces configuration at admission | `change-record`, `policy-decision` |
| 3 | ISO 27001 A.8.15–A.8.16 — logging & monitoring | `devsecops.evidence_completeness` (requires the `ci-log` type to carry a hash) | "Final gate" — M4 collector evaluates the bundle manifest after all gates | `ci-log`, `control-evidence-index` |
| 4 | ISO 27001 A.5.19–A.5.22 — supplier relationships | `devsecops.dependency_kev` + `devsecops.license_policy` (over the SBOM) | Gate 3/8 (vulnerabilities) and Gate 7 (license) after Gate 6 generates the SBOM | `sbom`, `vuln-risk-ranking`, `policy-decision` |
| 5 | NIST SSDF PW.7 + PW.9 — code review, secure build configuration | `devsecops.pipeline_policy` (in full: permissions, SHA pinning, OIDC, review/SAST gate completeness) | Gate 9 + Gate 2 at PR; Gate 10 plugs into the same position when flagship #1 passes its publish gate | `pipeline-config-verification`, `pr-review-report` (only when gate 10 is enabled) |
| 6 | NIST SSDF PS.3 + RV.1–RV.2 — artefact/provenance protection, vulnerability analysis | `devsecops.provenance` + `devsecops.dependency_kev` + Kyverno `verify-image-signatures` | Gate 6 generates SBOM/signing/provenance; provenance.rego decides before deployment; Kyverno blocks at target admission | `provenance-attestation`, `sbom`, `vuln-risk-ranking` |
| 7 | NIST CSF PR.DS + ID.RA — data protection, IaC risk assessment | `devsecops.network_exposure` + `devsecops.storage_encryption` | Gate 4 — OPA over the Terraform plan before apply | `iac-assessment`, `policy-decision` |
| 8 | PCI DSS 4.0 Req 6 — secure development + change management (6.5) | `devsecops.change_record` (gate_results covers the entire gate suite) | Decision layer at release; all gates 1–9 feed results into the record | `change-record` |
| 9 | PCI DSS 4.0 Req 2 + Req 8 — no default configurations, identification/MFA | `devsecops.network_exposure` + `devsecops.iam_least_privilege` + `devsecops.pipeline_policy` (OIDC/static secret part) | Gate 4 (IaC: IAM/SG) + Gate 9 (workload identity in CI) | `config-baseline-report`, `access-review-report`, `iac-assessment` |
| 10 | PCI DSS 4.0 Req 11 — periodic security testing | `devsecops.dependency_kev` (runs on a schedule over the current SBOM) | Gate 3/5 run scheduled + Gate 8 ranks/escalates KEV | `vuln-risk-ranking` |
| 11 | APRA CPS 234 — systematic maintenance & testing of controls, continuous evidence | `devsecops.evidence_completeness` (evaluates the evidence index quarterly) + all policies in the pack as decision sources | "Final gate" on a periodic basis — collector aggregates the quarterly evidence package | `control-evidence-index` |
| 12 | SOC 2 CC8.1 — change management | `devsecops.change_record` | Decision layer at merge/release (shared with rows 2/8) | `change-record` |
| 13 | SOC 2 CC7.1–CC7.2 — system operations, detection of unauthorised changes | `devsecops.drift_control` (built on `network_exposure`/`storage_encryption` re-evaluating actual state) | Gate 4 extended as a scheduled drift check | `drift-report` |
| 14 | SOC 2 CC6.1 + CC6.6 — logical access & system boundaries | `devsecops.iam_least_privilege` + `devsecops.network_exposure` + `devsecops.pipeline_policy` (workflow OIDC/least-privilege) | Gate 4 (IAM/SG over the plan) + Gate 9 (workflow permissions), reporting on a periodic basis | `access-review-report`, `config-baseline-report` |

Phase 2 rows (not part of pack v1, recorded to avoid misunderstanding): CPS 234
incident notification to APRA; CPS 230 operational risk / material
suppliers — see the phase 2 roadmap in blueprint section 3.3.

## Policy catalogue

| Policy | Type | File | Documentation |
|---|---|---|---|
| network_exposure | Rego | `rego/network_exposure.rego` | `docs/network_exposure.md` |
| storage_encryption | Rego | `rego/storage_encryption.rego` | `docs/storage_encryption.md` |
| iam_least_privilege | Rego | `rego/iam_least_privilege.rego` | `docs/iam_least_privilege.md` |
| secret_findings | Rego (decision over gitleaks results) | `rego/secret_findings.rego` | `docs/secret_findings.md` |
| dependency_kev | Rego (over OSV + KEV/EPSS) | `rego/dependency_kev.rego` | `docs/dependency_kev.md` |
| license_policy | Rego (over the SBOM) | `rego/license_policy.rego` | `docs/license_policy.md` |
| base_image | Rego (pre-check for container scan) | `rego/base_image.rego` | `docs/base_image.md` |
| pipeline_policy | Rego | `rego/pipeline_policy.rego` | `docs/pipeline_policy.md` |
| change_record | Rego | `rego/change_record.rego` | `docs/change_record.md` |
| provenance | Rego | `rego/provenance.rego` | `docs/provenance.md` |
| evidence_completeness | Rego | `rego/evidence_completeness.rego` | `docs/evidence_completeness.md` |
| drift_control | Rego | `rego/drift_control.rego` | `docs/drift_control.md` |
| workload-baseline | Kyverno ClusterPolicy | `kyverno/workload-baseline.yaml` | `docs/kyverno_workload_baseline.md` |
| verify-image-signatures | Kyverno ClusterPolicy (verifyImages) | `kyverno/verify-image-signatures.yaml` | `docs/kyverno_verify_image_signatures.md` |

Each Rego policy has an accompanying `*_test.rego` file (tested with `opa test`) and
a fixture pair `fixtures/<name>.pass.json` / `.fail.json`. Fixtures for
the Kyverno baseline: a clean workload manifest (pass) and
`fixtures/k8s-bad-pod.yaml` (fail).
