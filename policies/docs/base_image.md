# base_image — block on EOL/frozen base image or `latest` tag

- **Code**: `devsecops.base_image` · **Mechanism**: OPA/Rego over the
  FROM list of the Dockerfile + EOL data bundled in the pack · **Consuming
  gate**: Gate 5 (container scanning) at the pre-check step (before
  scanning for CVEs with Trivy/Grype) · **Evidence**: `policy-decision` +
  the scan report of gate 5 (`sarif-report`).

**Which control** (reference mapping): PCI DSS 4.0 Requirement 6.3 (only
use software that is still supported) and Requirement 11 (periodic scanning); SSDF
PS.3/PW.9; ISO 27001 A.8.8/A.8.9.

**Why**: a base image pinned at an old patch level (planted fault #4:
`python:3.10.4-slim-bullseye`, snapshot 4/2022) never receives
patches — it carries CVEs already fixed elsewhere (OpenSSL 1.1.1n, CPython <3.10.9)
and a base operating system that is no longer supported. The scanner reports CVEs; this policy blocks
the structural risk pattern even before scanning.

**How to fix a violation**: move to an image line that is still maintained
(the clean variant uses `python:3.13-slim`), pin a specific tag or digest; update
the EOL data in the pack when the vendor publishes a new EOL schedule.
