#!/usr/bin/env bash
# Thư viện chung cho các gate chạy cục bộ (M3). Các workflow GitHub trong
# .github/workflows/ gọi đúng các script gate-XX.sh ở đây sau khi checkout
# + fetch_tools.sh, nên kiểm chứng cục bộ và CI dùng chung một mã nguồn.
#
# Biến môi trường vào (runner/workflow đặt):
#   REPO_ROOT   thư mục gốc của devsecops-os
#   WORKLOAD    thư mục biến thể workload (clean/ hoặc planted/)
#   OUT_ROOT    thư mục đầu ra bằng chứng của lần chạy (evidence/output/<run>)
#   COMMIT_SHA  định danh lần chạy (ở CI là github.sha; cục bộ là tree digest)
#   RUN_TS      timestamp UTC của lần chạy
#   TOOLS_DIR   nơi chứa binary công cụ (mặc định ~/workspace/tools)
set -u

TOOLS_DIR="${TOOLS_DIR:-$HOME/workspace/tools}"
# Chỉ đưa TOOLS_DIR vào PATH — KHÔNG đưa semgrep-venv: python3 của venv
# thiếu pyyaml mà các adapter cần (gate 02 gọi semgrep bằng đường dẫn
# tuyệt đối nên không cần venv trên PATH).
export PATH="$TOOLS_DIR:$PATH"
# /tmp trên máy kiểm chứng là tmpfs nhỏ (512MB) — trivy giải nén DB
# (~130MB+) và terraform tải provider đều tràn. Ép TMPDIR về đĩa thật.
mkdir -p "$TOOLS_DIR/tmp"
export TMPDIR="$TOOLS_DIR/tmp"

OPA="${OPA:-$TOOLS_DIR/opa}"
GATE_OUT=""          # thư mục đầu ra riêng của gate (đặt bởi gate_begin)
GATE_ID="${GATE_ID:-unknown}"
RUN_TS="${RUN_TS:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
COMMIT_SHA="${COMMIT_SHA:-local-unspecified}"

gate_begin() { # gate_begin <số gate> <tên>
  GATE_ID="$1"
  GATE_OUT="$OUT_ROOT/gate-$1-$2"
  mkdir -p "$GATE_OUT"
  export GATE_OUT GATE_ID
  echo "[gate $1] $2 — workload: $WORKLOAD"
  echo "[gate $1] tools: $TOOLS_DIR | out: $GATE_OUT"
}

# record <tên-file> : đọc JSON record từ stdin, ghi vào $GATE_OUT/<tên-file>
record() {
  python3 -c 'import sys, json, pathlib
data = json.load(sys.stdin)
p = pathlib.Path(sys.argv[1]); p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print(f"[record] {p}")' "$GATE_OUT/$1"
}

# opa_decide <package> <input.json> <policy_id> <gate-số>
# Chạy opa eval trên bundle policies/rego, ghi policy-decision record,
# in PASS/DENY; trả exit 1 khi DENY để script gọi quyết định chặn hay không.
opa_decide() {
  python3 "$REPO_ROOT/gates/local/adapters/opa_decide.py" \
    --opa "$OPA" --bundle "$REPO_ROOT/policies/rego" \
    --package "$1" --input "$2" --policy-id "$3" --gate "$4" \
    --out "$GATE_OUT" --commit-sha "$COMMIT_SHA" --timestamp "$RUN_TS"
}

sha256_of() { sha256sum "$1" | awk '{print $1}'; }

# ensure_feeds — tải feed CISA KEV + FIRST EPSS vào $OUT_ROOT/.feeds
# (dùng chung cho gate 5 và gate 8; tải một lần cho cả lần chạy).
ensure_feeds() {
  local feeds="$OUT_ROOT/.feeds"
  mkdir -p "$feeds"
  if [ ! -s "$feeds/kev.json" ]; then
    echo "[feeds] tải CISA KEV catalog..."
    curl -sL --fail --max-time 300 -o "$feeds/kev.json" \
      https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
  fi
  if [ ! -s "$feeds/epss.csv.gz" ]; then
    echo "[feeds] tải FIRST EPSS scores..."
    curl -sL --fail --max-time 300 -o "$feeds/epss.csv.gz" \
      https://epss.cyentia.com/epss_scores-current.csv.gz
  fi
  export FEEDS_DIR="$feeds"
}
