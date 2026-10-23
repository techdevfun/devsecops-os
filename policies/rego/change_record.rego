# change_record — the change record for a release/merge into a
# protected branch must have: (1) a PR approval from someone other
# than the author; (2) every required gate run and passing (or an
# approved, unexpired exception); (3) evidence links. Missing any
# item -> the release is not eligible. This policy decides on the
# change-record data produced by the gate/evidence collector (M3/M4)
# — serves ISO A.8.32, PCI DSS Req 6.5, SOC 2 CC8.1 (reference
# mapping).
#
# Input:
#   { "change": { "id": "PR-123", "target_branch": "release",
#                 "author": "dev1", "approvals": ["lead1"],
#                 "gate_results": {"secret": "pass", "sast": "pass"},
#                 "evidence_links": ["evidence://run/456"],
#                 "exceptions": [] },
#     "config": {"required_gates": ["secret","sast","sca"],
#                "protected_branches": ["main","release"]} }
package devsecops.change_record

deny contains msg if {
	c := input.change
	c.target_branch in input.config.protected_branches
	count(c.approvals) == 0
	msg := sprintf("change %s into protected branch %s has no PR approval (A.8.32 / PCI 6.5 / SOC 2 CC8.1)", [c.id, c.target_branch])
}

deny contains msg if {
	c := input.change
	c.author in c.approvals
	msg := sprintf("change %s was approved by its own author %s — self-approval is forbidden", [c.id, c.author])
}

deny contains msg if {
	c := input.change
	g := input.config.required_gates[_]
	c.gate_results[g] != "pass"
	not exception_active(c, g)
	msg := sprintf("change %s: required gate %q has not passed (status: %v)", [c.id, g, object.get(c.gate_results, g, "missing")])
}

deny contains msg if {
	c := input.change
	c.target_branch in input.config.protected_branches
	count(c.evidence_links) == 0
	msg := sprintf("change %s has no evidence links — the evidence collector must collect them before release", [c.id])
}

exception_active(c, gate) if {
	e := c.exceptions[_]
	e.gate == gate
	e.expires >= input.today
}
