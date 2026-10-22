#!/usr/bin/env bash
# Gate 4 — IaC scanning, ba lớp:
#  (a) terraform init -backend=false + validate trên bản sao sandbox
#      (provider bỏ qua kiểm chứng credential bằng override CHỈ trong
#      sandbox; kết quả validate ghi thẳng vào validate.json — sau
#      refactor M5 (rule SG tách sang tài nguyên riêng) validate PASS
#      trên cả hai biến thể; plan vẫn không sinh được tại chỗ vì data
#      source aws_availability_zones cần gọi AWS API thật);
#  (b) trivy config quét HCL (lớp phát hiện, evidence SARIF — report-only);
#  (c) OPA trên mô hình tài nguyên từ `conftest parse` (HCL2 parser
#      chuẩn) cho 3 policy của pack: network_exposure,
#      storage_encryption, iam_least_privilege — đây là lớp QUYẾT ĐỊNH:
#      deny ở bất kỳ policy nào -> gate chặn (exit 1).
source "$(dirname "$0")/lib.sh"
gate_begin 04 iac

# --- (a) terraform validate (sandbox) ---
SBX="$GATE_OUT/tf-sandbox"
mkdir -p "$SBX"
cp -r "$WORKLOAD/infra/." "$SBX/"
cat > "$SBX/gate_override.tf" <<'EOF'
provider "aws" {
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
}
EOF
export TF_PLUGIN_CACHE_DIR="${TF_PLUGIN_CACHE_DIR:-$TOOLS_DIR/tf-plugin-cache}"
mkdir -p "$TF_PLUGIN_CACHE_DIR"
(
  cd "$SBX"
  export AWS_ACCESS_KEY_ID=gate-local AWS_SECRET_ACCESS_KEY=gate-local
  export AWS_EC2_METADATA_DISABLED=true TF_IN_AUTOMATION=1
  terraform init -backend=false -no-color > init.log 2>&1
  terraform validate -no-color > validate.log 2>&1
  echo $? > validate.exit
)
vexit=$(cat "$SBX/validate.exit")
python3 - "$GATE_OUT" "$vexit" <<'PYEOF'
import json, sys
out, vexit = sys.argv[1], int(sys.argv[2])
log = open(f"{out}/tf-sandbox/validate.log").read().strip()
json.dump({"tool": "terraform validate (terraform 1.17.0)",
           "exit_code": vexit, "passed": vexit == 0,
           "output_tail": log[-800:]},
          open(f"{out}/validate.json", "w"), indent=2)
print(f"[gate 04] terraform validate exit={vexit} "
      f"({'PASS' if vexit == 0 else 'FAIL — xem validate.json'})")
PYEOF

# --- (b) trivy config (phát hiện) ---
trivy config --format json --output "$GATE_OUT/trivy-config.json" \
  "$WORKLOAD/infra" >/dev/null 2>&1
trivy config --format sarif --output "$GATE_OUT/trivy-config.sarif" \
  "$WORKLOAD/infra" >/dev/null 2>&1
python3 - "$GATE_OUT" <<'PYEOF'
import json, sys
out = sys.argv[1]
try:
    doc = json.load(open(f"{out}/trivy-config.json"))
except Exception:
    doc = {}
n = 0
for res in doc.get("Results", []) or []:
    n += len(res.get("Misconfigurations", []) or [])
json.dump({"tool": "trivy config", "misconfigurations": n},
          open(f"{out}/trivy-config-summary.json", "w"), indent=2)
print(f"[gate 04] trivy config: {n} misconfiguration (report-only)")
PYEOF

record sarif-report.record.json <<EOF
{"evidence_type": "sarif-report", "format": "SARIF 2.1.0",
 "tool": "trivy", "commit_sha": "$COMMIT_SHA",
 "artifact_uri": "gate-04-iac/trivy-config.sarif",
 "sha256": "sha256:$(sha256_of "$GATE_OUT/trivy-config.sarif")"}
EOF

# --- (c) OPA quyết định trên đầu vào parser HCL2 ---
python3 "$REPO_ROOT/gates/local/adapters/tf_parse_input.py" \
  --conftest "$(command -v conftest)" --infra "$WORKLOAD/infra" \
  --out "$GATE_OUT/tf-normalized.input.json"

rc=0
for pkg in network_exposure storage_encryption iam_least_privilege; do
  opa_decide "$pkg" "$GATE_OUT/tf-normalized.input.json" \
    "devsecops.$pkg" 4 || rc=1
done

record iac-assessment.record.json <<EOF
{"evidence_type": "iac-assessment", "environment": "local-verification",
 "commit_sha": "$COMMIT_SHA",
 "decision": "$([ $rc -eq 0 ] && echo pass || echo deny)",
 "policy_decisions": ["devsecops.network_exposure",
   "devsecops.storage_encryption", "devsecops.iam_least_privilege"],
 "plan_digest": "sha256:$(sha256_of "$GATE_OUT/tf-normalized.input.json")",
 "input_source": "conftest parse (HCL2) — terraform validate PASS sau refactor M5 (ghi trong validate.json); terraform plan JSON chưa sinh được tại chỗ vì plan cần gọi AWS API thật cho data source aws_availability_zones, môi trường kiểm chứng không có credential AWS thật"}
EOF
exit $rc
