# Golden Path — paved road templates (M5)

A golden path is a "paved road": a new service that starts from this
template is **secure by default** — 10 CI gates, default policies,
self-generated evidence — without the team having to assemble it
themselves. Original design: section 6 of
[`../docs/blueprint.md`](../docs/blueprint.md), details in
[`../docs/golden-paths.md`](../docs/golden-paths.md).

## Available templates

| Template | Use for | Status |
|---|---|---|
| [`api-service/`](api-service/) | API backend (Python/Starlette) + static frontend + minimal AWS IaC + K8s manifests | Dogfooded at M5 (see below) |

A template includes: a source-code skeleton (backend/frontend), a standard
Dockerfile (maintained base image, non-root, healthcheck), standard IaC
(encryption by default, security groups not open to the Internet on the
application/SSH ports — rules as separate
`aws_vpc_security_group_*_rule` resources), standard K8s manifests
(non-root, drop ALL capabilities, probes, secrets by reference), CI that
calls 10 gates (`.github/workflows/ci.yml`), a secure-by-default
`devsecops-os.yml` configuration, CODEOWNERS and `branch-protection.json`
(reference protection-as-code).

## Create a new service from a template (step by step)

1. **Copy** the entire `api-service/` directory into the new service's
   directory/repo. (When the organization splits out a separate repo:
   keep this tree as is and point `uses:` in the workflow at the system
   repo — see the note at the top of `.github/workflows/ci.yml`.)
2. **Rename**: replace `example-service` with the service name in every
   file (app, IaC, manifests, the service README), and rename the sample
   secret `EXAMPLE_API_KEY` after the real provider.
3. **Fill in the service README**: the "What this service does" section +
   the data sensitivity level; the Operations section
   (deploy/rollback/on-call).
4. **Configuration**: review `devsecops-os.yml` — keep the default
   principle (gate 1 and gate 9 block; the rest are report-only) until
   calibration is complete on the service's own history.
5. **CODEOWNERS**: replace `@your-org/...` with the real teams; apply
   `branch-protection.json` to the main branch using the organization's
   administration tooling.
6. **Run the full pipeline locally before the first PR** (exactly the
   scripts CI will call):
   ```bash
   export REPO_ROOT=<system-repo> WORKLOAD=<service-dir> \
          OUT_ROOT=evidence/output/local-<service> \
          COMMIT_SHA=local-dogfood TOOLS_DIR=~/workspace/tools
   for g in gates/local/gate-*.sh; do bash "$g"; done
   python3 evidence/bundle_tool.py collect "$OUT_ROOT" \
       --run-id local-<service> --out-dir evidence/bundles/local-<service>
   python3 evidence/verify_bundle.py evidence/bundles/local-<service>
   ```
   Expected: every gate PASSes (gate 10 is off by default — the job
   completes without blocking), and verification reports `bundle OK`.
7. **Open the first PR** — on GitHub Actions, the same workflow set must
   be green on the very first run (acceptance criterion 5; real Actions
   verification happens at the M5-B release milestone).

Safety condition R7 (blueprint section 7): the template **itself must
pass the system's own gate suite** — that is why the dogfood below
exists, and every change to a template must re-run the dogfood before it
is accepted.

## Dogfood (local evidence)

At M5, the sample service [`../examples/checkout-sample/`](../examples/checkout-sample/)
was built **from this very template** (not copied from payments-sample)
and run through the full local pipeline: 10 gates, an evidence bundle,
single-command verification. The full record (timings and per-step
results):
[`../release/dogfood-checkout-sample.md`](../release/dogfood-checkout-sample.md).
The "CI green on real GitHub Actions" part belongs to M5-B acceptance —
**UNVERIFIED** at the time of writing.
