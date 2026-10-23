#!/usr/bin/env python3
"""Render gates/verification/results.md from results.json (every number
comes from the real verification run; this file contains no hand-typed numbers)."""
import json
from pathlib import Path

VER = Path(__file__).resolve().parent
data = json.loads((VER / "results.json").read_text())
C, P = data["clean"], data["planted"]


def cell(variant, gate):
    t = variant["timing"].get(gate, {})
    return t.get("exit"), t.get("seconds")


def detail(variant, gate):
    g = variant["gates"][gate]
    if gate == "01":
        return f"policy {g['decision']} ({g['violations']} violations)"
    if gate == "02":
        return f"{g['findings']} finding {g.get('by_severity') or ''} — report-only"
    if gate == "03":
        return f"{len(g['vulns'])} vulnerabilities: {', '.join(g['vulns']) or '—'}"
    if gate == "04":
        pols = "; ".join(
            f"{k}={v['decision']}({v['violations']})"
            for k, v in g["policies"].items())
        return (f"validate={'PASS' if g['validate_passed'] else 'FAIL'}; "
                f"{pols}; trivy-config={g['trivy_config_misconfigs']} misconfig")
    if gate == "05":
        return (f"image {g['image_total']} CVE {g['image_counts'] or ''}; "
                f"KEV blocking group={g['blocking_kev_criticals']}; "
                f"base_image={g['base_image_decision']}({g['base_image_violations']})")
    if gate == "06":
        return (f"provenance {g['decision']}; SBOM {g['components']} components, "
                f"signed={g['signed']}")
    if gate == "07":
        return f"license_policy {g['decision']} ({g['violations']} violations)"
    if gate == "08":
        blocks = [e["cve"] for e in g["entries"] if e["decision"] == "block"]
        return (f"dependency_kev {g['decision']} ({g['violations']} violations); "
                f"{len(g['entries'])} ranked entries, block: {blocks or '—'}")
    if gate == "09":
        return f"pipeline_policy {g['decision']} ({g['violations']} violations)"
    if gate == "10":
        return g["state"]
    return ""


NAMES = {
    "01": "Secret scanning", "02": "SAST", "03": "SCA",
    "04": "IaC scanning", "05": "Container scanning",
    "06": "SBOM + attestation", "07": "License compliance",
    "08": "EPSS/CISA KEV", "09": "Pipeline hygiene",
    "10": "AI PR Review Gate",
}

lines = []
lines.append("# M3 verification results — the CI gate suite run for real on the sample workloads")
lines.append("")
lines.append("Generated automatically from `results.json` (the gates' real output) by")
lines.append("`render_results_md.py`. Raw log per gate: `gates/verification/logs/`.")
lines.append("Evidence per run: `evidence/output/local-<variant>/`.")
lines.append("")
lines.append("Exit code convention: 0 = pass; 1 = blocked under the blueprint's default")
lines.append("blocking conditions; 2 = infrastructure error (with scan-error.json).")
lines.append("")
lines.append("| Gate | Clean — result (exit code, seconds) | Planted — result (exit code, seconds) |")
lines.append("|---|---|---|")
for g in [f"{i:02d}" for i in range(1, 11)]:
    ce, cs = cell(C, g)
    pe, ps = cell(P, g)
    lines.append(
        f"| {g} {NAMES[g]} | exit {ce}, {cs}s — {detail(C, g)} "
        f"| exit {pe}, {ps}s — {detail(P, g)} |")
lines.append("")
lines.append(f"Total sequential run time (local, warm cache): "
             f"clean {C['total_seconds']}s, planted {P['total_seconds']}s. "
             f"Slowest gate: {max(C['max_gate_seconds'], P['max_gate_seconds'])}s.")
lines.append("")
lines.append("## Check against M3's mandatory expectations")
lines.append("")
exp_clean = all(C["timing"][g]["exit"] == 0 for g in C["timing"])
lines.append(f"- Clean passes every gate (all exit codes = 0): "
             f"**{'PASS' if exp_clean else 'FAIL'}**")
for g, want in (("01", 1), ("04", 1), ("05", 1), ("08", 1)):
    got = P["timing"][g]["exit"]
    lines.append(f"- Planted is blocked at gate {g} (exit code 1): "
                 f"**{'PASS' if got == want else f'FAIL (exit {got})'}**")
for g in ("02", "03", "06", "07", "09", "10"):
    got = P["timing"][g]["exit"]
    lines.append(f"- Planted is NOT blocked at gate {g} (exit code 0): "
                 f"**{'PASS' if got == 0 else f'FAIL (exit {got})'}**")
lines.append(f"- Gate 3 planted detects CVE-2026-48710: "
             f"**{'PASS' if 'CVE-2026-48710' in P['gates']['03']['vulns'] else 'FAIL'}**")
kev_block = any(e["cve"] == "CVE-2026-48710" and e["decision"] == "block"
                for e in P["gates"]["08"]["entries"])
lines.append(f"- Gate 8 planted ranks CVE-2026-48710 in the block group (KEV): "
             f"**{'PASS' if kev_block else 'FAIL'}**")
if C['gates']['04']['validate_passed'] and P['gates']['04']['validate_passed']:
    lines.append("- Gate 4 both variants: terraform validate = PASS "
                 "(clean) / PASS (planted) — after the M5 refactor split the security group "
                 "rules into separate resources, the reference cycle "
                 "is gone; details in each run's validate.json. "
                 "terraform plan JSON still cannot be generated locally because plan "
                 "needs to call the real AWS API (data source aws_availability_zones).")
else:
    lines.append(f"- Gate 4 both variants: terraform validate = "
                 f"{'PASS' if C['gates']['04']['validate_passed'] else 'FAIL'} "
                 f"(clean) / {'PASS' if P['gates']['04']['validate_passed'] else 'FAIL'} "
                 f"(planted) — recorded in each run's validate.json.")
lines.append("")
(VER / "results.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
