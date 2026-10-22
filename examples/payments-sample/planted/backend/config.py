"""Runtime configuration for payments-sample (PLANTED variant).

========================================================================
PLANTED FLAW #1 — hardcoded secret fallback (see ../PLANTED.md).
The value below is a FAKE, non-functional example string planted on
purpose so the secret-scanning gate (blueprint gate 1) has something real
to catch. It is not, and never was, a real credential. Do not copy this
pattern; the clean variant (../../clean/backend/config.py) reads the key
from the environment only.
========================================================================
"""

import os


class Settings:
    # PLANTED: hardcoded fallback key committed to source. FAKE value.
    PAYMENT_PROVIDER_API_KEY = os.environ.get(
        "PAYMENT_PROVIDER_API_KEY",
        "sk_live_FAKENOTREAL00000000000000000000",
    )
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "local")


settings = Settings()
