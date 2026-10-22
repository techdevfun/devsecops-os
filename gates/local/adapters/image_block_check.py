#!/usr/bin/env python3
"""Gate 5 — tổng hợp kết quả quét image của Trivy: đếm theo severity và
áp quy tắc chặn của blueprint cho gate 5 (CVE CRITICAL có bản vá VÀ
thuộc CISA KEV). Đồng thời xuất danh sách lỗ hổng chuẩn hoá để gate 8
xếp hạng chung với gate 3.
"""
import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trivy-json", required=True)
    ap.add_argument("--kev", required=True)
    ap.add_argument("--out-vulns", required=True)
    ap.add_argument("--out-summary", required=True)
    a = ap.parse_args()

    kev = json.loads(Path(a.kev).read_text())
    kev_ids = {v["cveID"] for v in kev.get("vulnerabilities", [])}
    raw = json.loads(Path(a.trivy_json).read_text())

    counts, vulns, blocking = {}, [], []
    for result in raw.get("Results", []) or []:
        for v in result.get("Vulnerabilities", []) or []:
            sev = v.get("Severity", "UNKNOWN")
            counts[sev] = counts.get(sev, 0) + 1
            fixed = (v.get("FixedVersion") or "").split(",")[0].strip() \
                or None
            entry = {"id": v.get("VulnerabilityID"),
                     "package": v.get("PkgName"),
                     "version": v.get("InstalledVersion"),
                     "affected": ">=0", "fixed": fixed}
            vulns.append(entry)
            if sev == "CRITICAL" and fixed and entry["id"] in kev_ids:
                blocking.append(entry)
    Path(a.out_vulns).write_text(
        json.dumps(vulns, indent=2, ensure_ascii=False) + "\n")
    summary = {"counts_by_severity": counts, "total": len(vulns),
               "blocking_critical_fixed_kev": blocking}
    Path(a.out_summary).write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(f"[image_block_check] tổng {len(vulns)} lỗ hổng {counts}; "
          f"thuộc nhóm chặn (CRITICAL+fixed+KEV): {len(blocking)}")
    for b in blocking:
        print(f"    - {b['id']} {b['package']}=={b['version']} fixed={b['fixed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
