#!/usr/bin/env python3
"""devsecops-os — evidence bundle tool (M4: evidence automation).

Một công cụ, hai việc:

  collect   Thu thập toàn bộ evidence record từ một lần chạy gates
            (thư mục `evidence/output/<lần chạy>/` theo hợp đồng M3),
            kiểm tra từng record khớp schema bằng chứng của policy
            pack v1 (M2), sinh báo cáo tổng hợp + bảng truy vết
            framework -> policy -> gate -> bằng chứng, và đóng gói
            thành một evidence bundle có manifest SHA-256. Tuỳ chọn
            `--sign`: ký mật mã `bundle.sha256` bằng Cosign (khoá tạm
            theo lần chạy, sinh ngoài cây và huỷ ngay sau khi ký —
            xem mục ký ở evidence/README.md).

  verify    Kiểm chứng độc lập một bundle đã đóng gói bằng MỘT lệnh:
            đối chiếu mọi hash trong manifest + `bundle.sha256`
            (tương thích `sha256sum -c`), kiểm tra lại tính khớp
            schema của mọi record trong bundle, và — khi bundle có
            khai báo chữ ký — kiểm chứng thêm chữ ký Cosign trên
            `bundle.sha256` (thiếu/sai chữ ký là FAIL ồn ào).

Từ M5-A3, collector còn: (a) quét thư mục `supplementary-records/`
của lần chạy — nơi các bộ sinh bằng chứng quyết định/định kỳ
(evidence/generators.py) ghi change-record, drift-report,
access-review-report, config-baseline-report kèm policy-decision
của chúng — và kiểm schema như mọi record khác; (b) tự phát hành
record `ci-log`: đóng gói toàn bộ file log (.log) của lần chạy
thành một artefact zip kèm SHA-256, để hàng A.8.15–A.8.16 của bản
đồ pha 1 có bằng chứng thật thay vì "chưa có".

Chỉ dùng thư viện chuẩn của Python 3 — chạy được trên runner CI
trắng mà không cần cài thêm gói. Nguyên tắc thừa hưởng từ blueprint:
mọi thứ thiếu/sai đều phải BÁO ỒN ÀO (record sai schema bị nêu tên,
gate thiếu bằng chứng bị gắn cờ), không bao giờ im lặng cho qua.

Cách dùng:
  python3 evidence/bundle_tool.py collect evidence/output/local-clean
  python3 evidence/bundle_tool.py collect <run-dir> --out-dir <dir> \
      --run-id <id> [--allow-incomplete]
  python3 evidence/verify_bundle.py <bundle-dir>     # == lệnh verify

Chế độ mặc định là NGHIÊM: có bất kỳ record nào sai schema, gate nào
thiếu thư mục hoặc thiếu bằng chứng thì collect DỪNG và không sinh
bundle. `--allow-incomplete` (dùng trong CI, chế độ chỉ-thu-thập):
vẫn sinh bundle, record sai bị tách vào `rejected/` kèm lý do, và
bundle bị gắn cờ `evidence-incomplete` trong manifest + báo cáo.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "devsecops-os evidence bundle tool"
TOOL_VERSION = "1.2.0"
BUNDLE_FORMAT = "devsecops-os/evidence-bundle/1"

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_SCHEMAS_DIR = REPO_ROOT / "policies" / "evidence-schemas"
MAPPING_FILE = SCRIPT_DIR / "mapping.phase1.json"
DEFAULT_BUNDLES_DIR = SCRIPT_DIR / "bundles"

GATE_DIR_RE = re.compile(r"^gate-(\d{2})-")
EXPECTED_GATES = list(range(1, 11))  # blueprint mục 5: gate 1..10

# Thư mục nguồn record phụ trợ trong một lần chạy: các bộ sinh bằng
# chứng quyết định/định kỳ (evidence/generators.py) ghi record vào
# đây; collector quét và kiểm schema như record của gate.
SUPPLEMENTARY_DIR_NAME = "supplementary-records"
SUPPLEMENTARY_LABEL = "supplementary"

# Loại bằng chứng do chính collector phát hành (không đến từ gate):
# chỉ mục kiểm soát cho CPS 234 và gói log CI cho ISO A.8.15–16.
COLLECTOR_TYPES = ("control-evidence-index", "ci-log")
CI_LOG_BUNDLE_PATH = "records/collector/ci-log.record.json"
CI_LOG_ARTIFACT_PATH = "artifacts/ci-logs/run-logs.zip"

# Không bao giờ đưa khoá riêng vào bundle — dù nó nằm ngay trong thư
# mục đầu ra của gate (gate 6 sinh cosign.key tạm khi chạy cục bộ).
PRIVATE_KEY_SUFFIXES = (".key", ".pem")

# Ký bundle (M5-A2): chữ ký Cosign nằm trên chính `bundle.sha256` —
# file bao phủ mọi file còn lại kể cả manifest.json. Hai file chữ ký
# vì thế CỐ Ý đứng ngoài manifest và ngoài bundle.sha256 (chúng chứng
# thực bundle.sha256, không thể tự nằm trong đó).
SIG_BUNDLE_NAME = "bundle.sigstore.json"
SIG_PUBKEY_NAME = "cosign.pub"
SIGNATURE_FILES = (SIG_BUNDLE_NAME, SIG_PUBKEY_NAME)
DEFAULT_SIGNING_CONFIG = (REPO_ROOT / "gates" / "local"
                          / "signing-config-offline.json")


# ---------------------------------------------------------------------------
# Tiện ích chung
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_mtime(path: Path) -> str:
    ts = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Ký mật mã cho bundle (M5-A2) — Cosign sign-blob trên bundle.sha256.
# Cùng mẫu với gate 6: khoá cục bộ TẠM theo lần chạy, signing-config
# offline (không Rekor), verify bằng --insecure-ignore-tlog. Khác
# biệt bắt buộc so với gate 6: khoá sinh trong thư mục tạm NGOÀI cây
# và bị huỷ ngay sau khi ký — khoá riêng không bao giờ vào bundle và
# không nằm lại trong cây (bài học quét rủi ro M5-A). Giới hạn trung
# thực của chữ ký cục bộ so với keyless OIDC trên CI: xem README.
# ---------------------------------------------------------------------------

def find_cosign(explicit=None):
    """Tìm cosign: --cosign > biến môi trường COSIGN_BINARY > PATH.
    Giá trị explicit không tồn tại = lỗi cấu hình, không âm thầm bỏ
    qua (trả None để nơi gọi FAIL ồn ào)."""
    if explicit:
        return explicit if Path(explicit).is_file() else None
    env_bin = os.environ.get("COSIGN_BINARY")
    if env_bin and Path(env_bin).is_file():
        return env_bin
    return shutil.which("cosign")


def _run_cosign(args, cwd, what):
    env = dict(os.environ, COSIGN_PASSWORD="")
    proc = subprocess.run([str(a) for a in args], cwd=cwd, env=env,
                          stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, timeout=180)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"cosign {what} thất bại: {detail[:400]}")
    return proc


def generate_signing_keypair(cosign, workdir: Path) -> Path:
    """Sinh cặp khoá tạm trong workdir; trả về đường dẫn cosign.pub."""
    _run_cosign([cosign, "generate-key-pair"], workdir,
                "generate-key-pair")
    pub_path = workdir / "cosign.pub"
    if not pub_path.is_file():
        raise RuntimeError(
            "cosign generate-key-pair không sinh ra cosign.pub")
    return pub_path


def cosign_sign_blob(cosign, key_path, target: Path, out_bundle: Path,
                     signing_config, cwd):
    args = [cosign, "sign-blob", "--key", str(key_path),
            "--bundle", str(out_bundle)]
    if signing_config:
        args += ["--signing-config", str(signing_config)]
    args += ["--yes", str(target)]
    _run_cosign(args, cwd, "sign-blob")


def cosign_verify_blob(cosign, pub_path, sig_bundle: Path,
                       target: Path, cwd):
    """Ném RuntimeError khi chữ ký không hợp lệ."""
    args = [cosign, "verify-blob", "--key", str(pub_path),
            "--bundle", str(sig_bundle), "--insecure-ignore-tlog",
            str(target)]
    _run_cosign(args, cwd, "verify-blob")


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


# ---------------------------------------------------------------------------
# Bộ kiểm tra JSON Schema tối thiểu (tập con mà schema M2 thực dùng:
# type / const / enum / required / properties / items /
# additionalProperties). Schema M2 chỉ dùng type/const/required/
# properties, nhưng verify phải bắt được đúng các lỗi đó một cách
# độc lập — không phụ thuộc gói `jsonschema` trên runner.
# ---------------------------------------------------------------------------

_TYPE_CHECKS = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: (isinstance(v, (int, float))
                         and not isinstance(v, bool)),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


def validate(instance, schema, path="$"):
    """Trả về danh sách lỗi (rỗng = hợp lệ)."""
    errors = []
    if not isinstance(schema, dict):
        return errors
    if "const" in schema and instance != schema["const"]:
        errors.append(
            f"{path}: phải bằng hằng số {schema['const']!r}, "
            f"thực tế {instance!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} không thuộc enum "
                      f"{schema['enum']!r}")
    expected_type = schema.get("type")
    if expected_type is not None:
        types = expected_type if isinstance(expected_type, list) \
            else [expected_type]
        if not any(_TYPE_CHECKS.get(t, lambda v: True)(instance)
                   for t in types):
            errors.append(
                f"{path}: sai kiểu — kỳ vọng {'/'.join(types)}, "
                f"thực tế {type(instance).__name__}")
            return errors  # sai kiểu gốc thì không đào sâu thêm
    if isinstance(instance, dict):
        for field in schema.get("required", []):
            if field not in instance:
                errors.append(f"{path}: thiếu trường bắt buộc {field!r}")
        props = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in props:
                errors.extend(validate(value, props[key], f"{path}.{key}"))
            elif additional is False:
                errors.append(f"{path}: trường {key!r} không có trong schema")
            elif isinstance(additional, dict):
                errors.extend(validate(value, additional, f"{path}.{key}"))
    if isinstance(instance, list) and isinstance(schema.get("items"), dict):
        for i, item in enumerate(instance):
            errors.extend(validate(item, schema["items"], f"{path}[{i}]"))
    return errors


def load_schemas(schemas_dir: Path):
    """Map evidence_type -> schema, theo tên file `<type>.schema.json`."""
    schemas = {}
    for f in sorted(schemas_dir.glob("*.schema.json")):
        evidence_type = f.name[: -len(".schema.json")]
        schemas[evidence_type] = load_json(f)
    return schemas


def build_ci_log_archive(run_dir: Path, log_files):
    """Đóng gói các file log của lần chạy thành một zip XÁC ĐỊNH
    (deterministic): thứ tự tên cố định, mốc thời gian zip cố định
    (1980-01-01) — cùng một tập log luôn cho cùng một SHA-256, để
    record ci-log mang hash ổn định và verify đối chiếu được.
    Trả về (bytes_của_zip, sha256_hex)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in log_files:
            relp = f.relative_to(run_dir).as_posix()
            info = zipfile.ZipInfo(relp, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, f.read_bytes())
    data = buf.getvalue()
    return data, hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# COLLECT
# ---------------------------------------------------------------------------

def discover_gate_dirs(run_dir: Path):
    gates = {}
    for child in sorted(run_dir.iterdir()):
        if child.is_dir():
            m = GATE_DIR_RE.match(child.name)
            if m:
                gates[int(m.group(1))] = child
    return gates


def display_uri(uri: str) -> str:
    """Rút gọn URI tuyệt đối kiểu cục bộ cho dễ đọc trong báo cáo;
    giá trị gốc vẫn nằm nguyên trong record/SARIF của bundle."""
    marker = "/examples/"
    if marker in uri:
        return "examples/" + uri.split(marker, 1)[1]
    return uri


def extract_secret_findings(run_dir: Path, gate_dirs):
    """Finding secret lấy từ artefact SARIF mà record của gate 1 trỏ
    tới — dữ liệu thật trong lần chạy, không suy diễn."""
    findings = []
    gate1 = gate_dirs.get(1)
    if gate1 is None:
        return findings
    for candidate in sorted(gate1.glob("*.sarif")):
        try:
            sarif = load_json(candidate)
        except Exception:
            continue
        for run in sarif.get("runs", []):
            for result in run.get("results", []):
                locs = result.get("locations") or [{}]
                phys = (locs[0].get("physicalLocation") or {})
                region = phys.get("region") or {}
                uri = ((phys.get("artifactLocation") or {}).get("uri") or "")
                findings.append({
                    "rule": result.get("ruleId"),
                    "file": display_uri(uri),
                    "file_as_recorded": uri,
                    "line": region.get("startLine"),
                    "message": (result.get("message") or {}).get("text", ""),
                })
    return findings


def extract_vuln_summary(records):
    """Tóm tắt lỗ hổng từ record vuln-risk-ranking (gate 8) — nguồn
    quyết định chặn/issue của cả lần chạy."""
    for rec in records:
        if rec["data"].get("evidence_type") != "vuln-risk-ranking":
            continue
        entries = rec["data"].get("entries") or []
        block, kev = {}, {}
        issue_count = 0
        for e in entries:
            key = (e.get("cve"), e.get("package"), e.get("version"))
            if e.get("decision") == "block":
                block.setdefault(key, {
                    "cve": e.get("cve"), "package": e.get("package"),
                    "version": e.get("version"), "in_kev": e.get("in_kev"),
                    "epss": e.get("epss")})
            elif e.get("decision") == "issue":
                issue_count += 1
            if e.get("in_kev"):
                kev.setdefault(key, {
                    "cve": e.get("cve"), "package": e.get("package"),
                    "version": e.get("version"),
                    "decision": e.get("decision"), "epss": e.get("epss")})
        return {
            "source_record": rec["bundle_path"],
            "entries_total": len(entries),
            "unique_cves": len({e.get("cve") for e in entries}),
            "block_unique": sorted(block.values(),
                                     key=lambda x: x["cve"] or ""),
            "kev_unique": sorted(kev.values(),
                                   key=lambda x: x["cve"] or ""),
            "issue_entries": issue_count,
            "feed_versions": rec["data"].get("feed_versions"),
        }
    return None


def collect(run_dir: Path, out_dir: Path | None, run_id: str | None,
            allow_incomplete: bool, sign: bool = False,
            cosign: str | None = None,
            signing_config: str | None = None) -> int:
    if not run_dir.is_dir():
        print(f"LỖI: thư mục lần chạy không tồn tại: {run_dir}",
              file=sys.stderr)
        return 2
    # Tiền điều kiện cho --sign: fail sớm và ồn ào, trước khi đóng gói.
    cosign_bin = None
    if sign:
        cosign_bin = find_cosign(cosign)
        if not cosign_bin:
            print("LỖI: --sign yêu cầu cosign nhưng không tìm thấy "
                  "(truyền --cosign <đường dẫn> hoặc đặt biến môi "
                  "trường COSIGN_BINARY)", file=sys.stderr)
            return 2
        if signing_config:
            if not Path(signing_config).is_file():
                print(f"LỖI: signing-config không tồn tại: "
                      f"{signing_config}", file=sys.stderr)
                return 2
        elif DEFAULT_SIGNING_CONFIG.is_file():
            signing_config = str(DEFAULT_SIGNING_CONFIG)
        else:
            print("LỖI: --sign cần signing-config offline (không tìm "
                  f"thấy {DEFAULT_SIGNING_CONFIG}; truyền "
                  "--signing-config <đường dẫn>) — không ký bằng cấu "
                  "hình mặc định có thể đẩy lên Rekor công cộng",
                  file=sys.stderr)
            return 2
    run_id = run_id or run_dir.name
    schemas = load_schemas(DEFAULT_SCHEMAS_DIR)
    if not schemas:
        print(f"LỖI: không tìm thấy schema M2 tại {DEFAULT_SCHEMAS_DIR}",
              file=sys.stderr)
        return 2
    mapping = load_json(MAPPING_FILE)

    gate_dirs = discover_gate_dirs(run_dir)
    records = []        # record hợp lệ
    rejected = []       # record sai schema / không đọc được — nêu tên
    problems = []       # vấn đề khiến bundle không đầy đủ
    artifacts = []      # file phụ trợ được đưa vào bundle
    excluded = []       # file KHÔNG đưa vào bundle, kèm lý do
    commit_shas = set()

    def rel(p: Path) -> str:
        return p.relative_to(run_dir).as_posix()

    # --- Quét từng gate -----------------------------------------------------
    gate_status = {}
    for gate_no in EXPECTED_GATES:
        gdir = gate_dirs.get(gate_no)
        label = f"gate-{gate_no:02d}"
        if gdir is None:
            gate_status[gate_no] = {
                "gate": gate_no, "status": "absent", "records": [],
                "decisions": [], "note": "thư mục gate không có trong "
                                         "lần chạy này"}
            problems.append(f"{label}: thiếu thư mục gate trong lần chạy")
            continue
        gate_records, gate_decisions = [], []
        disabled_note = None
        has_scan_error = (gdir / "scan-error.json").exists()
        # URI artefact mà các record của gate này trỏ tới (để gom artefact)
        referenced = set()
        pending_json = []     # JSON không có evidence_type — quyết sau
        pending_other = []    # file không phải JSON — quyết sau
        for f in sorted(gdir.iterdir()):
            if f.is_dir():
                n_files = sum(1 for _ in f.rglob("*") if _.is_file())
                excluded.append({
                    "path": rel(f) + "/", "category": "thư mục con của gate",
                    "reason": f"{n_files} file trong thư mục con (vd sandbox "
                              f"của công cụ) — không phải bằng chứng dạng "
                              f"record, không đưa vào bundle"})
                continue
            name = f.name
            if name == "disabled-note.txt":
                disabled_note = f.read_text(encoding="utf-8",
                                             errors="replace")
                artifacts.append({"source": f, "path": rel(f),
                                  "gate": gate_no, "kind": "disabled-note"})
                continue
            if name.endswith(PRIVATE_KEY_SUFFIXES):
                excluded.append({
                    "path": rel(f), "category": "khoá riêng",
                    "reason": "vật liệu khoá riêng — KHÔNG bao giờ đưa vào "
                              "bundle bằng chứng"})
                continue
            if not name.endswith(".json"):
                pending_other.append(f)
                continue
            # File JSON: ứng viên record?
            try:
                data = load_json(f)
            except Exception as exc:
                if name.endswith(".record.json") or \
                        name.startswith("policy-decision-"):
                    rejected.append({
                        "source": rel(f), "gate": gate_no,
                        "errors": [f"không đọc được JSON: {exc}"]})
                else:
                    excluded.append({
                        "path": rel(f),
                        "category": "đầu ra thô của công cụ",
                        "reason": f"JSON không đọc được ({exc}) và không "
                                  f"phải file record"})
                continue
            if isinstance(data, dict) and "evidence_type" in data:
                etype = data.get("evidence_type")
                if etype not in schemas:
                    rejected.append({
                        "source": rel(f), "gate": gate_no,
                        "errors": [f"evidence_type {etype!r} không có "
                                   f"schema trong pack M2"]})
                    continue
                errs = validate(data, schemas[etype])
                if errs:
                    rejected.append({"source": rel(f), "gate": gate_no,
                                     "errors": errs})
                    continue
                rec = {"source": f, "path": rel(f), "gate": gate_no,
                       "data": data, "evidence_type": etype,
                       "bundle_path": f"records/{rel(f)}"}
                records.append(rec)
                gate_records.append(rec)
                if data.get("commit_sha"):
                    commit_shas.add(str(data["commit_sha"]))
                if etype == "policy-decision":
                    gate_decisions.append({
                        "policy_id": data.get("policy_id"),
                        "engine": data.get("engine"),
                        "decision": data.get("decision"),
                        "violations": data.get("violations") or []})
                uri = data.get("artifact_uri")
                if uri:
                    referenced.add(uri)
                if data.get("subject"):
                    referenced.add(f"{gdir.name}/{data['subject']}")
                continue
            if name.endswith(".record.json") or \
                    name.startswith("policy-decision-"):
                rejected.append({
                    "source": rel(f), "gate": gate_no,
                    "errors": ["file mang tên record nhưng không có trường "
                               "evidence_type — không khớp hợp đồng M2"]})
                continue
            pending_json.append(f)
        # Lượt 2: khi tập `referenced` đã đầy đủ mới quyết định các file
        # phụ trợ — artefact là file được record tham chiếu, đầu vào của
        # policy, hoặc tài liệu SBOM/provenance đi kèm record.
        for f in pending_json:
            run_rel = rel(f)
            if run_rel in referenced or f.name.endswith(".input.json") \
                    or f.name in ("sbom.cdx.json", "sbom.bundle.json",
                                  "provenance.intoto.json", "cosign.pub"):
                artifacts.append({"source": f, "path": run_rel,
                                  "gate": gate_no, "kind": "artifact"})
            else:
                excluded.append({
                    "path": run_rel,
                    "category": "đầu ra thô của công cụ",
                    "reason": "JSON không có evidence_type và không được "
                              "record nào tham chiếu"})
        for f in pending_other:
            run_rel = rel(f)
            if run_rel in referenced or f.name.endswith(".sarif") \
                    or f.name == "cosign.pub":
                artifacts.append({"source": f, "path": run_rel,
                                  "gate": gate_no, "kind": "artifact"})
            else:
                excluded.append({
                    "path": run_rel,
                    "category": "log/đầu ra thô của công cụ",
                    "reason": "không phải record có schema và không được "
                              "record nào tham chiếu"})
        # Trạng thái gate
        if disabled_note is not None and not gate_records:
            status = "disabled"
            note = disabled_note.strip().splitlines()[0] \
                if disabled_note.strip() else ""
        elif any(d["decision"] == "deny" for d in gate_decisions):
            status, note = "deny", ""
        elif has_scan_error:
            status = "scan-error"
            note = "gate có scan-error.json — lần quét không hoàn tất"
            problems.append(f"{label}: scan-error (quét không hoàn tất)")
        elif gate_decisions:
            status, note = "pass", ""
        elif gate_records:
            status = "evidence-only"
            note = "có record bằng chứng nhưng gate này không sinh " \
                   "policy-decision (quyết định chặn nằm ở gate khác)"
        else:
            status = "no-evidence"
            note = "gate không sinh record bằng chứng nào"
            problems.append(f"{label}: không có record bằng chứng")
        gate_status[gate_no] = {
            "gate": gate_no, "status": status,
            "records": [r["bundle_path"] for r in gate_records],
            "decisions": gate_decisions, "note": note}

    # --- Nguồn record phụ trợ: supplementary-records/ ------------------
    # Các bộ sinh bằng chứng quyết định/định kỳ (evidence/generators.py)
    # ghi record vào đây vì chúng không thuộc một gate CI nào. Kiểm
    # schema đúng như record của gate; file JSON không có evidence_type
    # trong thư mục này là đầu vào của policy (provenance) -> artefact.
    supplementary_paths = []
    supp_dir = run_dir / SUPPLEMENTARY_DIR_NAME
    if supp_dir.is_dir():
        for f in sorted(supp_dir.iterdir()):
            if not f.is_file():
                continue
            run_rel = rel(f)
            if not f.name.endswith(".json"):
                excluded.append({
                    "path": run_rel,
                    "category": "đầu ra thô của bộ sinh bằng chứng",
                    "reason": "file không phải JSON trong "
                              "supplementary-records/"})
                continue
            try:
                data = load_json(f)
            except Exception as exc:
                rejected.append({
                    "source": run_rel, "gate": SUPPLEMENTARY_LABEL,
                    "errors": [f"không đọc được JSON: {exc}"]})
                continue
            if isinstance(data, dict) and "evidence_type" in data:
                etype = data.get("evidence_type")
                if etype not in schemas:
                    rejected.append({
                        "source": run_rel, "gate": SUPPLEMENTARY_LABEL,
                        "errors": [f"evidence_type {etype!r} không có "
                                   f"schema trong pack M2"]})
                    continue
                errs = validate(data, schemas[etype])
                if errs:
                    rejected.append({
                        "source": run_rel, "gate": SUPPLEMENTARY_LABEL,
                        "errors": errs})
                    continue
                rec = {"source": f, "path": run_rel,
                       "gate": SUPPLEMENTARY_LABEL, "data": data,
                       "evidence_type": etype,
                       "bundle_path": f"records/{run_rel}"}
                records.append(rec)
                supplementary_paths.append(rec["bundle_path"])
                if data.get("commit_sha"):
                    commit_shas.add(str(data["commit_sha"]))
                uri = data.get("artifact_uri")
                if uri and (supp_dir / uri).is_file():
                    artifacts.append({"source": supp_dir / uri,
                                      "path": f"{SUPPLEMENTARY_DIR_NAME}/{uri}",
                                      "gate": SUPPLEMENTARY_LABEL,
                                      "kind": "artifact"})
                continue
            artifacts.append({"source": f, "path": run_rel,
                              "gate": SUPPLEMENTARY_LABEL,
                              "kind": "generator-input"})

    # --- Kế hoạch ci-log (record do collector phát hành) ---------------
    # Gom mọi file log của lần chạy (log của các gate trong thư mục
    # gate-*) thành một artefact zip xác định kèm hash — bằng chứng
    # cho hàng ISO A.8.15–A.8.16. Không có log thì không bịa record.
    run_date = None
    for rec in records:
        ts = rec["data"].get("timestamp")
        if ts:
            run_date = ts[:10]
            break
    run_date = run_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_files = sorted(
        p for p in run_dir.rglob("*.log")
        if p.is_file()
        and ".feeds" not in p.parts
        and SUPPLEMENTARY_DIR_NAME not in p.parts)
    ci_log_plan = None
    if log_files:
        zip_bytes, zip_sha = build_ci_log_archive(run_dir, log_files)
        ci_log_plan = {
            "zip_bytes": zip_bytes,
            "record": {
                "evidence_type": "ci-log",
                "period": run_date,
                "artifact_uri": CI_LOG_ARTIFACT_PATH,
                "sha256": f"sha256:{zip_sha}",
                "sources": ["ci-log"],
                "sources_note": "repo-audit-log không tồn tại ở lần "
                                "chạy cục bộ (cây chưa phải git repo, "
                                "chưa có GitHub repo) — nguồn duy nhất "
                                "là log của các gate trong lần chạy",
                "log_files": [p.relative_to(run_dir).as_posix()
                              for p in log_files],
                "log_file_count": len(log_files),
                "archive_format": "zip xác định (deterministic): tên "
                                  "file sắp xếp, mốc thời gian cố "
                                  "định — cùng tập log cho cùng hash",
                "generated_by": f"{TOOL_NAME} {TOOL_VERSION} "
                                f"(M4 collector, phát hành tại M5-A3)",
                "run_id": run_id,
            },
        }

    # Các thư mục ngoài gate-* ở gốc lần chạy (vd .feeds cache)
    for child in sorted(run_dir.iterdir()):
        if child.name == SUPPLEMENTARY_DIR_NAME:
            continue  # đã quét ở trên như nguồn record phụ trợ
        if child.is_dir() and not GATE_DIR_RE.match(child.name):
            n_files = sum(1 for _ in child.rglob("*") if _.is_file())
            excluded.append({
                "path": child.name + "/", "category": "dữ liệu phụ của lần chạy",
                "reason": f"{n_files} file ngoài hợp đồng gate (vd cache "
                          f"feed) — không đưa vào bundle"})

    for rej in rejected:
        problems.append(
            f"record sai schema: {rej['source']} — "
            + "; ".join(rej["errors"]))

    # --- Truy vết mapping pha 1 --------------------------------------------
    type_to_records = {}
    for rec in records:
        type_to_records.setdefault(rec["evidence_type"], []).append(
            rec["bundle_path"])
    if ci_log_plan is not None:
        # ci-log do collector phát hành (như control-evidence-index):
        # ghi nhận hiện diện ngay từ lượt truy vết đầu để chỉ mục
        # kiểm soát (sinh ngay sau) dẫn được tới file record này.
        type_to_records.setdefault("ci-log", []).append(
            CI_LOG_BUNDLE_PATH)
    traceability = []
    for row in mapping["rows"]:
        per_type = []
        for etype in row["evidence_types"]:
            files = type_to_records.get(etype, [])
            per_type.append({
                "evidence_type": etype,
                "present": bool(files),
                "origin": ("collector" if etype in COLLECTOR_TYPES
                           and files else "gate") if files else None,
                "files": files})
        present_n = sum(1 for t in per_type if t["present"])
        status = ("full" if present_n == len(per_type)
                  else "partial" if present_n else "none")
        traceability.append({
            "row": row["id"], "framework": row["framework"],
            "control_group": row["control_group"],
            "control_ids": row["control_ids"],
            "policies": row["policies"], "gates": row["gates"],
            "gate_note": row.get("gate_note", ""),
            "evidence": per_type, "status": status})
    full_rows = sum(1 for t in traceability if t["status"] == "full")
    completeness = round(full_rows / len(traceability), 4) \
        if traceability else 0.0

    # --- Record chỉ mục bằng chứng do collector sinh (schema M2) ------------
    period = run_date
    index_controls = {}
    for t in traceability:
        files = []
        for per in t["evidence"]:
            if per["present"] and per["evidence_type"] != \
                    "control-evidence-index":
                files.extend(per["files"])
        for cid in t["control_ids"]:
            index_controls[cid] = files
    index_record = {
        "evidence_type": "control-evidence-index",
        "period": period,
        "controls": index_controls,
        "completeness": completeness,
        "completeness_basis": "số hàng ánh xạ pha 1 có đủ mọi loại bằng "
                              "chứng / tổng số hàng pha 1 — collector "
                              "tính từ dữ liệu thật của lần chạy",
        "generated_by": f"{TOOL_NAME} {TOOL_VERSION} (M4 collector)",
        "run_id": run_id,
    }
    idx_errs = validate(index_record,
                        schemas["control-evidence-index"])
    if idx_errs:  # không bao giờ được xảy ra — lỗi của chính collector
        print("LỖI NỘI BỘ: record chỉ mục do collector sinh không khớp "
              f"schema: {idx_errs}", file=sys.stderr)
        return 2
    # Sau khi có index, cập nhật truy vết cho các hàng dùng loại này
    for t in traceability:
        for per in t["evidence"]:
            if per["evidence_type"] == "control-evidence-index":
                per["present"] = True
                per["origin"] = "collector"
                per["files"] = ["records/collector/"
                                "control-evidence-index.record.json"]
        present_n = sum(1 for x in t["evidence"] if x["present"])
        t["status"] = ("full" if present_n == len(t["evidence"])
                       else "partial" if present_n else "none")
    full_rows = sum(1 for t in traceability if t["status"] == "full")
    completeness = round(full_rows / len(traceability), 4)
    index_record["completeness"] = completeness

    # --- Tóm tắt finding -----------------------------------------------------
    secret_findings = extract_secret_findings(run_dir, gate_dirs)
    vuln_summary = extract_vuln_summary(records)
    denied_gates = [g for g, s in gate_status.items()
                    if s["status"] == "deny"]
    disabled_gates = [g for g, s in gate_status.items()
                      if s["status"] == "disabled"]
    bundle_status = "evidence-incomplete" if problems else "complete"

    if problems and not allow_incomplete:
        print("COLLECT DỪNG — lần chạy không đủ điều kiện đóng bundle:",
              file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print("Dùng --allow-incomplete nếu vẫn muốn đóng bundle kèm cờ "
              "'evidence-incomplete' (chế độ CI chỉ-thu-thập).",
              file=sys.stderr)
        return 1

    # --- Chuẩn bị chữ ký (nếu --sign): sinh khoá tạm NGOÀI cây trước
    # khi viết metadata, để khai báo chữ ký (kèm vân tay khoá công
    # khai) nằm ngay trong bundle.json + manifest.json — cả hai đều
    # được bundle.sha256 bao phủ, và chữ ký ký trên bundle.sha256.
    sign_tmp = None
    sign_dir = None
    signature_decl = None
    if sign:
        sign_tmp = tempfile.TemporaryDirectory(
            prefix="devsecops-os-sign-")
        sign_dir = Path(sign_tmp.name)
        try:
            pub_path = generate_signing_keypair(cosign_bin, sign_dir)
        except RuntimeError as exc:
            sign_tmp.cleanup()
            print(f"LỖI: {exc}", file=sys.stderr)
            return 2
        signature_decl = {
            "scheme": "cosign sign-blob (định dạng Sigstore bundle)",
            "signed_file": "bundle.sha256",
            "signature_file": SIG_BUNDLE_NAME,
            "public_key_file": SIG_PUBKEY_NAME,
            "public_key_sha256": sha256_file(pub_path),
            "identity": "local:cosign-ephemeral-key",
            "note": "Khoá tạm theo lần chạy, sinh ngoài cây và HUỶ "
                    "ngay sau khi ký; khoá riêng không vào bundle. "
                    "Chữ ký cục bộ không có transparency log và "
                    "không gắn danh tính OIDC — keyless OIDC + Rekor "
                    "trên CI là việc M5-B. Muốn chữ ký có giá trị "
                    "chống ký-lại, đối chiếu public_key_sha256 này "
                    "với bản ghi ngoài bundle (hồ sơ phát hành / log "
                    "CI) trước khi tin cosign.pub trong bundle.",
        }

    # --- Đóng gói -------------------------------------------------------------
    generated_at = iso_now()
    bundle_id = f"{run_id}-{generated_at.replace(':', '').replace('-', '')}"
    bundle_dir = out_dir or (DEFAULT_BUNDLES_DIR / bundle_id)
    if bundle_dir.exists():
        if sign_tmp is not None:
            sign_tmp.cleanup()
        print(f"LỖI: thư mục bundle đã tồn tại: {bundle_dir}",
              file=sys.stderr)
        return 2
    bundle_dir.mkdir(parents=True)

    manifest_files = []

    def add_file(src: Path, bundle_rel: str, role: str, extra=None):
        dest = bundle_dir / bundle_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        entry = {"path": bundle_rel, "sha256": sha256_file(dest),
                 "size_bytes": dest.stat().st_size, "role": role,
                 "source_mtime": iso_mtime(src)}
        if extra:
            entry.update(extra)
        manifest_files.append(entry)

    type_rows = {}
    for row in mapping["rows"]:
        for etype in row["evidence_types"]:
            type_rows.setdefault(etype, []).append(row["id"])

    for rec in records:
        data = rec["data"]
        extra = {"evidence_type": rec["evidence_type"],
                 "gate": rec["gate"],
                 "mapping_rows": type_rows.get(rec["evidence_type"], [])}
        if data.get("commit_sha"):
            extra["commit_sha"] = str(data["commit_sha"])
        for ts_key in ("timestamp", "period", "generated_at",
                       "report_date"):
            if data.get(ts_key):
                extra["record_timestamp"] = str(data[ts_key])
                break
        add_file(rec["source"], rec["bundle_path"], "record", extra)

    # record chỉ mục của collector
    idx_path = bundle_dir / "records/collector/" \
        "control-evidence-index.record.json"
    write_json(idx_path, index_record)
    manifest_files.append({
        "path": "records/collector/control-evidence-index.record.json",
        "sha256": sha256_file(idx_path),
        "size_bytes": idx_path.stat().st_size,
        "role": "record (collector-generated)",
        "evidence_type": "control-evidence-index",
        "mapping_rows": type_rows.get("control-evidence-index", []),
        "source_mtime": generated_at})

    # record ci-log + artefact zip log (khi lần chạy có file log)
    ci_log_summary = None
    if ci_log_plan is not None:
        ci_rec = ci_log_plan["record"]
        ci_errs = validate(ci_rec, schemas["ci-log"])
        if ci_errs:  # không bao giờ được xảy ra — lỗi của collector
            print("LỖI NỘI BỘ: record ci-log do collector sinh không "
                  f"khớp schema: {ci_errs}", file=sys.stderr)
            if sign_tmp is not None:
                sign_tmp.cleanup()
            return 2
        ci_path = bundle_dir / CI_LOG_BUNDLE_PATH
        write_json(ci_path, ci_rec)
        manifest_files.append({
            "path": CI_LOG_BUNDLE_PATH,
            "sha256": sha256_file(ci_path),
            "size_bytes": ci_path.stat().st_size,
            "role": "record (collector-generated)",
            "evidence_type": "ci-log",
            "mapping_rows": type_rows.get("ci-log", []),
            "source_mtime": generated_at})
        zip_path = bundle_dir / CI_LOG_ARTIFACT_PATH
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        zip_path.write_bytes(ci_log_plan["zip_bytes"])
        manifest_files.append({
            "path": CI_LOG_ARTIFACT_PATH,
            "sha256": sha256_file(zip_path),
            "size_bytes": zip_path.stat().st_size,
            "role": "artifact", "kind": "ci-log-archive",
            "gate": "collector"})
        ci_log_summary = {
            "record": CI_LOG_BUNDLE_PATH,
            "artifact": CI_LOG_ARTIFACT_PATH,
            "sha256": ci_rec["sha256"],
            "log_file_count": ci_rec["log_file_count"],
            "log_files": ci_rec["log_files"],
        }

    for art in artifacts:
        add_file(art["source"], f"artifacts/{art['path']}", "artifact",
                 {"gate": art["gate"], "kind": art["kind"]})

    for rej in rejected:  # chỉ tới đây khi --allow-incomplete
        dest_rel = f"rejected/{rej['source']}"
        add_file(run_dir / rej["source"], dest_rel, "rejected-record",
                 {"gate": rej["gate"], "schema_errors": rej["errors"]})

    for schema_file in sorted(DEFAULT_SCHEMAS_DIR.glob("*.schema.json")):
        add_file(schema_file, f"schemas/{schema_file.name}", "schema")

    summary = {
        "bundle_id": bundle_id, "run_id": run_id,
        "generated_at": generated_at, "status": bundle_status,
        "commit_shas": sorted(commit_shas),
        "problems": problems,
        "gates": [gate_status[g] for g in EXPECTED_GATES],
        "gates_denied": denied_gates, "gates_disabled": disabled_gates,
        "records_valid": len(records) + 1
                         + (1 if ci_log_plan is not None else 0),
        # +1: index của collector; +1 nữa khi có record ci-log
        "records_rejected": rejected,
        "supplementary_records": supplementary_paths,
        "ci_log": ci_log_summary,
        "artifacts_bundled": len(artifacts),
        "excluded": excluded,
        "secret_findings": secret_findings,
        "vulnerabilities": vuln_summary,
        "traceability": traceability,
        "completeness_full_rows": f"{full_rows}/{len(traceability)}",
    }
    write_json(bundle_dir / "summary.json", summary)
    manifest_files.append({
        "path": "summary.json",
        "sha256": sha256_file(bundle_dir / "summary.json"),
        "size_bytes": (bundle_dir / "summary.json").stat().st_size,
        "role": "report", "source_mtime": generated_at})
    (bundle_dir / "summary.md").write_text(
        render_summary_md(summary, mapping), encoding="utf-8")
    manifest_files.append({
        "path": "summary.md",
        "sha256": sha256_file(bundle_dir / "summary.md"),
        "size_bytes": (bundle_dir / "summary.md").stat().st_size,
        "role": "report", "source_mtime": generated_at})

    bundle_meta = {
        "bundle_format": BUNDLE_FORMAT, "bundle_id": bundle_id,
        "run_id": run_id, "generated_at": generated_at,
        "status": bundle_status, "commit_shas": sorted(commit_shas),
        "collector": {"tool": TOOL_NAME, "version": TOOL_VERSION},
        "verify_command": "python3 evidence/verify_bundle.py <bundle-dir>",
    }
    if signature_decl:
        bundle_meta["signature"] = signature_decl
    write_json(bundle_dir / "bundle.json", bundle_meta)
    manifest_files.append({
        "path": "bundle.json",
        "sha256": sha256_file(bundle_dir / "bundle.json"),
        "size_bytes": (bundle_dir / "bundle.json").stat().st_size,
        "role": "metadata", "source_mtime": generated_at})

    manifest_files.sort(key=lambda e: e["path"])
    manifest = {
        "bundle_format": BUNDLE_FORMAT, "bundle_id": bundle_id,
        "run_id": run_id, "generated_at": generated_at,
        "status": bundle_status, "commit_shas": sorted(commit_shas),
        "collector": {"tool": TOOL_NAME, "version": TOOL_VERSION},
        "note": "Mọi file trong bundle (trừ manifest.json và "
                "bundle.sha256) đều có một dòng ở đây kèm SHA-256, kích "
                "thước và vai trò. bundle.sha256 bao phủ thêm cả "
                "manifest.json để mọi sửa đổi đều bị phát hiện khi "
                "chạy verify hoặc `sha256sum -c bundle.sha256`."
                + (" Bundle này CÓ chữ ký Cosign trên bundle.sha256 "
                   "(trường 'signature' ở trên); hai file "
                   "bundle.sigstore.json và cosign.pub cố ý không có "
                   "dòng trong manifest và không được bundle.sha256 "
                   "bao phủ — chúng chứng thực chính bundle.sha256."
                   if signature_decl else ""),
        "files": manifest_files,
    }
    if signature_decl:
        manifest["signature"] = signature_decl
    write_json(bundle_dir / "manifest.json", manifest)

    sha_lines = []
    for entry in manifest_files:
        sha_lines.append(f"{entry['sha256']}  {entry['path']}")
    sha_lines.append(
        f"{sha256_file(bundle_dir / 'manifest.json')}  manifest.json")
    sha_lines.sort(key=lambda line: line.split("  ", 1)[1])
    (bundle_dir / "bundle.sha256").write_text(
        "\n".join(sha_lines) + "\n", encoding="utf-8")

    # --- Ký bundle.sha256 bằng khoá tạm, rồi huỷ khoá -----------------
    if sign:
        try:
            sig_tmp_out = sign_dir / SIG_BUNDLE_NAME
            cosign_sign_blob(cosign_bin, sign_dir / "cosign.key",
                             bundle_dir / "bundle.sha256", sig_tmp_out,
                             signing_config, sign_dir)
            shutil.copy2(sig_tmp_out, bundle_dir / SIG_BUNDLE_NAME)
            shutil.copy2(sign_dir / "cosign.pub",
                         bundle_dir / SIG_PUBKEY_NAME)
            # Tự kiểm chứng ngay như gate 6: chữ ký vừa tạo phải
            # verify được bằng chính bản sao đã đưa vào bundle.
            cosign_verify_blob(cosign_bin, bundle_dir / SIG_PUBKEY_NAME,
                               bundle_dir / SIG_BUNDLE_NAME,
                               bundle_dir / "bundle.sha256", bundle_dir)
        except RuntimeError as exc:
            print(f"LỖI: ký bundle thất bại — xoá bundle chưa ký: "
                  f"{exc}", file=sys.stderr)
            shutil.rmtree(bundle_dir, ignore_errors=True)
            sign_tmp.cleanup()
            return 2
        sign_tmp.cleanup()

    print(f"Bundle: {bundle_dir}")
    print(f"  run={run_id}  trạng thái={bundle_status}  "
          f"records={len(records) + 1 + (1 if ci_log_plan is not None else 0)} "
          f"(gồm {1 + (1 if ci_log_plan is not None else 0)} do "
          f"collector sinh)  "
          f"artefact={len(artifacts)}  bị loại={len(rejected)}")
    print(f"  gate chặn: {denied_gates or 'không'}  "
          f"gate tắt: {disabled_gates or 'không'}  "
          f"truy vết đầy đủ: {full_rows}/{len(traceability)} hàng pha 1")
    if signature_decl:
        print(f"  chữ ký: Cosign trên bundle.sha256 (khoá tạm cục bộ, "
              f"vân tay khoá công khai "
              f"{signature_decl['public_key_sha256'][:16]}…) — verify "
              f"sẽ kiểm thêm chữ ký")
    print(f"  Kiểm chứng: python3 evidence/verify_bundle.py {bundle_dir}")
    return 0


def render_summary_md(summary, mapping) -> str:
    lines = []
    lines.append(f"# Báo cáo tổng hợp bằng chứng — {summary['run_id']}")
    lines.append("")
    lines.append(f"- Bundle: `{summary['bundle_id']}`")
    lines.append(f"- Sinh lúc (UTC): {summary['generated_at']}")
    lines.append(f"- Trạng thái bundle: **{summary['status']}**")
    commits = ", ".join(f"`{c}`" for c in summary["commit_shas"]) or "—"
    lines.append(f"- Commit SHA trong các record: {commits}")
    lines.append(f"- Record hợp lệ: {summary['records_valid']} · "
                 f"record bị loại: {len(summary['records_rejected'])} · "
                 f"artefact kèm theo: {summary['artifacts_bundled']}")
    if summary["problems"]:
        lines.append("")
        lines.append("## Vấn đề (bundle bị gắn cờ evidence-incomplete)")
        for p in summary["problems"]:
            lines.append(f"- {p}")
    lines.append("")
    lines.append("## Kết quả theo gate")
    lines.append("")
    lines.append("| Gate | Trạng thái | Quyết định policy | Record |")
    lines.append("|---|---|---|---|")
    for g in summary["gates"]:
        decs = "; ".join(
            f"{d['policy_id']} → **{d['decision']}**"
            + (f" ({len(d['violations'])} vi phạm)"
               if d["violations"] else "")
            for d in g["decisions"]) or "—"
        note = f" — {g['note']}" if g["note"] else ""
        lines.append(f"| {g['gate']} | {g['status']}{note} | {decs} | "
                     f"{len(g['records'])} |")
    denies = [d for g in summary["gates"] for d in g["decisions"]
              if d["decision"] == "deny"]
    if denies:
        lines.append("")
        lines.append("### Lý do chặn (nguyên văn từ policy-decision)")
        for d in denies:
            lines.append(f"- **{d['policy_id']}**:")
            for v in d["violations"]:
                lines.append(f"  - {v}")
    lines.append("")
    lines.append("## Finding secret (từ SARIF của gate 1)")
    lines.append("")
    if summary["secret_findings"]:
        for s in summary["secret_findings"]:
            lines.append(f"- rule `{s['rule']}` tại `{s['file']}:"
                         f"{s['line']}`")
    else:
        lines.append("- Không có finding secret nào trong lần chạy này.")
    lines.append("")
    lines.append("## Lỗ hổng (record vuln-risk-ranking, gate 8)")
    lines.append("")
    vuln = summary["vulnerabilities"]
    if vuln:
        feeds = vuln.get("feed_versions") or {}
        feeds_txt = ", ".join(f"{k}={v}" for k, v in feeds.items()) \
            if isinstance(feeds, dict) else str(feeds)
        lines.append(f"- Tổng số dòng xếp hạng: {vuln['entries_total']} "
                     f"({vuln['unique_cves']} CVE khác nhau); nguồn: "
                     f"`{vuln['source_record']}`; feed: {feeds_txt}")
        lines.append(f"- Quyết định issue: {vuln['issue_entries']} dòng.")
        lines.append(f"- Quyết định BLOCK (đã khử trùng lặp theo "
                     f"CVE/gói/phiên bản): {len(vuln['block_unique'])}")
        for b in vuln["block_unique"]:
            lines.append(f"  - {b['cve']} — {b['package']}=={b['version']}"
                         f" (KEV: {b['in_kev']}, EPSS: {b['epss']})")
        lines.append(f"- Thuộc CISA KEV: {len(vuln['kev_unique'])} CVE "
                     f"khác nhau.")
    else:
        lines.append("- Không có record vuln-risk-ranking trong lần "
                     "chạy này.")
    lines.append("")
    lines.append("## Truy vết: khung → policy → gate → bằng chứng")
    lines.append("")
    lines.append(f"Hàng pha 1 có đủ mọi loại bằng chứng: "
                 f"**{summary['completeness_full_rows']}**. Loại bằng "
                 f"chứng chưa có trong lần chạy được ghi rõ, không để "
                 f"trống im lặng.")
    lines.append("")
    lines.append("| Hàng | Khung — nhóm kiểm soát | Policy | Gate | "
                 "Bằng chứng | Trạng thái |")
    lines.append("|---|---|---|---|---|---|")
    for t in summary["traceability"]:
        ev = "<br>".join(
            f"{'✅' if e['present'] else '❌'} {e['evidence_type']}"
            + (" (collector sinh)" if e["origin"] == "collector" else "")
            for e in t["evidence"])
        gates = ", ".join(str(g) for g in t["gates"]) or \
            (t["gate_note"] or "—")
        status_vi = {"full": "đủ", "partial": "một phần",
                     "none": "chưa có"}[t["status"]]
        lines.append(
            f"| {t['row']} | {t['framework']} — {t['control_group']} | "
            f"{', '.join(t['policies'])} | {gates} | {ev} | "
            f"{status_vi} |")
    missing_notes = {
        "change-record": "chưa có trong lần chạy này — sinh bằng "
                         "`evidence/generators.py change-record "
                         "--run-dir <lần chạy>` (từ kết quả gate "
                         "thật của chính lần chạy) trước khi collect",
        "ci-log": "lần chạy không chứa file log (.log) nào để "
                  "collector đóng gói — ci-log chỉ được phát hành "
                  "khi có log thật của lần chạy",
        "drift-report": "chưa có trong lần chạy này — sinh bằng "
                        "`evidence/generators.py drift-report` (so "
                        "cấu hình hiện tại với baseline đã khai) "
                        "trước khi collect",
        "config-baseline-report": "chưa có trong lần chạy này — sinh "
                                  "bằng `evidence/generators.py "
                                  "config-baseline` trước khi collect",
        "access-review-report": "chưa có trong lần chạy này — sinh "
                                "bằng `evidence/generators.py "
                                "access-review` trước khi collect",
        "pr-review-report": "chỉ sinh khi gate 10 bật — gate 10 đang "
                            "TẮT theo thiết kế pha 1",
    }
    lines.append("")
    lines.append("### Loại bằng chứng chưa có — lý do")
    lines.append("")
    seen_missing = set()
    for t in summary["traceability"]:
        for e in t["evidence"]:
            if not e["present"] and e["evidence_type"] not in seen_missing:
                seen_missing.add(e["evidence_type"])
                reason = missing_notes.get(
                    e["evidence_type"],
                    "chưa có nguồn sinh trong lần chạy này")
                lines.append(f"- `{e['evidence_type']}`: {reason}")
    if summary["records_rejected"]:
        lines.append("")
        lines.append("## Record bị loại (sai schema — nêu tên)")
        lines.append("")
        for r in summary["records_rejected"]:
            lines.append(f"- `{r['source']}`: " + "; ".join(r["errors"]))
    lines.append("")
    lines.append("## File của lần chạy KHÔNG đưa vào bundle")
    lines.append("")
    by_cat = {}
    for e in summary["excluded"]:
        by_cat.setdefault(e["category"], []).append(e)
    for cat, items in sorted(by_cat.items()):
        lines.append(f"- **{cat}**: {len(items)} mục — "
                     f"{items[0]['reason']}")
        for it in items:
            lines.append(f"  - `{it['path']}`")
    if summary.get("supplementary_records"):
        lines.append("")
        lines.append("## Record phụ trợ (bộ sinh bằng chứng quyết "
                     "định/định kỳ)")
        lines.append("")
        lines.append("Sinh bởi `evidence/generators.py` từ dữ liệu "
                     "thật của lần chạy/cây, ghi vào "
                     "`supplementary-records/` và được collector kiểm "
                     "schema như mọi record khác:")
        for p in summary["supplementary_records"]:
            lines.append(f"- `{p}`")
    if summary.get("ci_log"):
        ci = summary["ci_log"]
        lines.append("")
        lines.append("## Log CI (record ci-log do collector phát hành)")
        lines.append("")
        lines.append(f"- Record: `{ci['record']}`")
        lines.append(f"- Artefact gói log: `{ci['artifact']}` "
                     f"({ci['log_file_count']} file log)")
        lines.append(f"- SHA-256 của gói log (khai trong record): "
                     f"`{ci['sha256']}` — verify đối chiếu lại hash "
                     f"này với artefact trong bundle")
    lines.append("")
    lines.append("## Kiểm chứng bundle này")
    lines.append("")
    lines.append("```bash")
    lines.append("python3 evidence/verify_bundle.py <thư-mục-bundle>")
    lines.append("# hoặc thuần tuý kiểm hash:")
    lines.append("cd <thư-mục-bundle> && sha256sum -c bundle.sha256")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# VERIFY
# ---------------------------------------------------------------------------

def verify(bundle_dir: Path, cosign: str | None = None) -> int:
    errors, notes = [], []
    if not bundle_dir.is_dir():
        print(f"FAIL: thư mục bundle không tồn tại: {bundle_dir}")
        return 1
    sha_path = bundle_dir / "bundle.sha256"
    manifest_path = bundle_dir / "manifest.json"
    if not sha_path.is_file():
        errors.append("thiếu bundle.sha256 — không kiểm chứng được")
    if not manifest_path.is_file():
        errors.append("thiếu manifest.json — không kiểm chứng được")
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1

    # 1) bundle.sha256 bao phủ mọi file, hash khớp từng file
    recorded = {}
    for line in sha_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, _, name = line.partition("  ")
        recorded[name.lstrip("*").strip()] = digest.strip()
    disk_files = {}
    for p in sorted(bundle_dir.rglob("*")):
        if p.is_file():
            relp = p.relative_to(bundle_dir).as_posix()
            # bundle.sha256 tự bao phủ các file khác; hai file chữ ký
            # ở gốc bundle chứng thực chính bundle.sha256 nên cũng
            # đứng ngoài diện bao phủ này (kiểm riêng ở bước 4).
            if relp != "bundle.sha256" and relp not in SIGNATURE_FILES:
                disk_files[relp] = p
    for name, digest in sorted(recorded.items()):
        if name not in disk_files:
            errors.append(f"bundle.sha256 liệt kê nhưng file không có: "
                          f"{name}")
        else:
            actual = sha256_file(disk_files[name])
            if actual != digest:
                errors.append(
                    f"hash không khớp: {name} (manifest ghi {digest[:16]}"
                    f"…, thực tế {actual[:16]}… — file đã bị sửa đổi)")
    for name in sorted(disk_files):
        if name not in recorded:
            errors.append(f"file có trong bundle nhưng không được "
                          f"bundle.sha256 bao phủ: {name}")

    # 2) manifest nhất quán với bundle.sha256 và với đĩa
    try:
        manifest = load_json(manifest_path)
    except Exception as exc:
        errors.append(f"manifest.json không đọc được: {exc}")
        manifest = None
    manifest_entries = {}
    if manifest is not None:
        for entry in manifest.get("files", []):
            manifest_entries[entry["path"]] = entry
            if entry["path"] in recorded and \
                    recorded[entry["path"]] != entry["sha256"]:
                errors.append(
                    f"manifest và bundle.sha256 lệch nhau tại "
                    f"{entry['path']}")
        expected = set(disk_files) - {"manifest.json"}
        if set(manifest_entries) != expected:
            diff = sorted(set(manifest_entries) ^ expected)
            errors.append(
                f"manifest không khớp tập file trên đĩa tại: "
                f"{', '.join(diff[:5])}")
        if manifest.get("status") == "evidence-incomplete":
            notes.append("bundle mang cờ 'evidence-incomplete' từ lúc "
                         "collect (xem summary.json để biết vấn đề)")

    # 3) Kiểm tra lại schema của mọi record trong bundle
    schemas_dir = bundle_dir / "schemas"
    if not schemas_dir.is_dir():
        schemas_dir = DEFAULT_SCHEMAS_DIR
        notes.append("bundle không kèm schemas/ — dùng schema M2 trong "
                     "repo để kiểm tra lại")
    schemas = load_schemas(schemas_dir)
    records_dir = bundle_dir / "records"
    n_records = 0
    ci_log_records = []
    if records_dir.is_dir():
        for p in sorted(records_dir.rglob("*.json")):
            relp = p.relative_to(bundle_dir).as_posix()
            n_records += 1
            try:
                data = load_json(p)
            except Exception as exc:
                errors.append(f"{relp}: không đọc được JSON: {exc}")
                continue
            etype = data.get("evidence_type") if isinstance(data, dict) \
                else None
            if etype not in schemas:
                errors.append(f"{relp}: evidence_type {etype!r} không "
                              f"có schema tương ứng")
                continue
            for err in validate(data, schemas[etype]):
                errors.append(f"{relp}: {err}")
            if etype == "ci-log":
                ci_log_records.append((relp, data))
    else:
        errors.append("bundle không có thư mục records/")

    # 3b) Đối chiếu chéo record ci-log: hash khai trong record phải
    # khớp SHA-256 thật của artefact gói log nằm trong bundle — bắt
    # được cả trường hợp record và artefact bị sửa không nhất quán.
    for relp, data in ci_log_records:
        artifact_uri = data.get("artifact_uri") or ""
        declared = (data.get("sha256") or "").removeprefix("sha256:")
        artifact_path = bundle_dir / artifact_uri
        if not artifact_uri or not artifact_path.is_file():
            errors.append(
                f"{relp}: record ci-log trỏ tới artefact "
                f"{artifact_uri!r} không có trong bundle")
        elif declared and sha256_file(artifact_path) != declared:
            errors.append(
                f"{relp}: hash gói log khai trong record "
                f"({declared[:16]}…) không khớp SHA-256 thật của "
                f"{artifact_uri} — record hoặc artefact đã bị sửa "
                f"không nhất quán")
        else:
            notes.append(
                f"ci-log: hash gói log ({artifact_uri}) khớp khai "
                f"báo trong record")
    rejected_dir = bundle_dir / "rejected"
    if rejected_dir.is_dir():
        n_rej = sum(1 for _ in rejected_dir.rglob("*") if _.is_file())
        notes.append(f"bundle chứa {n_rej} record bị collector loại "
                     f"(đã nêu lý do trong manifest/summary) — các file "
                     f"này đã được kiểm hash ở bước 1 nhưng không nằm "
                     f"trong diện kiểm schema")

    # 4) Chữ ký Cosign trên bundle.sha256 — khi bundle CÓ khai báo
    # chữ ký (trong manifest.json, dự phòng bundle.json; cả hai đều
    # được bundle.sha256 bao phủ nên khai báo không bị sửa âm thầm).
    # Khai báo mà thiếu file/không kiểm được/sai chữ ký = FAIL ồn ào,
    # không bao giờ hạ xuống "chỉ kiểm hash".
    decl = None
    if manifest is not None:
        decl = manifest.get("signature")
    if decl is None and (bundle_dir / "bundle.json").is_file():
        try:
            decl = load_json(bundle_dir / "bundle.json").get("signature")
        except Exception:
            decl = None
    has_sig_files = (bundle_dir / SIG_BUNDLE_NAME).is_file() or \
        (bundle_dir / SIG_PUBKEY_NAME).is_file()
    if decl:
        sig_path = bundle_dir / decl.get("signature_file",
                                         SIG_BUNDLE_NAME)
        pub_path = bundle_dir / decl.get("public_key_file",
                                         SIG_PUBKEY_NAME)
        if not sig_path.is_file():
            errors.append("bundle khai báo có chữ ký Cosign nhưng "
                          f"thiếu file chữ ký {sig_path.name}")
        if not pub_path.is_file():
            errors.append("bundle khai báo có chữ ký Cosign nhưng "
                          f"thiếu khoá công khai {pub_path.name}")
        if sig_path.is_file() and pub_path.is_file():
            fingerprint = decl.get("public_key_sha256")
            if fingerprint and sha256_file(pub_path) != fingerprint:
                errors.append(
                    "cosign.pub không khớp vân tay khoá công khai đã "
                    "khai báo trong manifest — khoá đã bị thay")
            cosign_bin = find_cosign(cosign)
            if not cosign_bin:
                errors.append(
                    "bundle có khai báo chữ ký Cosign nhưng không "
                    "tìm thấy cosign để kiểm chứng (cài cosign hoặc "
                    "truyền --cosign / COSIGN_BINARY) — không coi "
                    "là đạt")
            else:
                try:
                    cosign_verify_blob(
                        cosign_bin, pub_path, sig_path,
                        bundle_dir / "bundle.sha256", bundle_dir)
                    notes.append(
                        "chữ ký Cosign trên bundle.sha256: HỢP LỆ "
                        "(khoá cục bộ tạm thời; giới hạn so với "
                        "keyless OIDC — xem evidence/README.md)")
                except RuntimeError as exc:
                    errors.append(f"chữ ký Cosign KHÔNG hợp lệ: {exc}")
    elif has_sig_files:
        notes.append("bundle có file chữ ký ở gốc nhưng manifest "
                     "không khai báo chữ ký — không kiểm chứng chữ ký")
    else:
        notes.append("bundle không có chữ ký mật mã — chỉ kiểm toàn "
                     "vẹn bằng SHA-256")

    print(f"Bundle: {bundle_dir}")
    print(f"  file được kiểm hash: {len(recorded)} · "
          f"record được kiểm schema: {n_records}")
    for n in notes:
        print(f"  LƯU Ý: {n}")
    if errors:
        print("KẾT QUẢ: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("KẾT QUẢ: PASS — mọi hash khớp manifest, mọi record khớp "
          "schema M2")
    return 0


# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="bundle_tool",
        description="devsecops-os evidence bundle tool (M4)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_collect = sub.add_parser(
        "collect", help="thu thập + đóng bundle từ một lần chạy gates")
    p_collect.add_argument("run_dir",
                           help="thư mục lần chạy (evidence/output/<run>)")
    p_collect.add_argument("--out-dir", default=None,
                           help="thư mục bundle đầu ra (mặc định: "
                                "evidence/bundles/<run>-<thời gian>)")
    p_collect.add_argument("--run-id", default=None,
                           help="định danh lần chạy (mặc định: tên thư "
                                "mục lần chạy)")
    p_collect.add_argument("--allow-incomplete", action="store_true",
                           help="vẫn đóng bundle khi có record sai "
                                "schema/gate thiếu bằng chứng, kèm cờ "
                                "evidence-incomplete (chế độ CI)")
    p_collect.add_argument("--sign", action="store_true",
                           help="ký bundle.sha256 bằng Cosign (khoá "
                                "tạm theo lần chạy, huỷ ngay sau khi "
                                "ký; cần cosign + signing-config "
                                "offline)")
    p_collect.add_argument("--cosign", default=None,
                           help="đường dẫn cosign (mặc định: "
                                "COSIGN_BINARY hoặc PATH)")
    p_collect.add_argument("--signing-config", default=None,
                           help="signing-config cho cosign (mặc định: "
                                "gates/local/signing-config-offline."
                                "json của repo)")

    p_verify = sub.add_parser("verify", help="kiểm chứng một bundle")
    p_verify.add_argument("bundle_dir", help="thư mục bundle")
    p_verify.add_argument("--cosign", default=None,
                          help="đường dẫn cosign để kiểm chữ ký "
                               "(mặc định: COSIGN_BINARY hoặc PATH)")

    args = parser.parse_args(argv)
    if args.command == "collect":
        return collect(Path(args.run_dir),
                       Path(args.out_dir) if args.out_dir else None,
                       args.run_id, args.allow_incomplete,
                       sign=args.sign, cosign=args.cosign,
                       signing_config=args.signing_config)
    return verify(Path(args.bundle_dir), cosign=args.cosign)


if __name__ == "__main__":
    raise SystemExit(main())
