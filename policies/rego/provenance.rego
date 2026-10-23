# provenance — an artefact may only be deployed when it has all
# of: an SBOM, a signature (Cosign), and a provenance attestation
# (SLSA) matching the artefact digest. This policy decides at the
# deployment point (gate 6 produces the data, Kyverno verifyImages
# enforces at the destination — see policies/kyverno/). Serves
# SSDF PS.3 (artefact & provenance protection), ISO A.5.19-A.5.22.
#
# Input:
#   { "artifact": { "name": "payments-sample", "digest": "sha256:abc..." },
#     "sbom": { "format": "CycloneDX", "digest": "sha256:..." } | null,
#     "signature": { "verified": true, "identity": "repo:...:ref:..." } | null,
#     "provenance": { "builder": "...", "digest": "sha256:abc...",
#                     "slsa_level": 2 } | null,
#     "config": {"min_slsa_level": 1} }
package devsecops.provenance

deny contains msg if {
	input.sbom == null
	msg := sprintf("artefact %s is missing its SBOM — not eligible for deployment (SSDF PS.3)", [input.artifact.name])
}

deny contains msg if {
	input.signature == null
	msg := sprintf("artefact %s is not signed (Cosign)", [input.artifact.name])
}

deny contains msg if {
	s := input.signature
	s != null
	s.verified != true
	msg := sprintf("artefact %s has a signature but verification failed (identity: %v)", [input.artifact.name, object.get(s, "identity", "unknown")])
}

deny contains msg if {
	input.provenance == null
	msg := sprintf("artefact %s is missing its provenance attestation (SLSA)", [input.artifact.name])
}

deny contains msg if {
	p := input.provenance
	p != null
	p.digest != input.artifact.digest
	msg := sprintf("provenance of %s does not match the artefact digest (%s != %s)", [input.artifact.name, p.digest, input.artifact.digest])
}

deny contains msg if {
	p := input.provenance
	p != null
	p.slsa_level < input.config.min_slsa_level
	msg := sprintf("provenance of %s is at SLSA level %v, below the minimum %v", [input.artifact.name, p.slsa_level, input.config.min_slsa_level])
}
