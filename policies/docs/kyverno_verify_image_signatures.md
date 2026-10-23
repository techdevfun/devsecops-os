# kyverno/verify-image-signatures — only accept signed images + provenance

- **File**: `../kyverno/verify-image-signatures.yaml` (ClusterPolicy
  of type `verifyImages`) · **Mechanism**: Kyverno admission + Sigstore
  (Cosign keyless via GitHub Actions OIDC, checking Rekor) · **Consuming
  gate**: the target-layer enforcement point of Gate 6; on the CI side, the
  corresponding decision is handled by `devsecops.provenance` (Rego) · **Evidence**:
  `provenance-attestation` + `policy-decision`.

**Which control** (reference mapping): SSDF PS.3 (provenance); ISO
27001 A.5.19–A.5.22, A.8.28; SOC 2 CC7.1 at reference level.

**Why**: signature verification at admission is the final checkpoint — even if the registry
or pipeline is compromised, an image without the signature of the organisation's workflow identity
and without a matching SLSA attestation will not run. This file
formalises the M1 pattern at `docs/examples/kyverno-verify-images.yaml`.

**Verification status (stated plainly)**: at M2 it could only be verified with
the Kyverno CLI at parse/structure-application level. The `verifyImages` rule needs a real cluster
+ Rekor/Cosign to run — **not yet runtime-verified at M2**, left
for M3/M5 on an Actions/test cluster environment. Before use
`<OWNER>/<REPO>`, the registry and the image name pattern must be replaced.

**How to fix a violation**: build the image through a pipeline with keyless signing +
attestation; do not loosen the policy to accept images outside the pipeline.
