# Dogfood golden-path record — checkout-sample service (M5-A)

**Run date:** 2026-10-22 (system time UTC; the factory's local
verification machine). **Run by:** worker M5-A. **Environment:**
local — the same `gates/local/gate-*.sh` scripts that GitHub Actions
calls (see `gates/README.md`). The part running on real GitHub
Actions: **UNVERIFIED**, belongs to milestone M5-B.

## How the service was created (following the golden path)

1. Copied the entire `templates/api-service/` tree →
   `examples/checkout-sample/` (not copied from payments-sample).
2. Renamed `example-service` → `checkout-sample` and
   `EXAMPLE_API_KEY` → `CHECKOUT_API_KEY` across all files (source
   code, IaC, manifests, docs).
3. Filled in the service README (purpose, data sensitivity level:
   internal; the operations section reads "not applicable — dogfood
   sample service").
4. Ran the entire local pipeline as in step 6 of
   `templates/README.md`.

## Per-step results (first run, no re-run)

| Step | Result | Duration |
|---|---|---|
| Smoke: install dependencies into a clean venv + run the real backend + call `GET /health` | ✅ `{"status":"ok","service":"checkout-sample"}` | (combined with gate 01 ≈ the first 20 seconds) |
| Gate 01 — secret scanning | ✅ PASS, 0 violations | ~5 seconds |
| Gate 02 — SAST (report-only) | ✅ exit 0, 0 blocking findings | ~17 seconds |
| Gate 03 — SCA (report-only) | ✅ exit 0 | ~10 seconds |
| Gate 04 — IaC | ✅ terraform validate PASS; network_exposure / storage_encryption / iam_least_privilege all PASS | ~33 seconds |
| Gate 05 — container | ✅ base_image PASS | ~12 seconds |
| Gate 06 — SBOM + attestation | ✅ provenance PASS, SBOM signed (the run's temporary key) | ~6 seconds |
| Gate 07 — license | ✅ PASS | <1 second |
| Gate 08 — KEV/EPSS | ✅ dependency_kev PASS | ~2 seconds |
| Gate 09 — pipeline hygiene | ✅ PASS | <1 second |
| Gate 10 — AI PR review | ✅ completed in its default-off state (phase 1) | <1 second |
| Close evidence bundle | ✅ `evidence/bundles/local-checkout-sample/` | <1 second |
| Verify bundle (one command) | ✅ "PASS — all hashes match the manifest, all records match the M2 schema" | <1 second |
| **TOTAL** | **All steps exit 0 on the first run** | **100 seconds** (measured by the running script's wall clock) |

Per-step durations were recovered from output-file timestamps
(error ±2 seconds) because the `bc` utility is not present on the
run machine, so the script's per-step timer recorded 0.00 — the
100-second total is a direct measurement, not an inference. Raw
log: `release/dogfood-run.log`; per-step exit-code table:
`release/dogfood-timings.tsv`.

## Cross-check against blueprint acceptance criterion 5

"Golden path ≤ 30 minutes, CI green on the first run":

- **Local part: MET** — from having the service tree to the bundle
  being verified: ~100 seconds for the pipeline (plus a few minutes
  of manual copy/rename operations following the instructions),
  every step green on the first attempt, no mid-run fixes.
- **Part on real GitHub Actions: UNVERIFIED** — the repo has not
  been published yet; creating a service from the template in a real
  GitHub repo and having CI green on the first Actions run belongs
  to M5-B acceptance after the owner approves the release.

## Honest notes

- Gates 02/03 run in report-only mode by phase-1 default: "green"
  means completed with no findings in the blocking category; for
  checkout-sample, gate 03 still sees the low-level CVEs of the
  pinned dependencies themselves (the same group as the clean
  variant of payments-sample) — recorded in the bundle.
- Checkout-sample shares its dependency/IaC versions with the
  template, so this result verifies the template, not a different
  ecosystem.
