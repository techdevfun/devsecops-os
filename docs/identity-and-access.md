# Identity & attestation (identity-first)

> **Status (M1)**: design document + static sample configurations
> in `docs/examples/`. Applying these configurations to real
> workflows belongs to M3.

The through-line principle: **no long-lived static credentials** —
no AWS access keys in GitHub secrets, no non-expiring registry
tokens, no shared passwords. Every permission is attached to a
verifiable identity and a short-lived session.

## 1. People: the organisation's SSO/OIDC

- Repos, registries, the evidence store and every target system sit
  behind the organisation's SSO/OIDC (Entra ID, Okta, Keycloak…
  depending on the organisation). This system does not act as an IdP
  itself and does not store user passwords.
- Merge rights into release branches are tied to CODEOWNERS PR
  approval — that approval is simultaneously the change evidence
  for the control frameworks (gathered by the evidence collector
  at M4).

## 2. Workloads: OIDC federation (GitHub Actions → cloud)

- Each workflow declares `permissions: id-token: write` and uses the
  OIDC token issued by GitHub (lifetime measured in minutes, bound
  tightly to repo + branch + environment) to exchange for a
  short-lived cloud IAM role.
- The AWS trust policy conditions must pin to exactly
  `repo:<owner>/<repo>` and, for deploy jobs, to exactly the
  `environment`.
- **[sample configuration]** `docs/examples/github-actions-oidc-aws-trust-policy.json`
  — a sample IAM trust policy for the GitHub OIDC provider, with
  placeholders that must be replaced before use; it also notes
  separating the read (scanning) role from the write (deploy) role.

The accompanying separation-of-duties principle: the role for
*scanning* jobs is read-only; the role for *deploy* jobs writes
only to that service's own resources (least privilege per service —
no single role shared across the whole organisation).

## 3. Artefacts: Cosign signing + SLSA provenance

- Images/artefacts are signed with Cosign, either keyless (the
  workflow's OIDC identity *is* the "key") or via the organisation's
  KMS/HSM if the organisation requires centralised key management.
- Each artefact carries an attached **SLSA provenance
  attestation**: who built it, from which commit, through which
  workflow, with which parameters. The destination layer verifies
  this attestation before accepting it (Kyverno `verifyImages` —
  see the sample configuration).
- **[sample configuration]** `docs/examples/kyverno-verify-images.yaml`
  — a sample ClusterPolicy: only allows images signed keyless by
  the organisation's workflows and carrying a provenance
  attestation; nonconforming images are rejected at admission.
  This file is a static reference sample; it was not verified on a
  real cluster at M1.

## 4. What this design deliberately leaves out

- No PAT/token shared across multiple repos (an operating lesson
  from the factory itself: tokens separated by account/role, scopes
  pinned to the minimum).
- No `pull_request_target` with checkout of PR code in the known
  dangerous pattern; workflows that process fork PRs follow the
  two-workflow pattern (unprivileged build / privileged comment) —
  details when the gates are installed at M3.
- No storage of user secrets anywhere outside the organisation's own
  infrastructure.
