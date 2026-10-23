# secret_findings — decision policy on secret SCAN RESULTS.
#
# Why this mechanism (not a policy on code directly): detecting
# secrets is the job of a dedicated scanner (gitleaks — gate 1).
# This policy is the decision layer: any secret finding that is not
# covered by an active allowlist entry BLOCKS. Input is normalised
# JSON from scan results (gitleaks JSON or an equivalent extractor
# in the harness), so swapping the scanner does not change the
# policy.
#
# Input:
#   { "findings": [ { "file": "backend/config.py", "line": 18,
#                     "rule": "generic-api-key", "match_preview": "sk_live_...",
#                     "allowlisted_until": null } ],
#     "scan_date": "2026-10-22" }
package devsecops.secret_findings

deny contains msg if {
	f := input.findings[_]
	not allowlist_active(f)
	msg := sprintf("non-allowlisted secret at %s:%d (rule %s) — remove it and rotate the credential (ISO A.8.28, PCI DSS Req 6/8 reference)", [f.file, f.line, f.rule])
}

allowlist_active(f) if {
	f.allowlisted_until != null
	f.allowlisted_until >= input.scan_date
}
