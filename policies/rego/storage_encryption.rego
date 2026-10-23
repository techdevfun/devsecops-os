# storage_encryption — every data store (S3 bucket, volume, DB)
# must enable encryption at rest and block public access.
#
# Input (normalised JSON from a Terraform plan):
#   { "storage": [ { "address": "aws_s3_bucket.artefacts",
#                    "type": "aws_s3_bucket",
#                    "encryption_enabled": true,
#                    "public_access_blocked": true } ] }
package devsecops.storage_encryption

deny contains msg if {
	s := input.storage[_]
	s.encryption_enabled != true
	msg := sprintf("%s (%s) does not have encryption at rest enabled — NIST CSF PR.DS, PCI DSS Req 3 reference", [s.address, s.type])
}

deny contains msg if {
	s := input.storage[_]
	s.type == "aws_s3_bucket"
	s.public_access_blocked != true
	msg := sprintf("%s (aws_s3_bucket) does not fully block public access (public access block)", [s.address])
}
