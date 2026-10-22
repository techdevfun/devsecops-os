#!/usr/bin/env python3
"""Gate 6 — chuỗi SBOM + attestation chạy thật ở cục bộ:
  1. đóng gói artefact (tar.gz của biến thể workload) + digest SHA-256;
  2. Syft sinh SBOM CycloneDX của artefact;
  3. Cosign: sinh khoá cục bộ tạm thời, ký SBOM (sign-blob), verify-blob;
  4. sinh provenance (định dạng SLSA v1 rút gọn, builder cục bộ — SLSA
     Build L1: build trên máy/runner thường, không có nền tảng build
     cách ly như slsa-github-generator ở CI — ghi đúng mức này);
  5. ghi evidence record `sbom` + `provenance-attestation` và input
     cho policy devsecops.provenance.
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
    # stdin=DEVNULL: mọi prompt tương tác bất ngờ của công cụ (ví dụ
    # cosign hỏi ghi đè khoá) phải fail ngay, không treo cả pipeline.
    kw.setdefault("stdin", subprocess.DEVNULL)
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(f"[provenance] LỖI chạy {' '.join(map(str, cmd))}:\n"
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
                    help="Signing config KHÔNG có Rekor (ký offline bằng "
                         "khoá cục bộ — xem gates/local/README trong "
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
    # Khoá là TẠM THỜI theo từng lần chạy: xoá khoá cũ nếu thư mục đầu
    # ra được dùng lại (generate-key-pair sẽ hỏi ghi đè và treo nếu
    # khoá đã tồn tại).
    for old in ("cosign.key", "cosign.pub"):
        (out / old).unlink(missing_ok=True)
    run([a.cosign, "generate-key-pair"], cwd=out, env=env)
    # Cosign v3: --output-signature đã deprecated; định dạng hiện hành
    # là bundle Sigstore (--bundle). Ký bằng khoá cục bộ + signing
    # config đã lược bỏ Rekor => ký hoàn toàn offline, không đẩy gì
    # lên transparency log công cộng; phía xác minh vì thế dùng
    # --insecure-ignore-tlog (đúng bản chất SLSA L1 cục bộ; ở CI dùng
    # keyless OIDC + Rekor sẽ có tlog đầy đủ — M5).
    bundle_path = out / "sbom.bundle.json"
    run([a.cosign, "sign-blob", "--key", "cosign.key",
         "--bundle", str(bundle_path),
         "--signing-config", a.signing_config, "--yes", str(sbom_path)],
        cwd=out, env=env)
    run([a.cosign, "verify-blob", "--key", "cosign.pub",
         "--bundle", str(bundle_path), "--insecure-ignore-tlog",
         str(sbom_path)], cwd=out, env=env)
    print("[provenance] cosign sign-blob + verify-blob (bundle, "
          "offline, không tlog): OK")

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
    print("[provenance] records + policy input đã ghi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
