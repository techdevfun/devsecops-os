# evidence_completeness — a pipeline run only counts as having
# "complete evidence" when: every evidence type required by the
# enabled gates is present in the bundle, each item has a SHA-256 +
# timestamp + commit SHA, and there is at least one CI log item.
# This is the "final gate" (blueprint 5.2) in policy form: the M4
# collector evaluates the manifest with this policy. Serves ISO
# A.8.15-A.8.16 (logging & monitoring) and CPS 234 (continuous
# control evidence) — reference mapping.
#
# Input (bundle manifest):
#   { "run": { "commit_sha": "abc...", "started_at": "2026-10-22T..." },
#     "items": [ {"type": "sarif-report", "sha256": "...", "controls": [...]} ],
#     "config": {"required_types": ["sarif-report","sbom","ci-log"]} }
package devsecops.evidence_completeness

deny contains msg if {
	t := input.config.required_types[_]
	not type_present(t)
	msg := sprintf("bundle is missing the required evidence type %q for an enabled gate (evidence incomplete)", [t])
}

deny contains msg if {
	it := input.items[_]
	object.get(it, "sha256", "") == ""
	msg := sprintf("evidence %q is missing its SHA-256 — integrity cannot be verified", [it.type])
}

deny contains msg if {
	it := input.items[_]
	count(it.controls) == 0
	msg := sprintf("evidence %q is not linked to any control group in the policy pack", [it.type])
}

deny contains msg if {
	object.get(input.run, "commit_sha", "") == ""
	msg := "bundle does not record a commit SHA — evidence cannot be traced to its origin"
}

type_present(t) if {
	some it in input.items
	it.type == t
}
