#!/usr/bin/env python3
"""Normalize osv-scanner's JSON output (gate 3) into:
  { "dependencies": [...], "vulnerabilities": [...] }
where each vulnerability has a CVE id (preferring the CVE alias), package,
affected as the pack's constraint string (">=a,<b"), and fixed (the first fix
version). in_kev/epss are filled in by gate 8 (kev_epss_enrich.py) from the real feeds.
"""
import argparse
import json
from pathlib import Path


def range_string(vuln) -> tuple[str, str | None]:
    lo, hi, fixed = None, None, None
    for aff in vuln.get("affected", []):
        for rng in aff.get("ranges", []) or []:
            if rng.get("type") != "ECOSYSTEM":
                continue
            for ev in rng.get("events", []):
                if "introduced" in ev and lo is None:
                    lo = ev["introduced"]
                if "fixed" in ev and fixed is None:
                    fixed = ev["fixed"]
                    hi = ev["fixed"]
    parts = []
    if lo is not None:
        parts.append(f">={lo}")
    if hi is not None:
        parts.append(f"<{hi}")
    return (",".join(parts) if parts else ">=0"), fixed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--osv-json", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    raw = json.loads(Path(a.osv_json).read_text())
    deps, vulns, seen = [], [], set()
    for result in raw.get("results", []):
        for pkg in result.get("packages", []):
            p = pkg.get("package", {})
            dep = {"name": p.get("name"), "version": p.get("version"),
                   "ecosystem": p.get("ecosystem")}
            key = (dep["name"], dep["version"])
            if key not in seen:
                seen.add(key)
                deps.append(dep)
            for v in pkg.get("vulnerabilities", []) or []:
                aliases = v.get("aliases", []) or []
                cve = next((x for x in aliases if x.startswith("CVE-")),
                           v.get("id"))
                affected, fixed = range_string(v)
                entry = {
                    "id": cve, "osv_id": v.get("id"),
                    "package": p.get("name"), "version": p.get("version"),
                    "affected": affected, "fixed": fixed,
                    "summary": (v.get("summary") or "")[:200],
                }
                # OSV often returns the same CVE via multiple sources (PYSEC +
                # GHSA) — deduplicate by (CVE, package, version), preferring
                # the record that has a fixed version.
                dup = next((x for x in vulns
                            if (x["id"], x["package"], x["version"])
                            == (cve, entry["package"], entry["version"])),
                           None)
                if dup is None:
                    vulns.append(entry)
                elif dup["fixed"] is None and fixed is not None:
                    dup.update(entry)
    doc = {"dependencies": deps, "vulnerabilities": vulns}
    Path(a.out).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"[osv_normalize] {len(deps)} dependency, "
          f"{len(vulns)} vulnerability -> {a.out}")
    for v in vulns:
        print(f"    - {v['package']}=={v['version']}: {v['id']} "
              f"({v['osv_id']}) affected={v['affected']} fixed={v['fixed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
