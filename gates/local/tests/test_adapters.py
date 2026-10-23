#!/usr/bin/env python3
"""Unit tests for the gate adapters (gates/local/adapters).

Run from the repo root:

    python3 -m unittest discover -s gates/local/tests -v

Three coverage tiers:
  1. Pure module functions (direct import): osv_normalize,
     syft_license_input, tf_parse_input, kev_epss_enrich.
  2. CLI via subprocess with minimal hand-written JSON/YAML fixtures:
     gitleaks_input, image_block_check, workflow_input,
     kev_epss_enrich, opa_decide (requires the opa binary in ~/workspace/tools).
  3. The real gate 6 chain (provenance_build: Syft + Cosign over a minimal
     workload directory) — skipped automatically when the binaries are missing.
"""

import gzip
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ADAPTERS = REPO_ROOT / "gates" / "local" / "adapters"
sys.path.insert(0, str(ADAPTERS))

import kev_epss_enrich  # noqa: E402
import osv_normalize  # noqa: E402
import syft_license_input  # noqa: E402
import tf_parse_input  # noqa: E402

TOOLS = Path.home() / "workspace" / "tools"
OPA = TOOLS / "opa"
SYFT = TOOLS / "syft"
COSIGN = TOOLS / "cosign"
COMMIT = "0123456789abcdef0123456789abcdef01234567"
NOW = "2026-10-22T00:00:00Z"


def run_cli(script: str, args: list, expect=0):
    proc = subprocess.run([sys.executable, str(ADAPTERS / script),
                           *args], capture_output=True, text=True,
                          timeout=600)
    if expect is not None:
        assert proc.returncode == expect, (
            f"{script} rc={proc.returncode}\nstdout: {proc.stdout}"
            f"\nstderr: {proc.stderr}")
    return proc


class OsvNormalizeTests(unittest.TestCase):
    def test_range_string(self):
        vuln = {"affected": [{"ranges": [
            {"type": "ECOSYSTEM", "events": [
                {"introduced": "0.8.3"}, {"fixed": "1.0.1"}]}]}]}
        self.assertEqual(osv_normalize.range_string(vuln),
                         (">=0.8.3,<1.0.1", "1.0.1"))
        self.assertEqual(osv_normalize.range_string({"affected": []}),
                         (">=0", None))
        git_only = {"affected": [{"ranges": [
            {"type": "GIT", "events": [{"introduced": "abc"}]}]}]}
        self.assertEqual(osv_normalize.range_string(git_only),
                         (">=0", None))

    def test_cli_dedupes_and_prefers_fixed(self):
        with tempfile.TemporaryDirectory() as td:
            inp = Path(td) / "osv.json"
            out = Path(td) / "out.json"
            doc = {"results": [
                {"source": {"path": "backend/requirements.txt"},
                 "packages": [{"package": {"name": "starlette",
                                            "version": "1.0.0",
                                            "ecosystem": "PyPI"},
                               "vulnerabilities": [
                                   {"id": "GHSA-86qp-5c8j-p5mr",
                                    "aliases": ["CVE-2026-48710"],
                                    "summary": "BadHost",
                                    "affected": [{"ranges": [
                                        {"type": "ECOSYSTEM",
                                         "events": [
                                             {"introduced": "0.8.3"}]}]}]},
                                   {"id": "CVE-2026-48710",
                                    "summary": "BadHost",
                                    "affected": [{"ranges": [
                                        {"type": "ECOSYSTEM",
                                         "events": [
                                             {"introduced": "0.8.3"},
                                             {"fixed": "1.0.1"}]}]}]},
                               ]}]},
            ]}
            inp.write_text(json.dumps(doc), encoding="utf-8")
            run_cli("osv_normalize.py", ["--osv-json", str(inp),
                                         "--out", str(out)])
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(len(data["dependencies"]), 1)
            vulns = data["vulnerabilities"]
            self.assertEqual(len(vulns), 1)
            self.assertEqual(vulns[0]["id"], "CVE-2026-48710")
            self.assertEqual(vulns[0]["osv_id"], "CVE-2026-48710")
            self.assertEqual(vulns[0]["fixed"], "1.0.1")
            self.assertEqual(vulns[0]["affected"], ">=0.8.3,<1.0.1")


class SyftLicenseTests(unittest.TestCase):
    def test_component_licenses(self):
        self.assertEqual(syft_license_input.component_licenses(
            {"licenses": [{"license": {"id": "MIT"}}]}), ["MIT"])
        self.assertEqual(syft_license_input.component_licenses(
            {"licenses": [{"expression": "Apache-2.0 OR GPL-2.0"}]}),
            ["Apache-2.0", "GPL-2.0"])
        self.assertEqual(syft_license_input.component_licenses(
            {"licenses": [{"license": {"name": "Custom"}}]}),
            ["Custom"])
        self.assertEqual(syft_license_input.component_licenses({}),
                         ["NOASSERTION"])

    def test_cli_flattens_components(self):
        with tempfile.TemporaryDirectory() as td:
            sbom = Path(td) / "sbom.json"
            out = Path(td) / "out.json"
            sbom.write_text(json.dumps({"components": [
                {"name": "x", "version": "1",
                 "licenses": [{"license": {"id": "MIT"}}]},
                {"name": "y", "version": "2",
                 "licenses": [{"expression": "Apache-2.0 OR GPL-2.0"}]},
            ]}), encoding="utf-8")
            run_cli("syft_license_input.py",
                    ["--sbom", str(sbom), "--out", str(out)])
            data = json.loads(out.read_text(encoding="utf-8"))
            pairs = {(c["name"], c["license"])
                     for c in data["components"]}
            self.assertEqual(pairs, {("x", "MIT"),
                                     ("y", "Apache-2.0"),
                                     ("y", "GPL-2.0")})
            self.assertIn("GPL-3.0-only",
                          data["config"]["denied_licenses"])


class KevEpssTests(unittest.TestCase):
    KEV_JSON = {"catalogVersion": "2026.10.21", "vulnerabilities": [
        {"cveID": "CVE-2026-48710"}, {"cveID": "CVE-1999-0001"}]}
    EPSS_LINES = ["#model_version:v2025.03.14,score_date:2026-10-22",
                  "cve,epss,percentile",
                  "CVE-2026-48710,0.90000,0.99",
                  "CVE-2020-9999,0.50000,0.80",
                  "CVE-2020-1111,0.00100,0.01"]

    def _feeds(self, td: Path):
        kev = td / "kev.json"
        kev.write_text(json.dumps(self.KEV_JSON), encoding="utf-8")
        epss = td / "epss.csv.gz"
        with gzip.open(epss, "wt", encoding="utf-8") as f:
            f.write("\n".join(self.EPSS_LINES) + "\n")
        return kev, epss

    def test_loaders(self):
        with tempfile.TemporaryDirectory() as td:
            kev, epss = self._feeds(Path(td))
            ids, version = kev_epss_enrich.load_kev(kev)
            self.assertEqual(ids, {"CVE-2026-48710", "CVE-1999-0001"})
            self.assertEqual(version, "2026.10.21")
            scores, model = kev_epss_enrich.load_epss(epss)
            self.assertEqual(model, "v2025.03.14")
            self.assertAlmostEqual(scores["CVE-2020-9999"], 0.5)

    def test_cli_kev_blocks_epss_threshold_blocks_else_issue(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            kev, epss = self._feeds(td)
            norm = td / "normalized.json"
            norm.write_text(json.dumps({
                "dependencies": [{"name": "starlette",
                                  "version": "1.0.0",
                                  "ecosystem": "PyPI"}],
                "vulnerabilities": [
                    {"id": "CVE-2026-48710", "package": "starlette",
                     "version": "1.0.0", "affected": ">=0.8.3,<1.0.1",
                     "fixed": "1.0.1"},
                    {"id": "CVE-2020-9999", "package": "pkg",
                     "version": "1", "affected": ">=0", "fixed": None},
                    {"id": "CVE-2020-1111", "package": "pkg2",
                     "version": "1", "affected": ">=0", "fixed": None},
                ]}), encoding="utf-8")
            out_in = td / "input.json"
            out_rank = td / "ranking.json"
            run_cli("kev_epss_enrich.py", [
                "--normalized", str(norm), "--kev", str(kev),
                "--epss", str(epss), "--threshold", "0.3",
                "--out-input", str(out_in), "--out-ranking",
                str(out_rank)])
            doc = json.loads(out_in.read_text(encoding="utf-8"))
            by_id = {v["id"]: v for v in doc["vulnerabilities"]}
            self.assertTrue(by_id["CVE-2026-48710"]["in_kev"])
            self.assertAlmostEqual(
                by_id["CVE-2026-48710"]["epss"], 0.9)
            ranking = json.loads(out_rank.read_text(encoding="utf-8"))
            self.assertEqual(ranking["evidence_type"],
                             "vuln-risk-ranking")
            entries = {e["cve"]: e for e in ranking["entries"]}
            today = date.today().isoformat()
            plus30 = (date.today() + timedelta(days=30)).isoformat()
            self.assertEqual(entries["CVE-2026-48710"]["decision"],
                             "block")
            self.assertEqual(entries["CVE-2026-48710"]["due"], today)
            self.assertEqual(entries["CVE-2020-9999"]["decision"],
                             "block")
            self.assertEqual(entries["CVE-2020-1111"]["decision"],
                             "issue")
            self.assertEqual(entries["CVE-2020-1111"]["due"], plus30)


class ImageBlockCheckTests(unittest.TestCase):
    def test_only_critical_fixed_and_kev_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            trivy = td / "trivy.json"
            kev = td / "kev.json"
            out_v = td / "vulns.json"
            out_s = td / "summary.json"
            trivy.write_text(json.dumps({"Results": [
                {"Vulnerabilities": [
                    {"VulnerabilityID": "CVE-1", "Severity": "CRITICAL",
                     "PkgName": "openssl", "InstalledVersion": "1.0",
                     "FixedVersion": "2.0"},
                    {"VulnerabilityID": "CVE-2", "Severity": "CRITICAL",
                     "PkgName": "zlib", "InstalledVersion": "1.0",
                     "FixedVersion": ""},
                    {"VulnerabilityID": "CVE-3", "Severity": "HIGH",
                     "PkgName": "curl", "InstalledVersion": "1.0",
                     "FixedVersion": "2.0"},
                ]}]}), encoding="utf-8")
            kev.write_text(json.dumps({"vulnerabilities": [
                {"cveID": "CVE-1"}, {"cveID": "CVE-3"}]}),
                encoding="utf-8")
            run_cli("image_block_check.py", [
                "--trivy-json", str(trivy), "--kev", str(kev),
                "--out-vulns", str(out_v), "--out-summary", str(out_s)])
            summary = json.loads(out_s.read_text(encoding="utf-8"))
            self.assertEqual(summary["total"], 3)
            self.assertEqual(summary["counts_by_severity"],
                             {"CRITICAL": 2, "HIGH": 1})
            blocking = summary["blocking_critical_fixed_kev"]
            self.assertEqual([b["id"] for b in blocking], ["CVE-1"])
            vulns = json.loads(out_v.read_text(encoding="utf-8"))
            self.assertEqual(len(vulns), 3)


class GitleaksInputTests(unittest.TestCase):
    def test_cli_builds_secret_input_with_truncated_preview(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            workload = td / "workload"
            workload.mkdir()
            target = workload / "a.py"
            target.write_text("x = 1\n", encoding="utf-8")
            gl = td / "gitleaks.json"
            out = td / "out.json"
            secret = "FAKEVALUE-SHOULD-NOT-LEAK-0001"
            gl.write_text(json.dumps([
                {"RuleID": "generic-api-key", "File": str(target),
                 "StartLine": 3, "Match": secret},
            ]), encoding="utf-8")
            run_cli("gitleaks_input.py", [
                "--gitleaks-json", str(gl), "--workload", str(workload),
                "--scan-date", "2026-10-22", "--out", str(out)])
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["scan_date"], "2026-10-22")
            self.assertEqual(len(data["findings"]), 1)
            f0 = data["findings"][0]
            self.assertEqual(f0["file"], "a.py")
            self.assertEqual(f0["line"], 3)
            self.assertEqual(f0["match_preview"], secret[:12] + "...")
            self.assertNotIn(secret, json.dumps(data))


class TfParsePureTests(unittest.TestCase):
    def test_bodies_var_defaults_resolve(self):
        parsed = {"resource": {"aws_security_group": {
            "app": [{"description": "x"}]}}}
        self.assertEqual(
            tf_parse_input.bodies(parsed, "aws_security_group"),
            {"app": {"description": "x"}})
        self.assertEqual(
            tf_parse_input.bodies(parsed, "aws_s3_bucket"), {})
        defaults = tf_parse_input.var_defaults({"variable": {
            "web_port": [{"default": 8080}],
            "name": [{"default": "app"}],
            "nodefault": [{}]}})
        self.assertEqual(defaults, {"web_port": 8080, "name": "app"})
        self.assertEqual(
            tf_parse_input.resolve("${var.web_port}", defaults), 8080)
        self.assertEqual(
            tf_parse_input.resolve("${aws_security_group.app.id}", {}),
            "aws_security_group.app.id")
        self.assertEqual(tf_parse_input.resolve("literal", {}),
                         "literal")
        self.assertEqual(
            tf_parse_input.resolve(["${var.name}", 3], defaults),
            ["app", 3])


class WorkflowInputTests(unittest.TestCase):
    def test_cli_reports_workflows_and_gates_enabled(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "all-gates.yml").write_text(
                "name: all\n"
                "permissions:\n  contents: read\n"
                "jobs:\n"
                "  gate-01-secret:\n"
                "    uses: ./.github/workflows/gate-01-secret.yml\n",
                encoding="utf-8")
            (td / "plain.yml").write_text(
                "name: plain\n"
                "jobs:\n"
                "  build:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps: []\n", encoding="utf-8")
            out = td / "out.json"
            run_cli("workflow_input.py", ["--workflows-dir", str(td),
                                          "--out", str(out)])
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["config"]["required_gates"],
                             ["secret", "sast", "sca", "iac", "kev"])
            by_file = {w["file"]: w for w in data["workflows"]}
            allg = by_file[".github/workflows/all-gates.yml"]
            self.assertEqual(allg["permissions"],
                             {"contents": "read"})
            self.assertIn("secret", allg["gates_enabled"])
            plain = by_file[".github/workflows/plain.yml"]
            self.assertIsNone(plain["permissions"])
            self.assertEqual(plain["jobs"][0]["name"], "build")
            self.assertFalse(plain["jobs"][0]["oidc"])


@unittest.skipUnless(OPA.is_file(), "opa not found")
class OpaDecideTests(unittest.TestCase):
    def _run(self, td, fixture, package, gate, policy_id=None):
        pid = policy_id or f"devsecops.{package}"
        out_dir = Path(td) / "gate-out"
        out_dir.mkdir()
        proc = run_cli("opa_decide.py", [
            "--opa", str(OPA),
            "--bundle", str(REPO_ROOT / "policies" / "rego"),
            "--package", package, "--input", fixture,
            "--policy-id", pid,
            "--gate", str(gate), "--out", str(out_dir),
            "--commit-sha", COMMIT, "--timestamp", NOW], expect=None)
        rec_path = out_dir / (
            "policy-decision-" + pid.replace("devsecops.", "") + ".json")
        rec = json.loads(rec_path.read_text(encoding="utf-8")) \
            if rec_path.is_file() else None
        return proc, rec

    def test_pass_case_writes_pass_record(self):
        with tempfile.TemporaryDirectory() as td:
            fixture = str(REPO_ROOT / "policies" / "fixtures"
                          / "secret_findings.pass.json")
            proc, rec = self._run(td, fixture, "secret_findings", 1)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(rec["decision"], "pass")
            self.assertEqual(rec["evidence_type"], "policy-decision")
            self.assertTrue(
                rec["inputs_digest"].startswith("sha256:"))

    def test_deny_case_exits_1(self):
        with tempfile.TemporaryDirectory() as td:
            fixture = str(REPO_ROOT / "policies" / "fixtures"
                          / "change_record.fail.json")
            proc, rec = self._run(td, fixture, "change_record", 2)
            self.assertEqual(proc.returncode, 1, proc.stderr)
            self.assertEqual(rec["decision"], "deny")
            self.assertGreater(len(rec["violations"]), 0)


@unittest.skipUnless(SYFT.is_file() and COSIGN.is_file(),
                     "requires syft + cosign in ~/workspace/tools")
class ProvenanceBuildTests(unittest.TestCase):
    def test_full_chain_on_tiny_workload(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            workload = td / "workload"
            workload.mkdir()
            (workload / "hello.txt").write_text("hello\n",
                                                encoding="utf-8")
            out = td / "out"
            run_cli("provenance_build.py", [
                "--syft", str(SYFT), "--cosign", str(COSIGN),
                "--workload", str(workload), "--variant", "test",
                "--out", str(out), "--commit-sha", COMMIT,
                "--signing-config", str(
                    REPO_ROOT / "gates" / "local"
                    / "signing-config-offline.json")])
            sbom_rec = json.loads(
                (out / "sbom.record.json").read_text(encoding="utf-8"))
            att_rec = json.loads(
                (out / "provenance-attestation.record.json").read_text(
                    encoding="utf-8"))
            self.assertEqual(sbom_rec["evidence_type"], "sbom")
            self.assertTrue(sbom_rec["signed"])
            self.assertEqual(att_rec["slsa_level"], 1)
            self.assertTrue(att_rec["signature_verified"])
            self.assertEqual(sbom_rec["artifact_digest"],
                             att_rec["artifact_digest"])


if __name__ == "__main__":
    unittest.main()
