#!/usr/bin/env bash
# M3 local verification: run the 10 gates (exactly the scripts the GitHub workflows
# call) on BOTH workload variants, time each gate, write the raw
# logs to gates/verification/logs/<variant>/ and the results table to
# gates/verification/results.json (+ print to stdout).
#
# Usage: bash gates/verification/run_verification.sh [clean|planted|all]
set -u
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export REPO_ROOT
TOOLS_DIR="${TOOLS_DIR:-$HOME/workspace/tools}"
export TOOLS_DIR
export PATH="$TOOLS_DIR:$PATH"
WHICH="${1:-all}"

tree_digest() { # local run identifier: sha256 over the workload file tree
  (cd "$1" && find . -type f -exec sha256sum {} + | sort -k2 | sha256sum |
    awk '{print "local-tree-" substr($1, 1, 12)}')
}

run_variant() {
  local variant="$1"
  local workload="$REPO_ROOT/examples/payments-sample/$variant"
  local out_root="$REPO_ROOT/evidence/output/local-$variant"
  local logs="$REPO_ROOT/gates/verification/logs/$variant"
  rm -rf "$out_root"
  mkdir -p "$out_root" "$logs"
  export WORKLOAD="$workload" OUT_ROOT="$out_root"
  export COMMIT_SHA="$(tree_digest "$workload")"
  export RUN_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "=== Variant $variant | commit_sha=$COMMIT_SHA | ts=$RUN_TS ==="

  : > "$logs/summary.tsv"
  local g start end dur rc
  for g in 01 02 03 04 05 06 07 08 09 10; do
    start=$(date +%s.%N)
    bash "$REPO_ROOT/gates/local/gate-$g.sh" > "$logs/gate-$g.log" 2>&1
    rc=$?
    end=$(date +%s.%N)
    dur=$(awk -v e="$end" -v s="$start" 'BEGIN {printf "%.2f", e - s}')
    printf "%s\t%s\t%s\n" "$g" "$rc" "$dur" >> "$logs/summary.tsv"
    echo "  gate-$g: exit=$rc, ${dur}s (log: gates/verification/logs/$variant/gate-$g.log)"
  done
}

[ "$WHICH" = "all" ] || [ "$WHICH" = "clean" ] && run_variant clean
[ "$WHICH" = "all" ] || [ "$WHICH" = "planted" ] && run_variant planted

python3 "$REPO_ROOT/gates/verification/build_results.py"
