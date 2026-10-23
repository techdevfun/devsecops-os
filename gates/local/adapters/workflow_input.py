#!/usr/bin/env python3
"""Gate 9 — normalize the repo's own GitHub Actions workflows into the
input for policy devsecops.pipeline_policy: workflow-level permissions,
the `uses` list (SHA pinning check), enabled gates (read from all-gates.yml —
which jobs call a gate-* reusable workflow), and each job's OIDC/static-secret
information.
"""
import argparse
import json
import re
from pathlib import Path

import yaml

REQUIRED_GATES = ["secret", "sast", "sca", "iac", "kev"]
GATE_JOB_MAP = {
    "gate-01-secret": "secret", "gate-02-sast": "sast",
    "gate-03-sca": "sca", "gate-04-iac": "iac",
    "gate-05-container": "container", "gate-06-sbom-attestation": "sbom",
    "gate-07-license": "license", "gate-08-kev-epss": "kev",
    "gate-09-pipeline-hygiene": "pipeline",
    "gate-10-ai-pr-review": "ai-pr-review",
}
STATIC_SECRET_RE = re.compile(
    r"secrets\.(AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|GCP_|AZURE_)",
    re.IGNORECASE)


def job_uses(job):
    uses = []
    if isinstance(job.get("uses"), str):
        uses.append(job["uses"])
    for step in job.get("steps", []) or []:
        if isinstance(step, dict) and isinstance(step.get("uses"), str):
            uses.append(step["uses"])
    return uses


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflows-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    wdir = Path(a.workflows_dir)
    workflows = []
    gates_enabled = []
    for path in sorted(wdir.glob("*.yml")) + sorted(wdir.glob("*.yaml")):
        doc = yaml.safe_load(path.read_text()) or {}
        jobs = doc.get("jobs", {}) or {}
        uses, job_docs = [], []
        for jname, job in jobs.items():
            if not isinstance(job, dict):
                continue
            ju = job_uses(job)
            uses.extend(ju)
            for u in ju:
                for wf_name, gate_id in GATE_JOB_MAP.items():
                    if wf_name in u and gate_id not in gates_enabled:
                        gates_enabled.append(gate_id)
            perms = job.get("permissions") or doc.get("permissions") or {}
            blob = json.dumps(job, default=str)
            job_docs.append({
                "name": jname,
                "oidc": isinstance(perms, dict)
                        and perms.get("id-token") == "write",
                "cloud_access": bool(STATIC_SECRET_RE.search(blob))
                                or (isinstance(perms, dict)
                                    and perms.get("id-token") == "write"),
                "static_cloud_secrets": sorted(
                    set(STATIC_SECRET_RE.findall(blob))),
            })
        workflows.append({
            "file": f".github/workflows/{path.name}",
            "permissions": doc.get("permissions"),
            "uses": uses,
            # gates_enabled is a property of the PIPELINE (all-gates) that
            # this workflow belongs to — the reusable workflows are part
            # of that same pipeline, so they share the enabled list.
            "gates_enabled": gates_enabled,
            "jobs": job_docs,
        })

    doc = {"workflows": workflows,
           "config": {"required_gates": REQUIRED_GATES,
                      "internal_action_prefixes": ["./"]}}
    Path(a.out).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"[workflow_input] {len(workflows)} workflow, "
          f"gates_enabled={gates_enabled} -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
