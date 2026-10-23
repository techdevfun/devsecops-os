# pipeline_policy — combines three controls on the CI pipeline itself:
#  (1) Pipeline hygiene (gate 9): workflows must declare explicit
#      minimal `permissions`, must NOT use write-all; third-party
#      actions must be pinned to a full commit SHA (lesson R9 of
#      flagship #1).
#  (2) Secure build configuration (SSDF PW.9): every gate-running
#      workflow must enable all required gates of the active pack.
#  (3) Workload identity (SOC 2 CC6.1 / PCI Req 8 reference): jobs
#      that touch the cloud must use OIDC (id-token: write + a declared audience),
#      long-lived cloud secrets as static variable names in workflows are forbidden.
#
# Input (normalised JSON from workflow YAML):
#   { "workflows": [ { "file": ".github/workflows/ci.yml",
#       "permissions": {"contents": "read"},
#       "uses": ["actions/checkout@<40-hex-sha>"],
#       "gates_enabled": ["secret","sast","sca","iac"],
#       "jobs": [ {"name": "deploy", "oidc": true,
#                  "static_cloud_secrets": []} ] } ],
#     "config": {"required_gates": ["secret","sast","sca","iac","kev"]} }
package devsecops.pipeline_policy

deny contains msg if {
	w := input.workflows[_]
	w.permissions == "write-all"
	msg := sprintf("workflow %s uses permissions write-all — declare minimal per-job permissions (SSDF PW.9, SOC 2 CC6.1)", [w.file])
}

deny contains msg if {
	w := input.workflows[_]
	w.permissions == null
	msg := sprintf("workflow %s does not declare permissions — platform defaults may over-grant; declare minimal permissions (gate 9)", [w.file])
}

deny contains msg if {
	w := input.workflows[_]
	u := w.uses[_]
	not pinned_to_sha(u)
	msg := sprintf("workflow %s uses action %q not pinned to a full commit SHA — supply-chain risk (gate 9)", [w.file, u])
}

deny contains msg if {
	w := input.workflows[_]
	g := input.config.required_gates[_]
	not g in w.gates_enabled
	msg := sprintf("workflow %s is missing required gate %q of the active pack (ISO A.8.25-A.8.28, SSDF PW.9)", [w.file, g])
}

deny contains msg if {
	w := input.workflows[_]
	j := w.jobs[_]
	s := j.static_cloud_secrets[_]
	msg := sprintf("workflow %s job %s uses static cloud secret %q — switch to OIDC federation (PCI Req 8/SOC 2 CC6.1 reference, identity-first)", [w.file, j.name, s])
}

deny contains msg if {
	w := input.workflows[_]
	j := w.jobs[_]
	j.cloud_access == true
	j.oidc != true
	msg := sprintf("workflow %s job %s accesses the cloud but does not use OIDC — long-lived credentials are forbidden in CI", [w.file, j.name])
}

# "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683" → true
pinned_to_sha(u) if {
	parts := split(u, "@")
	count(parts) == 2
	regex.match(`^[0-9a-f]{40}$`, parts[1])
}

# Internal actions of the organisation itself, declared in config, are exempt from SHA pinning.
pinned_to_sha(u) if {
	some prefix in input.config.internal_action_prefixes
	startswith(u, prefix)
}
