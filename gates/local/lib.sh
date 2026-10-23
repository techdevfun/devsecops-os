#!/usr/bin/env bash
# Shared library for the locally run gates (M3). The GitHub workflows in
# .github/workflows/ call exactly the gate-XX.sh scripts here after checkout
# + fetch_tools.sh, so local verification and CI share the same source code.
#
# Input environment variables (set by the runner/workflow):
#   REPO_ROOT   root directory of devsecops-os
#   WORKLOAD    workload variant directory (clean/ or planted/)
#   OUT_ROOT    evidence output directory for the run (evidence/output/<run>)
#   COMMIT_SHA  run identifier (github.sha in CI; tree digest locally)
#   RUN_TS      UTC timestamp of the run
#   TOOLS_DIR   directory containing the tool binaries (default ~/workspace/tools)
set -u

TOOLS_DIR="${TOOLS_DIR:-$HOME/workspace/tools}"
# Only put TOOLS_DIR on PATH — do NOT add semgrep-venv: the venv's python3
# lacks pyyaml, which the adapters need (gate 02 calls semgrep by absolute
# path, so it does not need the venv on PATH).
export PATH="$TOOLS_DIR:$PATH"
# /tmp on the verification machine is a small tmpfs (512MB) — both trivy's DB
# extraction (~130MB+) and terraform's provider downloads overflow it. Force TMPDIR onto a real disk.
mkdir -p "$TOOLS_DIR/tmp"
export TMPDIR="$TOOLS_DIR/tmp"

OPA="${OPA:-$TOOLS_DIR/opa}"
GATE_OUT=""          # per-gate output directory (set by gate_begin)
GATE_ID="${GATE_ID:-unknown}"
RUN_TS="${RUN_TS:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
COMMIT_SHA="${COMMIT_SHA:-local-unspecified}"

gate_begin() { # gate_begin <gate number> <name>
  GATE_ID="$1"
  GATE_OUT="$OUT_ROOT/gate-$1-$2"
  mkdir -p "$GATE_OUT"
  export GATE_OUT GATE_ID
  echo "[gate $1] $2 — workload: $WORKLOAD"
  echo "[gate $1] tools: $TOOLS_DIR | out: $GATE_OUT"
}

# record <filename> : read a JSON record from stdin and write it to $GATE_OUT/<filename>
record() {
  python3 -c 'import sys, json, pathlib
data = json.load(sys.stdin)
p = pathlib.Path(sys.argv[1]); p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print(f"[record] {p}")' "$GATE_OUT/$1"
}

# opa_decide <package> <input.json> <policy_id> <gate-number>
# Run opa eval on the policies/rego bundle, write a policy-decision record,
# print PASS/DENY; return exit 1 on DENY so the calling script can decide whether to block.
opa_decide() {
  python3 "$REPO_ROOT/gates/local/adapters/opa_decide.py" \
    --opa "$OPA" --bundle "$REPO_ROOT/policies/rego" \
    --package "$1" --input "$2" --policy-id "$3" --gate "$4" \
    --out "$GATE_OUT" --commit-sha "$COMMIT_SHA" --timestamp "$RUN_TS"
}

sha256_of() { sha256sum "$1" | awk '{print $1}'; }

# ensure_feeds — download the CISA KEV + FIRST EPSS feeds into $OUT_ROOT/.feeds
# (shared by gate 5 and gate 8; downloaded once for the whole run).
ensure_feeds() {
  local feeds="$OUT_ROOT/.feeds"
  mkdir -p "$feeds"
  if [ ! -s "$feeds/kev.json" ]; then
    echo "[feeds] downloading CISA KEV catalog..."
    curl -sL --fail --max-time 300 -o "$feeds/kev.json" \
      https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
  fi
  if [ ! -s "$feeds/epss.csv.gz" ]; then
    echo "[feeds] downloading FIRST EPSS scores..."
    curl -sL --fail --max-time 300 -o "$feeds/epss.csv.gz" \
      https://epss.cyentia.com/epss_scores-current.csv.gz
  fi
  export FEEDS_DIR="$feeds"
}
