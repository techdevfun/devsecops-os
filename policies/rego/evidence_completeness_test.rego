package devsecops.evidence_completeness

good := {
	"run": {"commit_sha": "abc123", "started_at": "2026-10-22T07:00:00Z"},
	"items": [
		{"type": "sarif-report", "sha256": "h1", "controls": ["ISO-A.8.25"]},
		{"type": "sbom", "sha256": "h2", "controls": ["ISO-A.5.19"]},
		{"type": "ci-log", "sha256": "h3", "controls": ["ISO-A.8.15"]},
	],
	"config": {"required_types": ["sarif-report", "sbom", "ci-log"]},
}

test_complete_bundle_passes if {
	count(deny) == 0 with input as good
}

test_missing_required_type_denied if {
	count(deny) == 1 with input as object.union(good, {"items": [
		{"type": "sarif-report", "sha256": "h1", "controls": ["ISO-A.8.25"]},
		{"type": "sbom", "sha256": "h2", "controls": ["ISO-A.5.19"]},
	]})
}

test_missing_hash_denied if {
	count(deny) == 1 with input as object.union(good, {"items": [
		{"type": "sarif-report", "sha256": "h1", "controls": ["ISO-A.8.25"]},
		{"type": "sbom", "sha256": "h2", "controls": ["ISO-A.5.19"]},
		{"type": "ci-log", "controls": ["ISO-A.8.15"]},
	]})
}

test_missing_commit_denied if {
	count(deny) == 1 with input as {
		"run": {"started_at": "2026-10-22T07:00:00Z"},
		"items": [
			{"type": "sarif-report", "sha256": "h1", "controls": ["ISO-A.8.25"]},
			{"type": "sbom", "sha256": "h2", "controls": ["ISO-A.5.19"]},
			{"type": "ci-log", "sha256": "h3", "controls": ["ISO-A.8.15"]},
		],
		"config": {"required_types": ["sarif-report", "sbom", "ci-log"]},
	}
}
