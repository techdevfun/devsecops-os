# M3 verification results — the CI gate suite run for real on the sample workloads

Generated automatically from `results.json` (the gates' real output) by
`render_results_md.py`. Raw log per gate: `gates/verification/logs/`.
Evidence per run: `evidence/output/local-<variant>/`.

Exit code convention: 0 = pass; 1 = blocked under the blueprint's default
blocking conditions; 2 = infrastructure error (with scan-error.json).

| Gate | Clean — result (exit code, seconds) | Planted — result (exit code, seconds) |
|---|---|---|
| 01 Secret scanning | exit 0, 6.67s — policy pass (0 violations) | exit 1, 4.88s — policy deny (1 violations) |
| 02 SAST | exit 0, 37.82s — 0 finding  — report-only | exit 0, 25.6s — 0 finding  — report-only |
| 03 SCA | exit 0, 18.63s — 4 vulnerabilities: CVE-2026-64847, CVE-2026-63374, CVE-2025-43859, CVE-2026-45409 | exit 0, 16.81s — 9 vulnerabilities: CVE-2026-48710, CVE-2026-48817, CVE-2026-48818, CVE-2026-54282, CVE-2026-54283, CVE-2026-64847, CVE-2026-63374, CVE-2025-43859, CVE-2026-45409 |
| 04 IaC scanning | exit 0, 49.62s — validate=PASS; network_exposure=pass(0); storage_encryption=pass(0); iam_least_privilege=pass(0); trivy-config=8 misconfig | exit 1, 68.79s — validate=PASS; network_exposure=deny(2); storage_encryption=pass(0); iam_least_privilege=pass(0); trivy-config=9 misconfig |
| 05 Container scanning | exit 0, 13.72s — image 170 CVE {'LOW': 61, 'HIGH': 48, 'MEDIUM': 60, 'UNKNOWN': 1}; KEV blocking group=0; base_image=pass(0) | exit 1, 14.85s — image 621 CVE {'LOW': 184, 'HIGH': 166, 'MEDIUM': 245, 'UNKNOWN': 9, 'CRITICAL': 17}; KEV blocking group=0; base_image=deny(2) |
| 06 SBOM + attestation | exit 0, 8.74s — provenance pass; SBOM 3 components, signed=True | exit 0, 7.5s — provenance pass; SBOM 3 components, signed=True |
| 07 License compliance | exit 0, 0.32s — license_policy pass (0 violations) | exit 0, 0.31s — license_policy pass (0 violations) |
| 08 EPSS/CISA KEV | exit 0, 4.11s — dependency_kev pass (0 violations); 174 ranked entries, block: — | exit 1, 2.15s — dependency_kev deny (1 violations); 630 ranked entries, block: ['CVE-2026-48710', 'CVE-2023-4911', 'CVE-2024-2961', 'CVE-2023-4911', 'CVE-2024-2961', 'CVE-2011-3389', 'CVE-2025-6965', 'CVE-2022-2068', 'CVE-2023-0286', 'CVE-2023-2650', 'CVE-2024-2511', 'CVE-2023-50387', 'CVE-2023-50868', 'CVE-2023-50387', 'CVE-2023-50868', 'CVE-2022-2068', 'CVE-2023-0286', 'CVE-2023-2650', 'CVE-2024-2511'] |
| 09 Pipeline hygiene | exit 0, 1.45s — pipeline_policy pass (0 violations) | exit 0, 0.47s — pipeline_policy pass (0 violations) |
| 10 AI PR Review Gate | exit 0, 0.05s — disabled (phase 1 default) | exit 0, 0.02s — disabled (phase 1 default) |

Total sequential run time (local, warm cache): clean 141.13s, planted 141.38s. Slowest gate: 68.79s.

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

