#!/usr/bin/env python3
"""Chuyển báo cáo JSON của gitleaks (gate 1) thành input chuẩn hoá cho
policy devsecops.secret_findings — thay bộ trích xuất regex của harness
M2 bằng đầu ra scanner thật. File trong input được ghi tương đối theo
thư mục workload để khớp định dạng pack.
"""
import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gitleaks-json", required=True)
    ap.add_argument("--workload", required=True)
    ap.add_argument("--scan-date", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    raw_path = Path(a.gitleaks_json)
    raw = json.loads(raw_path.read_text()) if raw_path.exists() and \
        raw_path.read_text().strip() else []
    workload = Path(a.workload).resolve()
    findings = []
    for f in raw:
        fp = Path(f.get("File", ""))
        try:
            rel = str(fp.resolve().relative_to(workload))
        except (ValueError, OSError):
            rel = str(fp)
        match = f.get("Match", "") or f.get("Secret", "")
        findings.append({
            "file": rel,
            "line": f.get("StartLine"),
            "rule": f.get("RuleID"),
            "match_preview": (match[:12] + "...") if match else "",
            "allowlisted_until": None,
        })
    doc = {"findings": findings, "scan_date": a.scan_date}
    Path(a.out).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"[gitleaks_input] {len(findings)} finding -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
