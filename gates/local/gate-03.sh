#!/usr/bin/env bash
# Gate 3 — SCA (osv-scanner over the workload's lockfiles/requirements).
# This gate DETECTS; the blocking decision belongs to gate 8 (KEV/EPSS) per the
# blueprint — avoiding blocking on raw CVSS.
# "Never silently clean" discipline: if an osv-scanner resolution error (network/API)
# leaves 0 dependencies scanned while the workload has a requirements.txt,
# the gate retries up to 3 times; still failing -> exit 2 (infrastructure error) with
# scan-error.json, NEVER reporting a false 0 vulnerabilities.
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
  echo "[gate 03] attempt $attempt: osv-scanner exit=$rc, $ndeps packages scanned"
  if [ "$ndeps" -gt 0 ] || [ "$attempt" -ge 3 ]; then break; fi
  attempt=$((attempt + 1))
  sleep 3
done

if [ "$ndeps" -eq 0 ] && grep -rq "==" "$WORKLOAD" --include=requirements.txt; then
  echo "[gate 03] INFRASTRUCTURE ERROR: osv-scanner could not scan any dependency" \
       "after $attempt attempts — see osv.log (do NOT treat as clean)"
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
