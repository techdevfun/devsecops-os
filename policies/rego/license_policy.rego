# license_policy — a dependency license (read from the SBOM) that
# is on the organisation's denied list is BLOCKED; an undetermined
# license triggers a mandatory review warning (not blocking in
# pack v1).
#
# Input:
#   { "components": [ {"name": "...", "version": "...",
#                      "license": "MIT"} ],
#     "config": {"denied_licenses": ["GPL-3.0-only", "AGPL-3.0-only"]} }
package devsecops.license_policy

default denied := {"GPL-3.0-only", "GPL-3.0-or-later", "AGPL-3.0-only", "AGPL-3.0-or-later", "SSPL-1.0"}

denied := {l | some l in input.config.denied_licenses} if {
	input.config.denied_licenses != null
}

deny contains msg if {
	c := input.components[_]
	denied[c.license]
	msg := sprintf("component %s@%s uses denied license %s — replace it or request an exception approval (ISO A.5.19-A.5.22 reference)", [c.name, c.version, c.license])
}

warn contains msg if {
	c := input.components[_]
	c.license == "NOASSERTION"
	msg := sprintf("component %s@%s has no determined license — manual review required before release", [c.name, c.version])
}
