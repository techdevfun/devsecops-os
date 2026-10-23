#!/usr/bin/env bash
# Gate 8 — EPSS/CISA KEV prioritization: enrich gate 3's vulnerabilities (+ gate 5's
# if present in the same run) with the real feeds, run policy
# devsecops.dependency_kev and produce `vuln-risk-ranking` evidence.
# Blocks (exit 1) when a dependency is hit by a CVE in KEV or with EPSS >= the
# 0.5 threshold (the blocking condition of blueprint section 5.1 — the anti-alert-fatigue mechanism).
source "$(dirname "$0")/lib.sh"
gate_begin 08 kev-epss

NORM="$OUT_ROOT/gate-03-sca/normalized.json"
if [ ! -f "$NORM" ]; then
  echo "[gate 08] gate 3 output not found — running osv-scanner"
  osv-scanner scan source --recursive --format json \
    --output-file "$GATE_OUT/osv.json" "$WORKLOAD" >/dev/null 2>&1
  python3 "$REPO_ROOT/gates/local/adapters/osv_normalize.py" \
    --osv-json "$GATE_OUT/osv.json" --out "$GATE_OUT/normalized.json"
  NORM="$GATE_OUT/normalized.json"
fi

ensure_feeds
IMG_VULNS="$OUT_ROOT/gate-05-container/image-vulns.json"
EXTRA=()
[ -f "$IMG_VULNS" ] && EXTRA=(--image-vulns "$IMG_VULNS")

python3 "$REPO_ROOT/gates/local/adapters/kev_epss_enrich.py" \
  --normalized "$NORM" "${EXTRA[@]}" \
  --kev "$FEEDS_DIR/kev.json" --epss "$FEEDS_DIR/epss.csv.gz" \
  --threshold 0.5 \
  --out-input "$GATE_OUT/dependency-kev.input.json" \
  --out-ranking "$GATE_OUT/vuln-risk-ranking.record.json"

opa_decide dependency_kev "$GATE_OUT/dependency-kev.input.json" \
  devsecops.dependency_kev 8
