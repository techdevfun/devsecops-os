#!/usr/bin/env python3
"""Build the devsecops.runtime_version policy input for one workload.

Extracts the images declared by the workload's Dockerfile — reusing
the pack harness extractor (policies/harness/build_workload_fixtures.
extract_docker), exactly like gate 05 builds its base_image input —
and attaches the pack's runtime-floor data
(policies/data/runtime_floors.json). The policy then compares each
declared runtime version against the floor of its branch.

The version source is the Dockerfile FROM declaration — the runtime
that actually runs. A composer.json "platform" requirement is a
constraint expression, not the running runtime, so it is deliberately
NOT used as a version source.

CLI:
    runtime_input.py --workload DIR --floors FILE --out FILE

Importable:
    build_input(workload, floors) -> dict
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_harness_extractor():
    spec = importlib.util.spec_from_file_location(
        "bwf", str(REPO_ROOT / "policies" / "harness"
                   / "build_workload_fixtures.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_input(workload, floors) -> dict:
    """Return {"dockerfiles": [...], "runtime_floors": floors} for a
    workload directory. A workload without a Dockerfile yields an
    empty dockerfiles list (the policy then has nothing in scope and
    passes as not-applicable)."""
    workload = Path(workload)
    if (workload / "Dockerfile").is_file():
        bwf = _load_harness_extractor()
        doc = bwf.extract_docker(workload)
        dockerfiles = doc["dockerfiles"]
    else:
        print(f"[runtime_input] no Dockerfile in {workload} — "
              "empty dockerfiles list (not applicable)", file=sys.stderr)
        dockerfiles = []
    return {"dockerfiles": dockerfiles, "runtime_floors": floors}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workload", required=True)
    ap.add_argument("--floors", required=True,
                    help="path to policies/data/runtime_floors.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    floors = json.loads(Path(a.floors).read_text())
    doc = build_input(a.workload, floors)
    Path(a.out).write_text(json.dumps(doc, indent=2) + "\n")
    imgs = [i for d in doc["dockerfiles"] for i in d["images"]]
    print(f"[runtime_input] declared images: {imgs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
