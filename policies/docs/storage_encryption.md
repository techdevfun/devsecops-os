# storage_encryption — encryption at rest + block public access

- **Code**: `devsecops.storage_encryption` · **Mechanism**: OPA/Rego over the
  Terraform plan · **Consuming gate**: Gate 4 (IaC scanning) · **Evidence**:
  `iac-assessment` + `config-baseline-report`.

**Which control** (reference mapping): NIST CSF PR.DS (protect data
at rest); PCI DSS 4.0 Requirement 3 (protect stored cardholder data —
at the level of the encryption principle); ISO 27001 A.8.24 (use of cryptography); SOC 2
CC6.1.

**Why**: an unencrypted or publicly open bucket/volume is the most common group of cloud
data leaks; this system's own evidence/artifacts also live in a bucket so they must be private-by-construction.

**How to fix a violation**: add
`aws_s3_bucket_server_side_encryption_configuration` (AES256 or KMS)
and `aws_s3_bucket_public_access_block` with all 4 options enabled; for other storage
types, enable the service's default encryption flag and record it in the IaC.
