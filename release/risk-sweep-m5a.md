# Pre-release risk sweep — devsecops-os (M5-A, STANDING RULE 5)

Sweep date: 2026-10-22. Scope: the entire repo tree as of the end of
M5-A. Method: gitleaks (full-tree filesystem scan), manual review by
risk class, cross-checking documents against real run evidence.

*M5-A2 update (2026-10-22): item R1 changed status thanks to Cosign
signing of the evidence bundle — see the R1 row in section 6 and the
amended limitation sentence in section 4. The rest of this sweep is
unchanged.*

## 1. Secrets in the tree / history

- Gitleaks full-tree scan: 16 findings, classified as follows:
  - **1 finding in source code**: a fake Stripe secret in
    `examples/payments-sample/planted/backend/config.py` — the fake
    value is planted DELIBERATELY as verification fault number 1
    (stated clearly in PLANTED.md), not a real credential. Its copies
    in gate 1's output and in the planted variant's bundle are the
    correct consequence of the design (the gate detects and records
    it).
  - **6 `private-key` findings**: the `cosign.key` files in the output
    directories of gate 6 runs (`evidence/output/**`) — temporary
    keys generated per run, in an already gitignored directory.
    **All 3 files DELETED in place**; the gate's tool generates a new
    key on every run, so deleting them has no effect. Re-checked: no
    `.key`/`.pem` file or `PRIVATE KEY` string remains anywhere in
    the tree or in the bundles.
  - **6 `generic-api-key` findings** in `trivy-image.json`: Trivy's
    output when scanning a public base image (the scanner's report
    about the image's contents), not a secret of this project; it
    sits in a gitignored output directory.
- **History**: the current tree is not a git repository (no `.git`
  yet), so no commit history exists to scan — when the repo is
  created at M5-B, the first commit will be exactly this scanned
  tree.
- The bundle contains only `cosign.pub` (the public key) — as
  designed.

## 2. Junk files / temporary artifacts — CLEANED IN PLACE

- Deleted 3 `cosign.key` files (as above) and 3 `__pycache__`
  directories (including 1 created by M5-A's own smoke run inside
  checkout-sample).
- `.gitignore` already covers the right layers: `*.key`/`*.pem`,
  `__pycache__/`, `.terraform/`, tfstate, `evidence/output/`
  (including the tf-sandbox and the logs of each run),
  `evidence/bundles/`, `gates/verification/logs/`. Conversely,
  `gates/verification/results.*` and the demo recording in
  `release/demo/` are kept deliberately as release evidence.
- The output directories still hold ~24MB (`evidence/output`) +
  ~5.9MB (`evidence/bundles`) — all gitignored, none of it enters
  the repo on release; kept in place as verification evidence.

## 3. Licensing

- The repo has a `LICENSE` (MIT) and `SECURITY.md` (added at M5-A —
  missing before that).
- The code in the repo is the project's own original code; external
  tools (gitleaks, Semgrep, Trivy, Syft, Cosign, OPA/conftest,
  Kyverno, osv-scanner, Starlette…) are only *invoked* at runtime,
  their code is not embedded into the repo; tool names are credited
  in the documentation. No third-party asset (image/font/code) has
  been copied into the tree — the font in the demo GIF is the
  system's DejaVu Sans Mono, used only when rendering the image.
- Gate 7 (license compliance) applied to the workload: PASS on both
  variants.

## 4. Overclaims versus evidence — FIXED IN PLACE

- The original README still carried a banner "at milestone M1, no
  policy/gate/evidence yet" — untrue after M2–M4. **Rewritten**: the
  status banner + structure table + try-it section now match the
  M5-A state, with an UNVERIFIED label on the GitHub Actions part.
- `examples/payments-sample/README.md` still said "not yet verified
  with terraform" — **fixed** (fmt + validate PASS from M3/M5; plan
  still needs a real AWS API, stated clearly).
- `docs/golden-paths.md` still had an "M1 status" header — **updated**
  to the M5-A status, keeping the original design section below it.
- `gates/verification/render_results_md.py` hardcoded the phrase
  "security-group cycle error" — **fixed** so the wording follows the
  real validate result; results.md re-rendered: validate=PASS on
  both variants.
- Swept risky wording across the tree ("bank-grade", "compliance
  certification", "guarantee"…): it now only appears in negating /
  honesty-bounding sentences.
- Known limits remain disclosed in the README/landing: evidence
  traceability complete on 6/14 (4 partial, 4 not yet — all of them
  decision/periodic-type evidence that needs real operational data),
  bundle signing only at the temporary local per-run key level (not
  yet keyless OIDC/Rekor — M5-A2 update), terraform plan needs a
  real AWS API.

## 5. Unpinned dependencies

- Gate tools: version + SHA-256 pinned in
  `gates/local/fetch_tools.sh` (hash checked on download).
- GitHub Actions in every workflow: pinned to full commit SHAs
  (gate 9 enforces this — PASS after removing the
  `collect-gate-outputs` job at M5-A).
- Workload/template dependencies: pinned exactly with `==` in
  requirements.txt. Internal Python tooling uses only the standard
  library.
- Terraform provider: `versions.tf` locks `hashicorp/aws ~> 5.x` (a
  compatibility range, not patch-pinned) — **low** severity,
  acceptable for a reference workload; recorded here.

## 6. Remaining (cannot be fixed in place)

| # | Item | Severity | Handling |
|---|---|---|---|
| R1 | ~~Bundle not cryptographically signed (SHA-256 integrity only)~~ — MITIGATED AT M5-A2: bundles closed with `--sign` are Cosign-signed over `bundle.sha256` (a temporary per-run key, generated outside the tree and destroyed immediately; the one-command verify adds a signature check; verified: sign → PASS, change 1 byte → FAIL, swap in another bundle's signature → FAIL, edit plus consistently recompute the hashes → FAIL at the signature layer). Remainder: the signing identity is not tied to OIDC and there is no transparency log (Rekor) — a full trust anchor requires matching the public-key fingerprint against a record outside the bundle, or keyless signing on CI | Low (remainder) | The remainder belongs to M5-B (keyless/OIDC signing on CI) — M5-B is frozen per the owner's 2026-10-22 decision; the current limitation is disclosed in `evidence/README.md` + the landing. |
| R2 | ~~4/14 evidence traceability rows not auto-generated (decision/periodic)~~ — CLOSED AT M5-A3: all 4 types (`change-record`, `drift-report`, `access-review-report`, `config-baseline-report`) + `ci-log` have automatic generators running on the run's/tree's real data (`evidence/generators.py` + the release ci-log collector with cross-hash checking at verify); proven by the `local-clean-m5a3` bundle verifying PASS, traceability **13/14 complete**. Remainder (not a technical fault): the full audit value of decision records still needs real operational data (a real PR approval — the local change-record is correctly DENIED by policy because there is no approval) and row-05 (`pr-review-report`) is still partial because gate 10 is OFF by phase-1 design | Low (remainder) | Disclosed in `evidence/README.md` + the landing (M5-A3 update). |
| R6 (new, M5-A3) | Final full-tree gitleaks sweep at the end of the M5-A3 round: after deleting 2 leftover `cosign.key` files in the output directories of old runs and fixing the sample secret string in the test fixture (avoiding the `sk_live_…` pattern even though it is fake), the remaining 12 findings are all in known categories: the planted variant's pre-planted fake secret (with its own gate 1 report in the artefact) and generic-api-key noise in Trivy's JSON output in the run directory (all of `evidence/output/` is gitignored) | Low | No findings remain in the tree's source code/documentation. Moving gate 6 to keyless belongs to R5. |
| R3 | terraform plan JSON cannot be generated locally (needs a real AWS API) | Low | The gate is designed around conftest parse + validate; the real reason is stated clearly. |
| R4 | GitHub Actions workflow time + golden path on real CI not yet measured | High (for the release gate) | UNVERIFIED — belongs to M5-B after the owner approves repo creation. |
| R5 | Gate 6's temporary Cosign key sits in each run's output directory (albeit gitignored) | Low | Existing copies deleted; in the long term it should move to keyless/OIDC — recorded, does not block phase 1. |

Sweep conclusion: no risk remains in the release-blocking category
at the local layer beyond M5-B's UNVERIFIED items (R4) — the release
gate is decided by the council score sheet in `RELEASE-DOSSIER.md`.
