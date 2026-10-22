package devsecops.secret_findings

test_no_findings_passes if {
	count(deny) == 0 with input as {"findings": [], "scan_date": "2026-10-22"}
}

test_planted_secret_denied if {
	count(deny) == 1 with input as {
		"scan_date": "2026-10-22",
		"findings": [{"file": "backend/config.py", "line": 18, "rule": "generic-api-key", "match_preview": "sk_live_FAKENOTREAL...", "allowlisted_until": null}],
	}
}

test_expired_allowlist_denied if {
	count(deny) == 1 with input as {
		"scan_date": "2026-10-22",
		"findings": [{"file": "a.py", "line": 1, "rule": "generic-api-key", "match_preview": "x", "allowlisted_until": "2026-01-01"}],
	}
}

test_active_allowlist_passes if {
	count(deny) == 0 with input as {
		"scan_date": "2026-10-22",
		"findings": [{"file": "a.py", "line": 1, "rule": "generic-api-key", "match_preview": "x", "allowlisted_until": "2027-01-01"}],
	}
}
