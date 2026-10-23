#!/usr/bin/env python3
"""Gate 4 — generate the normalized input for the pack's 3 IaC policies
(network_exposure, storage_encryption, iam_least_privilege) from the output
of a standard HCL2 parser (`conftest parse`, Open Policy Agent project),
REPLACING the M2 harness's regex extractor.

Why not Terraform plan JSON: after the M5 refactor (SG rules split out
into aws_vpc_security_group_*_rule), `terraform validate` PASSes,
but `terraform plan` still needs permission to call the real AWS API for data source
aws_availability_zones — the verification environment has no real AWS credentials,
so plan JSON cannot be generated here. The HCL2 parser yields the same model
of the declared resources; ${var.*} references are resolved from the
defaults in variables.tf, and resource references keep address form.
Standalone-resource rules (aws_vpc_security_group_ingress_rule) are
merged into the target SG's ingress list, keeping the output format unchanged.

The output format is UNCHANGED from the pack: {security_groups, storage,
iam_policies, managed_policy_attachments}.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def conftest_parse(conftest, path):
    r = subprocess.run([conftest, "parse", str(path)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"conftest parse error ({path}): {r.stderr.strip()}")
    return json.loads(r.stdout)


def bodies(parsed, rtype):
    """resource.<type>.<name> -> {name: body} (conftest wraps each body in a list)."""
    out = {}
    for name, items in (parsed.get("resource", {}).get(rtype, {}) or {}).items():
        out[name] = items[0] if isinstance(items, list) else items
    return out


def var_defaults(parsed_vars):
    defaults = {}
    for name, items in (parsed_vars.get("variable", {}) or {}).items():
        body = items[0] if isinstance(items, list) else items
        if isinstance(body, dict) and "default" in body:
            defaults[name] = body["default"]
    return defaults


def resolve(value, defaults):
    if isinstance(value, str):
        m = re.fullmatch(r"\$\{var\.([A-Za-z0-9_]+)\}", value)
        if m and m.group(1) in defaults:
            return defaults[m.group(1)]
        m = re.fullmatch(r"\$\{([A-Za-z0-9_.]+)\.id\}", value)
        if m:
            return f"{m.group(1)}.id"
        return value
    if isinstance(value, list):
        return [resolve(v, defaults) for v in value]
    return value


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conftest", required=True)
    ap.add_argument("--infra", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    infra = Path(a.infra)
    parsed = conftest_parse(a.conftest, infra / "main.tf")
    defaults = var_defaults(conftest_parse(a.conftest, infra / "variables.tf"))

    # An SG attached to an Internet-facing LB (internal=false) is the "public web" SG.
    lbs = bodies(parsed, "aws_lb")
    public_sgs = set()
    for lb in lbs.values():
        if lb.get("internal") is False:
            for ref in lb.get("security_groups", []) or []:
                m = re.search(r"aws_security_group\.([A-Za-z0-9_]+)\.id",
                              str(ref))
                if m:
                    public_sgs.add(m.group(1))

    sgs = []
    for name, body in bodies(parsed, "aws_security_group").items():
        ingress = []
        for rule in body.get("ingress", []) or []:
            cidrs = rule.get("cidr_blocks")
            cidrs = resolve(cidrs, defaults) if cidrs is not None else []
            if isinstance(cidrs, str):
                cidrs = [cidrs]
            ingress.append({
                "from_port": resolve(rule.get("from_port"), defaults),
                "to_port": resolve(rule.get("to_port"), defaults),
                "cidr_blocks": cidrs or [],
                "security_groups": [
                    resolve(s, defaults)
                    for s in (rule.get("security_groups") or [])],
            })
        sgs.append({"name": f"aws_security_group.{name}",
                    "public_web": name in public_sgs, "ingress": ingress})

    # Standalone-resource ingress rules (aws_vpc_security_group_
    # ingress_rule — the standard form after the M5 refactor): merge into the
    # target SG's ingress so the policy input format is unchanged.
    by_sg_name = {sg["name"]: sg for sg in sgs}
    standalone = bodies(parsed, "aws_vpc_security_group_ingress_rule")
    for body in standalone.values():
        sg_ref = resolve(body.get("security_group_id"), defaults)
        m = re.search(r"aws_security_group\.([A-Za-z0-9_]+)", str(sg_ref))
        if not m:
            continue
        target = by_sg_name.get(f"aws_security_group.{m.group(1)}")
        if target is None:
            continue
        cidrs = []
        cidr4 = body.get("cidr_ipv4")
        if cidr4 is not None:
            if str(cidr4).strip() == "${each.value}":
                # for_each over a list variable: expand using
                # the variable's default (for example allowed_ingress_cidrs).
                vm = re.search(r"var\.([A-Za-z0-9_]+)",
                               str(body.get("for_each", "")))
                if vm and isinstance(defaults.get(vm.group(1)), list):
                    cidrs = list(defaults[vm.group(1)])
            else:
                cidrs = [resolve(cidr4, defaults)]
        ref_sgs = []
        ref = body.get("referenced_security_group_id")
        if ref:
            ref_sgs = [resolve(ref, defaults)]
        target["ingress"].append({
            "from_port": resolve(body.get("from_port"), defaults),
            "to_port": resolve(body.get("to_port"), defaults),
            "cidr_blocks": cidrs,
            "security_groups": ref_sgs,
        })

    pab = bodies(parsed, "aws_s3_bucket_public_access_block")
    sse = bodies(parsed, "aws_s3_bucket_server_side_encryption_configuration")
    storage = []
    for name in bodies(parsed, "aws_s3_bucket"):
        p = next(iter(pab.values()), {}) if pab else {}
        flags = [p.get(k) for k in ("block_public_acls", "block_public_policy",
                                     "ignore_public_acls",
                                     "restrict_public_buckets")]
        storage.append({
            "address": f"aws_s3_bucket.{name}", "type": "aws_s3_bucket",
            "encryption_enabled": bool(sse),
            "public_access_blocked": bool(pab) and all(f is True for f in flags),
        })

    attachments = []
    for body in bodies(parsed, "aws_iam_role_policy_attachment").values():
        role_ref = str(body.get("role", ""))
        m = re.search(r"aws_iam_role\.([A-Za-z0-9_]+)\.", role_ref)
        attachments.append({
            "role": f"aws_iam_role.{m.group(1)}" if m else role_ref,
            "policy_arn": body.get("policy_arn"),
        })

    doc = {"security_groups": sgs, "storage": storage,
           "iam_policies": [], "managed_policy_attachments": attachments}
    Path(a.out).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"[tf_parse_input] {len(sgs)} SG, {len(storage)} storage, "
          f"{len(attachments)} IAM attachment -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
