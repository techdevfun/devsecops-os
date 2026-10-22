package devsecops.pipeline_policy

good_workflow := {
	"file": ".github/workflows/ci.yml",
	"permissions": {"contents": "read"},
	"uses": ["actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683"],
	"gates_enabled": ["secret", "sast", "sca", "iac", "kev"],
	"jobs": [{"name": "deploy", "cloud_access": true, "oidc": true, "static_cloud_secrets": []}],
}

cfg := {"required_gates": ["secret", "sast", "sca", "iac", "kev"], "internal_action_prefixes": ["./.github/actions/"]}

test_good_workflow_passes if {
	count(deny) == 0 with input as {"workflows": [good_workflow], "config": cfg}
}

test_write_all_denied if {
	w := object.union(good_workflow, {"permissions": "write-all"})
	count(deny) == 1 with input as {"workflows": [w], "config": cfg}
}

test_unpinned_action_denied if {
	w := object.union(good_workflow, {"uses": ["actions/checkout@v4"]})
	count(deny) == 1 with input as {"workflows": [w], "config": cfg}
}

test_missing_gate_denied if {
	w := object.union(good_workflow, {"gates_enabled": ["secret", "sast"]})
	count(deny) == 3 with input as {"workflows": [w], "config": cfg}
}

test_static_cloud_secret_denied if {
	j := {"name": "deploy", "cloud_access": true, "oidc": false, "static_cloud_secrets": ["AWS_ACCESS_KEY_ID"]}
	w := object.union(good_workflow, {"jobs": [j]})
	count(deny) == 2 with input as {"workflows": [w], "config": cfg}
}
