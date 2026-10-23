#!/usr/bin/env python3
"""Single-command bundle verification for devsecops-os (blueprint
acceptance criterion 4): verify the hashes of the whole bundle against the manifest +
bundle.sha256 and re-check the M2 schema of every record.

    python3 evidence/verify_bundle.py <bundle-dir>

The real code lives in bundle_tool.py (same directory) — this file is only a
short entry point for the "single command" contract.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bundle_tool import main  # noqa: E402

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "verify", *sys.argv[1:]]
    raise SystemExit(main())
