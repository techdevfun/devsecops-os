#!/usr/bin/env python3
"""Sinh input JSON chuẩn hoá cho các policy từ file THẬT của workload
payments-sample (cả hai biến thể clean/ và planted/).

Đây là bộ trích xuất tham chiếu của pack v1: ở M3, lớp này được thay/bổ
sung bằng đầu ra thật của Terraform plan JSON, gitleaks, osv-scanner,
Syft và Trivy — nhưng định dạng input của policy KHÔNG đổi.

Cách dùng:
    python3 build_workload_fixtures.py [thư-mục-workload] [thư-mục-đầu-ra]

Đầu ra (mỗi biến thể): tf.json, secrets.json, deps.json, docker.json
"""
import json
import re
import sys
from pathlib import Path

SECRET_PATTERNS = [
    ("stripe-like-key", re.compile(r"sk_live_[A-Za-z0-9]{8,}")),
    ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----")),
    ("generic-token-assignment", re.compile(
        r"(?i)(api[_-]?key|secret|password)\s*=\s*[\"'][A-Za-z0-9_\-]{16,}[\"']")),
]

KEV_REFERENCE = [{
    "id": "CVE-2026-48710", "package": "starlette",
    "affected": ">=0.8.3,<1.0.1", "fixed": "1.0.1",
    "in_kev": True, "epss": 0.42,
    "_source": "PLANTED.md (CISA KEV catalog 2026.10.21 + GHSA-86qp-5c8j-p5mr, "
               "đối chiếu 2026-10-22). Ở production, dữ liệu này do gate 3/8 "
               "nạp từ OSV + feed CISA KEV/EPSS tại thời điểm chạy.",
}]

EOL_IMAGES = [
    {"image": "python", "tag_prefix": "3.10", "eol": "2026-04-01",
     "note": "CPython 3.10 EOL thang 4/2026"},
    {"image": "python", "tag_contains": "bullseye", "eol": "2024-08-01",
     "note": "Debian bullseye het ho tro thuong"},
    {"image": "python", "tag_prefix": "3.11", "eol": "2027-04-01",
     "note": "CPython 3.11 EOL thang 4/2027 (du phong)"},
]


def parse_app_port(vars_tf: str) -> int:
    m = re.search(r'variable\s+"app_port"\s*\{(.*?)\}', vars_tf, re.S)
    if m:
        d = re.search(r"default\s*=\s*(\d+)", m.group(1))
        if d:
            return int(d.group(1))
    return 8000


def resolve(expr: str, app_port: int):
    expr = expr.strip()
    if expr == "var.app_port":
        return app_port
    if re.fullmatch(r"\d+", expr):
        return int(expr)
    return expr


def extract_tf(variant_dir: Path) -> dict:
    tf = (variant_dir / "infra" / "main.tf").read_text()
    vars_tf = (variant_dir / "infra" / "variables.tf").read_text()
    app_port = parse_app_port(vars_tf)

    sgs = []
    # Tìm từng resource aws_security_group và các ingress block trong nó.
    for m in re.finditer(
            r'resource\s+"aws_security_group"\s+"(\w+)"\s*\{(.*?)\n\}',
            tf, re.S):
        name, body = m.group(1), m.group(2)
        ingress = []
        for im in re.finditer(r"ingress\s*\{(.*?)\}", body, re.S):
            blk = im.group(1)
            fp = re.search(r"from_port\s*=\s*(\S+)", blk)
            tp = re.search(r"to_port\s*=\s*(\S+)", blk)
            cidrs = re.search(r"cidr_blocks\s*=\s*\[(.*?)\]", blk, re.S)
            cidr_list = (re.findall(r'"([^"]+)"', cidrs.group(1))
                         if cidrs else [])
            sgs_ref = re.findall(r"security_groups\s*=\s*\[(.*?)\]", blk, re.S)
            ingress.append({
                "from_port": resolve(fp.group(1), app_port) if fp else None,
                "to_port": resolve(tp.group(1), app_port) if tp else None,
                "cidr_blocks": cidr_list,
                "security_groups": sgs_ref,
            })
        sgs.append({"name": f"aws_security_group.{name}",
                    "public_web": False, "ingress": ingress})

    # Rule ingress dạng tài nguyên riêng (aws_vpc_security_group_
    # ingress_rule — dạng chuẩn sau refactor M5): gộp vào ingress của
    # SG đích, giữ nguyên định dạng fixture. cidr_ipv4 = each.value
    # (for_each trên biến) không phân giải được ở lớp regex này -> để
    # rỗng, đúng như cách biến cidr_blocks tham chiếu var được xử lý
    # trước refactor.
    by_sg_name = {sg["name"]: sg for sg in sgs}
    for rm in re.finditer(
            r'resource\s+"aws_vpc_security_group_ingress_rule"\s+"(\w+)"'
            r'\s*\{(.*?)\n\}',
            tf, re.S):
        blk = rm.group(2)
        tgt = re.search(
            r"security_group_id\s*=\s*aws_security_group\.(\w+)\.id", blk)
        if not tgt:
            continue
        sg = by_sg_name.get(f"aws_security_group.{tgt.group(1)}")
        if sg is None:
            continue
        fp = re.search(r"from_port\s*=\s*(\S+)", blk)
        tp = re.search(r"to_port\s*=\s*(\S+)", blk)
        cidr = re.search(r'cidr_ipv4\s*=\s*"([^"]+)"', blk)
        ref = re.search(
            r"referenced_security_group_id\s*=\s*(aws_security_group\.\w+\.id)",
            blk)
        sg["ingress"].append({
            "from_port": resolve(fp.group(1), app_port) if fp else None,
            "to_port": resolve(tp.group(1), app_port) if tp else None,
            "cidr_blocks": [cidr.group(1)] if cidr else [],
            "security_groups": [ref.group(1)] if ref else [],
        })

    has_sse = "aws_s3_bucket_server_side_encryption_configuration" in tf
    pab = None
    pm = re.search(
        r'resource\s+"aws_s3_bucket_public_access_block"[^{]*\{(.*?)\}',
        tf, re.S)
    if pm:
        pab = all(v.strip() == "true" for v in
                  re.findall(r"=\s*(true|false)", pm.group(1))) \
            and len(re.findall(r"=\s*(true|false)", pm.group(1))) >= 4
    storage = [{
        "address": "aws_s3_bucket.artefacts", "type": "aws_s3_bucket",
        "encryption_enabled": has_sse, "public_access_blocked": bool(pab),
    }]
    # Một file tf.json dùng chung: network_exposure đọc security_groups,
    # storage_encryption đọc storage, iam_least_privilege đọc từ plan ở M3.
    return {"security_groups": sgs, "storage": storage}


def extract_secrets(variant_dir: Path) -> dict:
    findings = []
    for path in sorted(variant_dir.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for rule, pat in SECRET_PATTERNS:
                m = pat.search(line)
                if m:
                    findings.append({
                        "file": str(path.relative_to(variant_dir)),
                        "line": i, "rule": rule,
                        "match_preview": m.group(0)[:12] + "...",
                        "allowlisted_until": None,
                    })
    return {"findings": findings, "scan_date": "2026-10-22"}


def extract_deps(variant_dir: Path) -> dict:
    deps = []
    for line in (variant_dir / "backend" / "requirements.txt").read_text().splitlines():
        line = line.strip()
        m = re.match(r"^([A-Za-z0-9_.\-]+)==([0-9][^;\s]*)$", line)
        if m:
            deps.append({"name": m.group(1), "version": m.group(2),
                         "ecosystem": "pip"})
    return {"dependencies": deps, "vulnerabilities": KEV_REFERENCE,
            "config": {"epss_threshold": 0.5}}


def extract_docker(variant_dir: Path) -> dict:
    images = []
    for line in (variant_dir / "Dockerfile").read_text().splitlines():
        m = re.match(r"\s*FROM\s+(\S+)", line)
        if m:
            ref = m.group(1)
            if ":" in ref:
                image, tag = ref.rsplit(":", 1)
            else:
                image, tag = ref, "latest"
            images.append({"image": image, "tag": tag, "digest": None})
    return {"dockerfiles": [{"path": "Dockerfile", "images": images}],
            "eol_images": EOL_IMAGES}


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        __file__).resolve().parents[2] / "examples" / "payments-sample"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(
        __file__).resolve().parent / "workload-fixtures"
    for variant in ("clean", "planted"):
        vdir = root / variant
        o = out / variant
        o.mkdir(parents=True, exist_ok=True)
        (o / "tf.json").write_text(json.dumps(
            extract_tf(vdir), indent=2, sort_keys=True))
        (o / "secrets.json").write_text(json.dumps(
            extract_secrets(vdir), indent=2, sort_keys=True))
        (o / "deps.json").write_text(json.dumps(
            extract_deps(vdir), indent=2, sort_keys=True))
        (o / "docker.json").write_text(json.dumps(
            extract_docker(vdir), indent=2, sort_keys=True))
        print(f"[build] {variant}: tf/secrets/deps/docker -> {o}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
