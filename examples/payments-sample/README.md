# payments-sample — sample workload of devsecops-os (M1)

A minimal, self-contained payment application used as a **verification workload** for
the devsecops-os gate suite: the `clean/` variant is expected to pass every gate, the `planted/`
variant plants exactly 4 intentional flaws expected to be blocked at the corresponding gate (acceptance
criterion 2 of blueprint section 3.2 — the block/no-block conclusion belongs to M3/M5 when
the gates run for real; at M1 the workload only needs to *exist as designed and be runnable*).

## Structure of each variant

```
clean/  (planted/ is analogous)
├── backend/     Python API (Starlette + uvicorn): /health, GET/POST /api/payments
├── frontend/    Minimal static page (index.html + app.js + style.css)
├── infra/       Minimal AWS Terraform: VPC + ALB + ECS Fargate + IAM + S3
├── Dockerfile   Backend packaging
└── k8s/         Minimal Kubernetes manifests (Deployment + Service)
```

## Run the backend locally (both variants)

```bash
cd clean/backend            # or planted/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
PORT=8000 python app.py
```

Quick check:

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok","service":"payments-sample"}

curl http://127.0.0.1:8000/api/payments
curl -X POST http://127.0.0.1:8000/api/payments \
  -H 'Content-Type: application/json' \
  -d '{"amount": 50000, "currency": "VND", "description": "Invoice INV-1002"}'
```

Frontend: open `frontend/index.html` with any static server (for example
`python3 -m http.server 3000 --directory frontend`); the page calls the API at
`http://localhost:8000` per the default configuration in `app.js` (the backend has
CORS enabled for the localhost origin to serve the local demo; when deployed behind the ALB,
the frontend and API share the same origin — see the note in `app.js`).

## Infra / Docker / Kubernetes at M1

- `infra/*.tf` must not be `terraform apply`-ed to a real AWS account
  (the sample workload only serves gate verification). From M3 they are
  verified with real terraform in gate 4; from M5 (the security group rules refactored
  into separate resources) `terraform fmt -check` and
  `terraform validate` both PASS on both variants — the results of each
  run are in `gates/verification/results.md` and `validate.json` of
  gate 4. `terraform plan` still needs the real AWS API (the availability zones
  data source) so it cannot yet be generated in the verification environment.
- `Dockerfile` and `k8s/` are deployment artifacts for the container gate (M3) and
  manifest checks (M2/M3) to scan at later milestones; the runnable path at M1 is
  the local venv above.

## Differences between the two variants

Only exactly 4 points — all of them are in `planted/PLANTED.md`:

| # | Difference | File (planted variant) |
|---|---|---|
| 1 | Hardcoded fake secret as a fallback value | `backend/config.py` |
| 2 | `starlette==1.0.0` — affected by CVE-2026-48710 (CISA KEV) | `backend/requirements.txt` |
| 3 | Security group open to `0.0.0.0/0` (app port + SSH) | `infra/main.tf` |
| 4 | Base image frozen from 2022 (`python:3.10.4-slim-bullseye`) | `Dockerfile` |

Every other file is identical to the `clean/` variant so that the comparison at M3/M5 stays clean:
if the gates block the planted variant, it can only be because of these 4 flaws.
