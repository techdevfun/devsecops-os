#!/usr/bin/env python3
"""Gate 6 — the SBOM + attestation chain, run for real locally:
  1. package the artefact (tar.gz of the workload variant) + SHA-256 digest;
  2. Syft generates a CycloneDX SBOM of the artefact;
  3. Cosign: generate a temporary local key, sign the SBOM (sign-blob), verify-blob;
  4. generate provenance (condensed SLSA v1 format, local builder — SLSA
     Build L1: built on a regular machine/runner, with no isolated build platform
     like slsa-github-generator in CI — recorded honestly at this level);
  5. write the `sbom` + `provenance-attestation` evidence records and the input
     for policy devsecops.provenance.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def run(cmd, **kw):
    kw.setdefault("timeout", 900)
    # stdin=DEVNULL: any unexpected interactive prompt from a tool (for example
    # cosign asking to overwrite a key) must fail immediately, not hang the whole pipeline.
    kw.setdefault("stdin", subprocess.DEVNULL)
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(f"[provenance] ERROR running {' '.join(map(str, cmd))}:\n"
              f"{r.stdout}\n{r.stderr}", file=sys.stderr)
        raise SystemExit(2)
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--syft", required=True)
    ap.add_argument("--cosign", required=True)
    ap.add_argument("--workload", required=True)
    ap.add_argument("--variant", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--commit-sha", required=True)
    ap.add_argument("--signing-config", required=True,
                    help="Signing config WITHOUT Rekor (offline signing with a "
                         "local key — see gates/local/README in "
                         "signing-config-offline.json)")
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    workload = Path(a.workload)

    artefact = out / f"payments-sample-{a.variant}.tar.gz"
    with tarfile.open(artefact, "w:gz") as tf:
        for p in sorted(workload.rglob("*")):
            if p.is_file():
                tf.add(p, arcname=str(p.relative_to(workload)))
    art_digest = f"sha256:{sha256_file(artefact)}"
    print(f"[provenance] artefact {artefact.name} digest {art_digest}")

    sbom_path = out / "sbom.cdx.json"
    run([a.syft, f"dir:{workload}", "--output",
         f"cyclonedx-json={sbom_path}", "--quiet"])
    sbom = json.loads(sbom_path.read_text())
    n_components = len(sbom.get("components", []) or [])
    print(f"[provenance] SBOM CycloneDX: {n_components} components")

    env = dict(os.environ, COSIGN_PASSWORD="")
    # The key is EPHEMERAL per run: delete old keys if the output
    # directory is reused (generate-key-pair would prompt to overwrite and hang if
    # a key already exists).
    for old in ("cosign.key", "cosign.pub"):
        (out / old).unlink(missing_ok=True)
    run([a.cosign, "generate-key-pair"], cwd=out, env=env)
    # Cosign v3: --output-signature is deprecated; the current format
    # is the Sigstore bundle (--bundle). Signing with a local key + a signing
    # config with Rekor stripped out => fully offline signing, nothing pushed
    # to a public transparency log; the verification side therefore uses
    # --insecure-ignore-tlog (true to the nature of local SLSA L1; in CI,
    # keyless OIDC + Rekor will have a full tlog — M5).
    bundle_path = out / "sbom.bundle.json"
    run([a.cosign, "sign-blob", "--key", "cosign.key",
         "--bundle", str(bundle_path),
         "--signing-config", a.signing_config, "--yes", str(sbom_path)],
        cwd=out, env=env)
    run([a.cosign, "verify-blob", "--key", "cosign.pub",
         "--bundle", str(bundle_path), "--insecure-ignore-tlog",
         str(sbom_path)], cwd=out, env=env)
    print("[provenance] cosign sign-blob + verify-blob (bundle, "
          "offline, no tlog): OK")

    builder = ("devsecops-os gate-06 local runner "
               "(CI: slsa-github-generator)")
    provenance = {
        "predicateType": "https://slsa.dev/provenance/v1",
        "subject": [{"name": artefact.name,
                     "digest": {"sha256": art_digest.split(":", 1)[1]}}],
        "predicate": {"buildType": "devsecops-os/payments-sample-tarball",
                      "builder": {"id": builder}},
    }
    prov_path = out / "provenance.intoto.json"
    prov_path.write_text(json.dumps(provenance, indent=2) + "\n")

    sbom_record = {
        "evidence_type": "sbom", "format": "CycloneDX",
        "artifact_digest": art_digest,
        "sha256": f"sha256:{sha256_file(sbom_path)}",
        "signed": True, "components_count": n_components,
    }
    (out / "sbom.record.json").write_text(
        json.dumps(sbom_record, indent=2) + "\n")
    att_record = {
        "evidence_type": "provenance-attestation",
        "artifact_digest": art_digest, "builder": builder,
        "slsa_level": 1, "signature_verified": True,
        "subject": artefact.name,
        "predicate_type": "https://slsa.dev/provenance/v1",
    }
    (out / "provenance-attestation.record.json").write_text(
        json.dumps(att_record, indent=2) + "\n")

    policy_input = {
        "artifact": {"name": artefact.name, "digest": art_digest},
        "sbom": {"format": "CycloneDX",
                 "digest": f"sha256:{sha256_file(sbom_path)}"},
        "signature": {"verified": True,
                      "identity": "local:cosign-ephemeral-key"},
        "provenance": {"builder": builder, "digest": art_digest,
                       "slsa_level": 1},
        "config": {"min_slsa_level": 1},
    }
    (out / "provenance.input.json").write_text(
        json.dumps(policy_input, indent=2) + "\n")
    print("[provenance] records + policy input written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
