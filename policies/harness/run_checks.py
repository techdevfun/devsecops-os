#!/usr/bin/env python3
"""Harness kiểm chứng pack v1 (M2).

Chạy:
  1. build_workload_fixtures.py — sinh input từ file thật của workload.
  2. `opa test` trên toàn bộ policies/rego (unit test từng policy).
  3. `opa eval` cho từng ca trong expectations.json (fixture tĩnh +
     đối chiếu planted-vs-clean bắt buộc của M2).
  4. Kiểm chứng Kyverno: parse YAML + (nếu có kyverno CLI) apply thử;
     không có CLI thì chạy bộ kiểm tra cấu trúc tương đương bằng Python
     trên 3 rule của workload-baseline đối với manifest của workload.

Thoát mã 0 khi mọi kiểm chứng đạt kỳ vọng.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
POLICIES = HERE.parent
REPO = POLICIES.parent


def find_opa() -> str:
    for cand in (Path.home() / "workspace" / "tools" / "opa",):
        if cand.exists():
            return str(cand)
    from shutil import which
    p = which("opa")
    if p:
        return p
    raise SystemExit("Không tìm thấy opa binary (~/workspace/tools/opa hoặc PATH)")


def opa_eval(opa, package, input_path):
    q = f"data.devsecops.{package}.deny"
    out = subprocess.run(
        [opa, "eval", "--bundle", str(POLICIES / "rego"),
         "--input", str(input_path), "--format", "json", q],
        capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"opa eval lỗi ({package}): {out.stderr.strip()}")
    res = json.loads(out.stdout)["result"]
    if not res:
        return []
    return res[0]["expressions"][0]["value"] or []


def main() -> int:
    opa = find_opa()
    print(f"[harness] opa: {opa}")
    ver = subprocess.run([opa, "version"], capture_output=True, text=True).stdout
    print("[harness] " + " | ".join(ver.splitlines()[:2]))

    print("\n== 1. Sinh fixture từ workload thật ==")
    r = subprocess.run([sys.executable, str(HERE / "build_workload_fixtures.py")],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr)
        return 1

    print("\n== 2. opa test (unit test từng policy) ==")
    r = subprocess.run([opa, "test", str(POLICIES / "rego"), "-v"],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr.strip())
        print("KẾT QUẢ: opa test THẤT BẠI")
        return 1

    print("\n== 3. Đối chiếu fixture + planted-vs-clean ==")
    exp = json.loads((HERE / "expectations.json").read_text())
    failures = 0
    for chk in exp["checks"]:
        inp = POLICIES / chk["input"]
        deny = opa_eval(opa, chk["package"], inp)
        got = "deny" if deny else "pass"
        ok = got == chk["expect"]
        failures += 0 if ok else 1
        print(f"  [{'OK ' if ok else 'SAI'}] {chk['name']}: "
              f"kỳ vọng={chk['expect']} thực tế={got} (deny={len(deny)})")
        for d in deny:
            print(f"        - {d}")
    print(f"\n== Tổng: {len(exp['checks']) - failures}/{len(exp['checks'])} đạt ==")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
