#!/usr/bin/env bash
# replay.sh — tái hiện buổi demo devsecops-os từ các lần chạy THẬT.
#
# Script này chạy thật: gate 1 (secret), gate 4 (IaC) và gate 8
# (KEV/EPSS) trên cả hai biến thể của workload mẫu, đóng + kiểm chứng
# evidence bundle, rồi thử sửa 1 byte trong bundle để cho thấy kiểm
# chứng FAIL. Không có output nào được in sẵn — mọi dòng kết quả đều do
# công cụ thật sinh ra trong lúc chạy.
#
# Thời gian chạy thật: ~2-3 phút (gate 4 chạy terraform validate +
# trivy config). Bản GIF đi kèm (demo-terminal.gif) nén thời gian chờ
# giữa các dòng của đúng phiên chạy này; nội dung dòng không đổi.
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
  echo "-> mã thoát của gate: ${PIPESTATUS[0]}"
}

banner "devsecops-os — bản SẠCH (clean): kỳ vọng qua mọi gate"
run_gate clean gate-01.sh
run_gate clean gate-04.sh
run_gate clean gate-08.sh

banner "devsecops-os — bản GÀI LỖI (planted): 4 lỗi có chủ đích, kỳ vọng chặn đúng gate"
run_gate planted gate-01.sh
run_gate planted gate-04.sh
run_gate planted gate-08.sh

banner "Evidence bundle — đóng gói + kiểm chứng một lệnh"
python3 "$R/evidence/bundle_tool.py" collect "$R/evidence/output/local-clean" \
  --run-id demo-clean --out-dir "$R/evidence/bundles/demo-clean" | tail -3
python3 "$R/evidence/verify_bundle.py" "$R/evidence/bundles/demo-clean"

banner "Thử phá hoại: sửa 1 byte trong bundle rồi kiểm chứng lại"
rm -rf /tmp/demo-tamper && cp -r "$R/evidence/bundles/demo-clean" /tmp/demo-tamper
python3 - <<'EOF'
from pathlib import Path
p = next(Path('/tmp/demo-tamper/records').rglob('*.json'))
b = bytearray(p.read_bytes()); b[len(b)//2] ^= 0xFF; p.write_bytes(bytes(b))
print('đã sửa 1 byte trong', p.name)
EOF
python3 "$R/evidence/verify_bundle.py" /tmp/demo-tamper || echo "-> kiểm chứng FAIL đúng như thiết kế (mã thoát $?)"

banner "HẾT DEMO — mọi kết quả trên đều từ công cụ thật trong phiên chạy này"
