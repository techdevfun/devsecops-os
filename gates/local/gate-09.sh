#!/usr/bin/env bash
# Gate 9 — Pipeline hygiene: run policy devsecops.pipeline_policy over
# the repo's own workflows (.github/workflows/): minimum permissions
# , third-party actions pinned to full SHAs, all required gates present, OIDC for
# cloud-touching jobs, no static cloud secrets. Blocks (exit 1) on DENY.
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
 "checks": ["minimum permissions declared explicitly",
   "third-party actions pinned to full commit SHAs",
   "all required pack gates present (secret, sast, sca, iac, kev)",
   "cloud-touching jobs use OIDC, no static cloud secrets"]}
EOF
exit $rc
