#!/usr/bin/env bash
# Gate 6 — SBOM + attestation: Syft generates a CycloneDX SBOM of the artefact,
# Cosign signs + verifies the SBOM (temporary local key), condensed SLSA provenance
# , and policy devsecops.provenance decides deployability
# . Blocks (exit 1) when provenance DENYs (missing SBOM/signature/provenance
# or a digest mismatch).
source "$(dirname "$0")/lib.sh"
gate_begin 06 sbom-attestation

VARIANT=$(basename "$WORKLOAD")
python3 "$REPO_ROOT/gates/local/adapters/provenance_build.py" \
  --syft "$(command -v syft)" --cosign "$(command -v cosign)" \
  --workload "$WORKLOAD" --variant "$VARIANT" --out "$GATE_OUT" \
  --commit-sha "$COMMIT_SHA" \
  --signing-config "$REPO_ROOT/gates/local/signing-config-offline.json"

opa_decide provenance "$GATE_OUT/provenance.input.json" \
  devsecops.provenance 6
