# evidence_completeness — a bundle missing required evidence is not done

- **Code**: `devsecops.evidence_completeness` · **Mechanism**: OPA/Rego over the
  manifest of an evidence bundle · **Consuming gate**: the "final gate"
  (blueprint 5.2) run by the M4 collector after all other gates · **Evidence**:
  `control-evidence-index` (periodic index) — this policy is
  the completeness evaluator of the evidence system itself.

**Which control** (reference mapping): ISO 27001 A.8.15–A.8.16 (logging
and monitoring of activities — CI log evidence must be present, with
a hash); APRA CPS 234 (systematic maintenance and testing of controls —
continuous control evidence on a periodic basis); SOC 2 CC7.2 at reference level.

**Why**: a pipeline that blocks faults without leaving evidence means the audit
season still has to be redone by hand — exactly the pain this flagship exists
to remove. "Evidence incomplete" must be a visible state, not
silence treated as passing.

**How to fix a violation**: enable the gate that is missing the corresponding evidence
type; fix the collector if evidence is generated but does not enter
the bundle; do not edit the manifest by hand — the bundle must be regenerated from the run.
