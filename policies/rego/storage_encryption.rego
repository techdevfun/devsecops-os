# storage_encryption — mọi kho lưu trữ dữ liệu (S3 bucket, volume, DB)
# phải bật mã hoá khi lưu (encryption at rest) và chặn truy cập công khai.
#
# Input (JSON chuẩn hoá từ Terraform plan):
#   { "storage": [ { "address": "aws_s3_bucket.artefacts",
#                    "type": "aws_s3_bucket",
#                    "encryption_enabled": true,
#                    "public_access_blocked": true } ] }
package devsecops.storage_encryption

deny contains msg if {
	s := input.storage[_]
	s.encryption_enabled != true
	msg := sprintf("%s (%s) chua bat ma hoa khi luu (encryption at rest) — NIST CSF PR.DS, PCI DSS Req 3 tham chieu", [s.address, s.type])
}

deny contains msg if {
	s := input.storage[_]
	s.type == "aws_s3_bucket"
	s.public_access_blocked != true
	msg := sprintf("%s (aws_s3_bucket) chua chan truy cap cong khai toan dien (public access block)", [s.address])
}
