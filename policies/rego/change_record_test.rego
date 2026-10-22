package devsecops.change_record

cfg := {"required_gates": ["secret", "sast", "sca"], "protected_branches": ["main", "release"]}

good_change := {
	"id": "PR-1", "target_branch": "main", "author": "dev1",
	"approvals": ["lead1"],
	"gate_results": {"secret": "pass", "sast": "pass", "sca": "pass"},
	"evidence_links": ["evidence://run/1"], "exceptions": [],
}

test_good_change_passes if {
	count(deny) == 0 with input as {"change": good_change, "config": cfg, "today": "2026-10-22"}
}

test_no_approval_denied if {
	c := object.union(good_change, {"approvals": []})
	count(deny) == 1 with input as {"change": c, "config": cfg, "today": "2026-10-22"}
}

test_self_approval_denied if {
	c := object.union(good_change, {"approvals": ["dev1"]})
	count(deny) == 1 with input as {"change": c, "config": cfg, "today": "2026-10-22"}
}

test_failing_gate_denied if {
	c := object.union(good_change, {"gate_results": {"secret": "pass", "sast": "fail", "sca": "pass"}})
	count(deny) == 1 with input as {"change": c, "config": cfg, "today": "2026-10-22"}
}

test_active_exception_passes if {
	c := object.union(good_change, {
		"gate_results": {"secret": "pass", "sast": "fail", "sca": "pass"},
		"exceptions": [{"gate": "sast", "expires": "2026-12-31"}],
	})
	count(deny) == 0 with input as {"change": c, "config": cfg, "today": "2026-10-22"}
}

test_missing_evidence_denied if {
	c := object.union(good_change, {"evidence_links": []})
	count(deny) == 1 with input as {"change": c, "config": cfg, "today": "2026-10-22"}
}
