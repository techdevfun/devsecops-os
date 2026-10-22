"""Runtime configuration for payments-sample (clean variant).

Secrets come ONLY from the environment (injected by the platform / secret
manager in real deployments). There is deliberately no hardcoded fallback:
if PAYMENT_PROVIDER_API_KEY is unset, the API still runs and records
payments locally with status "recorded" (provider calls are stubbed in
this sample).
"""

import os


class Settings:
    # API key for the (stubbed) payment provider. Never commit a real value.
    PAYMENT_PROVIDER_API_KEY = os.environ.get("PAYMENT_PROVIDER_API_KEY", "")
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "local")


settings = Settings()
