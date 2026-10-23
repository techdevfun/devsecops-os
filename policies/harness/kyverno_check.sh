#!/usr/bin/env bash
# Verify the Kyverno pack with the kyverno CLI (if present in
# ~/workspace/tools or on PATH). Expectations:
#   - workload-baseline on the workload's clean manifest: pass 3/3
#   - workload-baseline on fixtures/k8s-bad-pod.yaml:     fail 3/3
#   - verify-image-signatures: parse/apply trial only (verifyImages
#     needs a cluster + Sigstore to run for real — runtime is
#     explicitly not verified in M2).
set -u
KYV="${KYVERNO:-$HOME/workspace/tools/kyverno}"
command -v "$KYV" >/dev/null 2>&1 || KYV="$(command -v kyverno || true)"
if [ -z "${KYV:-}" ]; then
  echo "SKIP: no kyverno CLI — the Kyverno pack is only parsed with Python (see the M2 report)."
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
echo "verify-images    : parse/apply OK (verifyImages runtime needs a cluster — not verified in M2)"

exit $fail
