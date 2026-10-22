#!/usr/bin/env python3
"""Unit test cho evidence/generators.py (M5-A3) + các mở rộng
collector của bundle_tool (supplementary-records + ci-log).

Chạy từ gốc repo:

    python3 -m unittest discover -s evidence/tests -v

Fixture tự sinh trong thư mục tạm: lần chạy gates tối thiểu (mỗi
gate một policy-decision hợp lệ), workload IaC tối thiểu viết tay
cho drift, workflow YAML tối thiểu cho access-review. Các test cần
binary ngoài (opa/conftest) tự bỏ qua khi không tìm thấy — binary
được tìm ở ~/workspace/tools trên máy phát triển.
"""

import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

EVIDENCE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = EVIDENCE_DIR.parent
sys.path.insert(0, str(EVIDENCE_DIR))

import bundle_tool  # noqa: E402
import generators  # noqa: E402

TOOLS = Path.home() / "workspace" / "tools"
OPA = str(TOOLS / "opa") if (TOOLS / "opa").is_file() else None
CONFTEST = str(TOOLS / "conftest") if (TOOLS / "conftest").is_file() \
    else None
SCHEMAS = bundle_tool.load_schemas(
    REPO_ROOT / "policies" / "evidence-schemas")
COMMIT = "0123456789abcdef0123456789abcdef01234567"


def schema_errors(record):
    return bundle_tool.validate(record, SCHEMAS[record["evidence_type"]])


def make_decision(gate, policy_id, decision="pass"):
    return {
        "evidence_type": "policy-decision", "policy_id": policy_id,
        "engine": "opa", "gate": gate, "decision": decision,
        "violations": [] if decision == "pass" else ["vi phạm mẫu"],
        "commit_sha": COMMIT, "timestamp": "2026-10-22T00:00:00Z",
    }


def build_run_with_decisions(root: Path) -> Path:
    """Lần chạy tối thiểu có đủ quyết định cho change-record:
    secret_findings (gate 1), SARIF gate 2, 3 policy IaC (gate 4),
    dependency_kev (gate 8)."""
    run_dir = root / "local-clean"
    layout = {
        1: [make_decision(1, "devsecops.secret_findings")],
        4: [make_decision(4, "devsecops.network_exposure"),
            make_decision(4, "devsecops.storage_encryption"),
            make_decision(4, "devsecops.iam_least_privilege")],
        8: [make_decision(8, "devsecops.dependency_kev")],
    }
    for gate, recs in layout.items():
        gdir = run_dir / f"gate-{gate:02d}-fixture"
        gdir.mkdir(parents=True)
        for rec in recs:
            name = ("policy-decision-"
                    + rec["policy_id"].replace("devsecops.", "")
                    + ".json")
            (gdir / name).write_text(json.dumps(rec, indent=2),
                                     encoding="utf-8")
    g2 = run_dir / "gate-02-fixture"
    g2.mkdir()
    (g2 / "sarif-report.record.json").write_text(json.dumps({
        "evidence_type": "sarif-report", "format": "SARIF 2.1.0",
        "tool": "semgrep", "commit_sha": COMMIT,
        "artifact_uri": "gate-02-fixture/semgrep.sarif",
        "sha256": "sha256:" + "0" * 64,
    }), encoding="utf-8")
    return run_dir


MINIMAL_MAIN_TF = """
resource "aws_security_group" "app" {
  ingress {
    from_port   = 443
    to_port     = 443
    cidr_blocks = ["10.0.0.0/8"]
  }
}
"""

MINIMAL_VARS_TF = """
variable "region" {
  default = "eu-west-1"
}
"""

WORLD_OPEN_RULE = """
resource "aws_vpc_security_group_ingress_rule" "app_open" {
  security_group_id = aws_security_group.app.id
  from_port         = 22
  to_port           = 22
  cidr_ipv4         = "0.0.0.0/0"
}
"""


def build_infra(root: Path, extra: str = "") -> Path:
    infra = root / "infra"
    infra.mkdir(parents=True)
    (infra / "main.tf").write_text(MINIMAL_MAIN_TF + extra,
                                   encoding="utf-8")
    (infra / "variables.tf").write_text(MINIMAL_VARS_TF,
                                        encoding="utf-8")
    return infra


class ChangeRecordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gen-cr-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    @unittest.skipUnless(OPA, "không tìm thấy opa tại ~/workspace/tools")
    def test_change_record_from_run_decisions(self):
        run_dir = build_run_with_decisions(self.tmp)
        out = self.tmp / "supp"
        res = generators.gen_change_record(run_dir, out, OPA)
        rec = res["record"]
        self.assertEqual(schema_errors(rec), [])
        self.assertEqual(rec["gate_results"], {
            "secret": "pass", "sast": "pass", "sca": "pass",
            "iac": "pass"})
        self.assertEqual(rec["approvals"], [])
        self.assertEqual(rec["commit_sha"], COMMIT)
        dec = res["decision"]
        self.assertEqual(schema_errors(dec), [])
        # Không có phê duyệt PR thật ở lần chạy cục bộ -> policy DENY
        # đúng một vi phạm (phê duyệt). Đây là hành vi đúng thiết kế:
        # bộ sinh ghi giá trị thật, policy tự kết luận.
        self.assertEqual(dec["decision"], "deny")
        self.assertEqual(len(dec["violations"]), 1)
        self.assertIn("phe duyet", dec["violations"][0])

    @unittest.skipUnless(OPA, "không tìm thấy opa tại ~/workspace/tools")
    def test_change_record_reflects_denied_gate(self):
        run_dir = build_run_with_decisions(self.tmp)
        # Lật quyết định secret thành deny ngay trên đĩa rồi sinh lại.
        p = (run_dir / "gate-01-fixture"
             / "policy-decision-secret_findings.json")
        data = json.loads(p.read_text(encoding="utf-8"))
        data["decision"] = "deny"
        data["violations"] = ["có finding secret"]
        p.write_text(json.dumps(data), encoding="utf-8")
        res = generators.gen_change_record(run_dir, self.tmp / "s2", OPA)
        self.assertEqual(res["record"]["gate_results"]["secret"], "deny")


@unittest.skipUnless(CONFTEST, "không tìm thấy conftest")
class DriftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gen-drift-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.infra = build_infra(self.tmp / "wl")
        self.baseline = self.tmp / "baseline.json"
        generators.write_baseline(self.infra, self.baseline, CONFTEST)

    @unittest.skipUnless(OPA, "không tìm thấy opa tại ~/workspace/tools")
    def test_no_drift_against_own_baseline(self):
        res = generators.gen_drift_report(self.infra, self.baseline,
                                          self.tmp / "out", OPA,
                                          CONFTEST)
        self.assertEqual(res["record"]["drift_items"], [])
        self.assertEqual(schema_errors(res["record"]), [])
        self.assertEqual(res["decision"]["decision"], "pass")

    @unittest.skipUnless(OPA, "không tìm thấy opa tại ~/workspace/tools")
    def test_world_open_rule_is_detected_as_network_drift(self):
        infra2 = build_infra(self.tmp / "wl2", extra=WORLD_OPEN_RULE)
        res = generators.gen_drift_report(infra2, self.baseline,
                                          self.tmp / "out2", OPA,
                                          CONFTEST)
        items = res["record"]["drift_items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["resource"], "aws_security_group.app")
        self.assertEqual(items[0]["category"], "network")
        self.assertEqual(len(items[0]["added_rules"]), 1)
        self.assertEqual(items[0]["added_rules"][0]["cidr_blocks"],
                         ["0.0.0.0/0"])

    def test_parse_infra_matches_gate4_adapter_cli(self):
        # Đầu ra parse của generators phải khớp byte-for-byte về mặt
        # dữ liệu với adapter CLI của gate 4 trên workload thật.
        import subprocess
        real_infra = (REPO_ROOT / "examples" / "payments-sample"
                      / "clean" / "infra")
        mine = generators.parse_infra(CONFTEST, real_infra)
        out = self.tmp / "adapter-out.json"
        proc = subprocess.run(
            [sys.executable,
             str(REPO_ROOT / "gates" / "local" / "adapters"
                 / "tf_parse_input.py"),
             "--conftest", CONFTEST, "--infra", str(real_infra),
             "--out", str(out)],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(mine, json.loads(out.read_text()))


class AccessReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gen-ar-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _repo(self, files: dict) -> Path:
        root = self.tmp / "repo"
        wdir = root / ".github" / "workflows"
        wdir.mkdir(parents=True)
        for name, text in files.items():
            (wdir / name).write_text(text, encoding="utf-8")
        return root

    def test_parse_permissions_block_and_job_level(self):
        text = (
            "name: x\n"
            "permissions:\n"
            "  contents: read\n"
            "jobs:\n"
            "  build:\n"
            "    runs-on: ubuntu-latest\n"
            "    permissions:\n"
            "      id-token: write\n"
            "      contents: read\n"
            "    steps: []\n")
        parsed = generators.parse_workflow_permissions(text)
        self.assertEqual(parsed["top"], {"contents": "read"})
        self.assertEqual(parsed["jobs"]["build"],
                         {"id-token": "write", "contents": "read"})
        self.assertTrue(parsed["oidc"])

    def test_parse_permissions_scalar_and_missing(self):
        parsed = generators.parse_workflow_permissions(
            "name: x\npermissions: write-all\njobs: {}\n")
        self.assertEqual(parsed["top"], "write-all")
        parsed2 = generators.parse_workflow_permissions("name: x\n")
        self.assertIsNone(parsed2["top"])

    def test_findings_for_missing_and_write_all(self):
        root = self._repo({
            "a.yml": "name: a\njobs:\n  j:\n    steps: []\n",
            "b.yml": "name: b\npermissions: write-all\njobs: {}\n",
        })
        res = generators.gen_access_review(root, self.tmp / "out")
        rec = res["record"]
        self.assertEqual(schema_errors(rec), [])
        levels = {(s["workflow"].split("/")[-1],
                   f["level"]) for s in rec["subjects"]
                  for f in s["findings"]}
        self.assertIn(("a.yml", "high"), levels)
        self.assertIn(("b.yml", "high"), levels)

    def test_real_repo_workflows_all_declare_permissions(self):
        res = generators.gen_access_review(REPO_ROOT, self.tmp / "out2")
        rec = res["record"]
        self.assertEqual(schema_errors(rec), [])
        highs = [f for s in rec["subjects"] for f in s["findings"]
                 if f["level"] == "high"]
        self.assertEqual(highs, [])
        self.assertGreaterEqual(
            rec["summary"]["workflows_scanned"], 12)


@unittest.skipUnless(OPA and CONFTEST, "cần opa + conftest")
class ConfigBaselineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gen-cb-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_clean_workload_all_pass(self):
        infra = REPO_ROOT / "examples" / "payments-sample" / "clean"
        res = generators.gen_config_baseline(
            infra / "infra", "test/clean", self.tmp / "out", OPA,
            CONFTEST, REPO_ROOT)
        rec = res["record"]
        self.assertEqual(schema_errors(rec), [])
        statuses = {f["control"]: f["status"] for f in rec["findings"]}
        self.assertEqual(statuses["devsecops.network_exposure"], "pass")
        self.assertEqual(statuses["devsecops.storage_encryption"],
                         "pass")
        self.assertEqual(statuses["devsecops.iam_least_privilege"],
                         "pass")

    def test_planted_workload_network_denied(self):
        infra = REPO_ROOT / "examples" / "payments-sample" / "planted"
        res = generators.gen_config_baseline(
            infra / "infra", "test/planted", self.tmp / "out", OPA,
            CONFTEST, REPO_ROOT)
        statuses = {f["control"]: f["status"]
                    for f in res["record"]["findings"]}
        self.assertEqual(statuses["devsecops.network_exposure"], "deny")


# ---------------------------------------------------------------------------
# Mở rộng collector: supplementary-records + ci-log (bundle_tool M5-A3)
# ---------------------------------------------------------------------------

def build_minimal_run(root: Path) -> Path:
    run_dir = root / "run-x"
    for g in range(1, 11):
        gdir = run_dir / f"gate-{g:02d}-fixture"
        gdir.mkdir(parents=True)
        if g == 10:
            (gdir / "disabled-note.txt").write_text(
                "gate 10 tắt\n", encoding="utf-8")
            continue
        rec = {
            "evidence_type": "policy-decision",
            "policy_id": f"devsecops.fixture_{g}", "engine": "opa",
            "gate": g, "decision": "pass", "violations": [],
            "commit_sha": COMMIT, "timestamp": "2026-10-22T00:00:00Z",
        }
        (gdir / "policy-decision-fixture.json").write_text(
            json.dumps(rec, indent=2), encoding="utf-8")
    return run_dir


def collect(run_dir, out_dir, **kw):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = bundle_tool.collect(run_dir, out_dir, run_dir.name,
                                 kw.pop("allow_incomplete", False), **kw)
    return rc, out.getvalue(), err.getvalue()


def verify(bundle_dir):
    out = io.StringIO()
    with redirect_stdout(out):
        rc = bundle_tool.verify(bundle_dir)
    return rc, out.getvalue()


CHANGE_RECORD_OK = {
    "evidence_type": "change-record", "change_id": "run-x",
    "target_branch": "main", "approvals": ["lead1"],
    "gate_results": {"secret": "pass"}, "evidence_links": ["e://1"],
}


class CollectorExtensionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="collector-ext-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_supplementary_record_collected_and_traced(self):
        run_dir = build_minimal_run(self.tmp)
        supp = run_dir / "supplementary-records"
        supp.mkdir()
        (supp / "change-record.record.json").write_text(
            json.dumps(CHANGE_RECORD_OK), encoding="utf-8")
        bundle = self.tmp / "bundle"
        rc, _, err = collect(run_dir, bundle)
        self.assertEqual(rc, 0, err)
        self.assertTrue((bundle / "records" / "supplementary-records"
                         / "change-record.record.json").is_file())
        summary = json.loads((bundle / "summary.json").read_text(
            encoding="utf-8"))
        self.assertEqual(len(summary["supplementary_records"]), 1)
        row08 = [t for t in summary["traceability"]
                 if t["row"] == "row-08"][0]
        self.assertEqual(row08["status"], "full")
        rc, out = verify(bundle)
        self.assertEqual(rc, 0, out)

    def test_supplementary_bad_record_stops_strict_collect(self):
        run_dir = build_minimal_run(self.tmp)
        supp = run_dir / "supplementary-records"
        supp.mkdir()
        bad = dict(CHANGE_RECORD_OK)
        bad.pop("approvals")
        (supp / "change-record.record.json").write_text(
            json.dumps(bad), encoding="utf-8")
        bundle = self.tmp / "bundle"
        rc, _, err = collect(run_dir, bundle)
        self.assertEqual(rc, 1)
        self.assertIn("change-record.record.json", err)
        self.assertFalse(bundle.exists())

    def test_ci_log_record_emitted_and_cross_checked(self):
        run_dir = build_minimal_run(self.tmp)
        (run_dir / "gate-01-fixture" / "tool.log").write_text(
            "dòng log mẫu của gate 1\n", encoding="utf-8")
        bundle = self.tmp / "bundle"
        rc, _, err = collect(run_dir, bundle)
        self.assertEqual(rc, 0, err)
        ci_rec_path = (bundle / "records" / "collector"
                       / "ci-log.record.json")
        self.assertTrue(ci_rec_path.is_file())
        ci_rec = json.loads(ci_rec_path.read_text(encoding="utf-8"))
        self.assertEqual(schema_errors(ci_rec), [])
        zip_path = bundle / "artifacts" / "ci-logs" / "run-logs.zip"
        self.assertTrue(zip_path.is_file())
        digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
        self.assertEqual(ci_rec["sha256"], f"sha256:{digest}")
        rc, out = verify(bundle)
        self.assertEqual(rc, 0, out)
        self.assertIn("ci-log: hash gói log", out)
        row03 = [t for t in json.loads(
            (bundle / "summary.json").read_text(encoding="utf-8"))
            ["traceability"] if t["row"] == "row-03"][0]
        self.assertEqual(row03["status"], "full")

    def test_ci_log_cross_check_catches_inconsistent_record(self):
        run_dir = build_minimal_run(self.tmp)
        (run_dir / "gate-01-fixture" / "tool.log").write_text(
            "log mẫu\n", encoding="utf-8")
        bundle = self.tmp / "bundle"
        rc, _, err = collect(run_dir, bundle)
        self.assertEqual(rc, 0, err)
        tampered = self.tmp / "bundle-t"
        shutil.copytree(bundle, tampered)
        # Sửa hash khai trong record ci-log RỒI tính lại nhất quán
        # manifest + bundle.sha256 — lớp hash khớp hết, chỉ đối
        # chiếu chéo record <-> artefact mới bắt được.
        relp = "records/collector/ci-log.record.json"
        rec_path = tampered / relp
        data = json.loads(rec_path.read_text(encoding="utf-8"))
        data["sha256"] = "sha256:" + "f" * 64
        rec_path.write_text(json.dumps(data, indent=2),
                            encoding="utf-8")

        def digest(p):
            return hashlib.sha256(p.read_bytes()).hexdigest()

        manifest_path = tampered / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            if entry["path"] == relp:
                entry["sha256"] = digest(rec_path)
                entry["size_bytes"] = rec_path.stat().st_size
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        lines = {}
        for line in (tampered / "bundle.sha256").read_text(
                encoding="utf-8").splitlines():
            d, _, n = line.partition("  ")
            lines[n.strip()] = d.strip()
        lines[relp] = digest(rec_path)
        lines["manifest.json"] = digest(manifest_path)
        (tampered / "bundle.sha256").write_text(
            "".join(f"{lines[k]}  {k}\n" for k in sorted(lines)),
            encoding="utf-8")
        rc, out = verify(tampered)
        self.assertEqual(rc, 1, out)
        self.assertIn("không khớp SHA-256 thật", out)


if __name__ == "__main__":
    unittest.main()
