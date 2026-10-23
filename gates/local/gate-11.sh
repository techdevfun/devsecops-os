#!/usr/bin/env bash
# Gate 11 — Runtime version floor (policy devsecops.runtime_version):
# every runtime a workload DECLARES in its Dockerfile FROM lines must
# be at or above the security floor recorded for its branch in the
# pack data (policies/data/runtime_floors.json). This gate exists
# because interpreter-level vulnerabilities can be invisible to both
# image CVE matching (gate 5: a runtime compiled from source into the
# image is not a scannable package) and CISA KEV (gate 8: membership
# lags disclosure) — measured on 2026-10-23 with PHP2Shell
# (CVE-2026-109618 / CVE-2026-109619), which neither gate caught.
# The declared-version check needs neither signal.
# Blocks (exit 1) when the policy DENYs: declared version below its
# branch floor, an end-of-life branch with no fixed upstream release,
# or an unpinned/unparseable tag ("latest", partial versions).
# Workloads declaring no runtime covered by the floor data pass as
# not-applicable.
source "$(dirname "$0")/lib.sh"
gate_begin 11 runtime-version

python3 "$REPO_ROOT/gates/local/adapters/runtime_input.py" \
  --workload "$WORKLOAD" \
  --floors "$REPO_ROOT/policies/data/runtime_floors.json" \
  --out "$GATE_OUT/runtime-version.input.json"

opa_decide runtime_version "$GATE_OUT/runtime-version.input.json" \
  devsecops.runtime_version 11
