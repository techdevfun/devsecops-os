package devsecops.network_exposure

test_clean_workload_passes if {
	count(deny) == 0 with input as {"security_groups": [
		{"name": "app", "ingress": [{"from_port": 8000, "to_port": 8000, "protocol": "tcp", "cidr_blocks": [], "security_groups": ["aws_security_group.alb"]}]},
		{"name": "alb", "public_web": false, "ingress": [{"from_port": 443, "to_port": 443, "protocol": "tcp", "cidr_blocks": ["10.0.0.0/8"]}]},
	]}
}

test_planted_flaw3_denied if {
	count(deny) == 2 with input as {"security_groups": [
		{"name": "app", "ingress": [
			{"from_port": 8000, "to_port": 8000, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"]},
			{"from_port": 22, "to_port": 22, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"]},
		]},
	]}
}

test_public_web_443_exception if {
	count(deny) == 0 with input as {"security_groups": [
		{"name": "web", "public_web": true, "ingress": [{"from_port": 443, "to_port": 443, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"]}]},
	]}
}
