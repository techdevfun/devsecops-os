"""Runtime configuration for example-service (golden-path template).

Secrets come ONLY from the environment (injected by the platform / secret
manager in real deployments). There is deliberately no hardcoded fallback:
never add a default value for a secret here — the secret-scanning gate
(gate 1) treats any literal fallback as a finding.
"""

import os


class Settings:
    SERVICE_NAME = os.environ.get("SERVICE_NAME", "example-service")
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "local")
    # API key for an external provider, if the service needs one. Injected
    # from a secret store at deploy time; never commit a real value.
    EXAMPLE_API_KEY = os.environ.get("EXAMPLE_API_KEY")


settings = Settings()
