# runtime_version — block declared runtimes below their security floor

- **Code**: `devsecops.runtime_version` · **Mechanism**: OPA/Rego over the
  runtime versions a workload declares in its Dockerfile `FROM` lines,
  compared against the floor table in the pack data file
  (`policies/data/runtime_floors.json`) · **Consuming gate**: Gate 11
  (runtime version floor) · **Evidence**: `policy-decision`.

**Which control** (reference mapping): PCI DSS 4.0 Requirement 6.3
(keep software supported and patched) and 2 (no unsupported software);
ISO 27001 A.8.8 (management of technical vulnerabilities); SSDF RV.1
(identify vulnerabilities) / PW.9 (secure default configurations).

**Why**: some critical vulnerabilities live in the runtime interpreter
itself and are invisible to the pack's other signals. CVE matching
over image packages (Gate 5, Trivy) cannot attach an interpreter CVE
to a runtime that is compiled from source into the image — the
official PHP image is exactly that — and CISA KEV membership
(Gate 8) lags disclosure. Both failure modes were measured on
2026-10-23 with PHP2Shell (CVE-2026-109618 / CVE-2026-109619,
unauthenticated RCE in PHP itself, present since PHP 5.4): the
vulnerable `php:8.3.0` image scan reported neither CVE, and neither
CVE was in the KEV catalog 2026.10.21. A declared-version floor needs
neither signal: the Dockerfile `FROM` line is the runtime that
actually runs, and the floor is data, not code.

**What is blocked**:

- a declared version below the floor of its branch (for PHP: 8.2 →
  8.2.35, 8.3 → 8.3.36, 8.4 → 8.4.27, 8.5 → 8.5.12), with the
  advisory and CVE references named in the violation message;
- a branch older than every branch in the floor table — an
  end-of-life line with no fixed upstream release (PHP ≤ 8.1 for
  PHP2Shell). Distro backports are deliberately **not** guessed: the
  message tells the team to move to a supported branch;
- a tag that is not an exact `x.y.z` version (`latest`, `8.3`) —
  a floating tag cannot be verified against a floor, so it is denied
  as unpinned/unparseable. A suffix after the numeric core
  (`8.3.0-fpm-alpine`) is fine.

**What is not blocked**: runtimes with no entry in the floor table
(for example the Python sample workload) and workloads with no
Dockerfile pass as *not applicable* — the check never invents a
verdict for a runtime it has no floor data for.

**Version source**: the Dockerfile `FROM` declaration. A
`composer.json` platform requirement is a constraint expression, not
the running runtime, so it is deliberately not used as the version
source.

**Updating the floors**: edit `policies/data/runtime_floors.json`
only — add a branch, raise a minimum, or add a whole runtime (image
names + branches). Neither the policy nor the gate script changes.
Record the advisory source and date in the data file when you do.

**How to fix a violation**: rebuild on a base image at or above the
floor for your branch (`php:8.3.36` or later on the 8.3 branch), or
move to a supported branch; then pin the exact `x.y.z` tag in the
Dockerfile so the next run can verify it.
