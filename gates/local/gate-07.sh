#!/usr/bin/env bash
# Gate 7 — License compliance over the SBOM (Syft): split out each
# component's licenses from the CycloneDX SBOM, then run policy devsecops.license_policy.
# Blocks (exit 1) when a license is on the pack's denied list.
# Reuses gate 6's SBOM within the same run; when run standalone it
# generates its own SBOM into this gate's directory.
source "$(dirname "$0")/lib.sh"
gate_begin 07 license

SBOM="$OUT_ROOT/gate-06-sbom-attestation/sbom.cdx.json"
if [ ! -f "$SBOM" ]; then
  echo "[gate 07] SBOM from gate 6 not found — generating a local SBOM"
  syft "dir:$WORKLOAD" --output "cyclonedx-json=$GATE_OUT/sbom.cdx.json" \
    --quiet
  SBOM="$GATE_OUT/sbom.cdx.json"
fi

python3 "$REPO_ROOT/gates/local/adapters/syft_license_input.py" \
  --sbom "$SBOM" --out "$GATE_OUT/license.input.json"

opa_decide license_policy "$GATE_OUT/license.input.json" \
  devsecops.license_policy 7
