#!/usr/bin/env bash
# Gate 1 — Secret scanning (gitleaks) + policy devsecops.secret_findings.
# Blocks (exit 1) while a secret finding remains that is not allowlisted (blueprint section 5.1).
source "$(dirname "$0")/lib.sh"
gate_begin 01 secret

gitleaks dir "$WORKLOAD" --report-format json \
  --report-path "$GATE_OUT/gitleaks.json" --no-banner 2>&1 | tail -2
gl_json=$?
gitleaks dir "$WORKLOAD" --report-format sarif \
  --report-path "$GATE_OUT/gitleaks.sarif" --no-banner >/dev/null 2>&1
[ -f "$GATE_OUT/gitleaks.json" ] || echo "[]" > "$GATE_OUT/gitleaks.json"

python3 "$REPO_ROOT/gates/local/adapters/gitleaks_input.py" \
  --gitleaks-json "$GATE_OUT/gitleaks.json" --workload "$WORKLOAD" \
  --scan-date "${RUN_TS%%T*}" --out "$GATE_OUT/secret-findings.input.json"

record sarif-report.record.json <<EOF
{"evidence_type": "sarif-report", "format": "SARIF 2.1.0",
 "tool": "gitleaks", "commit_sha": "$COMMIT_SHA",
 "artifact_uri": "gate-01-secret/gitleaks.sarif",
 "sha256": "sha256:$(sha256_of "$GATE_OUT/gitleaks.sarif")"}
EOF

opa_decide secret_findings "$GATE_OUT/secret-findings.input.json" \
  devsecops.secret_findings 1
