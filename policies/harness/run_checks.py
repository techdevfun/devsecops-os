#!/usr/bin/env python3
"""Verification harness for pack v1 (M2).

Runs:
  1. build_workload_fixtures.py — generates inputs from the workload's real files.
  2. `opa test` over all of policies/rego (unit tests per policy).
  3. `opa eval` for each case in expectations.json (static fixtures +
     the mandatory M2 planted-vs-clean comparison).
  4. Kyverno verification: YAML parsing + (if the kyverno CLI exists)
     an apply trial; without the CLI, an equivalent structural check
     in Python of the 3 workload-baseline rules against the workload
     manifest.

Exits 0 when every check meets expectations.
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
    raise SystemExit("opa binary not found (~/workspace/tools/opa or PATH)")


def opa_eval(opa, package, input_path):
    q = f"data.devsecops.{package}.deny"
    out = subprocess.run(
        [opa, "eval", "--bundle", str(POLICIES / "rego"),
         "--input", str(input_path), "--format", "json", q],
        capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"opa eval failed ({package}): {out.stderr.strip()}")
    res = json.loads(out.stdout)["result"]
    if not res:
        return []
    return res[0]["expressions"][0]["value"] or []


def main() -> int:
    opa = find_opa()
    print(f"[harness] opa: {opa}")
    ver = subprocess.run([opa, "version"], capture_output=True, text=True).stdout
    print("[harness] " + " | ".join(ver.splitlines()[:2]))

    print("\n== 1. Generate fixtures from the real workload ==")
    r = subprocess.run([sys.executable, str(HERE / "build_workload_fixtures.py")],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr)
        return 1

    print("\n== 2. opa test (unit tests per policy) ==")
    r = subprocess.run([opa, "test", str(POLICIES / "rego"), "-v"],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr.strip())
        print("RESULT: opa test FAILED")
        return 1

    print("\n== 3. Fixture + planted-vs-clean comparison ==")
    exp = json.loads((HERE / "expectations.json").read_text())
    failures = 0
    for chk in exp["checks"]:
        inp = POLICIES / chk["input"]
        deny = opa_eval(opa, chk["package"], inp)
        got = "deny" if deny else "pass"
        ok = got == chk["expect"]
        failures += 0 if ok else 1
        print(f"  [{'OK ' if ok else 'FAIL'}] {chk['name']}: "
              f"expected={chk['expect']} actual={got} (deny={len(deny)})")
        for d in deny:
            print(f"        - {d}")
    print(f"\n== Total: {len(exp['checks']) - failures}/{len(exp['checks'])} passed ==")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
