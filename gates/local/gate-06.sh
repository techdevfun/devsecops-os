#!/usr/bin/env bash
# Gate 6 — SBOM + attestation: Syft sinh SBOM CycloneDX của artefact,
# Cosign ký + xác minh SBOM (khoá cục bộ tạm thời), provenance SLSA rút
# gọn, và policy devsecops.provenance quyết định đủ điều kiện triển
# khai. Chặn (exit 1) khi provenance DENY (thiếu SBOM/chữ ký/provenance
# hoặc digest không khớp).
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
