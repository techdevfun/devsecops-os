# license_policy — block if a prohibited license is in the SBOM

- **Code**: `devsecops.license_policy` · **Mechanism**: OPA/Rego over the
  component + license list read from the SBOM · **Consuming gate**: Gate 7
  (license compliance), run after Gate 6 (SBOM) · **Evidence**:
  `sbom` + `policy-decision`.

**Which control** (reference mapping): ISO 27001 A.5.19–A.5.22 (supplier
relationships — terms of use for third-party software); SSDF PS.3/
PW.4 (protect and reuse software securely); SOC 2 CC6.1 (control of
components brought into the system) at reference level.

**Why**: strong copyleft licenses (AGPL/GPL) entering a distributed product
can entail an unintended obligation to disclose source code; a license that
cannot be determined (NOASSERTION) is a legal blind spot that must be reviewed manually.

**How to fix a violation**: replace the component with a permissively licensed alternative,
or request an organisational exception approval and record it in the repo's
`denied_licenses`/allowlist configuration; for a NOASSERTION license, verify
manually from the original project page and then declare it again in the SBOM.
