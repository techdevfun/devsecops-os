package devsecops.iam_least_privilege

test_scoped_policy_passes if {
	count(deny) == 0 with input as {
		"iam_policies": [{"name": "task", "statements": [{"effect": "Allow", "actions": ["s3:GetObject"], "resources": ["arn:aws:s3:::b/*"]}]}],
		"managed_policy_attachments": [{"role": "exec", "policy_arn": "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"}],
	}
}

test_wildcard_on_star_denied if {
	count(deny) == 1 with input as {
		"iam_policies": [{"name": "bad", "statements": [{"effect": "Allow", "actions": ["s3:*"], "resources": ["*"]}]}],
		"managed_policy_attachments": [],
	}
}

test_admin_attachment_denied if {
	count(deny) == 1 with input as {
		"iam_policies": [],
		"managed_policy_attachments": [{"role": "dev", "policy_arn": "arn:aws:iam::aws:policy/AdministratorAccess"}],
	}
}
