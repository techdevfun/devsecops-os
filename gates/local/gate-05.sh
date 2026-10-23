#!/usr/bin/env bash
# Gate 5 — Container scanning (Trivy image over the base image declared in the
# Dockerfile) + policy devsecops.base_image (structural block on EOL/latest).
# Blocks (exit 1) when: base_image DENYs, or a CRITICAL CVE exists that has a
# fix and belongs to CISA KEV (the blocking condition of blueprint section 5.1).
# There is no docker daemon on the verification machine: trivy pulls the image directly
# from the registry with its own client — no docker needed.
# "Never silently clean" discipline: a trivy error (DB/registry/disk space) ->
# scan-error.json + exit 2 if there is no other independent blocking basis.
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
  echo "[gate 05] ERROR: trivy image did not produce a result — see trivy-image.log"
  printf '%s\n' '{"error": "trivy image scan failed", "log": "trivy-image.log"}' \
    > "$GATE_OUT/scan-error.json"
fi

# base_image input: reuse the M2 harness's FROM extractor (the Dockerfile extraction
# is outside M3's replacement scope) + the pack's EOL data.
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
    print("[gate 05] BLOCKED: a CRITICAL CVE with a fix belongs to CISA KEV")
    raise SystemExit(1)
print("[gate 05] no CVE in the CRITICAL+fixed+KEV blocking group")
PYEOF
elif [ "$rc" -eq 0 ]; then
  echo "[gate 05] exiting 2: image scan failed and there is no independent blocking basis"
  exit 2
else
  echo "[gate 05] BLOCKED by base_image; the image CVE scan did NOT complete (scan-error.json)"
fi
exit $rc
