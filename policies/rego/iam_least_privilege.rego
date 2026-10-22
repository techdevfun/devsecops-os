# iam_least_privilege — không policy IAM nào được cấp Action "*" hoặc
# service wildcard ("s3:*"...) trên Resource "*", và không gắn policy
# quản trị toàn quyền (AdministratorAccess) cho workload.
#
# Input (JSON chuẩn hoá):
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
	msg := sprintf("IAM policy %q cap action wildcard %q tren Resource \"*\" — vi pham least privilege (SOC 2 CC6.1, PCI DSS Req 7/8 tham chieu, ISO A.5.15)", [p.name, action])
}

deny contains msg if {
	a := input.managed_policy_attachments[_]
	endswith(a.policy_arn, "AdministratorAccess")
	msg := sprintf("role %q gan policy AdministratorAccess — cam cho workload (least privilege)", [a.role])
}

is_wildcard_action(a) if a == "*"
is_wildcard_action(a) if endswith(a, ":*")
