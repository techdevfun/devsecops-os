#!/usr/bin/env bash
# Download + checksum-verify the gate tools (shared by local runs & CI).
# Every version is PINNED + SHA-256 measured from the official release dated
# 2026-10-22. A tool already present at the right version in $TOOLS_DIR is skipped.
set -eu
TOOLS_DIR="${TOOLS_DIR:-$HOME/workspace/tools}"
mkdir -p "$TOOLS_DIR/downloads"
cd "$TOOLS_DIR/downloads"

fetch() { # fetch <destination-filename> <url> <sha256>
  local dest="$TOOLS_DIR/$1" url="$2" sum="$3"
  if [ -x "$dest" ]; then echo "[fetch_tools] already have $1 — skipping"; return 0; fi
  local tmp; tmp="$(basename "$url")"
  echo "[fetch_tools] downloading $1 from $url"
  curl -sL --fail -o "$tmp" "$url"
  echo "$sum  $tmp" | sha256sum -c - >/dev/null
  case "$tmp" in
    *.tar.gz) tar --no-same-owner -xzf "$tmp" ;;
    *.zip) python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall('.')" "$tmp" ;;
    *) cp "$tmp" "$dest" ;;
  esac
  # After extraction, the binary sits directly in the downloads directory (the tarballs of
  # these tools all contain the binary at the root).
  for b in gitleaks trivy syft conftest terraform; do
    if [ -f "$b" ] && [ "$1" = "$b" ]; then mv "$b" "$dest"; fi
  done
  chmod +x "$dest"
  echo "[fetch_tools] $1 OK (sha256 matches)"
}

fetch gitleaks    https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz 551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb
fetch osv-scanner https://github.com/google/osv-scanner/releases/download/v2.7.0/osv-scanner_linux_amd64 160c6253e2922e9e0a6a9771c5c4c40a4b3c6090b34a3cdd5e80c96cc2e4218b
fetch trivy       https://github.com/aquasecurity/trivy/releases/download/v0.76.1/trivy_0.76.1_Linux-64bit.tar.gz c7cbe3137fb8a48a17574bede3dd6beb16742d1e9772929940fc90082c39d9c0
fetch syft        https://github.com/anchore/syft/releases/download/v1.55.0/syft_1.55.0_linux_amd64.tar.gz bb65249542db5fedeeb4d3f9b018b75e7264dbfbbb10486f044581a92f90490d
fetch cosign      https://github.com/sigstore/cosign/releases/download/v3.1.4/cosign-linux-amd64 424e2c97d0b45fd7a6b608a87f090f35633f4c23ece5f092d48bba11aaf4bbfa
fetch conftest    https://github.com/open-policy-agent/conftest/releases/download/v0.71.1/conftest_0.71.1_Linux_x86_64.tar.gz c3f6b2a753bd56e377a1e51a95ae3e057f926f2e9139f7d5b5dfbbaf810f7985
fetch terraform   https://releases.hashicorp.com/terraform/1.17.0/terraform_1.17.0_linux_amd64.zip c168cab7c637a8769fdb90089ddd19de701bc6ff8aca64dc2e2185fe46f59f67

if [ ! -x "$TOOLS_DIR/opa" ]; then
  echo "[fetch_tools] downloading opa v1.21.3"
  curl -sL --fail -o "$TOOLS_DIR/opa" https://openpolicyagent.org/downloads/v1.21.3/opa_linux_amd64_static
  chmod +x "$TOOLS_DIR/opa"
fi
echo "[fetch_tools] done: $TOOLS_DIR"
