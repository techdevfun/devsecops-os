#!/usr/bin/env python3
"""Run one pack policy (opa eval data.devsecops.<package>.deny) over
a normalized JSON input, print the verdict and write an evidence record of type
`policy-decision` (schema policies/evidence-schemas/policy-decision).

Exit 0 on PASS (empty deny), 1 on DENY, 2 on an opa execution error.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--opa", required=True)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--package", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--policy-id", required=True)
    ap.add_argument("--gate", required=True, type=int)
    ap.add_argument("--out", required=True)
    ap.add_argument("--commit-sha", required=True)
    ap.add_argument("--timestamp", required=True)
    a = ap.parse_args()

    inp = Path(a.input)
    digest = hashlib.sha256(inp.read_bytes()).hexdigest()
    q = f"data.devsecops.{a.package}.deny"
    r = subprocess.run(
        [a.opa, "eval", "--bundle", a.bundle, "--input", str(inp),
         "--format", "json", q],
        capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[opa_decide] ERROR in opa eval ({a.package}): {r.stderr.strip()}",
              file=sys.stderr)
        return 2
    res = json.loads(r.stdout).get("result") or []
    deny = (res[0]["expressions"][0]["value"] or []) if res else []

    decision = "deny" if deny else "pass"
    rec = {
        "evidence_type": "policy-decision",
        "policy_id": a.policy_id,
        "engine": "opa",
        "gate": a.gate,
        "decision": decision,
        "violations": deny,
        "inputs_digest": f"sha256:{digest}",
        "commit_sha": a.commit_sha,
        "timestamp": a.timestamp,
    }
    name = f"policy-decision-{a.policy_id.replace('devsecops.', '')}.json"
    (Path(a.out) / name).write_text(
        json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
    print(f"[opa_decide] {a.policy_id} (gate {a.gate}): "
          f"{decision.upper()} ({len(deny)} violations)")
    for d in deny:
        print(f"    - {d}")
    return 1 if deny else 0


if __name__ == "__main__":
    raise SystemExit(main())
