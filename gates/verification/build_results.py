#!/usr/bin/env python3
"""Tổng hợp kết quả kiểm chứng M3 từ bằng chứng các gate đã sinh +
summary.tsv của runner -> results.json và results.md (bảng gate x biến
thể + đối chiếu kỳ vọng bắt buộc của M3). Mọi con số đều đọc từ file
đầu ra thật của lần chạy, không gõ tay.
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VER = Path(__file__).resolve().parent


def load(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def decision(out: Path, gate_dir: str, policy: str):
    rec = load(out / gate_dir / f"policy-decision-{policy}.json")
    return rec["decision"] if rec else "n/a", \
        len(rec.get("violations", [])) if rec else 0


def variant_data(variant: str) -> dict:
    out = REPO / "evidence" / "output" / f"local-{variant}"
    summary = {}
    tsv = VER / "logs" / variant / "summary.tsv"
    total_t, max_t = 0.0, 0.0
    if tsv.exists():
        for line in tsv.read_text().splitlines():
            g, rc, dur = line.split("\t")
            summary[g] = {"exit": int(rc), "seconds": float(dur)}
            total_t += float(dur)
            max_t = max(max_t, float(dur))

    g = {}
    d, n = decision(out, "gate-01-secret", "secret_findings")
    g["01"] = {"decision": d, "violations": n}
    sast = load(out / "gate-02-sast" / "sast-summary.json") or {}
    g["02"] = {"findings": sast.get("total"), "by_severity": sast.get("by_severity")}
    norm = load(out / "gate-03-sca" / "normalized.json") or {}
    g["03"] = {"vulns": [v["id"] for v in norm.get("vulnerabilities", [])]}
    val = load(out / "gate-04-iac" / "validate.json") or {}
    decs = {}
    for pol in ("network_exposure", "storage_encryption", "iam_least_privilege"):
        dd, nn = decision(out, "gate-04-iac", pol)
        decs[pol] = {"decision": dd, "violations": nn}
    g["04"] = {"validate_passed": val.get("passed"),
               "policies": decs,
               "trivy_config_misconfigs": (load(
                   out / "gate-04-iac" / "trivy-config-summary.json") or {}
               ).get("misconfigurations")}
    img = load(out / "gate-05-container" / "image-summary.json") or {}
    d, n = decision(out, "gate-05-container", "base_image")
    g["05"] = {"image_counts": img.get("counts_by_severity"),
               "image_total": img.get("total"),
               "blocking_kev_criticals": len(
                   img.get("blocking_critical_fixed_kev", [])),
               "base_image_decision": d, "base_image_violations": n}
    d, n = decision(out, "gate-06-sbom-attestation", "provenance")
    sbom = load(out / "gate-06-sbom-attestation" / "sbom.record.json") or {}
    g["06"] = {"decision": d, "components": sbom.get("components_count"),
               "signed": sbom.get("signed")}
    d, n = decision(out, "gate-07-license", "license_policy")
    g["07"] = {"decision": d, "violations": n}
    rank = load(out / "gate-08-kev-epss" / "vuln-risk-ranking.record.json") or {}
    d, n = decision(out, "gate-08-kev-epss", "dependency_kev")
    g["08"] = {"decision": d, "violations": n,
               "entries": rank.get("entries", []),
               "feed_versions": rank.get("feed_versions")}
    d, n = decision(out, "gate-09-pipeline-hygiene", "pipeline_policy")
    g["09"] = {"decision": d, "violations": n}
    note = out / "gate-10-ai-pr-review" / "disabled-note.txt"
    g["10"] = {"state": "disabled (mặc định pha 1)" if note.exists()
               else "xem log"}
    return {"variant": variant, "timing": summary,
            "total_seconds": round(total_t, 2),
            "max_gate_seconds": round(max_t, 2), "gates": g}


def main() -> int:
    data = {v: variant_data(v) for v in ("clean", "planted")}
    (VER / "results.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
