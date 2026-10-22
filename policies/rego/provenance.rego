# provenance — artefact chỉ được triển khai khi có đủ: SBOM, chữ ký
# (Cosign), và provenance attestation (SLSA) khớp digest của artefact.
# Policy quyết định tại điểm triển khai (gate 6 sinh dữ liệu, Kyverno
# verifyImages thực thi ở tầng đích — xem policies/kyverno/).
# Phục vụ SSDF PS.3 (bảo vệ artefact & provenance), ISO A.5.19–A.5.22.
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
	msg := sprintf("artefact %s thieu SBOM — khong du dieu kien trien khai (SSDF PS.3)", [input.artifact.name])
}

deny contains msg if {
	input.signature == null
	msg := sprintf("artefact %s chua duoc ky (Cosign)", [input.artifact.name])
}

deny contains msg if {
	s := input.signature
	s != null
	s.verified != true
	msg := sprintf("artefact %s co chu ky nhung xac minh that bai (identity: %v)", [input.artifact.name, object.get(s, "identity", "unknown")])
}

deny contains msg if {
	input.provenance == null
	msg := sprintf("artefact %s thieu provenance attestation (SLSA)", [input.artifact.name])
}

deny contains msg if {
	p := input.provenance
	p != null
	p.digest != input.artifact.digest
	msg := sprintf("provenance cua %s khong khop digest artefact (%s != %s)", [input.artifact.name, p.digest, input.artifact.digest])
}

deny contains msg if {
	p := input.provenance
	p != null
	p.slsa_level < input.config.min_slsa_level
	msg := sprintf("provenance cua %s dat SLSA level %v, thap hon muc toi thieu %v", [input.artifact.name, p.slsa_level, input.config.min_slsa_level])
}
