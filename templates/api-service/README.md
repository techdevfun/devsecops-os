# example-service — a service born from the golden path (template README)

> This is the skeleton README of a service using the `api-service` golden
> path. When creating a real service: rename `example-service` in every
> file, remove this skeleton note and fill in the TODO sections.

## What this service does

TODO: a short paragraph — the business purpose, the users, the data it
touches, and the data sensitivity level (public / internal /
confidential). The sensitivity level determines which policy pack
applies (see `devsecops-os.yml`).

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

- All configuration via environment variables (`backend/config.py`).
  Secrets come ONLY from the platform's secret store at deploy time — no
  hard-coded fallback values, no secrets in manifests (k8s uses
  `secretKeyRef`).
- Environment variables: `SERVICE_NAME`, `ENVIRONMENT`,
  `EXAMPLE_API_KEY` (rename after the service's real provider).

## Built-in security controls (from the template)

- The 10 devsecops-os CI gates run on every PR (`.github/workflows/`),
  secure by default: gate 1 (secret) and gate 9 (pipeline hygiene) are in
  **block** mode; the remaining gates are **report-only** until
  calibration is complete on the service's own history (blueprint
  principle: backtest → report-only → enforce).
- Default policy: the phase 1 pack (ISO 27001:2022 / NIST CSF+SSDF /
  PCI DSS 4 reference mapping) via `devsecops-os.yml`.
- Standard Dockerfile: maintained base image, non-root, healthcheck.
- Standard K8s manifests: `runAsNonRoot`, drop ALL capabilities, resource
  limits, probes, secrets by reference.
- Standard IaC: encryption by default, security groups not open to the
  Internet on the application/SSH ports (rules as separate
  `aws_vpc_security_group_*_rule` resources).
- Evidence: every CI run produces an evidence bundle with a SHA-256
  manifest, verified with a single command (`evidence/verify_bundle.py`
  in the system repo).

## Operations

- **Deploy**: TODO — environment, command/pipeline, deployment window.
- **Rollback**: TODO — how to return to the previous version in <15 minutes.
- **On-call / incident contact**: TODO — channel, owner (see CODEOWNERS
  for code ownership).
- **Logs & evidence**: the evidence bundle of each run lives in the CI
  artefacts / the organization's evidence store (configured in
  `devsecops-os.yml`, `evidence` section).
