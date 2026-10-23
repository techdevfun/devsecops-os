# Golden paths

> **Status (updated at release)**: a real template exists at
> `templates/api-service/` and was dogfooded on site with a second
> service, `examples/checkout-sample/` — the full local pipeline
> (10 gates + evidence bundle + verify) was green on the first run,
> ~100 seconds total (record:
> `release/dogfood-checkout-sample.md`). The "CI green on real
> GitHub Actions" part of the acceptance criteria has since also
> been **verified** at release milestone M5-B: the golden path was
> green on its first CI run, 5 minutes 42 seconds for build + CI.
> The text below is the original design document (M1), kept
> unchanged as the reference baseline.

## 1. The idea

A golden path is a "pre-paved trail": a template repo per service
type (API, worker, frontend) such that, when a team follows it, the
security controls are **there by default** instead of having to be
assembled by hand. Compliance becomes the path of least friction,
not extra effort.

## 2. What a golden-path template contains (design)

- Minimal skeleton source code for the service type (for example a
  Python API like the sample workload
  `examples/payments-sample/clean/` — this workload is itself the
  reference seed for the API template at M5).
- A standard `Dockerfile`: current base image, runs as non-root,
  has a healthcheck, versions pinned.
- Standard Kubernetes manifests: resource requests/limits, probes,
  minimal security context (non-root, no privilege escalation).
- A CI pipeline with the system's full gate suite installed (M3) in
  a safe default mode: report-only on first install, switching to
  blocking after calibration (see `gates/README.md`).
- The system's configuration file (`devsecops-os.yml` — sample in
  `docs/examples/devsecops-os.sample.yml`): policy pack selection,
  gate thresholds, evidence store location.
- `CODEOWNERS`, branch protection as code, a correct `.gitignore`
  (no committed secrets/tfstate).
- A service README with an operations section ready-made: how to run
  locally, environment variables, where to see the service's own
  evidence.

## 3. Lifecycle

1. Create the service from the template (GitHub template repository
   / the organisation's repo-generation tooling).
2. CI runs for the first time: the expectation is **green
   immediately** on the skeleton code (this is a measurable phase-1
   acceptance criterion, not a slogan).
3. The team develops features on that trail; when they need to step
   off it (disable a gate, loosen a policy), that action is a
   reviewed configuration change that leaves a trace in the evidence
   — not forbidden, but never silent.

## 4. Safety of the template itself (blueprint risk R7)

A faulty template (excess permissions, weak configuration) would
multiply that fault across every service created from it. So when
M5 implemented it:

- The template must **pass the system's own gate suite** in this
  repo's CI (mandatory dogfooding).
- Every third-party action used in the template must be pinned to a
  full commit SHA.
- A dangerous configuration discovered as already released in the
  template → fix + patch release + a public note in the CHANGELOG
  within 48 hours (a stop condition recorded in the blueprint risk
  register).
