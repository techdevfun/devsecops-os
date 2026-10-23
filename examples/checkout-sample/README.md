# checkout-sample — service generated from the golden path (template README)

> The second sample service of devsecops-os, built **from the golden path
> `templates/api-service`** at M5 (not copied from payments-sample) to
> verify the criterion "a new service onboards via the paved path". The dogfood
> record (time + result of each step of the pipeline):
> [`../../release/dogfood-checkout-sample.md`](../../release/dogfood-checkout-sample.md).

## What this service does

A minimal cart/checkout API for dogfood purposes: `/health` and a
sample resource `items` (in-memory). Data: no real data, no
payment information — sensitivity level **internal**. It exists to prove
the template passes the system's own gate suite on its own (condition R7 of
the blueprint); real checkout business logic is outside phase 1 scope.

## Run locally

```bash
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
PORT=8000 python app.py
curl http://127.0.0.1:8000/health
```

Static frontend: `python3 -m http.server 3000 --directory frontend`.

## Configuration & secrets

- All configuration via environment variables (`backend/config.py`). Secrets ONLY come
  from the platform's secret store at deployment time — no hardcoded fallback
  values, no secrets in manifests (k8s uses `secretKeyRef`).
- Environment variable list: `SERVICE_NAME`, `ENVIRONMENT`,
  `CHECKOUT_API_KEY` (rename to the service's real provider).

## Built-in security controls (from the template)

- The 10 devsecops-os CI gates run on every PR (`.github/workflows/`),
  safe by default: gate 1 (secret) and gate 9 (pipeline hygiene) in
  **blocking** mode; the remaining gates **report-only** until calibration is complete
  on the service's own history (blueprint principle: backtest →
  report-only → enforce).
- Default policy: phase 1 pack (ISO 27001:2022 / NIST CSF+SSDF / PCI DSS 4
  reference mapping) via `devsecops-os.yml`.
- Standard Dockerfile: a currently maintained base image, non-root, healthcheck.
- Standard K8s manifests: `runAsNonRoot`, drop ALL capabilities, resource
  limits, probes, secrets via reference.
- Standard IaC: encryption by default, security group not open to the Internet on
  application/SSH ports (rules in the separate resource form `aws_vpc_security_group_*_rule`).
- Evidence: each CI run produces an evidence bundle with a SHA-256 manifest,
  verified with a single command (`evidence/verify_bundle.py` in the system repo).

## Operations

- **Deploy**: not applicable — dogfood sample service, not really deployed.
- **Rollback**: not applicable (as above).
- **On-call / incident contact**: not applicable (as above); for code ownership see CODEOWNERS.
  CODEOWNERS for code ownership).
- **Logs & evidence**: the evidence bundle of each run is in the
  CI artefact / the organization's evidence store (configured in
  `devsecops-os.yml`, the `evidence` section).
