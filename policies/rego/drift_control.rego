# drift_control — scheduled drift checks (actual configuration
# deviating from the declared IaC): drift on critical resources
# (network, IAM, storage) that is not acknowledged/handled within
# the configured SLA BLOCKS the reporting period. This policy
# decides on the drift report produced by the IaC scan/drift job
# (extended gate 4) — serves SOC 2 CC7.1-CC7.2 (reference mapping).
#
# Input:
#   { "report_date": "2026-10-22",
#     "drift_items": [ {"resource": "aws_security_group.app",
#                       "category": "network", "detected_on": "2026-10-20",
#                       "acknowledged": false, "ticket": null} ],
#     "config": {"sla_days": 7,
#                "critical_categories": ["network","iam","storage"]} }
package devsecops.drift_control

deny contains msg if {
	d := input.drift_items[_]
	d.category in input.config.critical_categories
	not d.acknowledged
	age_days(d) > input.config.sla_days
	msg := sprintf("drift on %s (%s) detected %s, still unhandled after %d days (SLA %d) — SOC 2 CC7.2", [d.resource, d.category, d.detected_on, age_days(d), input.config.sla_days])
}

deny contains msg if {
	d := input.drift_items[_]
	d.category in input.config.critical_categories
	d.acknowledged == true
	object.get(d, "ticket", null) == null
	msg := sprintf("drift on %s was acknowledged but has no handling ticket", [d.resource])
}

age_days(d) := (time.parse_rfc3339_ns(sprintf("%sT00:00:00Z", [input.report_date])) - time.parse_rfc3339_ns(sprintf("%sT00:00:00Z", [d.detected_on]))) / 86400000000000
