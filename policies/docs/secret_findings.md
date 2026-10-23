# secret_findings — block on a secret finding not on the allowlist

- **Code**: `devsecops.secret_findings` · **Mechanism**: decision policy
  (Rego) over the scan results of a scanner — **reason for not rewriting the scanner**:
  secret detection is the job of gitleaks (gate 1) with a rule set maintained by the
  community; the pack only keeps the decision layer (block / time-limited allowlist) so that
  changing the scanner does not change the policy · **Consuming gate**: Gate 1 (secret
  scanning) at the decision step after scanning · **Evidence**: `sarif-report`
  (scan results) + `policy-decision`.

**Which control** (reference mapping): ISO 27001 A.8.28 (secure
coding — do not embed secrets in code); SSDF PW.6/PW.9 (secure build environment
configuration); PCI DSS 4.0 Requirements 6.2/8 (no hardcoded credentials);
SOC 2 CC6.1/CC7.1.

**Why**: a committed secret is treated as exposed (every copy of the repo
carries it) — planted fault #1 of payments-sample (a backup `sk_live_` key
in `config.py`).

**How to fix a violation**: remove the secret from the code (read from an environment
variable/secret manager as in the clean variant), **rotate the credential immediately** because
removing it from HEAD does not remove it from git history; if it is a false positive with a
reason, request an allowlist entry with an expiry — when it expires it is blocked again.
