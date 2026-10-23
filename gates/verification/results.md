# M3 verification results — the CI gate suite run for real on the sample workloads

Generated automatically from `results.json` (the gates' real output) by
`render_results_md.py`. Raw log per gate: `gates/verification/logs/`.
Evidence per run: `evidence/output/local-<variant>/`.

Exit code convention: 0 = pass; 1 = blocked under the blueprint's default
blocking conditions; 2 = infrastructure error (with scan-error.json).

| Gate | Clean — result (exit code, seconds) | Planted — result (exit code, seconds) |
|---|---|---|
| 01 Secret scanning | exit 0, 1.66s — policy pass (0 violations) | exit 1, 1.64s — policy deny (1 violations) |
| 02 SAST | exit 0, 14.05s — 0 finding  — report-only | exit 0, 15.43s — 0 finding  — report-only |
| 03 SCA | exit 0, 17.02s — 4 vulnerabilities: CVE-2026-64847, CVE-2026-63374, CVE-2025-43859, CVE-2026-45409 | exit 0, 14.44s — 9 vulnerabilities: CVE-2026-48710, CVE-2026-48817, CVE-2026-48818, CVE-2026-54282, CVE-2026-54283, CVE-2026-64847, CVE-2026-63374, CVE-2025-43859, CVE-2026-45409 |
| 04 IaC scanning | exit 0, 78.13s — validate=PASS; network_exposure=pass(0); storage_encryption=pass(0); iam_least_privilege=pass(0); trivy-config=8 misconfig | exit 1, 106.82s — validate=PASS; network_exposure=deny(2); storage_encryption=pass(0); iam_least_privilege=pass(0); trivy-config=9 misconfig |
| 05 Container scanning | exit 0, 13.46s — image 170 CVE {'LOW': 61, 'HIGH': 48, 'MEDIUM': 60, 'UNKNOWN': 1}; KEV blocking group=0; base_image=pass(0) | exit 1, 10.4s — image None CVE ; KEV blocking group=0; base_image=deny(2) |
| 06 SBOM + attestation | exit 0, 5.47s — provenance pass; SBOM 3 components, signed=True | exit 0, 4.68s — provenance pass; SBOM 3 components, signed=True |
| 07 License compliance | exit 0, 0.19s — license_policy pass (0 violations) | exit 0, 0.17s — license_policy pass (0 violations) |
| 08 EPSS/CISA KEV | exit 0, 1.43s — dependency_kev pass (0 violations); 174 ranked entries, block: — | exit 1, 6.98s — dependency_kev deny (1 violations); 9 ranked entries, block: ['CVE-2026-48710'] |
| 09 Pipeline hygiene | exit 0, 0.61s — pipeline_policy pass (0 violations) | exit 0, 0.29s — pipeline_policy pass (0 violations) |
| 10 AI PR Review Gate | exit 0, 0.01s — disabled (phase 1 default) | exit 0, 0.01s — disabled (phase 1 default) |

Total sequential run time (local, warm cache): clean 132.03s, planted 160.86s. Slowest gate: 106.82s.

## Check against M3's mandatory expectations

- Clean passes every gate (all exit codes = 0): **PASS**
- Planted is blocked at gate 01 (exit code 1): **PASS**
- Planted is blocked at gate 04 (exit code 1): **PASS**
- Planted is blocked at gate 05 (exit code 1): **PASS**
- Planted is blocked at gate 08 (exit code 1): **PASS**
- Planted is NOT blocked at gate 02 (exit code 0): **PASS**
- Planted is NOT blocked at gate 03 (exit code 0): **PASS**
- Planted is NOT blocked at gate 06 (exit code 0): **PASS**
- Planted is NOT blocked at gate 07 (exit code 0): **PASS**
- Planted is NOT blocked at gate 09 (exit code 0): **PASS**
- Planted is NOT blocked at gate 10 (exit code 0): **PASS**
- Gate 3 planted detects CVE-2026-48710: **PASS**
- Gate 8 planted ranks CVE-2026-48710 in the block group (KEV): **PASS**
- Gate 4 both variants: terraform validate = PASS (clean) / PASS (planted) — after the M5 refactor split the security group rules into separate resources, the reference cycle is gone; details in each run's validate.json. terraform plan JSON still cannot be generated locally because plan needs to call the real AWS API (data source aws_availability_zones).

