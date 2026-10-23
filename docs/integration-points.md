# Integration points: GitHub / Harness / GitLab

> **Status (M1)**: design document for the connection points. The
> system's invariant positioning: **integrate with the platforms an
> organisation already has — do not confront them head-on in
> pipeline scanning** (the full competitor analysis is in the
> project blueprint).

## 1. GitHub (the primary platform of phase 1)

- **Actions**: where the gates run (reusable workflows — M3).
- **Code scanning**: every scanner is required to emit SARIF so
  results land in GitHub code scanning — one shared surface for the
  whole team to view findings, independent of the specific scanning
  tool.
- **GitHub's attestation store**: where SLSA provenance for
  artefacts built in Actions is attached (alongside the Cosign
  signature).
- **Native platform features are reused, not rewritten**: Dependabot
  and GitHub secret scanning/push protection are recommended to be
  enabled when the organisation holds the licences; this system's
  gates add the policy + evidence layer on top and do not duplicate
  platform functionality that already exists.

## 2. Harness (optional, two-way)

If the organisation already uses Harness STO:

- **Push direction into Harness**: this system's scan results and
  gate states are pushed into Harness via API/webhook (SARIF/JSON
  formats), so Harness remains their orchestration and
  finding-deduplication point.
- **Independent direction**: this system's policy pack + evidence
  still run, and carry their full value, when there is *no* Harness
  — the governance + evidence layer living in the user's own
  infrastructure is what this system contributes, independent of
  any vendor.
- This system does not replace Harness STO and does not compete in
  scanner orchestration; and conversely, the presence of Harness
  does not remove the reason for an open policy/evidence layer to
  exist.

## 3. GitLab (phase 3 — connection points recorded only, in phase 1)

- The policy pack (OPA/Rego) is the shared asset; when porting to
  GitLab CI (phase 3), only the execution layer (CI templates)
  changes — the policies are not rewritten.
- **Honest limit**: there is no verification on a real GitLab
  instance at this time (even flagship #1's ready-made GitLab sample
  still carries a "not verified live" label). Everything about
  GitLab in the phase-1 documents is design intent, not a
  compatibility commitment.

## 4. Other connection points (design)

- **The organisation's SIEM/SOC**: the evidence store exports
  reports and (phase 2) events into the existing SOC system via
  API/webhook; the phase-2 AI SecOps layer connects onward to
  Vigil/Wazuh/Shuffle under the same "integration partner, not a
  replacement" principle.
- **Issue trackers**: phase 1 uses only the GitHub surface
  (issues/PR comments); Jira/Linear integration is phase 2–3
  roadmap.
