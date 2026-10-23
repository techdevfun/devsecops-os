#!/usr/bin/env bash
# Gate 2 — SAST (Semgrep, rulesets p/security-audit + p/python).
# Report-only by default on first installation (blueprint section 5.1 + the flagship
# #1 lesson): this gate does NOT block in phase 1 — it only produces SARIF + counts findings by
# severity into the summary for later calibration.
# Semgrep does not allow two --output flags in one run -> run it twice
# (the second run uses the cached rulesets). Scan error -> scan-error.json + exit 2,
# never disguised as 0 findings.
source "$(dirname "$0")/lib.sh"
gate_begin 02 sast

SEMGREP="${SEMGREP:-$TOOLS_DIR/semgrep-venv/bin/semgrep}"
TARGETS=("$WORKLOAD/backend" "$WORKLOAD/frontend")
"$SEMGREP" --config p/security-audit --config p/python \
  --sarif --output "$GATE_OUT/semgrep.sarif" \
  --metrics off --disable-version-check \
  "${TARGETS[@]}" > "$GATE_OUT/semgrep-sarif.log" 2>&1
"$SEMGREP" --config p/security-audit --config p/python \
  --json --output "$GATE_OUT/semgrep.json" \
  --metrics off --disable-version-check \
  "${TARGETS[@]}" > "$GATE_OUT/semgrep-json.log" 2>&1

if [ ! -s "$GATE_OUT/semgrep.sarif" ] || [ ! -s "$GATE_OUT/semgrep.json" ]; then
  echo "[gate 02] ERROR: semgrep did not produce complete output — see semgrep-*.log"
  printf '%s\n' '{"error": "semgrep scan failed", "logs": ["semgrep-sarif.log", "semgrep-json.log"]}' \
    > "$GATE_OUT/scan-error.json"
  exit 2
fi

python3 - "$GATE_OUT" <<'PYEOF'
import json, sys
out = sys.argv[1]
doc = json.load(open(f"{out}/semgrep.json"))
results = doc.get("results", [])
by_sev = {}
for r in results:
    sev = (r.get("extra", {}) or {}).get("severity", "UNKNOWN")
    by_sev[sev] = by_sev.get(sev, 0) + 1
json.dump({"tool": "semgrep", "total": len(results), "by_severity": by_sev},
          open(f"{out}/sast-summary.json", "w"), indent=2)
print(f"[gate 02] semgrep: {len(results)} finding {by_sev} (report-only)")
for r in results:
    print(f"    - {r.get('check_id')} @ "
          f"{r.get('path')}:{r.get('start', {}).get('line')}")
PYEOF

record sarif-report.record.json <<EOF
{"evidence_type": "sarif-report", "format": "SARIF 2.1.0",
 "tool": "semgrep", "commit_sha": "$COMMIT_SHA",
 "artifact_uri": "gate-02-sast/semgrep.sarif",
 "sha256": "sha256:$(sha256_of "$GATE_OUT/semgrep.sarif")"}
EOF
exit 0
