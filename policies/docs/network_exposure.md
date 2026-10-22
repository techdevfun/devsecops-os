# network_exposure — không mở ingress từ Internet tới cổng nội bộ

- **Mã**: `devsecops.network_exposure` · **Cơ chế**: OPA/Rego trên dữ liệu
  security group chuẩn hoá (từ Terraform plan ở M3; bộ trích xuất HCL ở
  M2) · **Gate tiêu thụ**: Gate 4 (IaC scanning) ở bước đánh giá plan,
  trước apply · **Bằng chứng sinh ra**: `iac-assessment` + `policy-decision`.

**Kiểm soát nào** (ánh xạ tham chiếu): NIST CSF PR.AC/PR.DS và SSDF
PW.9 (cấu hình an toàn); PCI DSS 4.0 Yêu cầu 1/2 (quy tắc tường lửa,
không cấu hình mặc định nguy hiểm); SOC 2 CC6.6 (ranh giới hệ thống);
ISO 27001 A.8.20–A.8.22 (an ninh mạng, phân đoạn mạng).

**Vì sao**: mở cổng ứng dụng/quản trị ra `0.0.0.0/0` là qua mặt toàn bộ
kiểm soát ở tầng load balancer/WAF — đúng lỗi gài #3 của payments-sample
(SG của task mở cổng 8000 và 22 ra Internet).

**Vi phạm thì sửa thế nào**: xoá rule `cidr_blocks = ["0.0.0.0/0"]` trên
security group nội bộ; nhận traffic qua SG của ALB
(`security_groups = [aws_security_group.alb.id]`) hoặc giới hạn CIDR nội
bộ của tổ chức. Ngoại lệ duy nhất của pack: SG khai báo `public_web: true`
được mở đúng cổng 443.
