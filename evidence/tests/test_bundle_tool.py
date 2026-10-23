#!/usr/bin/env python3
"""Unit tests for evidence/bundle_tool.py (M5-A2).

Run from the repo root:

    python3 -m unittest discover -s evidence/tests -v

or directly:

    python3 evidence/tests/test_bundle_tool.py

Fixture is a MINIMAL gate-run directory generated in a temp dir
(gates 1-9 each get exactly one policy-decision record valid against
the repo's real M2 schema; gate 10 only has disabled-note.txt) - it
does not depend on any full gate run. Signature tests use a real
cosign when found (PATH, COSIGN_BINARY, or ~/workspace/tools/cosign
on the dev machine); without cosign that test group skips itself.
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
sys.path.insert(0, str(EVIDENCE_DIR))

import bundle_tool  # noqa: E402

COMMIT_SHA = "0123456789abcdef0123456789abcdef01234567"


def find_cosign_for_tests():
    found = bundle_tool.find_cosign(None)
    if found:
        return found
    candidate = Path.home() / "workspace" / "tools" / "cosign"
    return str(candidate) if candidate.is_file() else None


COSIGN = find_cosign_for_tests()
SIGNING_CONFIG = bundle_tool.DEFAULT_SIGNING_CONFIG


def make_record(gate_no, **overrides):
    rec = {
        "evidence_type": "policy-decision",
        "policy_id": f"devsecops.fixture_{gate_no}",
        "engine": "opa",
        "gate": gate_no,
        "decision": "pass",
        "violations": [],
        "commit_sha": COMMIT_SHA,
        "timestamp": "2026-10-22T00:00:00Z",
    }
    rec.update(overrides)
    return rec


def build_run_dir(root: Path, bad_gate=None) -> Path:
    """Build a minimal run: gates 1-9 one valid record each, gate 10
    disabled. bad_gate: that gate's record drops the required
    'timestamp' field so it fails the schema."""
    run_dir = root / "run-fixture"
    run_dir.mkdir(parents=True)
    for g in range(1, 11):
        gdir = run_dir / f"gate-{g:02d}-fixture"
        gdir.mkdir()
        if g == 10:
            (gdir / "disabled-note.txt").write_text(
                "gate 10 disabled by phase 1 design\n", encoding="utf-8")
            continue
        rec = make_record(g)
        if bad_gate == g:
            rec.pop("timestamp")
        (gdir / "policy-decision-fixture.json").write_text(
            json.dumps(rec, indent=2), encoding="utf-8")
    return run_dir


def run_collect(run_dir, out_dir, **kwargs):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = bundle_tool.collect(run_dir, out_dir, "run-fixture",
                                 kwargs.pop("allow_incomplete", False),
                                 **kwargs)
    return rc, out.getvalue(), err.getvalue()


def run_verify(bundle_dir, **kwargs):
    out = io.StringIO()
    with redirect_stdout(out):
        rc = bundle_tool.verify(bundle_dir, **kwargs)
    return rc, out.getvalue()


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CollectVerifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="bundle-tool-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_collect_minimal_fixture_then_verify_passes(self):
        run_dir = build_run_dir(self.tmp)
        bundle = self.tmp / "bundle"
        rc, _, err = run_collect(run_dir, bundle)
        self.assertEqual(rc, 0, err)
        self.assertTrue((bundle / "manifest.json").is_file())
        self.assertTrue((bundle / "bundle.sha256").is_file())
        rc, out = run_verify(bundle)
        self.assertEqual(rc, 0, out)
        self.assertIn("PASS", out)

    def test_gate10_disabled_is_not_missing_evidence(self):
        run_dir = build_run_dir(self.tmp)
        bundle = self.tmp / "bundle"
        rc, _, err = run_collect(run_dir, bundle)
        self.assertEqual(rc, 0, err)
        summary = json.loads((bundle / "summary.json").read_text(
            encoding="utf-8"))
        self.assertEqual(summary["problems"], [])
        gate10 = [g for g in summary["gates"] if g["gate"] == 10][0]
        self.assertEqual(gate10["status"], "disabled")
        self.assertEqual(summary["gates_disabled"], [10])

    def test_bad_record_strict_mode_stops_and_names_file(self):
        run_dir = build_run_dir(self.tmp, bad_gate=3)
        bundle = self.tmp / "bundle"
        rc, _, err = run_collect(run_dir, bundle)
        self.assertEqual(rc, 1)
        self.assertIn("policy-decision-fixture.json", err)
        self.assertIn("gate-03-fixture", err)
        self.assertFalse(bundle.exists())

    def test_bad_record_allow_incomplete_rejects_with_flag(self):
        run_dir = build_run_dir(self.tmp, bad_gate=3)
        bundle = self.tmp / "bundle"
        rc, _, err = run_collect(run_dir, bundle, allow_incomplete=True)
        self.assertEqual(rc, 0, err)
        rejected = (bundle / "rejected" / "gate-03-fixture"
                    / "policy-decision-fixture.json")
        self.assertTrue(rejected.is_file())
        manifest = json.loads((bundle / "manifest.json").read_text(
            encoding="utf-8"))
        self.assertEqual(manifest["status"], "evidence-incomplete")
        summary = json.loads((bundle / "summary.json").read_text(
            encoding="utf-8"))
        self.assertEqual(len(summary["records_rejected"]), 1)

    def test_verify_fails_after_one_byte_change(self):
        run_dir = build_run_dir(self.tmp)
        bundle = self.tmp / "bundle"
        rc, _, err = run_collect(run_dir, bundle)
        self.assertEqual(rc, 0, err)
        tampered = self.tmp / "bundle-tampered"
        shutil.copytree(bundle, tampered)
        record = (tampered / "records" / "gate-01-fixture"
                  / "policy-decision-fixture.json")
        data = bytearray(record.read_bytes())
        idx = data.index(b"2026")  # change 1 byte in the timestamp
        data[idx] = ord("9")
        record.write_bytes(bytes(data))
        rc, out = run_verify(tampered)
        self.assertEqual(rc, 1, out)
        self.assertIn("hash mismatch", out)


@unittest.skipUnless(COSIGN and SIGNING_CONFIG.is_file(),
                     "cosign or the offline signing-config "
                     "not found for signature tests")
class SignatureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="bundle-sign-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.run_dir = build_run_dir(self.tmp)

    def collect_signed(self, name):
        bundle = self.tmp / name
        rc, _, err = run_collect(
            self.run_dir, bundle, sign=True, cosign=COSIGN,
            signing_config=str(SIGNING_CONFIG))
        self.assertEqual(rc, 0, err)
        return bundle

    def test_signed_bundle_verifies_hash_and_signature(self):
        bundle = self.collect_signed("bundle-signed")
        self.assertTrue((bundle / "bundle.sigstore.json").is_file())
        self.assertTrue((bundle / "cosign.pub").is_file())
        manifest = json.loads((bundle / "manifest.json").read_text(
            encoding="utf-8"))
        self.assertIn("signature", manifest)
        self.assertEqual(
            manifest["signature"]["public_key_sha256"],
            sha256_of(bundle / "cosign.pub"))
        # The private key must never appear in a bundle.
        self.assertEqual(list(bundle.rglob("*.key")), [])
        rc, out = run_verify(bundle, cosign=COSIGN)
        self.assertEqual(rc, 0, out)
        self.assertIn("Cosign signature on bundle.sha256: VALID", out)

    def test_signed_bundle_consistent_tamper_fails_signature(self):
        bundle = self.collect_signed("bundle-signed")
        tampered = self.tmp / "bundle-tampered"
        shutil.copytree(bundle, tampered)
        # Edit the record THEN recompute hashes consistently in the
        # manifest + bundle.sha256 - the hash layer will match fully;
        # only the signature on the original bundle.sha256 catches it.
        record_rel = ("records/gate-01-fixture/"
                      "policy-decision-fixture.json")
        record = tampered / record_rel
        data = json.loads(record.read_text(encoding="utf-8"))
        data["policy_id"] = "devsecops.fixture_1_TAMPERED"
        record.write_text(json.dumps(data, indent=2), encoding="utf-8")
        manifest_path = tampered / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            if entry["path"] == record_rel:
                entry["sha256"] = sha256_of(record)
                entry["size_bytes"] = record.stat().st_size
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        lines = {}
        for line in (tampered / "bundle.sha256").read_text(
                encoding="utf-8").splitlines():
            digest, _, name = line.partition("  ")
            lines[name.strip()] = digest.strip()
        lines[record_rel] = sha256_of(record)
        lines["manifest.json"] = sha256_of(manifest_path)
        (tampered / "bundle.sha256").write_text(
            "".join(f"{lines[k]}  {k}\n" for k in sorted(lines)),
            encoding="utf-8")
        rc, out = run_verify(tampered, cosign=COSIGN)
        self.assertEqual(rc, 1, out)
        self.assertIn("Cosign signature INVALID", out)

    def test_swapped_signature_from_other_bundle_fails(self):
        bundle_a = self.collect_signed("bundle-a")
        bundle_b = self.collect_signed("bundle-b")
        shutil.copy2(bundle_b / "bundle.sigstore.json",
                     bundle_a / "bundle.sigstore.json")
        rc, out = run_verify(bundle_a, cosign=COSIGN)
        self.assertEqual(rc, 1, out)
        self.assertIn("Cosign signature INVALID", out)


if __name__ == "__main__":
    unittest.main()
