# storage_encryption — mã hoá khi lưu + chặn truy cập công khai

- **Mã**: `devsecops.storage_encryption` · **Cơ chế**: OPA/Rego trên
  Terraform plan · **Gate tiêu thụ**: Gate 4 (IaC scanning) · **Bằng
  chứng**: `iac-assessment` + `config-baseline-report`.

**Kiểm soát nào** (ánh xạ tham chiếu): NIST CSF PR.DS (bảo vệ dữ liệu
khi lưu); PCI DSS 4.0 Yêu cầu 3 (bảo vệ dữ liệu chủ thẻ được lưu trữ —
ở mức nguyên tắc mã hoá); ISO 27001 A.8.24 (sử dụng mật mã); SOC 2
CC6.1.

**Vì sao**: bucket/volume không mã hoá hoặc mở công khai là nhóm rò rỉ
dữ liệu phổ biến nhất ở cloud; bằng chứng/artifacts của chính hệ này
cũng nằm trong bucket nên phải private-by-construction.

**Vi phạm thì sửa thế nào**: thêm
`aws_s3_bucket_server_side_encryption_configuration` (AES256 hoặc KMS)
và `aws_s3_bucket_public_access_block` bật cả 4 tuỳ chọn; với loại lưu
trữ khác, bật cờ mã hoá mặc định của dịch vụ và ghi lại trong IaC.
