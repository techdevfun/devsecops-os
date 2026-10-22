package devsecops.drift_control

cfg := {"sla_days": 7, "critical_categories": ["network", "iam", "storage"]}

test_no_drift_passes if {
	count(deny) == 0 with input as {"report_date": "2026-10-22", "drift_items": [], "config": cfg}
}

test_fresh_drift_within_sla_passes if {
	count(deny) == 0 with input as {"report_date": "2026-10-22", "drift_items": [
		{"resource": "aws_security_group.app", "category": "network", "detected_on": "2026-10-20", "acknowledged": false, "ticket": null},
	], "config": cfg}
}

test_stale_critical_drift_denied if {
	count(deny) == 1 with input as {"report_date": "2026-10-22", "drift_items": [
		{"resource": "aws_security_group.app", "category": "network", "detected_on": "2026-10-01", "acknowledged": false, "ticket": null},
	], "config": cfg}
}

test_acknowledged_without_ticket_denied if {
	count(deny) == 1 with input as {"report_date": "2026-10-22", "drift_items": [
		{"resource": "aws_iam_role.task", "category": "iam", "detected_on": "2026-10-21", "acknowledged": true, "ticket": null},
	], "config": cfg}
}

test_acknowledged_with_ticket_passes if {
	count(deny) == 0 with input as {"report_date": "2026-10-22", "drift_items": [
		{"resource": "aws_iam_role.task", "category": "iam", "detected_on": "2026-10-01", "acknowledged": true, "ticket": "SEC-123"},
	], "config": cfg}
}
