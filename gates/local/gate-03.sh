#!/usr/bin/env bash
# Gate 3 — SCA (osv-scanner trên lockfile/requirements của workload).
# Gate này PHÁT HIỆN; quyết định chặn thuộc gate 8 (KEV/EPSS) theo
# blueprint — tránh chặn theo CVSS thô.
# Kỷ luật "không sạch im lặng": nếu osv-scanner lỗi phân giải (mạng/API)
# khiến 0 dependency được quét trong khi workload có requirements.txt,
# gate thử lại tối đa 3 lần; vẫn lỗi -> thoát 2 (lỗi hạ tầng) kèm
# scan-error.json, KHÔNG BAO GIỜ báo 0 lỗ hổng giả.
source "$(dirname "$0")/lib.sh"
gate_begin 03 sca

run_osv() {
  osv-scanner scan source --recursive --format json \
    --output-file "$GATE_OUT/osv.json" "$WORKLOAD" \
    > "$GATE_OUT/osv.log" 2>&1
  echo $?
}

attempt=1
while : ; do
  rc=$(run_osv)
  ndeps=$(python3 - "$GATE_OUT/osv.json" <<'PYEOF'
import json, sys
try:
    doc = json.load(open(sys.argv[1]))
except Exception:
    print(0); raise SystemExit
n = 0
for r in doc.get("results", []) or []:
    n += len(r.get("packages", []) or [])
print(n)
PYEOF
)
  echo "[gate 03] lần thử $attempt: osv-scanner exit=$rc, $ndeps package được quét"
  if [ "$ndeps" -gt 0 ] || [ "$attempt" -ge 3 ]; then break; fi
  attempt=$((attempt + 1))
  sleep 3
done

if [ "$ndeps" -eq 0 ] && grep -rq "==" "$WORKLOAD" --include=requirements.txt; then
  echo "[gate 03] LỖI HẠ TẦNG: osv-scanner không quét được dependency nào" \
       "sau $attempt lần thử — xem osv.log (KHÔNG coi là sạch)"
  printf '{"error": "osv-scanner resolution failed after %s attempts", "log": "osv.log"}\n' \
    "$attempt" > "$GATE_OUT/scan-error.json"
  exit 2
fi

osv-scanner scan source --recursive --format sarif \
  --output-file "$GATE_OUT/osv.sarif" "$WORKLOAD" >/dev/null 2>&1
[ -f "$GATE_OUT/osv.json" ] || echo '{"results": []}' > "$GATE_OUT/osv.json"

python3 "$REPO_ROOT/gates/local/adapters/osv_normalize.py" \
  --osv-json "$GATE_OUT/osv.json" --out "$GATE_OUT/normalized.json"

record sarif-report.record.json <<EOF
{"evidence_type": "sarif-report", "format": "SARIF 2.1.0",
 "tool": "osv-scanner", "commit_sha": "$COMMIT_SHA",
 "artifact_uri": "gate-03-sca/osv.sarif",
 "sha256": "sha256:$(sha256_of "$GATE_OUT/osv.sarif")"}
EOF
exit 0
