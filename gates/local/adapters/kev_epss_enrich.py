#!/usr/bin/env python3
"""Gate 8 — làm giàu danh sách lỗ hổng (từ gate 3, và tuỳ chọn gate 5)
bằng feed thật CISA KEV + FIRST EPSS, sinh:
  1. input cho policy devsecops.dependency_kev,
  2. evidence record `vuln-risk-ranking` (quyết định block/issue + hạn).
Feed được tải bởi gate-08.sh vào thư mục cache dùng chung của lần chạy.
"""
import argparse
import csv
import gzip
import json
from datetime import date, timedelta
from pathlib import Path


def load_kev(path):
    doc = json.loads(Path(path).read_text())
    ids = {v["cveID"] for v in doc.get("vulnerabilities", [])}
    return ids, doc.get("catalogVersion", "unknown")


def load_epss(path):
    scores, model = {}, "unknown"
    with gzip.open(path, "rt") as fh:
        first = fh.readline().strip()
        if first.startswith("#model_version:"):
            model = first.split(":", 1)[1].split(",")[0]
        rd = csv.DictReader((l for l in fh if not l.startswith("#")))
        for row in rd:
            try:
                scores[row["cve"]] = float(row["epss"])
            except (KeyError, ValueError):
                continue
    return scores, model


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--normalized", required=True,
                    help="JSON từ osv_normalize.py (gate 3)")
    ap.add_argument("--image-vulns", help="JSON lỗ hổng image từ gate 5 (tuỳ chọn)")
    ap.add_argument("--kev", required=True)
    ap.add_argument("--epss", required=True)
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--out-input", required=True)
    ap.add_argument("--out-ranking", required=True)
    a = ap.parse_args()

    kev_ids, kev_ver = load_kev(a.kev)
    epss_scores, epss_model = load_epss(a.epss)

    norm = json.loads(Path(a.normalized).read_text())
    deps = norm["dependencies"]
    vulns = [dict(v) for v in norm["vulnerabilities"]]
    if a.image_vulns and Path(a.image_vulns).exists():
        for v in json.loads(Path(a.image_vulns).read_text()):
            vulns.append(v)

    today = date.today()
    enriched, entries = [], []
    for v in vulns:
        in_kev = v["id"] in kev_ids
        epss = epss_scores.get(v["id"])
        enriched.append({
            "id": v["id"], "package": v["package"],
            "affected": v.get("affected", ">=0"), "fixed": v.get("fixed"),
            "in_kev": in_kev, "epss": epss if epss is not None else 0.0,
        })
        block = in_kev or (epss is not None and epss >= a.threshold)
        entries.append({
            "cve": v["id"], "package": v["package"],
            "version": v.get("version"), "in_kev": in_kev, "epss": epss,
            "decision": "block" if block else "issue",
            "due": today.isoformat() if block
                   else (today + timedelta(days=30)).isoformat(),
        })

    doc = {"dependencies": deps, "vulnerabilities": enriched,
           "config": {"epss_threshold": a.threshold}}
    Path(a.out_input).write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    ranking = {
        "evidence_type": "vuln-risk-ranking",
        "period": today.isoformat(),
        "entries": entries,
        "feed_versions": {"kev_catalog": kev_ver, "epss_model": epss_model},
    }
    Path(a.out_ranking).write_text(
        json.dumps(ranking, indent=2, ensure_ascii=False) + "\n")
    nb = sum(1 for e in entries if e["decision"] == "block")
    print(f"[kev_epss] {len(entries)} lỗ hổng đã xếp hạng: {nb} block, "
          f"{len(entries) - nb} issue (KEV catalog {kev_ver}, EPSS {epss_model})")
    for e in entries:
        print(f"    - {e['cve']} {e['package']}=={e['version']}: "
              f"in_kev={e['in_kev']} epss={e['epss']} -> {e['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
