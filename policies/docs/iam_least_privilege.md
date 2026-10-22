# iam_least_privilege — không wildcard trên `*`, không AdministratorAccess

- **Mã**: `devsecops.iam_least_privilege` · **Cơ chế**: OPA/Rego trên
  IAM policy chuẩn hoá từ Terraform plan · **Gate tiêu thụ**: Gate 4
  (IaC) + Gate 9 (vệ sinh pipeline, cho quyền token workflow) · **Bằng
  chứng**: `access-review-report` + `policy-decision`.

**Kiểm soát nào** (ánh xạ tham chiếu): SOC 2 CC6.1 (truy cập logic theo
least privilege); PCI DSS 4.0 Yêu cầu 7 (hạn chế truy cập theo nhu cầu
công việc) và Yêu cầu 8 (định danh duy nhất); ISO 27001 A.5.15 (kiểm
soát truy cập); CPS 234 (kiểm soát bảo mật tương xứng với mối đe doạ).

**Vì sao**: policy `Action: *` trên `Resource: *` biến một credential bị
lộ thành toàn quyền tài khoản; đây là lỗi cấu hình IAM bị khai thác
nhiều nhất và cũng là lỗi dễ bắt nhất bằng policy.

**Vi phạm thì sửa thế nào**: thu hẹp action theo đúng API mà workload
gọi (tra CloudTrail/access advisor), gắn resource ARN cụ thể; không
gắn managed policy quản trị cho role của workload — tạo policy riêng
tối thiểu và ghi lý do trong IaC.
