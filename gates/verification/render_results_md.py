#!/usr/bin/env python3
"""Kết xuất gates/verification/results.md từ results.json (mọi con số
đều từ lần chạy kiểm chứng thật; file này không chứa số gõ tay)."""
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
        return f"policy {g['decision']} ({g['violations']} vi phạm)"
    if gate == "02":
        return f"{g['findings']} finding {g.get('by_severity') or ''} — report-only"
    if gate == "03":
        return f"{len(g['vulns'])} lỗ hổng: {', '.join(g['vulns']) or '—'}"
    if gate == "04":
        pols = "; ".join(
            f"{k}={v['decision']}({v['violations']})"
            for k, v in g["policies"].items())
        return (f"validate={'PASS' if g['validate_passed'] else 'FAIL'}; "
                f"{pols}; trivy-config={g['trivy_config_misconfigs']} misconfig")
    if gate == "05":
        return (f"image {g['image_total']} CVE {g['image_counts'] or ''}; "
                f"nhóm chặn KEV={g['blocking_kev_criticals']}; "
                f"base_image={g['base_image_decision']}({g['base_image_violations']})")
    if gate == "06":
        return (f"provenance {g['decision']}; SBOM {g['components']} components, "
                f"signed={g['signed']}")
    if gate == "07":
        return f"license_policy {g['decision']} ({g['violations']} vi phạm)"
    if gate == "08":
        blocks = [e["cve"] for e in g["entries"] if e["decision"] == "block"]
        return (f"dependency_kev {g['decision']} ({g['violations']} vi phạm); "
                f"{len(g['entries'])} mục xếp hạng, block: {blocks or '—'}")
    if gate == "09":
        return f"pipeline_policy {g['decision']} ({g['violations']} vi phạm)"
    if gate == "10":
        return g["state"]
    return ""


NAMES = {
    "01": "Secret scanning", "02": "SAST", "03": "SCA",
    "04": "IaC scanning", "05": "Container scanning",
    "06": "SBOM + attestation", "07": "License compliance",
    "08": "EPSS/CISA KEV", "09": "Vệ sinh pipeline",
    "10": "AI PR Review Gate",
}

lines = []
lines.append("# Kết quả kiểm chứng M3 — bộ CI gates chạy thật trên workload mẫu")
lines.append("")
lines.append("Sinh tự động từ `results.json` (đầu ra thật của các gate) bằng")
lines.append("`render_results_md.py`. Log thô từng gate: `gates/verification/logs/`.")
lines.append("Bằng chứng từng lần chạy: `evidence/output/local-<biến thể>/`.")
lines.append("")
lines.append("Quy ước mã thoát: 0 = qua; 1 = bị chặn theo điều kiện chặn mặc")
lines.append("định của blueprint; 2 = lỗi hạ tầng (kèm scan-error.json).")
lines.append("")
lines.append("| Gate | Clean — kết quả (mã thoát, giây) | Planted — kết quả (mã thoát, giây) |")
lines.append("|---|---|---|")
for g in [f"{i:02d}" for i in range(1, 11)]:
    ce, cs = cell(C, g)
    pe, ps = cell(P, g)
    lines.append(
        f"| {g} {NAMES[g]} | exit {ce}, {cs}s — {detail(C, g)} "
        f"| exit {pe}, {ps}s — {detail(P, g)} |")
lines.append("")
lines.append(f"Tổng thời gian chạy tuần tự (cục bộ, cache đã ấm): "
             f"clean {C['total_seconds']}s, planted {P['total_seconds']}s. "
             f"Gate lâu nhất: {max(C['max_gate_seconds'], P['max_gate_seconds'])}s.")
lines.append("")
lines.append("## Đối chiếu kỳ vọng bắt buộc của M3")
lines.append("")
exp_clean = all(C["timing"][g]["exit"] == 0 for g in C["timing"])
lines.append(f"- Clean qua mọi gate (mọi mã thoát = 0): "
             f"**{'ĐẠT' if exp_clean else 'KHÔNG ĐẠT'}**")
for g, want in (("01", 1), ("04", 1), ("05", 1), ("08", 1)):
    got = P["timing"][g]["exit"]
    lines.append(f"- Planted bị chặn ở gate {g} (mã thoát 1): "
                 f"**{'ĐẠT' if got == want else f'KHÔNG ĐẠT (exit {got})'}**")
for g in ("02", "03", "06", "07", "09", "10"):
    got = P["timing"][g]["exit"]
    lines.append(f"- Planted KHÔNG bị chặn ở gate {g} (mã thoát 0): "
                 f"**{'ĐẠT' if got == 0 else f'KHÔNG ĐẠT (exit {got})'}**")
lines.append(f"- Gate 3 planted phát hiện CVE-2026-48710: "
             f"**{'ĐẠT' if 'CVE-2026-48710' in P['gates']['03']['vulns'] else 'KHÔNG ĐẠT'}**")
kev_block = any(e["cve"] == "CVE-2026-48710" and e["decision"] == "block"
                for e in P["gates"]["08"]["entries"])
lines.append(f"- Gate 8 planted xếp CVE-2026-48710 vào nhóm block (KEV): "
             f"**{'ĐẠT' if kev_block else 'KHÔNG ĐẠT'}**")
if C['gates']['04']['validate_passed'] and P['gates']['04']['validate_passed']:
    lines.append("- Gate 4 cả hai biến thể: terraform validate = PASS "
                 "(clean) / PASS (planted) — sau refactor M5 tách rule "
                 "security group sang tài nguyên riêng, vòng tham chiếu "
                 "đã hết; chi tiết trong validate.json của từng lần chạy. "
                 "terraform plan JSON vẫn chưa sinh được tại chỗ vì plan "
                 "cần gọi AWS API thật (data source aws_availability_zones).")
else:
    lines.append(f"- Gate 4 cả hai biến thể: terraform validate = "
                 f"{'PASS' if C['gates']['04']['validate_passed'] else 'FAIL'} "
                 f"(clean) / {'PASS' if P['gates']['04']['validate_passed'] else 'FAIL'} "
                 f"(planted) — ghi trong validate.json của từng lần chạy.")
lines.append("")
(VER / "results.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
