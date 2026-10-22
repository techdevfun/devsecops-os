package devsecops.storage_encryption

test_encrypted_and_private_passes if {
	count(deny) == 0 with input as {"storage": [
		{"address": "aws_s3_bucket.artefacts", "type": "aws_s3_bucket", "encryption_enabled": true, "public_access_blocked": true},
	]}
}

test_unencrypted_denied if {
	count(deny) == 1 with input as {"storage": [
		{"address": "aws_s3_bucket.data", "type": "aws_s3_bucket", "encryption_enabled": false, "public_access_blocked": true},
	]}
}

test_public_bucket_denied if {
	count(deny) == 1 with input as {"storage": [
		{"address": "aws_s3_bucket.data", "type": "aws_s3_bucket", "encryption_enabled": true, "public_access_blocked": false},
	]}
}
