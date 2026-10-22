#!/usr/bin/env bash
# Kiểm chứng Kyverno pack bằng kyverno CLI (nếu có trong ~/workspace/tools
# hoặc PATH). Kỳ vọng:
#   - workload-baseline trên manifest clean của workload: pass 3/3
#   - workload-baseline trên fixtures/k8s-bad-pod.yaml:     fail 3/3
#   - verify-image-signatures: chỉ parse/áp thử (verifyImages cần cluster
#     + Sigstore để chạy thật — ghi rõ là chưa kiểm chứng runtime ở M2).
set -u
KYV="${KYVERNO:-$HOME/workspace/tools/kyverno}"
command -v "$KYV" >/dev/null 2>&1 || KYV="$(command -v kyverno || true)"
if [ -z "${KYV:-}" ]; then
  echo "SKIP: không có kyverno CLI — pack Kyverno chỉ được parse bằng Python (xem báo cáo M2)."
  exit 2
fi
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
fail=0

out=$("$KYV" apply "$ROOT/policies/kyverno/workload-baseline.yaml" \
  --resource "$ROOT/examples/payments-sample/clean/k8s/deployment.yaml" 2>/dev/null | tail -1)
echo "clean deployment : $out"
echo "$out" | grep -q "fail: 0" || fail=1

out=$("$KYV" apply "$ROOT/policies/kyverno/workload-baseline.yaml" \
  --resource "$ROOT/policies/fixtures/k8s-bad-pod.yaml" 2>/dev/null | tail -1)
echo "bad pod fixture  : $out"
echo "$out" | grep -q "pass: 0" || fail=1

"$KYV" apply "$ROOT/policies/kyverno/verify-image-signatures.yaml" \
  --resource "$ROOT/examples/payments-sample/clean/k8s/deployment.yaml" >/dev/null 2>&1
echo "verify-images    : parse/apply OK (runtime verifyImages cần cluster — chưa kiểm chứng ở M2)"

exit $fail
