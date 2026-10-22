#!/usr/bin/env bash
# Gate 9 — Vệ sinh pipeline: chạy policy devsecops.pipeline_policy trên
# chính các workflow của repo (.github/workflows/): permissions tối
# thiểu, action bên thứ ba ghim full SHA, đủ gate bắt buộc, OIDC cho
# job chạm cloud, cấm secret cloud tĩnh. Chặn (exit 1) khi DENY.
source "$(dirname "$0")/lib.sh"
gate_begin 09 pipeline-hygiene

python3 "$REPO_ROOT/gates/local/adapters/workflow_input.py" \
  --workflows-dir "$REPO_ROOT/.github/workflows" \
  --out "$GATE_OUT/workflows.input.json"

opa_decide pipeline_policy "$GATE_OUT/workflows.input.json" \
  devsecops.pipeline_policy 9
rc=$?

record pipeline-config-verification.record.json <<EOF
{"evidence_type": "pipeline-config-verification",
 "workflow_file": ".github/workflows/all-gates.yml",
 "commit_sha": "$COMMIT_SHA",
 "decision": "$([ $rc -eq 0 ] && echo pass || echo deny)",
 "checks": ["permissions tối thiểu khai báo tường minh",
   "action bên thứ ba ghim full commit SHA",
   "đủ gate bắt buộc của pack (secret, sast, sca, iac, kev)",
   "job chạm cloud dùng OIDC, không secret cloud tĩnh"]}
EOF
exit $rc
