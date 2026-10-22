#!/usr/bin/env bash
# Gate 5 — Container scanning (Trivy image trên base image khai trong
# Dockerfile) + policy devsecops.base_image (chặn cấu trúc EOL/latest).
# Chặn (exit 1) khi: base_image DENY, hoặc tồn tại CVE CRITICAL có bản
# vá thuộc CISA KEV (điều kiện chặn của blueprint mục 5.1).
# Không có docker daemon trên máy kiểm chứng: trivy kéo image trực tiếp
# từ registry bằng client của nó — không cần docker.
# Kỷ luật "không sạch im lặng": trivy lỗi (DB/registry/dung lượng) ->
# scan-error.json + thoát 2 nếu không có căn cứ chặn độc lập khác.
source "$(dirname "$0")/lib.sh"
gate_begin 05 container

export TRIVY_CACHE_DIR="${TRIVY_CACHE_DIR:-$TOOLS_DIR/trivy-cache}"
IMAGE=$(grep -m1 -E '^\s*FROM\s+' "$WORKLOAD/Dockerfile" | awk '{print $2}')
echo "[gate 05] base image: $IMAGE"

trivy image --scanners vuln --format json \
  --output "$GATE_OUT/trivy-image.json" "$IMAGE" \
  > "$GATE_OUT/trivy-image.log" 2>&1
trivy image --scanners vuln --format sarif \
  --output "$GATE_OUT/trivy-image.sarif" "$IMAGE" >/dev/null 2>&1

scan_ok=1
[ -s "$GATE_OUT/trivy-image.json" ] || scan_ok=0
if [ "$scan_ok" -eq 1 ]; then
  record sarif-report.record.json <<EOF
{"evidence_type": "sarif-report", "format": "SARIF 2.1.0",
 "tool": "trivy", "commit_sha": "$COMMIT_SHA",
 "artifact_uri": "gate-05-container/trivy-image.sarif",
 "sha256": "sha256:$(sha256_of "$GATE_OUT/trivy-image.sarif")"}
EOF
  ensure_feeds
  python3 "$REPO_ROOT/gates/local/adapters/image_block_check.py" \
    --trivy-json "$GATE_OUT/trivy-image.json" --kev "$FEEDS_DIR/kev.json" \
    --out-vulns "$GATE_OUT/image-vulns.json" \
    --out-summary "$GATE_OUT/image-summary.json"
else
  echo "[gate 05] LỖI: trivy image không sinh được kết quả — xem trivy-image.log"
  printf '%s\n' '{"error": "trivy image scan failed", "log": "trivy-image.log"}' \
    > "$GATE_OUT/scan-error.json"
fi

# Input base_image: tái dùng bộ trích FROM của harness M2 (phần trích
# Dockerfile không thuộc phạm vi thay thế của M3) + dữ liệu EOL của pack.
python3 - "$WORKLOAD" "$GATE_OUT" "$REPO_ROOT" <<'PYEOF'
import json, sys
from pathlib import Path
import importlib.util
spec = importlib.util.spec_from_file_location(
    "bwf", str(Path(sys.argv[3]) / "policies/harness/build_workload_fixtures.py"))
bwf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bwf)
doc = bwf.extract_docker(Path(sys.argv[1]))
Path(sys.argv[2], "base-image.input.json").write_text(
    json.dumps(doc, indent=2) + "\n")
print(f"[gate 05] base_image input: {doc['dockerfiles'][0]['images']}")
PYEOF

rc=0
opa_decide base_image "$GATE_OUT/base-image.input.json" \
  devsecops.base_image 5 || rc=1
if [ "$scan_ok" -eq 1 ]; then
  python3 - "$GATE_OUT" <<'PYEOF' || rc=1
import json, sys
s = json.load(open(f"{sys.argv[1]}/image-summary.json"))
if s["blocking_critical_fixed_kev"]:
    print("[gate 05] CHẶN: có CVE CRITICAL có bản vá thuộc CISA KEV")
    raise SystemExit(1)
print("[gate 05] không có CVE thuộc nhóm chặn CRITICAL+fixed+KEV")
PYEOF
elif [ "$rc" -eq 0 ]; then
  echo "[gate 05] thoát 2: quét image lỗi và không có căn cứ chặn độc lập"
  exit 2
else
  echo "[gate 05] CHẶN theo base_image; phần quét CVE của image CHƯA hoàn tất (scan-error.json)"
fi
exit $rc
