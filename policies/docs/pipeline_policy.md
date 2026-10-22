# pipeline_policy — vệ sinh pipeline + build an toàn + OIDC

- **Mã**: `devsecops.pipeline_policy` · **Cơ chế**: OPA/Rego trên
  workflow đã chuẩn hoá (từ YAML của GitHub Actions) · **Gate tiêu
  thụ**: Gate 9 (vệ sinh pipeline) cho phần quyền/ghim SHA/OIDC; Gate 2
  (SAST) + toàn bộ bộ gates cho phần "đủ gate bắt buộc" (hàng ISO
  A.8.25–A.8.28 / SSDF PW.7–PW.9) · **Bằng chứng**:
  `pipeline-config-verification` + `policy-decision` (+ `pr-review-report`
  khi gate 10 được bật).

**Kiểm soát nào** (ánh xạ tham chiếu): SSDF PW.9 (cấu hình môi trường
build an toàn) và PW.7 (review mã — qua yêu cầu gate review/SAST có
mặt); ISO 27001 A.8.25–A.8.28 (vòng đời phát triển an toàn); SOC 2
CC6.1/CC7.1; PCI DSS 4.0 Yêu cầu 6/8 (không credential tĩnh trong CI);
CPS 234 (kiểm soát tương xứng).

**Vì sao**: pipeline là đích tấn công supply-chain có giá trị cao nhất
(bài học R9 của flagship #1 về action bị chiếm quyền): action bên thứ
ba không ghim SHA có thể bị thay mã dưới cùng một tag; `write-all` và
secret cloud dài hạn biến một workflow bị lỗi thành toàn quyền hạ
tầng. OIDC federation thay credential tĩnh bằng token ngắn hạn theo
đúng repo/branch — nguyên tắc identity-first của kiến trúc.

**Vi phạm thì sửa thế nào**: khai báo `permissions` tối thiểu từng
job; ghim mọi action bên thứ ba theo full commit SHA (kèm comment ghi
phiên bản); job chạm cloud chuyển sang `id-token: write` + role ARN
theo OIDC; bật đủ các gate trong `required_gates` của pack.
