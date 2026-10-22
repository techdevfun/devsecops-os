package devsecops.provenance

good := {
	"artifact": {"name": "payments-sample", "digest": "sha256:aaa"},
	"sbom": {"format": "CycloneDX", "digest": "sha256:bbb"},
	"signature": {"verified": true, "identity": "repo:org/app:ref:refs/heads/main"},
	"provenance": {"builder": "slsa-github-generator", "digest": "sha256:aaa", "slsa_level": 2},
	"config": {"min_slsa_level": 1},
}

test_complete_provenance_passes if {
	count(deny) == 0 with input as good
}

test_missing_sbom_denied if {
	count(deny) == 1 with input as object.union(good, {"sbom": null})
}

test_unverified_signature_denied if {
	count(deny) == 1 with input as object.union(good, {"signature": {"verified": false, "identity": "unknown"}})
}

test_digest_mismatch_denied if {
	count(deny) == 1 with input as object.union(good, {"provenance": {"builder": "x", "digest": "sha256:zzz", "slsa_level": 2}})
}
