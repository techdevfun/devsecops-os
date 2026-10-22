#!/usr/bin/env python3
"""Gate 7 — chuyển SBOM CycloneDX (Syft, gate 6) thành input cho policy
devsecops.license_policy: {components: [{name, version, license}],
config: {denied_licenses}}. License lấy từ khai báo của component;
biểu thức (AND/OR) được tách thành từng license để policy đối chiếu.
"""
import argparse
import json
import re
from pathlib import Path

DENIED = ["GPL-3.0-only", "GPL-3.0-or-later", "AGPL-3.0-only",
          "AGPL-3.0-or-later", "SSPL-1.0"]


def component_licenses(comp):
    out = []
    for entry in comp.get("licenses", []) or []:
        lic = entry.get("license", {}) or {}
        if lic.get("id"):
            out.append(lic["id"])
        elif lic.get("name"):
            out.append(lic["name"])
        elif entry.get("expression"):
            out.extend(t for t in re.split(r"\s+(?:AND|OR|WITH)\s+|\s+",
                                            entry["expression"].strip("()"))
                       if t and t not in ("AND", "OR", "WITH"))
    return out or ["NOASSERTION"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sbom", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    sbom = json.loads(Path(a.sbom).read_text())
    components = []
    for comp in sbom.get("components", []) or []:
        for lic in component_licenses(comp):
            components.append({"name": comp.get("name"),
                               "version": comp.get("version"),
                               "license": lic})
    doc = {"components": components, "config": {"denied_licenses": DENIED}}
    Path(a.out).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"[syft_license_input] {len(components)} component-license -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
