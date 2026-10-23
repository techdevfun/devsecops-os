#!/usr/bin/env bash
# replay.sh — recreates the devsecops-os demo session from REAL runs.
#
# This script really runs: gate 1 (secret), gate 4 (IaC) and gate 8
# (KEV/EPSS) on both variants of the sample workload, closes +
# verifies the evidence bundle, then tries editing 1 byte in the
# bundle to show verification FAIL. No output is printed in advance —
# every result line is produced by real tools during the run.
#
# Real runtime: ~2-3 minutes (gate 4 runs terraform validate +
# trivy config). The accompanying GIF (demo-terminal.gif) compresses
# the waiting time between the lines of this exact run session; the
# line content is unchanged.
set -u
R="$(cd "$(dirname "$0")/../.." && pwd)"
export TOOLS_DIR="${TOOLS_DIR:-$HOME/workspace/tools}"
export TMPDIR="$TOOLS_DIR/tmp"
mkdir -p "$TMPDIR"
export COMMIT_SHA="demo-replay"

banner() { printf '\n\033[1;36m== %s ==\033[0m\n' "$1"; }
run_gate() { # variant gate-script label
  local variant="$1" script="$2"
  export REPO_ROOT="$R"
  export WORKLOAD="$R/examples/payments-sample/$variant"
  export OUT_ROOT="$R/evidence/output/local-$variant"
  bash "$R/gates/local/$script" 2>&1 | grep -E "gate 0|opa_decide|PASS|DENY|validate|gitleaks|CVE-2026-48710|exit" | head -12
  echo "-> gate exit code: ${PIPESTATUS[0]}"
}

banner "devsecops-os — CLEAN variant: expected to pass every gate"
run_gate clean gate-01.sh
run_gate clean gate-04.sh
run_gate clean gate-08.sh

banner "devsecops-os — PLANTED variant: 4 deliberate flaws, expected to be blocked at the right gates"
run_gate planted gate-01.sh
run_gate planted gate-04.sh
run_gate planted gate-08.sh

banner "Evidence bundle — package + verify in one command"
python3 "$R/evidence/bundle_tool.py" collect "$R/evidence/output/local-clean" \
  --run-id demo-clean --out-dir "$R/evidence/bundles/demo-clean" | tail -3
python3 "$R/evidence/verify_bundle.py" "$R/evidence/bundles/demo-clean"

banner "Tamper test: edit 1 byte in the bundle and verify again"
rm -rf /tmp/demo-tamper && cp -r "$R/evidence/bundles/demo-clean" /tmp/demo-tamper
python3 - <<'EOF'
from pathlib import Path
p = next(Path('/tmp/demo-tamper/records').rglob('*.json'))
b = bytearray(p.read_bytes()); b[len(b)//2] ^= 0xFF; p.write_bytes(bytes(b))
print('edited 1 byte in', p.name)
EOF
python3 "$R/evidence/verify_bundle.py" /tmp/demo-tamper || echo "-> verification FAILs exactly as designed (exit code $?)"

banner "END OF DEMO — every result above came from real tools in this session"
