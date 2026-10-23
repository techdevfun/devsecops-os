# devsecops-os

**devsecops-os** is an open-source, vendor-neutral operating layer for
DevSecOps and AI SecOps in regulated organisations. It gives platform
and security teams policy-as-code gates and automated audit-evidence
collection that run on the CI they already have — so a pipeline does
not just block faults, it proves that it did.

> ## Status: PHASE 1 — VERIFIED ON REAL GITHUB ACTIONS
>
> Milestones M1–M5 are complete: a working policy pack (14 policies,
> harness 34/34), 10 CI gates run for real on a sample workload with a
> full result matrix (the clean variant passes everything; the
> planted-fault variant is blocked at exactly 4 gates), evidence
> bundles packaged and verified with a single command — verified in
> both directions (edit 1 byte → verification FAILS), and a golden
> path that has been dogfooded to build a second service.
> **Measurements on real GitHub Actions** (this repository, `main`
> branch): the master workflow ran 3 times — 54, 66 and 58 seconds,
> **median 58 seconds** (acceptance limit: 15 minutes); the planted
> variant was blocked at exactly gates 1, 4, 5 and 8 on CI; the
> golden path built a service from the template and its CI was green
> **on the first run**, 5 minutes 42 seconds total for build + CI
> (limit: 30 minutes); the evidence bundle of each CI run is
> **signed keyless with Cosign via OIDC** and verifies itself inside
> the job. Evidence traceability covers **13 of 14** phase-1
> control-mapping rows; the one partial row belongs to gate 10,
> which is off by design in phase 1. Full release dossier:
> [`release/RELEASE-DOSSIER.md`](release/RELEASE-DOSSIER.md).
> Do not use this repository to claim compliance with any control
> framework: the mappings in these documents are **reference mappings
> for audit preparation, not a compliance certification**.

## Demo (raw capture from a real run)

![Demo: gates running for real on both variants + evidence bundle verification](release/demo/demo-terminal.gif)

The GIF above is a **raw terminal capture**: one real session running
[`release/demo/replay.sh`](release/demo/replay.sh), recorded verbatim
with `script` and rendered frame-by-frame from the raw recording
([`release/demo/demo-raw.typescript`](release/demo/demo-raw.typescript)
plus its timing file) through a VT emulator — no command retyped, no
output line edited, original line wrapping, real terminal colours
and true 1.0× playback speed preserved. Text transcript of the same
session: [`release/demo/demo-transcript.txt`](release/demo/demo-transcript.txt).
What it shows: the gate suite running on both variants of the sample
workload, an evidence bundle verification, and a 1-byte edit that
makes verification FAIL — nothing staged.

## Who hurts, and what this does about it

- **CISOs and platform teams in regulated organisations** hurt in
  three places: (1) every team assembles its security pipeline
  differently, so there is no standard path that reaches the controls
  just by being followed; (2) compliance policy lives in Word/PDF
  documents and is translated by hand into configuration at audit
  time, while evidence is gathered manually from everywhere; (3)
  scanner results from commercial vendors (Harness, GitHub Advanced
  Security, Snyk…) live inside each vendor's closed system — the
  cross-cutting governance and evidence layer for a specific
  regulatory framework still has to be built in-house.
- This system builds exactly that missing part: **policy-as-code that
  lives in the organisation's own repositories** (no third-party
  server holds the data), **CI gates** that block at calibrated
  points, and **audit evidence generated automatically** from the
  pipeline runs themselves — the pipeline does not only block
  faults, it proves that it did.

## Design principles (summary — details in `docs/architecture.md`)

1. **Vendor-neutral by structure**: scanners and connectors speak
   open formats (SARIF, CycloneDX/SPDX, Sigstore, SLSA) — swapping a
   scanning tool must not be allowed to break policy or evidence.
2. **Identity-first**: no long-lived static credentials in the
   pipeline; people go through SSO/OIDC, workloads through OIDC
   federation for short-lived tokens, artefacts are signed (Cosign)
   with SLSA provenance.
3. **Policy at the centre, enforcement at many points**: the same
   control intent compiled down to OPA/Rego, Kyverno and GitHub
   Actions gates.
4. **Evidence is an automatic by-product of operations**, not extra
   work at audit time.
5. **No data leaves the user's infrastructure**: every component runs
   in the organisation's own CI, runners and clusters.

## Control framework mappings

The policy pack ships pre-mapped to the control frameworks below.
These are **reference mappings to support audit preparation — not a
compliance certification**.

| Framework | Policy pack |
|---|---|
| ISO 27001:2022 | `iso-27001-2022` |
| NIST CSF 2.0 / SSDF | `nist-csf-ssdf` |
| PCI DSS 4.0 | `pci-dss-4` |
| APRA CPS 234 | `apra-cps-234` |
| APRA CPS 230 | `apra-cps-230` |
| SOC 2 | `soc-2` |

## Integrations

devsecops-os **integrates with** the platforms an organisation
already runs — GitHub, GitLab, Harness — instead of replacing them,
and it is not one more scanner. Phase 1 implements GitHub Actions;
the GitLab and Jenkins/on-prem integration points are designed, not
yet implemented (see
[`docs/integration-points.md`](docs/integration-points.md)).

## How it compares — honestly

Commercial platforms (Harness, GitHub Advanced Security, Snyk) are
far ahead of this system in scanning depth, enterprise support and
the vendors' own certifications; this system does not claim to
replace them (see the competitor analysis in the project blueprint).
Its wedge is the layer those platforms leave to you: governance and
verifiable audit evidence, in your own infrastructure, across the
tools you already run.

## Repository layout

| Directory | Contents | Milestone |
|---|---|---|
| `docs/` | Reference architecture + guides (including golden paths) | M1 ✓ |
| `examples/payments-sample/` | Sample workload in two variants (clean / planted faults) for verifying the gates | M1 ✓ |
| `examples/checkout-sample/` | Second service, built from the golden path (dogfood) | M5 ✓ |
| `policies/` | Policy packs mapped to control frameworks (14 policies, harness 34/34) | M2 ✓ |
| `gates/` | The 10 CI security gates as reusable workflows + local scripts | M3 ✓ |
| `evidence/` | Evidence collector + bundle with SHA-256 manifest + one-command verify | M4 ✓ |
| `templates/` | Golden-path service templates (`api-service`) | M5 ✓ |
| `release/` | Release dossier, dogfood record, demo, landing content | M5 |

## Try it now (locally — the same scripts CI calls)

```bash
# 1) Fetch the pinned toolset (versions + SHA-256 pinned)
bash gates/local/fetch_tools.sh            # TOOLS_DIR default: ~/workspace/tools

# 2) Run the full verification on both sample-workload variants
bash gates/verification/run_verification.sh all
#    -> result matrix: gates/verification/results.md

# 3) Collect + verify one run's evidence bundle (one verify command)
python3 evidence/bundle_tool.py collect evidence/output/local-clean \
    --run-id local-clean --out-dir evidence/bundles/local-clean
python3 evidence/verify_bundle.py evidence/bundles/local-clean
```

Expected (verified at M3–M5): the `clean` variant passes all 10
gates; the `planted` variant is blocked at exactly gate 1 (secret),
gate 4 (IaC — security group open to the Internet), gate 5
(end-of-life base image) and gate 8 (dependency in CISA KEV), and
is not blocked at any other gate.

## Sample workload

`examples/payments-sample/` contains a minimal payments application
(Python/Starlette API backend, static frontend, Terraform for AWS,
Dockerfile, Kubernetes manifests) in two parallel variants:

- `clean/` — correctly configured; expected to pass every gate.
- `planted/` — exactly 4 deliberate faults planted (fake secret,
  dependency carrying CVE-2026-48710 from CISA KEV, security group
  open to 0.0.0.0/0, old base image frozen since 2022) to verify the
  gates block at the right places. Each fault and its expected gate:
  `examples/payments-sample/planted/PLANTED.md`.

## Documentation

- [Reference architecture](docs/architecture.md)
- [Identity & attestation (identity-first)](docs/identity-and-access.md)
- [Golden paths](docs/golden-paths.md) + [template](templates/README.md)
- [Multiple environments: cloud + on-prem](docs/environments.md)
- [Integration points: GitHub / Harness / GitLab](docs/integration-points.md)
- [Gate verification result matrix](gates/verification/results.md)
- [Release dossier + council score sheet](release/RELEASE-DOSSIER.md)

## Honest limits

- This project makes no claim to be used by, endorsed by, or
  certified for any organisation — it is a blueprint plus a working
  reference implementation, verified on a sample workload.
- Commercial rivals (Harness, GitHub Advanced Security, Snyk) are
  well ahead of this system in scanning depth, enterprise support
  and the vendors' own certifications; this system does not claim to
  replace them (see "How it compares — honestly" above).
- The AI PR Review Gate (the factory's flagship #1) is an *optional*
  gate, **off** by default in phase 1, and is only enabled once
  flagship #1 passes its own separate release gate.

## License

MIT — see `LICENSE`.
