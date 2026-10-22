package devsecops.dependency_kev

kev_vuln := {"id": "CVE-2026-48710", "package": "starlette", "affected": ">=0.8.3,<1.0.1", "fixed": "1.0.1", "in_kev": true, "epss": 0.42}

test_planted_starlette_100_denied if {
	count(deny) == 1 with input as {
		"dependencies": [{"name": "starlette", "version": "1.0.0", "ecosystem": "pip"}],
		"vulnerabilities": [kev_vuln],
		"config": {"epss_threshold": 0.5},
	}
}

test_clean_starlette_190_passes if {
	count(deny) == 0 with input as {
		"dependencies": [{"name": "starlette", "version": "1.9.0", "ecosystem": "pip"}],
		"vulnerabilities": [kev_vuln],
		"config": {"epss_threshold": 0.5},
	}
}

test_first_fixed_version_passes if {
	count(deny) == 0 with input as {
		"dependencies": [{"name": "starlette", "version": "1.0.1", "ecosystem": "pip"}],
		"vulnerabilities": [kev_vuln],
		"config": {"epss_threshold": 0.5},
	}
}

test_high_epss_non_kev_denied if {
	count(deny) == 1 with input as {
		"dependencies": [{"name": "libx", "version": "2.0.0", "ecosystem": "pip"}],
		"vulnerabilities": [{"id": "CVE-2026-0001", "package": "libx", "affected": ">=2.0.0,<2.1.0", "fixed": "2.1.0", "in_kev": false, "epss": 0.9}],
		"config": {"epss_threshold": 0.5},
	}
}

test_low_epss_non_kev_passes if {
	count(deny) == 0 with input as {
		"dependencies": [{"name": "libx", "version": "2.0.0", "ecosystem": "pip"}],
		"vulnerabilities": [{"id": "CVE-2026-0002", "package": "libx", "affected": ">=2.0.0,<2.1.0", "fixed": "2.1.0", "in_kev": false, "epss": 0.01}],
		"config": {"epss_threshold": 0.5},
	}
}
