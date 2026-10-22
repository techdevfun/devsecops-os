#!/usr/bin/env python3
"""devsecops-os — bộ sinh bằng chứng quyết định/định kỳ (M5-A3).

Bốn loại bằng chứng của bản đồ pha 1 mà KHÔNG gate CI nào sinh ra
trong một lần chạy PR — vì chúng thuộc lớp quyết định (merge/release)
hoặc là việc theo kỳ/lịch — được sinh ở đây từ dữ liệu thật trong cây,
đúng schema M2 (policies/evidence-schemas):

  change-record          hồ sơ thay đổi của một lần chạy: kết quả
                         gate thật (đọc từ các policy-decision của
                         lần chạy) + phê duyệt + liên kết bằng chứng.
                         Kèm theo: policy devsecops.change_record
                         được chạy THẬT bằng OPA trên record vừa
                         sinh và quyết định của nó được ghi thành
                         một policy-decision record đi kèm.
  drift-report           so cấu hình IaC hiện tại (parse bằng đúng
                         adapter HCL2 của gate 4) với baseline đã khai
                         trong evidence/baselines/ — lệch ở đâu ghi
                         ở đó. Kèm policy-decision của
                         devsecops.drift_control chạy thật bằng OPA.
  access-review-report   rà soát quyền theo kỳ: permissions của mọi
                         workflow trong cây + mẫu OIDC trust policy.
  config-baseline-report báo cáo cấu hình theo môi trường: chạy 3
                         policy nhóm cấu hình của gate 4 (network /
                         storage / IAM) trên workload chỉ định, cộng
                         kiểm tra cấu hình repo (branch protection,
                         quyền workflow).

Mọi record sinh ra được ghi vào thư mục `supplementary-records/`
của lần chạy (mặc định) — collector của M4 (bundle_tool.py) quét
thư mục này như một nguồn record phụ trợ và kiểm schema như mọi
record khác. Không record nào bịa dữ liệu: trường nào không có
nguồn thật (ví dụ phê duyệt PR ở lần chạy cục bộ) thì ghi đúng
giá trị thật (rỗng) kèm ghi chú — chính policy change_record sẽ
deny vì thiếu phê duyệt, và quyết định deny đó cũng là bằng chứng.

Chỉ dùng thư viện chuẩn của Python 3 (cùng nguyên tắc với
bundle_tool.py). OPA/conftest là binary ngoài, tìm theo thứ tự:
tham số dòng lệnh > biến môi trường > ~/workspace/tools > PATH;
thiếu là lỗi ồn ào (exit 2), không âm thầm bỏ qua.

Cách dùng:
  python3 evidence/generators.py all --run-dir evidence/output/local-clean
  python3 evidence/generators.py change-record --run-dir <run> [--out <dir>]
  python3 evidence/generators.py drift-report --workload examples/payments-sample/clean
  python3 evidence/generators.py access-review [--repo-root .]
  python3 evidence/generators.py config-baseline --workload examples/payments-sample/clean
  python3 evidence/generators.py write-baseline --workload examples/payments-sample/clean
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

TOOL_NAME = "devsecops-os evidence generators"
TOOL_VERSION = "1.0.0 (M5-A3)"
GENERATED_BY = f"{TOOL_NAME} {TOOL_VERSION}"

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
REGO_BUNDLE = REPO_ROOT / "policies" / "rego"
DEFAULT_BASELINE = SCRIPT_DIR / "baselines" / "payments-sample.tf-normalized.json"
SUPPLEMENTARY_DIR_NAME = "supplementary-records"

# Cấu hình của policy change_record theo quy ước pack v1 (khớp
# policies/fixtures/change_record.pass.json + docs/change_record.md).
CHANGE_CONFIG = {
    "protected_branches": ["main", "release"],
    "required_gates": ["secret", "sast", "sca", "iac"],
}
DRIFT_CONFIG = {"sla_days": 7,
                "critical_categories": ["network", "iam", "storage"]}

STATIC_SECRET_RE = re.compile(
    r"secrets\.(AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|GCP_|AZURE_)",
    re.IGNORECASE)


# ---------------------------------------------------------------------------
# Tiện ích chung
# ---------------------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> str:
    return date.today().isoformat()


def write_json(path: Path, data) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return path


def load_json(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def find_tool(explicit, env_key, name):
    if explicit:
        return explicit if Path(explicit).is_file() else None
    env_bin = os.environ.get(env_key)
    if env_bin and Path(env_bin).is_file():
        return env_bin
    candidate = Path.home() / "workspace" / "tools" / name
    if candidate.is_file():
        return str(candidate)
    return shutil.which(name)


def require_tool(explicit, env_key, name, what):
    tool = find_tool(explicit, env_key, name)
    if not tool:
        print(f"LỖI: {what} cần binary {name} nhưng không tìm thấy "
              f"(truyền --{name} <đường dẫn>, đặt biến môi trường "
              f"{env_key}, hoặc để tại ~/workspace/tools/{name})",
              file=sys.stderr)
        raise SystemExit(2)
    return tool


def opa_deny(opa, package, input_doc):
    """Chạy thật một policy của pack: opa eval data.devsecops.<pkg>.deny.
    Trả về danh sách thông điệp deny (rỗng = pass)."""
    with _TempJson(input_doc) as input_path:
        proc = subprocess.run(
            [opa, "eval", "--bundle", str(REGO_BUNDLE),
             "--input", str(input_path), "--format", "json",
             f"data.devsecops.{package}.deny"],
            capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise RuntimeError(
            f"opa eval ({package}) thất bại: {proc.stderr.strip()[:400]}")
    res = json.loads(proc.stdout).get("result") or []
    if not res:
        return []
    return res[0]["expressions"][0]["value"] or []


class _TempJson:
    def __init__(self, doc):
        self.doc = doc
        self.path = None

    def __enter__(self):
        import tempfile
        fd, name = tempfile.mkstemp(prefix="generators-input-",
                                    suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(self.doc, fh, ensure_ascii=False)
        self.path = Path(name)
        return self.path

    def __exit__(self, *exc):
        if self.path:
            self.path.unlink(missing_ok=True)


def policy_decision_record(policy_id, gate, decision_doc_input,
                           deny, commit_sha, extra_note=None):
    rec = {
        "evidence_type": "policy-decision",
        "policy_id": policy_id,
        "engine": "opa",
        "gate": gate,
        "decision": "deny" if deny else "pass",
        "violations": deny,
        "inputs_digest": "sha256:" + sha256_bytes(
            json.dumps(decision_doc_input, ensure_ascii=False,
                       sort_keys=True).encode("utf-8")),
        "commit_sha": commit_sha,
        "timestamp": iso_now(),
        "generated_by": GENERATED_BY,
    }
    if extra_note:
        rec["gate_note"] = extra_note
    return rec


def load_tf_parser():
    """Nạp đúng adapter HCL2 của gate 4 (tf_parse_input.py) để parse
    IaC — một nguồn phân tích duy nhất cho cả gate lẫn bộ sinh."""
    path = REPO_ROOT / "gates" / "local" / "adapters" / "tf_parse_input.py"
    spec = importlib.util.spec_from_file_location("tf_parse_input", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_infra(conftest, infra_dir: Path):
    tf = load_tf_parser()
    parsed = tf.conftest_parse(conftest, infra_dir / "main.tf")
    defaults = tf.var_defaults(
        tf.conftest_parse(conftest, infra_dir / "variables.tf"))
    # Dùng lại nguyên logic chuẩn hoá của adapter bằng cách chạy các
    # hàm nội bộ của nó trên cùng dữ liệu parse — adapter không tách
    # hàm build doc riêng, nên ta tái cấu trúc từ các hàm bodies/
    # resolve của chính adapter (đầu ra phải khớp tf-normalized của
    # gate 4; test đối chiếu trực tiếp với adapter CLI).
    return build_normalized(tf, parsed, defaults)


def build_normalized(tf, parsed, defaults):
    """Tái tạo doc chuẩn hoá {security_groups, storage, iam_policies,
    managed_policy_attachments} từ dữ liệu conftest parse — bám sát
    từng bước của tf_parse_input.main() (adapter là nguồn sự thật;
    test_generators đối chiếu hai đầu ra trên workload thật)."""
    lbs = tf.bodies(parsed, "aws_lb")
    public_sgs = set()
    for lb in lbs.values():
        if lb.get("internal") is False:
            for ref in lb.get("security_groups", []) or []:
                m = re.search(r"aws_security_group\.([A-Za-z0-9_]+)\.id",
                              str(ref))
                if m:
                    public_sgs.add(m.group(1))
    sgs = []
    for name, body in tf.bodies(parsed, "aws_security_group").items():
        ingress = []
        for rule in body.get("ingress", []) or []:
            cidrs = rule.get("cidr_blocks")
            cidrs = tf.resolve(cidrs, defaults) if cidrs is not None else []
            if isinstance(cidrs, str):
                cidrs = [cidrs]
            ingress.append({
                "from_port": tf.resolve(rule.get("from_port"), defaults),
                "to_port": tf.resolve(rule.get("to_port"), defaults),
                "cidr_blocks": cidrs or [],
                "security_groups": [
                    tf.resolve(s, defaults)
                    for s in (rule.get("security_groups") or [])],
            })
        sgs.append({"name": f"aws_security_group.{name}",
                    "public_web": name in public_sgs, "ingress": ingress})
    by_sg_name = {sg["name"]: sg for sg in sgs}
    standalone = tf.bodies(parsed, "aws_vpc_security_group_ingress_rule")
    for body in standalone.values():
        sg_ref = tf.resolve(body.get("security_group_id"), defaults)
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
                vm = re.search(r"var\.([A-Za-z0-9_]+)",
                               str(body.get("for_each", "")))
                if vm and isinstance(defaults.get(vm.group(1)), list):
                    cidrs = list(defaults[vm.group(1)])
            else:
                cidrs = [tf.resolve(cidr4, defaults)]
        ref_sgs = []
        ref = body.get("referenced_security_group_id")
        if ref:
            ref_sgs = [tf.resolve(ref, defaults)]
        target["ingress"].append({
            "from_port": tf.resolve(body.get("from_port"), defaults),
            "to_port": tf.resolve(body.get("to_port"), defaults),
            "cidr_blocks": cidrs,
            "security_groups": ref_sgs,
        })
    pab = tf.bodies(parsed, "aws_s3_bucket_public_access_block")
    sse = tf.bodies(
        parsed, "aws_s3_bucket_server_side_encryption_configuration")
    storage = []
    for name in tf.bodies(parsed, "aws_s3_bucket"):
        p = next(iter(pab.values()), {}) if pab else {}
        flags = [p.get(k) for k in ("block_public_acls",
                                    "block_public_policy",
                                    "ignore_public_acls",
                                    "restrict_public_buckets")]
        storage.append({
            "address": f"aws_s3_bucket.{name}", "type": "aws_s3_bucket",
            "encryption_enabled": bool(sse),
            "public_access_blocked": bool(pab)
                and all(f is True for f in flags),
        })
    attachments = []
    for body in tf.bodies(parsed, "aws_iam_role_policy_attachment").values():
        role_ref = str(body.get("role", ""))
        m = re.search(r"aws_iam_role\.([A-Za-z0-9_]+)\.", role_ref)
        attachments.append({
            "role": f"aws_iam_role.{m.group(1)}" if m else role_ref,
            "policy_arn": body.get("policy_arn"),
        })
    return {"security_groups": sgs, "storage": storage,
            "iam_policies": [], "managed_policy_attachments": attachments}


# ---------------------------------------------------------------------------
# 1) change-record — từ kết quả gate thật của một lần chạy
# ---------------------------------------------------------------------------

# Ánh xạ gate bắt buộc của change_record -> nguồn quyết định thật.
_REQUIRED_GATE_SOURCES = {
    "secret": ("devsecops.secret_findings", 1),
    "sast": (None, 2),   # gate 2 report-only ở pha 1: không có policy-decision
    "sca": ("devsecops.dependency_kev", 8),  # quyết định chặn nằm ở gate 8
    "iac": (None, 4),    # tổ hợp 3 policy của gate 4
}
_IAC_POLICIES = ("devsecops.network_exposure",
                 "devsecops.storage_encryption",
                 "devsecops.iam_least_privilege")


def scan_run_decisions(run_dir: Path):
    """Đọc mọi policy-decision-*.json trong các thư mục gate của lần
    chạy. Trả về (decisions, commit_sha, latest_ts)."""
    decisions = []
    commit_sha, latest_ts = None, None
    for gdir in sorted(run_dir.glob("gate-*")):
        if not gdir.is_dir():
            continue
        for f in sorted(gdir.glob("policy-decision-*.json")):
            try:
                data = load_json(f)
            except Exception:
                continue
            if data.get("evidence_type") == "policy-decision":
                decisions.append(data)
                commit_sha = commit_sha or data.get("commit_sha")
                ts = data.get("timestamp")
                if ts and (latest_ts is None or ts > latest_ts):
                    latest_ts = ts
    return decisions, commit_sha or "local-unspecified", latest_ts


def gate_dir_has_record(run_dir: Path, gate_no: int, evidence_type: str):
    for gdir in sorted(run_dir.glob(f"gate-{gate_no:02d}-*")):
        for f in gdir.glob("*.json"):
            try:
                data = load_json(f)
            except Exception:
                continue
            if isinstance(data, dict) and \
                    data.get("evidence_type") == evidence_type:
                return True
    return False


def gen_change_record(run_dir: Path, out_dir: Path, opa) -> dict:
    if not run_dir.is_dir():
        print(f"LỖI: thư mục lần chạy không tồn tại: {run_dir}",
              file=sys.stderr)
        raise SystemExit(2)
    decisions, commit_sha, latest_ts = scan_run_decisions(run_dir)
    by_policy = {}
    for d in decisions:
        by_policy.setdefault(d.get("policy_id"), []).append(d)

    def decision_of(policy_id):
        ds = by_policy.get(policy_id) or []
        if any(d.get("decision") == "deny" for d in ds):
            return "deny"
        if ds:
            return "pass"
        return "missing"

    gate_details = {}
    for pid, ds in sorted(by_policy.items()):
        gate_details[pid] = {
            "decision": decision_of(pid),
            "gate": ds[0].get("gate"),
            "violations": sum(len(d.get("violations") or []) for d in ds),
        }
    gate_results = {}
    for gate_name, (policy_id, gate_no) in _REQUIRED_GATE_SOURCES.items():
        if gate_name == "iac":
            parts = {pid: decision_of(pid) for pid in _IAC_POLICIES}
            gate_results["iac"] = (
                "deny" if "deny" in parts.values()
                else "pass" if all(v == "pass" for v in parts.values())
                else "missing")
            gate_details["iac (tổ hợp gate 4)"] = parts
        elif gate_name == "sast":
            has_sarif = gate_dir_has_record(run_dir, 2, "sarif-report")
            gate_results["sast"] = "pass" if has_sarif else "missing"
            gate_details["sast (gate 2, report-only ở pha 1)"] = {
                "decision": gate_results["sast"],
                "note": "gate 2 không sinh policy-decision ở pha 1 "
                        "(report-only); kết quả ở đây nghĩa là bản quét "
                        "SAST đã chạy và có record SARIF trong lần chạy",
            }
        else:
            gate_results[gate_name] = decision_of(policy_id)
    run_id = run_dir.name
    record = {
        "evidence_type": "change-record",
        "change_id": run_id,
        "change_source": "lần chạy kiểm chứng cục bộ — cây này chưa "
                         "phải git repo và chưa có hệ thống PR; "
                         "change_id lấy theo định danh lần chạy, "
                         "author/phê duyệt ghi đúng trạng thái thật "
                         "của lần chạy cục bộ",
        "target_branch": "main",
        "author": "local-verification-harness",
        "approvals": [],
        "approvals_note": "lần chạy cục bộ không có PR và không có "
                          "người phê duyệt — approvals để rỗng đúng "
                          "sự thật; policy change_record vì thế DENY "
                          "(xem policy-decision-change_record đi "
                          "kèm): hồ sơ thay đổi chỉ đạt khi có phê "
                          "duyệt thật trên nhánh bảo vệ",
        "gate_results": gate_results,
        "gate_details": gate_details,
        "evidence_links": [f"evidence://run/{run_id}"],
        "exceptions": [],
        "commit_sha": commit_sha,
        "timestamp": latest_ts or iso_now(),
        "run_id": run_id,
        "generated_by": GENERATED_BY,
    }
    write_json(out_dir / "change-record.record.json", record)

    policy_input = {
        "change": {
            "id": record["change_id"],
            "target_branch": record["target_branch"],
            "author": record["author"],
            "approvals": record["approvals"],
            "gate_results": record["gate_results"],
            "evidence_links": record["evidence_links"],
            "exceptions": record["exceptions"],
        },
        "config": CHANGE_CONFIG,
        "today": today(),
    }
    write_json(out_dir / "change-record.policy-input.json", policy_input)
    deny = opa_deny(opa, "change_record", policy_input)
    decision = policy_decision_record(
        "devsecops.change_record", "decision-layer", policy_input, deny,
        commit_sha,
        "lớp quyết định merge/release — không thuộc gate 1–10; "
        "policy chạy thật bằng OPA trên change-record vừa sinh")
    write_json(out_dir / "policy-decision-change_record.json", decision)
    return {"record": record, "decision": decision}


# ---------------------------------------------------------------------------
# 2) drift-report — cấu hình hiện tại so với baseline đã khai
# ---------------------------------------------------------------------------

def _rule_key(rule):
    return (rule.get("from_port"), rule.get("to_port"),
            tuple(sorted(rule.get("cidr_blocks") or [])),
            tuple(sorted(rule.get("security_groups") or [])))


def diff_normalized(baseline: dict, current: dict, detected_on: str):
    items = []

    def add(resource, category, summary, **extra):
        item = {"resource": resource, "category": category,
                "detected_on": detected_on, "acknowledged": False,
                "ticket": None, "summary": summary}
        item.update(extra)
        items.append(item)

    base_sgs = {sg["name"]: sg for sg in baseline.get("security_groups", [])}
    cur_sgs = {sg["name"]: sg for sg in current.get("security_groups", [])}
    for name in sorted(set(base_sgs) | set(cur_sgs)):
        if name not in cur_sgs:
            add(name, "network",
                "security group có trong baseline nhưng biến mất "
                "khỏi cấu hình hiện tại")
            continue
        if name not in base_sgs:
            add(name, "network",
                "security group mới xuất hiện, chưa có trong baseline")
            continue
        b, c = base_sgs[name], cur_sgs[name]
        if b.get("public_web") != c.get("public_web"):
            add(name, "network",
                f"cờ public_web đổi {b.get('public_web')} -> "
                f"{c.get('public_web')}")
        b_rules = {_rule_key(r): r for r in b.get("ingress", [])}
        c_rules = {_rule_key(r): r for r in c.get("ingress", [])}
        added = [c_rules[k] for k in sorted(set(c_rules) - set(b_rules),
                                            key=str)]
        removed = [b_rules[k] for k in sorted(set(b_rules) - set(c_rules),
                                              key=str)]
        if added or removed:
            add(name, "network",
                f"rule ingress lệch baseline: +{len(added)} rule, "
                f"-{len(removed)} rule",
                added_rules=added, removed_rules=removed)
    base_st = {s["address"]: s for s in baseline.get("storage", [])}
    cur_st = {s["address"]: s for s in current.get("storage", [])}
    for addr in sorted(set(base_st) | set(cur_st)):
        if addr not in cur_st:
            add(addr, "storage", "storage biến mất khỏi cấu hình hiện tại")
            continue
        if addr not in base_st:
            add(addr, "storage", "storage mới, chưa có trong baseline")
            continue
        for flag in ("encryption_enabled", "public_access_blocked"):
            if base_st[addr].get(flag) != cur_st[addr].get(flag):
                add(addr, "storage",
                    f"{flag} đổi {base_st[addr].get(flag)} -> "
                    f"{cur_st[addr].get(flag)}")
    def att_key(a):
        return (a.get("role"), a.get("policy_arn"))
    base_att = {att_key(a): a
                for a in baseline.get("managed_policy_attachments", [])}
    cur_att = {att_key(a): a
               for a in current.get("managed_policy_attachments", [])}
    for key in sorted(set(cur_att) - set(base_att), key=str):
        add(key[0], "iam",
            f"gắn managed policy mới ngoài baseline: {key[1]}")
    for key in sorted(set(base_att) - set(cur_att), key=str):
        add(key[0], "iam",
            f"managed policy trong baseline đã bị gỡ: {key[1]}")
    return items


def gen_drift_report(infra_dir: Path, baseline_path: Path, out_dir: Path,
                     opa, conftest) -> dict:
    if not baseline_path.is_file():
        print(f"LỖI: baseline không tồn tại: {baseline_path} — sinh "
              f"trước bằng lệnh write-baseline", file=sys.stderr)
        raise SystemExit(2)
    baseline_doc = load_json(baseline_path)
    baseline_cfg = baseline_doc.get("config") or {}
    current_cfg = parse_infra(conftest, infra_dir)
    detected = today()
    items = diff_normalized(baseline_cfg, current_cfg, detected)
    record = {
        "evidence_type": "drift-report",
        "report_date": detected,
        "drift_items": items,
        "baseline": {
            "path": str(baseline_path.relative_to(REPO_ROOT))
                    if baseline_path.is_relative_to(REPO_ROOT)
                    else str(baseline_path),
            "sha256": "sha256:" + sha256_file(baseline_path),
            "source": (baseline_doc.get("provenance") or {}).get(
                "source", "không rõ"),
        },
        "target": {"infra_dir": str(infra_dir), "parser":
                   "conftest parse (HCL2) qua adapter của gate 4"},
        "generated_by": GENERATED_BY,
    }
    write_json(out_dir / "drift-report.record.json", record)
    policy_input = {"report_date": detected, "drift_items": items,
                    "config": DRIFT_CONFIG}
    write_json(out_dir / "drift-report.policy-input.json", policy_input)
    deny = opa_deny(opa, "drift_control", policy_input)
    decision = policy_decision_record(
        "devsecops.drift_control", 4, policy_input, deny,
        "local-unspecified",
        "drift check theo lịch — mở rộng của gate 4 (bản đồ pha 1, "
        "row-13); policy chạy thật bằng OPA trên drift-report vừa sinh")
    write_json(out_dir / "policy-decision-drift_control.json", decision)
    return {"record": record, "decision": decision}


def write_baseline(infra_dir: Path, baseline_path: Path, conftest) -> dict:
    cfg = parse_infra(conftest, infra_dir)
    doc = {
        "provenance": {
            "source": f"cấu hình IaC tại {infra_dir} — biến thể được "
                      f"duyệt làm chuẩn (baseline) cho drift check",
            "generated_at": iso_now(),
            "generated_by": GENERATED_BY,
            "parser": "conftest parse (HCL2) qua adapter của gate 4 "
                      "(tf_parse_input)",
        },
        "config": cfg,
    }
    write_json(baseline_path, doc)
    return doc


# ---------------------------------------------------------------------------
# 3) access-review-report — rà soát quyền theo kỳ từ cây thật
# ---------------------------------------------------------------------------

def parse_workflow_permissions(text: str):
    """Bộ parse YAML tối thiểu cho đúng phần cần rà soát quyền:
    permissions cấp workflow (khối hoặc scalar), permissions cấp job,
    và cờ OIDC (id-token: write) ở bất kỳ cấp nào. Trả về dict
    {top: dict|str|None, jobs: {job: dict|str|None}, oidc: bool}.
    Chỉ dùng thư viện chuẩn — tooling bằng chứng không phụ thuộc
    PyYAML (khác adapters của gates, vốn chạy trong môi trường gate)."""
    top = None
    jobs = {}
    oidc = False
    lines = text.splitlines()

    def read_block(start_idx, indent):
        """Đọc các dòng 'key: value' ở đúng mức indent cho trước, bắt
        đầu từ start_idx; trả về (dict, idx_kết_thúc)."""
        out = {}
        i = start_idx
        while i < len(lines):
            raw = lines[i]
            if not raw.strip() or raw.strip().startswith("#"):
                i += 1
                continue
            cur_indent = len(raw) - len(raw.lstrip(" "))
            if cur_indent < indent:
                break
            if cur_indent == indent:
                m = re.match(r"([A-Za-z0-9_.-]+):\s*(.*)$", raw.strip())
                if m:
                    out[m.group(1)] = m.group(2).strip().strip("'\"")
            i += 1
        return out, i

    i = 0
    in_jobs = False
    current_job = None
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent == 0:
            in_jobs = stripped.startswith("jobs:")
            current_job = None
            if stripped.startswith("permissions:"):
                scalar = stripped.split(":", 1)[1].strip()
                if scalar:
                    top = scalar.strip("'\"")
                    i += 1
                else:
                    top, i = read_block(i + 1, 2)
                if _perms_have_oidc(top):
                    oidc = True
                continue
            i += 1
            continue
        if in_jobs and indent == 2 and stripped.endswith(":"):
            current_job = stripped[:-1].strip()
            jobs.setdefault(current_job, None)
            i += 1
            continue
        if in_jobs and current_job and indent == 4 \
                and stripped.startswith("permissions:"):
            scalar = stripped.split(":", 1)[1].strip()
            if scalar:
                jobs[current_job] = scalar.strip("'\"")
                i += 1
            else:
                jobs[current_job], i = read_block(i + 1, 6)
            if _perms_have_oidc(jobs[current_job]):
                oidc = True
            continue
        i += 1
    return {"top": top, "jobs": jobs, "oidc": oidc}


def _perms_have_oidc(perms) -> bool:
    return isinstance(perms, dict) and perms.get("id-token") == "write"


def _perm_findings(label, parsed, raw_text):
    findings = []

    def add(level, message):
        findings.append({"level": level, "message": message})

    top = parsed["top"]
    if top is None:
        add("high", f"{label}: không khai báo permissions cấp "
                    f"workflow — GITHUB_TOKEN nhận quyền mặc định "
                    f"của repo (rộng hơn cần thiết)")
    elif isinstance(top, str):
        if top == "write-all":
            add("high", f"{label}: permissions: write-all ở cấp "
                        f"workflow — thừa quyền nghiêm trọng")
        else:
            add("info", f"{label}: permissions dạng scalar "
                        f"'{top}' ở cấp workflow")
    for job, perms in parsed["jobs"].items():
        if perms == "write-all":
            add("high", f"{label}: job '{job}' có permissions "
                        f"write-all")
    if parsed["oidc"]:
        add("info", f"{label}: có id-token: write — job nhận token "
                    f"OIDC ngắn hạn qua federation (đúng nguyên tắc "
                    f"identity-first; không dùng khoá tĩnh)")
    for m in sorted(set(STATIC_SECRET_RE.findall(raw_text))):
        add("high", f"{label}: tham chiếu secret tĩnh dạng "
                    f"secrets.{m} — nguy cơ dùng khoá cloud dài hạn "
                    f"thay cho OIDC")
    return findings


def gen_access_review(repo_root: Path, out_dir: Path) -> dict:
    scopes = [
        ("devsecops-os", repo_root / ".github" / "workflows"),
        ("examples/checkout-sample",
         repo_root / "examples" / "checkout-sample" / ".github"
         / "workflows"),
        ("templates/api-service",
         repo_root / "templates" / "api-service" / ".github"
         / "workflows"),
    ]
    subjects, scanned = [], []
    total_findings = {"high": 0, "medium": 0, "info": 0}
    for label, wdir in scopes:
        if not wdir.is_dir():
            scanned.append(f"{label}: (không có thư mục workflows — "
                           f"bỏ qua)")
            continue
        for wf in sorted(wdir.glob("*.yml")) + sorted(wdir.glob("*.yaml")):
            raw = wf.read_text(encoding="utf-8")
            parsed = parse_workflow_permissions(raw)
            findings = _perm_findings(wf.name, parsed, raw)
            for f in findings:
                total_findings[f["level"]] = \
                    total_findings.get(f["level"], 0) + 1
            rel = wf.relative_to(repo_root).as_posix()
            subjects.append({
                "repo": label,
                "workflow": rel,
                "permissions": parsed["top"],
                "job_permissions": {k: v for k, v in
                                    parsed["jobs"].items()
                                    if v is not None},
                "oidc": parsed["oidc"],
                "findings": findings,
            })
            scanned.append(rel)
    trust_policy = (repo_root / "docs" / "examples"
                    / "github-actions-oidc-aws-trust-policy.json")
    if trust_policy.is_file():
        try:
            doc = load_json(trust_policy)
            stmts = doc.get("Statement") or []
            actions = sorted({a for s in stmts
                              for a in (s.get("Action") or [])})
            findings = []
            blob = json.dumps(doc)
            if ":root" in blob or '"*"' in blob:
                findings.append({
                    "level": "info",
                    "message": "mẫu trust policy có mặt; cần đối "
                               "chiếu điều kiện sub/aud khi tổ chức "
                               "áp thật (mẫu giữ chỗ theo thiết kế)"})
            subjects.append({
                "repo": "docs/examples",
                "role": "mẫu OIDC trust policy (AWS) cho GitHub Actions",
                "permissions": {"actions": actions},
                "oidc": True,
                "findings": findings,
            })
            scanned.append(
                "docs/examples/github-actions-oidc-aws-trust-policy.json")
        except Exception as exc:
            subjects.append({
                "repo": "docs/examples",
                "role": "mẫu OIDC trust policy (AWS)",
                "permissions": None, "oidc": True,
                "findings": [{"level": "medium",
                              "message": f"không đọc được file mẫu: "
                                         f"{exc}"}]})
    now = datetime.now(timezone.utc)
    record = {
        "evidence_type": "access-review-report",
        "period": now.strftime("%Y-%m"),
        "generated_at": iso_now(),
        "subjects": subjects,
        "scope": scanned,
        "summary": {
            "workflows_scanned": len(
                [s for s in subjects if "workflow" in s]),
            "findings_by_level": total_findings,
            "note": "rà soát từ chính cây repo ở thời điểm sinh — "
                    "không phải dữ liệu từ GitHub API (repo chưa "
                    "phát hành); quyền hiệu lực trên GitHub chỉ xác "
                    "nhận được sau khi repo tồn tại",
        },
        "generated_by": GENERATED_BY,
    }
    write_json(out_dir / "access-review-report.record.json", record)
    return {"record": record}


# ---------------------------------------------------------------------------
# 4) config-baseline-report — policy nhóm cấu hình trên workload + repo
# ---------------------------------------------------------------------------

_CONFIG_POLICIES = ("network_exposure", "storage_encryption",
                    "iam_least_privilege")


def gen_config_baseline(infra_dir: Path, environment: str, out_dir: Path,
                        opa, conftest, repo_root: Path) -> dict:
    cfg = parse_infra(conftest, infra_dir)
    findings = []
    for pkg in _CONFIG_POLICIES:
        deny = opa_deny(opa, pkg, cfg)
        findings.append({
            "control": f"devsecops.{pkg}",
            "area": {"network_exposure": "network",
                     "storage_encryption": "storage",
                     "iam_least_privilege": "iam"}[pkg],
            "status": "deny" if deny else "pass",
            "violations": deny,
        })
    bp = repo_root / "templates" / "api-service" / "branch-protection.json"
    findings.append({
        "control": "repo.branch-protection-template",
        "area": "repo-config",
        "status": "pass" if bp.is_file() else "missing",
        "violations": [] if bp.is_file() else
        ["không tìm thấy branch-protection.json trong template "
         "golden path"],
    })
    wdir = repo_root / ".github" / "workflows"
    missing_perm = []
    if wdir.is_dir():
        for wf in sorted(wdir.glob("*.yml")):
            parsed = parse_workflow_permissions(
                wf.read_text(encoding="utf-8"))
            if parsed["top"] is None:
                missing_perm.append(wf.name)
    findings.append({
        "control": "repo.workflow-permissions-declared",
        "area": "repo-config",
        "status": "pass" if not missing_perm else "deny",
        "violations": [f"workflow {n} không khai báo permissions "
                        f"cấp workflow" for n in missing_perm],
    })
    record = {
        "evidence_type": "config-baseline-report",
        "environment": environment,
        "generated_at": iso_now(),
        "findings": findings,
        "workload_infra": str(infra_dir),
        "inputs_digest": "sha256:" + sha256_bytes(
            json.dumps(cfg, ensure_ascii=False, sort_keys=True)
            .encode("utf-8")),
        "generated_by": GENERATED_BY,
    }
    write_json(out_dir / "config-baseline-report.record.json", record)
    return {"record": record}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def resolve_workload(run_dir: Path, explicit):
    if explicit:
        return Path(explicit)
    name = run_dir.name
    if "checkout-sample" in name:
        return REPO_ROOT / "examples" / "checkout-sample"
    if "local-planted" in name:
        return REPO_ROOT / "examples" / "payments-sample" / "planted"
    if "local-clean" in name:
        return REPO_ROOT / "examples" / "payments-sample" / "clean"
    return None


def env_label_for(workload: Path) -> str:
    try:
        rel = workload.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        rel = str(workload)
    return f"{rel} (local)"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="generators",
        description="devsecops-os — bộ sinh bằng chứng quyết "
                    "định/định kỳ (M5-A3)")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p):
        p.add_argument("--out", default=None,
                       help="thư mục ghi record (mặc định: "
                            "<run-dir>/supplementary-records khi có "
                            "--run-dir, ngược lại ./supplementary-records)")
        p.add_argument("--run-dir", default=None)
        p.add_argument("--opa", default=None)
        p.add_argument("--conftest", default=None)

    p_all = sub.add_parser("all", help="sinh cả 4 loại cho một lần chạy")
    add_common(p_all)
    p_all.add_argument("--workload", default=None,
                       help="thư mục workload (mặc định suy từ tên "
                            "lần chạy: local-clean/local-planted/"
                            "local-checkout-sample)")
    p_all.add_argument("--baseline", default=str(DEFAULT_BASELINE))

    p_cr = sub.add_parser("change-record")
    add_common(p_cr)

    p_dr = sub.add_parser("drift-report")
    add_common(p_dr)
    p_dr.add_argument("--workload", required=True)
    p_dr.add_argument("--baseline", default=str(DEFAULT_BASELINE))

    p_wb = sub.add_parser("write-baseline")
    p_wb.add_argument("--workload", required=True)
    p_wb.add_argument("--baseline", default=str(DEFAULT_BASELINE))
    p_wb.add_argument("--conftest", default=None)

    p_ar = sub.add_parser("access-review")
    add_common(p_ar)
    p_ar.add_argument("--repo-root", default=str(REPO_ROOT))

    p_cb = sub.add_parser("config-baseline")
    add_common(p_cb)
    p_cb.add_argument("--workload", required=True)
    p_cb.add_argument("--environment", default=None)

    args = parser.parse_args(argv)

    def out_dir_for(a) -> Path:
        if a.out:
            return Path(a.out)
        if getattr(a, "run_dir", None):
            return Path(a.run_dir) / SUPPLEMENTARY_DIR_NAME
        return Path(SUPPLEMENTARY_DIR_NAME)

    if args.command == "write-baseline":
        conftest = require_tool(args.conftest, "CONFTEST", "conftest",
                                "write-baseline")
        workload = Path(args.workload)
        doc = write_baseline(workload / "infra", Path(args.baseline),
                             conftest)
        print(f"Baseline: {args.baseline} "
              f"({len(doc['config']['security_groups'])} SG, "
              f"{len(doc['config']['storage'])} storage)")
        return 0

    if args.command == "access-review":
        out = out_dir_for(args)
        res = gen_access_review(Path(args.repo_root), out)
        s = res["record"]["summary"]
        print(f"access-review-report: {s['workflows_scanned']} "
              f"workflow, findings={s['findings_by_level']} -> "
              f"{out / 'access-review-report.record.json'}")
        return 0

    if args.command == "change-record":
        if not args.run_dir:
            print("LỖI: change-record cần --run-dir", file=sys.stderr)
            return 2
        opa = require_tool(args.opa, "OPA", "opa", "change-record")
        out = out_dir_for(args)
        res = gen_change_record(Path(args.run_dir), out, opa)
        print(f"change-record: gate_results="
              f"{res['record']['gate_results']} · policy "
              f"change_record -> {res['decision']['decision'].upper()}"
              f" -> {out}")
        return 0

    if args.command == "drift-report":
        opa = require_tool(args.opa, "OPA", "opa", "drift-report")
        conftest = require_tool(args.conftest, "CONFTEST", "conftest",
                                "drift-report")
        out = out_dir_for(args)
        workload = Path(args.workload)
        res = gen_drift_report(workload / "infra",
                               Path(args.baseline), out, opa, conftest)
        print(f"drift-report: {len(res['record']['drift_items'])} "
              f"mục drift · policy drift_control -> "
              f"{res['decision']['decision'].upper()} -> {out}")
        return 0

    if args.command == "config-baseline":
        opa = require_tool(args.opa, "OPA", "opa", "config-baseline")
        conftest = require_tool(args.conftest, "CONFTEST", "conftest",
                                "config-baseline")
        out = out_dir_for(args)
        workload = Path(args.workload)
        env = args.environment or env_label_for(workload)
        res = gen_config_baseline(workload / "infra", env, out, opa,
                                  conftest, REPO_ROOT)
        stats = {}
        for f in res["record"]["findings"]:
            stats[f["status"]] = stats.get(f["status"], 0) + 1
        print(f"config-baseline-report ({env}): {stats} -> {out}")
        return 0

    if args.command == "all":
        if not args.run_dir:
            print("LỖI: all cần --run-dir", file=sys.stderr)
            return 2
        run_dir = Path(args.run_dir)
        workload = resolve_workload(run_dir, args.workload)
        if workload is None:
            print("LỖI: không suy được workload từ tên lần chạy — "
                  "truyền --workload", file=sys.stderr)
            return 2
        opa = require_tool(args.opa, "OPA", "opa", "all")
        conftest = require_tool(args.conftest, "CONFTEST", "conftest",
                                "all")
        out = out_dir_for(args)
        cr = gen_change_record(run_dir, out, opa)
        print(f"[all] change-record -> {out} (policy: "
              f"{cr['decision']['decision']})")
        dr = gen_drift_report(workload / "infra", Path(args.baseline),
                              out, opa, conftest)
        print(f"[all] drift-report: {len(dr['record']['drift_items'])} "
              f"mục (policy: {dr['decision']['decision']})")
        ar = gen_access_review(REPO_ROOT, out)
        print(f"[all] access-review-report: "
              f"{ar['record']['summary']['workflows_scanned']} workflow")
        cb = gen_config_baseline(workload / "infra",
                                 env_label_for(workload), out, opa,
                                 conftest, REPO_ROOT)
        print(f"[all] config-baseline-report: "
              f"{len(cb['record']['findings'])} finding")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
