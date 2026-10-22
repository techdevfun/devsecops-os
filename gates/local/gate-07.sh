#!/usr/bin/env bash
# Gate 7 — License compliance trên SBOM (Syft): tách license của từng
# component từ SBOM CycloneDX rồi chạy policy devsecops.license_policy.
# Chặn (exit 1) khi có license thuộc danh sách cấm của pack.
# Dùng lại SBOM của gate 6 trong cùng lần chạy; nếu chạy độc lập thì
# tự sinh SBOM vào thư mục của gate này.
source "$(dirname "$0")/lib.sh"
gate_begin 07 license

SBOM="$OUT_ROOT/gate-06-sbom-attestation/sbom.cdx.json"
if [ ! -f "$SBOM" ]; then
  echo "[gate 07] không thấy SBOM của gate 6 — tự sinh SBOM cục bộ"
  syft "dir:$WORKLOAD" --output "cyclonedx-json=$GATE_OUT/sbom.cdx.json" \
    --quiet
  SBOM="$GATE_OUT/sbom.cdx.json"
fi

python3 "$REPO_ROOT/gates/local/adapters/syft_license_input.py" \
  --sbom "$SBOM" --out "$GATE_OUT/license.input.json"

opa_decide license_policy "$GATE_OUT/license.input.json" \
  devsecops.license_policy 7
