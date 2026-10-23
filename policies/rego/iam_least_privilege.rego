# iam_least_privilege — no IAM policy may grant Action "*" or a
# service wildcard ("s3:*"...) on Resource "*", and no full-admin
# managed policy (AdministratorAccess) may be attached to a workload.
#
# Input (normalised JSON):
#   { "iam_policies": [ { "name": "...", "attached_to": "...",
#       "statements": [ {"effect": "Allow", "actions": ["s3:GetObject"],
#                        "resources": ["arn:..."]} ] } ],
#     "managed_policy_attachments": [ {"role": "...", "policy_arn": "..."} ] }
package devsecops.iam_least_privilege

deny contains msg if {
	p := input.iam_policies[_]
	st := p.statements[_]
	st.effect == "Allow"
	action := st.actions[_]
	is_wildcard_action(action)
	some res in st.resources
	res == "*"
	msg := sprintf("IAM policy %q grants wildcard action %q on Resource \"*\" — violates least privilege (SOC 2 CC6.1, PCI DSS Req 7/8 reference, ISO A.5.15)", [p.name, action])
}

deny contains msg if {
	a := input.managed_policy_attachments[_]
	endswith(a.policy_arn, "AdministratorAccess")
	msg := sprintf("role %q has the AdministratorAccess policy attached — forbidden for workloads (least privilege)", [a.role])
}

is_wildcard_action(a) if a == "*"
is_wildcard_action(a) if endswith(a, ":*")
