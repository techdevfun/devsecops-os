#!/usr/bin/env python3
"""devsecops-os — evidence bundle tool (M4: evidence automation).

One tool, two jobs:

  collect   Collect every evidence record from one gate run
            (directory `evidence/output/<run>/` per the M3
            contract), check each record against the evidence
            schemas of policy pack v1 (M2), generate a summary
            report + a framework -> policy -> gate -> evidence
            traceability table, and package it all into an evidence
            bundle with a SHA-256 manifest. Optional `--sign`:
            cryptographically sign `bundle.sha256` with Cosign
            (per-run ephemeral key, generated outside the tree and
            destroyed right after signing - see the signing section
            of evidence/README.md).

  verify    Independently verify a packaged bundle with ONE
            command: check every hash in the manifest +
            `bundle.sha256` (compatible with `sha256sum -c`),
            re-check every record in the bundle against its schema,
            and - when the bundle declares a signature - also verify
            the Cosign signature on `bundle.sha256` (a missing/bad
            signature is a loud FAIL).

Since M5-A3 the collector also: (a) scans the run's
`supplementary-records/` directory - where the decision/periodic
evidence generators (evidence/generators.py) write change-record,
drift-report, access-review-report and config-baseline-report plus
their policy-decisions - and schema-checks them like any other
record; (b) issues a `ci-log` record itself: packages all of the
run's log files (.log) into a zip artefact with a SHA-256, so
phase-1 map rows A.8.15-A.8.16 have real evidence instead of "none".

Python 3 standard library only - runs on a bare CI runner with no
extra packages. Principle inherited from the blueprint: anything
missing/wrong must FAIL LOUDLY (a record failing its schema is
named, a gate lacking evidence is flagged), never silently passed.

Usage:
  python3 evidence/bundle_tool.py collect evidence/output/local-clean
  python3 evidence/bundle_tool.py collect <run-dir> --out-dir <dir> \
      --run-id <id> [--allow-incomplete]
  python3 evidence/verify_bundle.py <bundle-dir>     # == the verify command

The default mode is STRICT: if any record fails its schema, or any
gate is missing a directory or evidence, collect STOPS and produces
no bundle. `--allow-incomplete` (used in CI, collect-only mode):
still produces a bundle, bad records are split into `rejected/`
with reasons, and the bundle is flagged `evidence-incomplete` in
the manifest + report.
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
TOOL_VERSION = "1.3.0"
BUNDLE_FORMAT = "devsecops-os/evidence-bundle/1"

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_SCHEMAS_DIR = REPO_ROOT / "policies" / "evidence-schemas"
MAPPING_FILE = SCRIPT_DIR / "mapping.phase1.json"
DEFAULT_BUNDLES_DIR = SCRIPT_DIR / "bundles"

GATE_DIR_RE = re.compile(r"^gate-(\d{2})-")
EXPECTED_GATES = list(range(1, 11))  # blueprint section 5: gates 1..10

# Supplementary record source directory within a run: the
# decision/periodic evidence generators (evidence/generators.py)
# write records here; the collector scans and schema-checks them
# like gate records.
SUPPLEMENTARY_DIR_NAME = "supplementary-records"
SUPPLEMENTARY_LABEL = "supplementary"

# Evidence types issued by the collector itself (not from a gate):
# the control index for CPS 234 and the CI log package for ISO
# A.8.15-16.
COLLECTOR_TYPES = ("control-evidence-index", "ci-log")
CI_LOG_BUNDLE_PATH = "records/collector/ci-log.record.json"
CI_LOG_ARTIFACT_PATH = "artifacts/ci-logs/run-logs.zip"

# Never put a private key in a bundle - even if it sits right in a
# gate's output directory (gate 6 generates a temporary cosign.key
# on local runs).
PRIVATE_KEY_SUFFIXES = (".key", ".pem")

# Bundle signing (M5-A2): the Cosign signature is over `bundle.sha256`
# itself - the file that covers every other file including
# manifest.json. The two signature files therefore INTENTIONALLY
# stand outside the manifest and outside bundle.sha256 (they
# authenticate bundle.sha256; they cannot be inside it).
SIG_BUNDLE_NAME = "bundle.sigstore.json"
SIG_PUBKEY_NAME = "cosign.pub"
SIGNATURE_FILES = (SIG_BUNDLE_NAME, SIG_PUBKEY_NAME)
DEFAULT_SIGNING_CONFIG = (REPO_ROOT / "gates" / "local"
                          / "signing-config-offline.json")


# ---------------------------------------------------------------------------
# Shared utilities
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
# Cryptographic bundle signing (M5-A2) - Cosign sign-blob over
# bundle.sha256. Same pattern as gate 6: a TEMPORARY per-run local
# key, offline signing-config (no Rekor), verify with
# --insecure-ignore-tlog. Mandatory difference from gate 6: the key
# is generated in a temp directory OUTSIDE the tree and destroyed
# right after signing - the private key never enters the bundle and
# never remains in the tree (M5-A risk-scan lesson). Honest limits
# of local signatures vs keyless OIDC on CI: see the README.
# ---------------------------------------------------------------------------

def find_cosign(explicit=None):
    """Find cosign: --cosign > COSIGN_BINARY env var > PATH. An explicit
    value that does not exist is a configuration error, never
    silently skipped (returns None so the caller FAILS loudly)."""
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
        raise RuntimeError(f"cosign {what} failed: {detail[:400]}")
    return proc


def generate_signing_keypair(cosign, workdir: Path) -> Path:
    """Generate a temporary key pair in workdir; return the cosign.pub path."""
    _run_cosign([cosign, "generate-key-pair"], workdir,
                "generate-key-pair")
    pub_path = workdir / "cosign.pub"
    if not pub_path.is_file():
        raise RuntimeError(
            "cosign generate-key-pair did not produce cosign.pub")
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
    """Raise RuntimeError when the signature is invalid."""
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
# Minimal JSON Schema checker (the subset the M2 schemas actually
# use: type / const / enum / required / properties / items /
# additionalProperties). The M2 schemas only use
# type/const/required/properties, but verify must catch exactly
# those errors independently - no `jsonschema` package on the runner.
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
    """Return the list of errors (empty = valid)."""
    errors = []
    if not isinstance(schema, dict):
        return errors
    if "const" in schema and instance != schema["const"]:
        errors.append(
            f"{path}: must equal the constant {schema['const']!r}, "
            f"actual {instance!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} is not in the enum "
                      f"{schema['enum']!r}")
    expected_type = schema.get("type")
    if expected_type is not None:
        types = expected_type if isinstance(expected_type, list) \
            else [expected_type]
        if not any(_TYPE_CHECKS.get(t, lambda v: True)(instance)
                   for t in types):
            errors.append(
                f"{path}: wrong type - expected {'/'.join(types)}, "
                f"actual {type(instance).__name__}")
            return errors  # wrong root type: do not dig deeper
    if isinstance(instance, dict):
        for field in schema.get("required", []):
            if field not in instance:
                errors.append(f"{path}: missing required field {field!r}")
        props = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in props:
                errors.extend(validate(value, props[key], f"{path}.{key}"))
            elif additional is False:
                errors.append(f"{path}: field {key!r} is not in the schema")
            elif isinstance(additional, dict):
                errors.extend(validate(value, additional, f"{path}.{key}"))
    if isinstance(instance, list) and isinstance(schema.get("items"), dict):
        for i, item in enumerate(instance):
            errors.extend(validate(item, schema["items"], f"{path}[{i}]"))
    return errors


def load_schemas(schemas_dir: Path):
    """Map evidence_type -> schema, by file name `<type>.schema.json`."""
    schemas = {}
    for f in sorted(schemas_dir.glob("*.schema.json")):
        evidence_type = f.name[: -len(".schema.json")]
        schemas[evidence_type] = load_json(f)
    return schemas


def build_ci_log_archive(run_dir: Path, log_files):
    """Package the run's log files into a DETERMINISTIC zip: fixed name
    order, fixed zip timestamp (1980-01-01) - the same log set always
    yields the same SHA-256, so the ci-log record carries a stable
    hash that verify can check against. Returns (zip_bytes,
    sha256_hex)."""
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
    """Shorten a local-style absolute URI for readability in reports;
    the original value remains untouched in the bundle's
    records/SARIF."""
    marker = "/examples/"
    if marker in uri:
        return "examples/" + uri.split(marker, 1)[1]
    return uri


def extract_secret_findings(run_dir: Path, gate_dirs):
    """Secret findings taken from the SARIF artefact that gate 1's
    record points to - real data from the run, no inference."""
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
    """Vulnerability summary from the vuln-risk-ranking record (gate 8)
    - the source of the run's block/issue decisions."""
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
        print(f"ERROR: run directory does not exist: {run_dir}",
              file=sys.stderr)
        return 2
    # Preconditions for --sign: fail early and loudly, before packaging.
    cosign_bin = None
    if sign:
        cosign_bin = find_cosign(cosign)
        if not cosign_bin:
            print("ERROR: --sign requires cosign but it was not found "
                  "(pass --cosign <path> or set the COSIGN_BINARY "
                  "environment variable)", file=sys.stderr)
            return 2
        if signing_config:
            if not Path(signing_config).is_file():
                print(f"ERROR: signing-config does not exist: "
                      f"{signing_config}", file=sys.stderr)
                return 2
        elif DEFAULT_SIGNING_CONFIG.is_file():
            signing_config = str(DEFAULT_SIGNING_CONFIG)
        else:
            print("ERROR: --sign needs an offline signing-config (not "
                  f"found: {DEFAULT_SIGNING_CONFIG}; pass "
                  "--signing-config <path>) - refusing to sign with "
                  "a default config that could push to public Rekor",
                  file=sys.stderr)
            return 2
    run_id = run_id or run_dir.name
    schemas = load_schemas(DEFAULT_SCHEMAS_DIR)
    if not schemas:
        print(f"ERROR: no M2 schemas found at {DEFAULT_SCHEMAS_DIR}",
              file=sys.stderr)
        return 2
    mapping = load_json(MAPPING_FILE)

    gate_dirs = discover_gate_dirs(run_dir)
    records = []        # valid records
    rejected = []       # records failing schema / unreadable - named
    problems = []       # problems that make the bundle incomplete
    artifacts = []      # auxiliary files included in the bundle
    excluded = []       # files NOT included in the bundle, with reasons
    commit_shas = set()

    def rel(p: Path) -> str:
        return p.relative_to(run_dir).as_posix()

    # --- Scan each gate -----------------------------------------------------
    gate_status = {}
    for gate_no in EXPECTED_GATES:
        gdir = gate_dirs.get(gate_no)
        label = f"gate-{gate_no:02d}"
        if gdir is None:
            gate_status[gate_no] = {
                "gate": gate_no, "status": "absent", "records": [],
                "decisions": [], "note": "gate directory not present "
                                         "in this run"}
            problems.append(f"{label}: gate directory missing from the run")
            continue
        gate_records, gate_decisions = [], []
        disabled_note = None
        has_scan_error = (gdir / "scan-error.json").exists()
        # Artefact URIs this gate's records point to (to gather artefacts)
        referenced = set()
        pending_json = []     # JSON without evidence_type - decided later
        pending_other = []    # non-JSON files - decided later
        for f in sorted(gdir.iterdir()):
            if f.is_dir():
                n_files = sum(1 for _ in f.rglob("*") if _.is_file())
                excluded.append({
                    "path": rel(f) + "/", "category": "gate subdirectory",
                    "reason": f"{n_files} file(s) in a subdirectory (e.g. a "
                              f"tool sandbox) - not record-form evidence, "
                              f"not included in the bundle"})
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
                    "path": rel(f), "category": "private key",
                    "reason": "private key material - NEVER included in "
                              "an evidence bundle"})
                continue
            if not name.endswith(".json"):
                pending_other.append(f)
                continue
            # JSON file: a record candidate?
            try:
                data = load_json(f)
            except Exception as exc:
                if name.endswith(".record.json") or \
                        name.startswith("policy-decision-"):
                    rejected.append({
                        "source": rel(f), "gate": gate_no,
                        "errors": [f"could not read JSON: {exc}"]})
                else:
                    excluded.append({
                        "path": rel(f),
                        "category": "raw tool output",
                        "reason": f"JSON unreadable ({exc}) and not a "
                                  f"record file"})
                continue
            if isinstance(data, dict) and "evidence_type" in data:
                etype = data.get("evidence_type")
                if etype not in schemas:
                    rejected.append({
                        "source": rel(f), "gate": gate_no,
                        "errors": [f"evidence_type {etype!r} has no "
                                   f"schema in the M2 pack"]})
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
                    "errors": ["file is named like a record but has no "
                               "evidence_type field - does not match the "
                               "M2 contract"]})
                continue
            pending_json.append(f)
        # Pass 2: only once `referenced` is complete, decide the
        # auxiliary files - an artefact is a file referenced by a
        # record, a policy input, or an SBOM/provenance document
        # accompanying a record.
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
                    "category": "raw tool output",
                    "reason": "JSON has no evidence_type and is not "
                              "referenced by any record"})
        for f in pending_other:
            run_rel = rel(f)
            if run_rel in referenced or f.name.endswith(".sarif") \
                    or f.name == "cosign.pub":
                artifacts.append({"source": f, "path": run_rel,
                                  "gate": gate_no, "kind": "artifact"})
            else:
                excluded.append({
                    "path": run_rel,
                    "category": "log/raw tool output",
                    "reason": "not a schema record and not referenced "
                              "by any record"})
        # Gate status
        if disabled_note is not None and not gate_records:
            status = "disabled"
            note = disabled_note.strip().splitlines()[0] \
                if disabled_note.strip() else ""
        elif any(d["decision"] == "deny" for d in gate_decisions):
            status, note = "deny", ""
        elif has_scan_error:
            status = "scan-error"
            note = "gate has scan-error.json - the scan did not complete"
            problems.append(f"{label}: scan-error (scan did not complete)")
        elif gate_decisions:
            status, note = "pass", ""
        elif gate_records:
            status = "evidence-only"
            note = "has evidence records but this gate produces no " \
                   "policy-decision (the blocking decision lives at " \
                   "another gate)"
        else:
            status = "no-evidence"
            note = "gate produced no evidence records"
            problems.append(f"{label}: no evidence records")
        gate_status[gate_no] = {
            "gate": gate_no, "status": status,
            "records": [r["bundle_path"] for r in gate_records],
            "decisions": gate_decisions, "note": note}

    # --- Supplementary record source: supplementary-records/ ---------
    # The decision/periodic evidence generators
    # (evidence/generators.py) write records here because they belong
    # to no CI gate. Schema-check exactly like gate records; a JSON
    # file without evidence_type in this directory is a policy input
    # (provenance) -> artefact.
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
                    "category": "raw evidence-generator output",
                    "reason": "non-JSON file in "
                              "supplementary-records/"})
                continue
            try:
                data = load_json(f)
            except Exception as exc:
                rejected.append({
                    "source": run_rel, "gate": SUPPLEMENTARY_LABEL,
                    "errors": [f"could not read JSON: {exc}"]})
                continue
            if isinstance(data, dict) and "evidence_type" in data:
                etype = data.get("evidence_type")
                if etype not in schemas:
                    rejected.append({
                        "source": run_rel, "gate": SUPPLEMENTARY_LABEL,
                        "errors": [f"evidence_type {etype!r} has no "
                                   f"schema in the M2 pack"]})
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

    # --- ci-log plan (record issued by the collector) ----------------
    # Gather every log file of the run (gate logs in the gate-*
    # directories) into one deterministic zip artefact with a hash -
    # evidence for ISO rows A.8.15-A.8.16. No logs, no fabricated
    # record.
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
                "sources_note": "repo-audit-log does not exist in a "
                                "local run (the tree is not yet a git "
                                "repo, there is no GitHub repo yet) - "
                                "the only source is the gates' logs "
                                "from the run",
                "log_files": [p.relative_to(run_dir).as_posix()
                              for p in log_files],
                "log_file_count": len(log_files),
                "archive_format": "deterministic zip: file names "
                                  "sorted, fixed timestamp - the same "
                                  "log set yields the same hash",
                "generated_by": f"{TOOL_NAME} {TOOL_VERSION} "
                                f"(M4 collector, issued at M5-A3)",
                "run_id": run_id,
            },
        }

    # Non-gate-* directories at the run root (e.g. the .feeds cache)
    for child in sorted(run_dir.iterdir()):
        if child.name == SUPPLEMENTARY_DIR_NAME:
            continue  # already scanned above as a supplementary record source
        if child.is_dir() and not GATE_DIR_RE.match(child.name):
            n_files = sum(1 for _ in child.rglob("*") if _.is_file())
            excluded.append({
                "path": child.name + "/", "category": "run auxiliary data",
                "reason": f"{n_files} file(s) outside the gate contract "
                          f"(e.g. a feed cache) - not included in the "
                          f"bundle"})

    for rej in rejected:
        problems.append(
            f"record failed schema: {rej['source']} - "
            + "; ".join(rej["errors"]))

    # --- Phase-1 mapping traceability --------------------------------------------
    type_to_records = {}
    for rec in records:
        type_to_records.setdefault(rec["evidence_type"], []).append(
            rec["bundle_path"])
    if ci_log_plan is not None:
        # ci-log is issued by the collector (like
        # control-evidence-index): record its presence from the first
        # traceability pass so the control index (generated right
        # after) can point to this record file.
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

    # --- Collector-generated evidence index record (M2 schema) ---------
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
        "completeness_basis": "phase-1 mapping rows with every "
                              "evidence type present / total phase-1 "
                              "rows - computed by the collector from "
                              "the run's real data",
        "generated_by": f"{TOOL_NAME} {TOOL_VERSION} (M4 collector)",
        "run_id": run_id,
    }
    idx_errs = validate(index_record,
                        schemas["control-evidence-index"])
    if idx_errs:  # must never happen - a bug in the collector itself
        print("INTERNAL ERROR: the collector-generated index record "
              f"does not match its schema: {idx_errs}", file=sys.stderr)
        return 2
    # Once the index exists, update traceability for rows using this type
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

    # --- Findings summary -----------------------------------------------------
    secret_findings = extract_secret_findings(run_dir, gate_dirs)
    vuln_summary = extract_vuln_summary(records)
    denied_gates = [g for g, s in gate_status.items()
                    if s["status"] == "deny"]
    disabled_gates = [g for g, s in gate_status.items()
                      if s["status"] == "disabled"]
    bundle_status = "evidence-incomplete" if problems else "complete"

    if problems and not allow_incomplete:
        print("COLLECT STOPPED - the run does not qualify for bundling:",
              file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print("Use --allow-incomplete to bundle anyway with the "
              "'evidence-incomplete' flag (CI collect-only mode).",
              file=sys.stderr)
        return 1

    # --- Prepare signing (if --sign): generate the ephemeral key
    # OUTSIDE the tree before writing metadata, so the signature
    # declaration (with the public-key fingerprint) sits in
    # bundle.json + manifest.json - both covered by bundle.sha256,
    # and the signature signs bundle.sha256.
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
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        signature_decl = {
            "scheme": "cosign sign-blob (Sigstore bundle format)",
            "signed_file": "bundle.sha256",
            "signature_file": SIG_BUNDLE_NAME,
            "public_key_file": SIG_PUBKEY_NAME,
            "public_key_sha256": sha256_file(pub_path),
            "identity": "local:cosign-ephemeral-key",
            "note": "Per-run ephemeral key, generated outside the "
                    "tree and DESTROYED right after signing; the "
                    "private key never enters the bundle. A local "
                    "signature has no transparency log and no OIDC "
                    "identity - keyless OIDC + Rekor on CI is M5-B "
                    "work. For re-signing resistance, compare this "
                    "public_key_sha256 against a record outside the "
                    "bundle (release record / CI log) before trusting "
                    "the cosign.pub inside the bundle.",
        }

    # --- Packaging -------------------------------------------------------------
    generated_at = iso_now()
    bundle_id = f"{run_id}-{generated_at.replace(':', '').replace('-', '')}"
    bundle_dir = out_dir or (DEFAULT_BUNDLES_DIR / bundle_id)
    if bundle_dir.exists():
        if sign_tmp is not None:
            sign_tmp.cleanup()
        print(f"ERROR: bundle directory already exists: {bundle_dir}",
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

    # the collector's index record
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

    # ci-log record + log zip artefact (when the run has log files)
    ci_log_summary = None
    if ci_log_plan is not None:
        ci_rec = ci_log_plan["record"]
        ci_errs = validate(ci_rec, schemas["ci-log"])
        if ci_errs:  # must never happen - a bug in the collector
            print("INTERNAL ERROR: the collector-generated ci-log record "
                  f"does not match its schema: {ci_errs}", file=sys.stderr)
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

    for rej in rejected:  # only reached with --allow-incomplete
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
        # +1: the collector's index; +1 more when there is a ci-log record
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
        "note": "Every file in the bundle (except manifest.json and "
                "bundle.sha256) has one line here with its SHA-256, "
                "size and role. bundle.sha256 additionally covers "
                "manifest.json so any modification is detected by "
                "verify or `sha256sum -c bundle.sha256`."
                + (" This bundle HAS a Cosign signature on "
                   "bundle.sha256 (the 'signature' field above); the "
                   "files bundle.sigstore.json and cosign.pub "
                   "intentionally have no manifest line and are not "
                   "covered by bundle.sha256 - they authenticate "
                   "bundle.sha256 itself."
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

    # --- Sign bundle.sha256 with the ephemeral key, then destroy it -----------------
    if sign:
        try:
            sig_tmp_out = sign_dir / SIG_BUNDLE_NAME
            cosign_sign_blob(cosign_bin, sign_dir / "cosign.key",
                             bundle_dir / "bundle.sha256", sig_tmp_out,
                             signing_config, sign_dir)
            shutil.copy2(sig_tmp_out, bundle_dir / SIG_BUNDLE_NAME)
            shutil.copy2(sign_dir / "cosign.pub",
                         bundle_dir / SIG_PUBKEY_NAME)
            # Self-verify immediately, like gate 6: the signature
            # just created must verify with the very copy placed in
            # the bundle.
            cosign_verify_blob(cosign_bin, bundle_dir / SIG_PUBKEY_NAME,
                               bundle_dir / SIG_BUNDLE_NAME,
                               bundle_dir / "bundle.sha256", bundle_dir)
        except RuntimeError as exc:
            print(f"ERROR: bundle signing failed - deleting the unsigned "
                  f"bundle: {exc}", file=sys.stderr)
            shutil.rmtree(bundle_dir, ignore_errors=True)
            sign_tmp.cleanup()
            return 2
        sign_tmp.cleanup()

    print(f"Bundle: {bundle_dir}")
    print(f"  run={run_id}  status={bundle_status}  "
          f"records={len(records) + 1 + (1 if ci_log_plan is not None else 0)} "
          f"({1 + (1 if ci_log_plan is not None else 0)} of them "
          f"collector-generated)  "
          f"artefacts={len(artifacts)}  rejected={len(rejected)}")
    print(f"  blocking gates: {denied_gates or 'none'}  "
          f"disabled gates: {disabled_gates or 'none'}  "
          f"full traceability: {full_rows}/{len(traceability)} phase-1 rows")
    if signature_decl:
        print(f"  signature: Cosign on bundle.sha256 (local ephemeral "
              f"key, public-key fingerprint "
              f"{signature_decl['public_key_sha256'][:16]}...) - verify "
              f"will also check the signature")
    print(f"  Verify: python3 evidence/verify_bundle.py {bundle_dir}")
    return 0


def render_summary_md(summary, mapping) -> str:
    lines = []
    lines.append(f"# Evidence summary report — {summary['run_id']}")
    lines.append("")
    lines.append(f"- Bundle: `{summary['bundle_id']}`")
    lines.append(f"- Generated at (UTC): {summary['generated_at']}")
    lines.append(f"- Bundle status: **{summary['status']}**")
    commits = ", ".join(f"`{c}`" for c in summary["commit_shas"]) or "—"
    lines.append(f"- Commit SHAs in the records: {commits}")
    lines.append(f"- Valid records: {summary['records_valid']} · "
                 f"rejected records: {len(summary['records_rejected'])} · "
                 f"bundled artefacts: {summary['artifacts_bundled']}")
    if summary["problems"]:
        lines.append("")
        lines.append("## Problems (bundle flagged evidence-incomplete)")
        for p in summary["problems"]:
            lines.append(f"- {p}")
    lines.append("")
    lines.append("## Results by gate")
    lines.append("")
    lines.append("| Gate | Status | Policy decision | Records |")
    lines.append("|---|---|---|---|")
    for g in summary["gates"]:
        decs = "; ".join(
            f"{d['policy_id']} → **{d['decision']}**"
            + (f" ({len(d['violations'])} violations)"
               if d["violations"] else "")
            for d in g["decisions"]) or "—"
        note = f" — {g['note']}" if g["note"] else ""
        lines.append(f"| {g['gate']} | {g['status']}{note} | {decs} | "
                     f"{len(g['records'])} |")
    denies = [d for g in summary["gates"] for d in g["decisions"]
              if d["decision"] == "deny"]
    if denies:
        lines.append("")
        lines.append("### Blocking reasons (verbatim from the policy-decisions)")
        for d in denies:
            lines.append(f"- **{d['policy_id']}**:")
            for v in d["violations"]:
                lines.append(f"  - {v}")
    lines.append("")
    lines.append("## Secret findings (from gate 1's SARIF)")
    lines.append("")
    if summary["secret_findings"]:
        for s in summary["secret_findings"]:
            lines.append(f"- rule `{s['rule']}` at `{s['file']}:"
                         f"{s['line']}`")
    else:
        lines.append("- No secret findings in this run.")
    lines.append("")
    lines.append("## Vulnerabilities (vuln-risk-ranking record, gate 8)")
    lines.append("")
    vuln = summary["vulnerabilities"]
    if vuln:
        feeds = vuln.get("feed_versions") or {}
        feeds_txt = ", ".join(f"{k}={v}" for k, v in feeds.items()) \
            if isinstance(feeds, dict) else str(feeds)
        lines.append(f"- Total ranked entries: {vuln['entries_total']} "
                     f"({vuln['unique_cves']} distinct CVEs); source: "
                     f"`{vuln['source_record']}`; feed: {feeds_txt}")
        lines.append(f"- Issue decisions: {vuln['issue_entries']} entries.")
        lines.append(f"- BLOCK decisions (deduplicated by "
                     f"CVE/package/version): {len(vuln['block_unique'])}")
        for b in vuln["block_unique"]:
            lines.append(f"  - {b['cve']} — {b['package']}=={b['version']}"
                         f" (KEV: {b['in_kev']}, EPSS: {b['epss']})")
        lines.append(f"- In CISA KEV: {len(vuln['kev_unique'])} distinct "
                     f"CVEs.")
    else:
        lines.append("- No vuln-risk-ranking record in this "
                     "run.")
    lines.append("")
    lines.append("## Traceability: framework → policy → gate → evidence")
    lines.append("")
    lines.append(f"Phase-1 rows with every evidence type present: "
                 f"**{summary['completeness_full_rows']}**. Evidence types "
                 f"absent from this run are stated explicitly, never "
                 f"left silently blank.")
    lines.append("")
    lines.append("| Row | Framework — control group | Policy | Gate | "
                 "Evidence | Status |")
    lines.append("|---|---|---|---|---|---|")
    for t in summary["traceability"]:
        ev = "<br>".join(
            f"{'✅' if e['present'] else '❌'} {e['evidence_type']}"
            + (" (collector-generated)" if e["origin"] == "collector" else "")
            for e in t["evidence"])
        gates = ", ".join(str(g) for g in t["gates"]) or \
            (t["gate_note"] or "—")
        status_vi = {"full": "full", "partial": "partial",
                     "none": "none"}[t["status"]]
        lines.append(
            f"| {t['row']} | {t['framework']} — {t['control_group']} | "
            f"{', '.join(t['policies'])} | {gates} | {ev} | "
            f"{status_vi} |")
    missing_notes = {
        "change-record": "not present in this run - generate it with "
                         "`evidence/generators.py change-record "
                         "--run-dir <run>` (from the real gate results "
                         "of this very run) before collecting",
        "ci-log": "the run contains no log file (.log) for the "
                  "collector to package - a ci-log is only issued "
                  "when the run has real logs",
        "drift-report": "not present in this run - generate it with "
                        "`evidence/generators.py drift-report` (compares "
                        "the current configuration with the declared baseline) "
                        "before collecting",
        "config-baseline-report": "not present in this run - generate "
                                  "it with `evidence/generators.py "
                                  "config-baseline` before collecting",
        "access-review-report": "not present in this run - generate "
                                "it with `evidence/generators.py "
                                "access-review` before collecting",
        "pr-review-report": "only generated when gate 10 is on - gate 10 is "
                            "OFF by phase-1 design",
    }
    lines.append("")
    lines.append("### Missing evidence types — reasons")
    lines.append("")
    seen_missing = set()
    for t in summary["traceability"]:
        for e in t["evidence"]:
            if not e["present"] and e["evidence_type"] not in seen_missing:
                seen_missing.add(e["evidence_type"])
                reason = missing_notes.get(
                    e["evidence_type"],
                    "no generator source in this run")
                lines.append(f"- `{e['evidence_type']}`: {reason}")
    if summary["records_rejected"]:
        lines.append("")
        lines.append("## Rejected records (schema failures — named)")
        lines.append("")
        for r in summary["records_rejected"]:
            lines.append(f"- `{r['source']}`: " + "; ".join(r["errors"]))
    lines.append("")
    lines.append("## Run files NOT included in the bundle")
    lines.append("")
    by_cat = {}
    for e in summary["excluded"]:
        by_cat.setdefault(e["category"], []).append(e)
    for cat, items in sorted(by_cat.items()):
        lines.append(f"- **{cat}**: {len(items)} items — "
                     f"{items[0]['reason']}")
        for it in items:
            lines.append(f"  - `{it['path']}`")
    if summary.get("supplementary_records"):
        lines.append("")
        lines.append("## Supplementary records (decision/periodic "
                     "evidence generators)")
        lines.append("")
        lines.append("Generated by `evidence/generators.py` from the "
                     "run's/tree's real data, written into "
                     "`supplementary-records/` and schema-checked by the collector "
                     "like every other record:")
        for p in summary["supplementary_records"]:
            lines.append(f"- `{p}`")
    if summary.get("ci_log"):
        ci = summary["ci_log"]
        lines.append("")
        lines.append("## CI logs (ci-log record issued by the collector)")
        lines.append("")
        lines.append(f"- Record: `{ci['record']}`")
        lines.append(f"- Log package artefact: `{ci['artifact']}` "
                     f"({ci['log_file_count']} log files)")
        lines.append(f"- SHA-256 of the log package (declared in the record): "
                     f"`{ci['sha256']}` — verify re-checks this hash "
                     f"against the artefact in the bundle")
    lines.append("")
    lines.append("## Verifying this bundle")
    lines.append("")
    lines.append("```bash")
    lines.append("python3 evidence/verify_bundle.py <bundle-dir>")
    lines.append("# or check hashes only:")
    lines.append("cd <bundle-dir> && sha256sum -c bundle.sha256")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# VERIFY
# ---------------------------------------------------------------------------

def verify(bundle_dir: Path, cosign: str | None = None) -> int:
    errors, notes = [], []
    if not bundle_dir.is_dir():
        print(f"FAIL: bundle directory does not exist: {bundle_dir}")
        return 1
    sha_path = bundle_dir / "bundle.sha256"
    manifest_path = bundle_dir / "manifest.json"
    if not sha_path.is_file():
        errors.append("missing bundle.sha256 — cannot verify")
    if not manifest_path.is_file():
        errors.append("missing manifest.json — cannot verify")
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1

    # 1) bundle.sha256 covers every file, hashes match file by file
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
            # bundle.sha256 covers the other files; the two signature
            # files at the bundle root authenticate bundle.sha256 itself,
            # so they also stand outside this coverage (checked in step 4).
            if relp != "bundle.sha256" and relp not in SIGNATURE_FILES:
                disk_files[relp] = p
    for name, digest in sorted(recorded.items()):
        if name not in disk_files:
            errors.append(f"bundle.sha256 lists it but the file is missing: "
                          f"{name}")
        else:
            actual = sha256_file(disk_files[name])
            if actual != digest:
                errors.append(
                    f"hash mismatch: {name} (manifest says {digest[:16]}"
                    f"…, actual {actual[:16]}… — the file has been modified)")
    for name in sorted(disk_files):
        if name not in recorded:
            errors.append(f"file present in the bundle but not covered "
                          f"by bundle.sha256: {name}")

    # 2) manifest consistent with bundle.sha256 and with disk
    try:
        manifest = load_json(manifest_path)
    except Exception as exc:
        errors.append(f"manifest.json cannot be parsed: {exc}")
        manifest = None
    manifest_entries = {}
    if manifest is not None:
        for entry in manifest.get("files", []):
            manifest_entries[entry["path"]] = entry
            if entry["path"] in recorded and \
                    recorded[entry["path"]] != entry["sha256"]:
                errors.append(
                    f"manifest and bundle.sha256 disagree at "
                    f"{entry['path']}")
        expected = set(disk_files) - {"manifest.json"}
        if set(manifest_entries) != expected:
            diff = sorted(set(manifest_entries) ^ expected)
            errors.append(
                f"manifest does not match the on-disk file set at: "
                f"{', '.join(diff[:5])}")
        if manifest.get("status") == "evidence-incomplete":
            notes.append("bundle carries the 'evidence-incomplete' flag from "
                         "collect time (see summary.json for the problems)")

    # 3) Re-check the schema of every record in the bundle
    schemas_dir = bundle_dir / "schemas"
    if not schemas_dir.is_dir():
        schemas_dir = DEFAULT_SCHEMAS_DIR
        notes.append("bundle has no schemas/ — using the M2 schemas in "
                     "the repo to re-check")
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
                errors.append(f"{relp}: cannot parse JSON: {exc}")
                continue
            etype = data.get("evidence_type") if isinstance(data, dict) \
                else None
            if etype not in schemas:
                errors.append(f"{relp}: evidence_type {etype!r} has no "
                              f"corresponding schema")
                continue
            for err in validate(data, schemas[etype]):
                errors.append(f"{relp}: {err}")
            if etype == "ci-log":
                ci_log_records.append((relp, data))
    else:
        errors.append("bundle has no records/ directory")

    # 3b) Cross-check the ci-log record: the hash declared in the record
    # must match the real SHA-256 of the log-package artefact inside the
    # bundle — catches record and artefact being edited inconsistently.
    for relp, data in ci_log_records:
        artifact_uri = data.get("artifact_uri") or ""
        declared = (data.get("sha256") or "").removeprefix("sha256:")
        artifact_path = bundle_dir / artifact_uri
        if not artifact_uri or not artifact_path.is_file():
            errors.append(
                f"{relp}: ci-log record points at artefact "
                f"{artifact_uri!r} which is not in the bundle")
        elif declared and sha256_file(artifact_path) != declared:
            errors.append(
                f"{relp}: log-package hash declared in the record "
                f"({declared[:16]}…) does not match the actual SHA-256 of "
                f"{artifact_uri} — the record or the artefact has been "
                f"edited inconsistently")
        else:
            notes.append(
                f"ci-log: log archive hash ({artifact_uri}) matches the "
                f"declaration in the record")
    rejected_dir = bundle_dir / "rejected"
    if rejected_dir.is_dir():
        n_rej = sum(1 for _ in rejected_dir.rglob("*") if _.is_file())
        notes.append(f"bundle contains {n_rej} records rejected by the collector "
                     f"(reasons stated in the manifest/summary) — these files "
                     f"were hash-checked in step 1 but are not in "
                     f"the schema-check set")

    # 4) Cosign signature on bundle.sha256 — when the bundle DECLARES
    # a signature (in manifest.json, fallback bundle.json; both are
    # covered by bundle.sha256 so the declaration cannot be edited
    # silently). A declaration with a missing/unverifiable/invalid
    # signature is a LOUD FAIL, never downgraded to "hash check only".
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
            errors.append("bundle declares a Cosign signature but is "
                          f"missing the signature file {sig_path.name}")
        if not pub_path.is_file():
            errors.append("bundle declares a Cosign signature but is "
                          f"missing the public key {pub_path.name}")
        if sig_path.is_file() and pub_path.is_file():
            fingerprint = decl.get("public_key_sha256")
            if fingerprint and sha256_file(pub_path) != fingerprint:
                errors.append(
                    "cosign.pub does not match the public-key fingerprint "
                    "declared in the manifest — the key has been replaced")
            cosign_bin = find_cosign(cosign)
            if not cosign_bin:
                errors.append(
                    "bundle declares a Cosign signature but no cosign "
                    "binary was found to verify it (install cosign or "
                    "pass --cosign / COSIGN_BINARY) — not counted "
                    "as passing")
            else:
                try:
                    cosign_verify_blob(
                        cosign_bin, pub_path, sig_path,
                        bundle_dir / "bundle.sha256", bundle_dir)
                    notes.append(
                        "Cosign signature on bundle.sha256: VALID "
                        "(local ephemeral key; limits vs keyless "
                        "keyless OIDC — xem evidence/README.md)")
                except RuntimeError as exc:
                    errors.append(f"Cosign signature INVALID: {exc}")
    elif has_sig_files:
        notes.append("bundle has signature files at its root but the manifest "
                     "declares no signature — signature not verified")
    else:
        notes.append("bundle has no cryptographic signature — integrity "
                     "checked by SHA-256 only")

    print(f"Bundle: {bundle_dir}")
    print(f"  files hash-checked: {len(recorded)} · "
          f"records schema-checked: {n_records}")
    for n in notes:
        print(f"  NOTE: {n}")
    if errors:
        print("RESULT: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("RESULT: PASS — every hash matches the manifest, every record "
          "matches the M2 schemas")
    return 0


# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="bundle_tool",
        description="devsecops-os evidence bundle tool (M4)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_collect = sub.add_parser(
        "collect", help="collect + package a bundle from one gates run")
    p_collect.add_argument("run_dir",
                           help="run directory (evidence/output/<run>)")
    p_collect.add_argument("--out-dir", default=None,
                           help="output bundle directory (default: "
                                "evidence/bundles/<run>-<timestamp>)")
    p_collect.add_argument("--run-id", default=None,
                           help="run identifier (default: the run "
                                "directory name)")
    p_collect.add_argument("--allow-incomplete", action="store_true",
                           help="still package a bundle when records fail "
                                "their schema/a gate lacks evidence, flagged "
                                "evidence-incomplete (CI mode)")
    p_collect.add_argument("--sign", action="store_true",
                           help="sign bundle.sha256 with Cosign (ephemeral "
                                "per-run key, destroyed right after signing; "
                                "requires cosign + an offline "
                                "signing-config)")
    p_collect.add_argument("--cosign", default=None,
                           help="path to cosign (default: "
                                "COSIGN_BINARY or PATH)")
    p_collect.add_argument("--signing-config", default=None,
                           help="signing-config for cosign (default: "
                                "the repo's gates/local/signing-config-offline."
                                "json)")

    p_verify = sub.add_parser("verify", help="verify a bundle")
    p_verify.add_argument("bundle_dir", help="bundle directory")
    p_verify.add_argument("--cosign", default=None,
                          help="path to cosign for signature verification "
                               "(default: COSIGN_BINARY or PATH)")

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
