# Security policy

## Reporting a vulnerability

If you find a security vulnerability in devsecops-os (policy, gate,
evidence tooling or template), please do **not** open a public issue.
Report it privately through the project owner's contact channel (the
techdev.fun site), together with:

- a description of the vulnerability and the affected component (file/gate/policy),
- the minimal steps to reproduce it,
- your assessment of the impact.

The project will acknowledge receipt of the report and coordinate a
fix before publishing details. This is an open-source project
maintained by a small team — response times are best effort, not an
SLA.

## Incident handling: suspected exposure of a secret or signing key

If you discover (or suspect) that a secret, token or private key has
been exposed in this repo, in an evidence bundle, or through a gate
run:

1. **Revoke/rotate immediately** — treat it as already exposed: for a
   token, revoke it and issue a new one; for a Cosign signing key,
   generate a new key pair and declare the old fingerprint no longer
   valid. Do not wait to verify "whether it has been exploited yet"
   before revoking.
2. **Remove it from the current tree** and state clearly in
   `CHANGELOG.md` (Security section) that there was an incident + a
   rotation — but understand that deleting a file does **not** delete
   git history or bundles that have already been distributed; step 1
   is the effective measure.
3. **Notify the maintainers** through the private channel above,
   together with: the type of secret, where it was found
   (file/bundle/run), and the suspected time of exposure. Do not send
   the secret value itself in the notification.
4. For a signed evidence bundle containing sensitive data: re-issue a
   cleaned bundle, sign it with the new key, and record the revoked
   key's fingerprint in this file so verifiers can exclude it.

## Scope

- The secrets appearing in `examples/payments-sample/planted/` are
  **fake values deliberately planted** to verify the secret-scanning
  gate — they are not real leaks; please do not report them as
  incidents.
- The Cosign keys used in local verification runs are temporary keys
  generated per run in the output directory (already gitignored), and
  are not used for any release artefact.
