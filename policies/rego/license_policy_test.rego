package devsecops.license_policy

test_permissive_passes if {
	res := deny with input as {"components": [{"name": "a", "version": "1.0", "license": "MIT"}, {"name": "b", "version": "2.0", "license": "Apache-2.0"}]}
	count(res) == 0
}

test_agpl_denied if {
	res := deny with input as {"components": [{"name": "c", "version": "1.0", "license": "AGPL-3.0-only"}]}
	count(res) == 1
}

test_unknown_license_warns_not_denies if {
	count(deny) == 0 with input as {"components": [{"name": "d", "version": "1.0", "license": "NOASSERTION"}]}
	count(warn) == 1 with input as {"components": [{"name": "d", "version": "1.0", "license": "NOASSERTION"}]}
}
