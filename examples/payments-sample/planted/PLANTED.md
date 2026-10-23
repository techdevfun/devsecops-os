# PLANTED — 4 intentionally planted flaws in this variant

The `planted/` variant is identical to `clean/` except for **exactly the 4 flaws** below.
Purpose: to verify that the devsecops-os gate suite blocks at the right places (acceptance
criterion 2 of blueprint section 3.2 — each flaw must be blocked at the expected gate,
and the `clean/` variant must have no false blocks). Whether the gates actually
block them is concluded at M3/M5 when the gates run for real; this document
is an *expectation specification*, not a measurement result.

> **Safety**: every "secret" in this variant is a FAKE example string,
> unusable anywhere. Never plant a real credential into
> a sample workload.

## Flaw 1 — Hardcoded fake secret in code

- **Where**: `backend/config.py` — `PAYMENT_PROVIDER_API_KEY` has a
  hardcoded fallback value of the form `sk_live_FAKENOTREAL…` when the environment variable is not
  set.
- **Nature**: The payment provider's API key is committed directly into
  source code — it leaks with every copy of the repo.
- **Expected blocking gate**: **Gate 1 — Secret scanning** (gitleaks; blueprint
  section 5.1). Gate 1's default blocking condition: detection of a seemingly
  real secret. The planted string uses the live key format (`sk_live_` + a long alphanumeric suffix)
  so the scanner can recognize it by pattern, but contains a clear fake marker
  (`FAKENOTREAL`) for humans.
- **How to remove**: delete the fallback value, read only from the environment — exactly as in
  `clean/backend/config.py`.

## Flaw 2 — Dependency affected by a CVE in CISA KEV

- **Where**: `backend/requirements.txt` — `starlette==1.0.0`.
- **CVE**: **CVE-2026-48710** ("BadHost", GHSA-86qp-5c8j-p5mr) — Starlette
  does not validate the `Host` header when reconstructing `request.url`, allowing
  path injection into the host part and bypassing authorization checks based on
  `request.url.path` (HTTP request smuggling / inconsistent interpretation,
  CWE-444).
- **Affected range**: Starlette `>= 0.8.3, < 1.0.1`; the first patch
  is **1.0.1** (released 2026-05-21). The planted variant uses `1.0.0` — the last version
  still affected. The `clean/` variant uses `1.9.0` (past the patch).
- **Verification sources** (cross-checked on 2026-10-22):
  - CISA Known Exploited Vulnerabilities catalog (the official JSON version,
    catalogVersion 2026.10.21): CVE-2026-48710 is present in the catalog,
    `dateAdded: 2026-09-02`, vendor/product listed as "Kludex / Starlette".
  - GitHub Security Advisory **GHSA-86qp-5c8j-p5mr** (repo Kludex/starlette):
    describes the flaw mechanism and the remediation direction "upgrade to the patched version".
  - Advisory **X41-2026-002** from X41 D-Sec (the discovering party): states
    "Confirmed Affected Versions: starlette >= 0.8.3, < 1.0.1" and
    "Confirmed Patched Versions: starlette 1.0.1".
- **Expected blocking gate**: **Gate 3 — SCA** (osv-scanner/Trivy scanning
  `requirements.txt`/SBOM and reporting CVE-2026-48710) combined with **Gate 8 — EPSS/CISA KEV prioritization**:
  because the CVE is in KEV, gate 8 places it in the first blocking group
  once the report-only phase ends (this is the system's anti-alert-fatigue
  mechanism: it does not block on raw CVSS, it blocks on real exploitation evidence).
- **How to remove**: upgrade `starlette` to `>= 1.0.1` (the clean variant uses `1.9.0`).

## Flaw 3 — Public IaC: security group 0.0.0.0/0

- **Where**: `infra/main.tf` — two separate ingress rule resources additionally
  attached to `aws_security_group.app` (`app_world_app_port` and
  `app_world_ssh`, annotated `PLANTED:` right in the file): the application
  port (`var.app_port`, default 8000) and the SSH port (22) open from
  `0.0.0.0/0`. (From M5, all rules of the workload use the separate
  `aws_vpc_security_group_*_rule` resource form instead of inline rules — the nature of
  the flaw is unchanged.)
- **Nature**: the ECS task should only receive traffic from the ALB (the original rule is still present),
  but the two planted rules allow any Internet address to connect directly to
  the task, bypassing the ALB and every control at the load balancer layer.
- **Expected blocking gate**: **Gate 4 — IaC scanning** (Trivy/Checkov scanning
  Terraform + OPA on the plan): a security group rule opening `0.0.0.0/0` to an
  admin/application port directly violates the system boundary control group
  in the phase 1 packs (for example SOC 2 CC6.6, PCI DSS requirement 2 in the
  mapping table in section 4 of the blueprint).
- **How to remove**: delete the two rule resources annotated `PLANTED:` — the file
  becomes identical to `clean/infra/main.tf`.

## Flaw 4 — Old frozen base image with known vulnerabilities

- **Where**: `Dockerfile` — `FROM python:3.10.4-slim-bullseye`.
- **Nature**: a snapshot frozen in April 2022: CPython 3.10.4 on Debian
  bullseye with OpenSSL 1.1.1n. A tag pinned at patch level means the image
  never receives patches: it carries vulnerabilities that have been fixed elsewhere,
  for example CVE-2022-1292 (OpenSSL 1.1.1n, fixed in 1.1.1o) and
  CVE-2022-45061 (CPython < 3.10.9). Debian bullseye has also reached the end of its
  regular support lifecycle. (The two CVEs cited here belong to *components inside the image*,
  independent of CVE-2026-48710 in flaw 2.)
- **Expected blocking gate**: **Gate 5 — Container scanning** (Trivy/Grype scanning
  the image by layer): expected to report many high/critical vulnerabilities in
  the operating system packages and libraries of the image, in contrast to the current image
  of the `clean/` variant (`python:3.13-slim`).
- **Honesty note**: at M1 there has been no Trivy/Grype run on either
  of these images — the specific vulnerability list and at what threshold gate 5 blocks
  are M3 measurement results, not to be inferred in advance from this document. The local
  run path at M1 is the venv on the machine's Python (see the workload README),
  not building this image.
- **How to remove**: use a current, maintained base image — exactly as in
  `clean/Dockerfile`.

## Summary table of expectations for M3/M5

| # | Planted flaw | File | Expected gate (blueprint section 5) |
|---|---|---|---|
| 1 | Hardcoded fake secret | `backend/config.py` | 1 — Secret scanning |
| 2 | `starlette==1.0.0` affected by CVE-2026-48710 (KEV) | `backend/requirements.txt` | 3 — SCA, escalated by 8 — KEV/EPSS |
| 3 | SG open to `0.0.0.0/0` (app + SSH) | `infra/main.tf` | 4 — IaC scanning |
| 4 | Base image `python:3.10.4-slim-bullseye` (2022) | `Dockerfile` | 5 — Container scanning |

And the mandatory reverse direction: **the `clean/` variant must pass 100% of the gates** — a
single false block on the clean variant also counts as a failure, equal to a single missed
flaw on the planted variant.
