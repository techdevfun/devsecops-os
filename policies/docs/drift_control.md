# drift_control — drift trọng yếu quá hạn xử lý thì chặn kỳ báo cáo

- **Mã**: `devsecops.drift_control` · **Cơ chế**: OPA/Rego trên báo cáo
  drift (job so IaC khai báo với trạng thái thực, chạy theo lịch) ·
  **Gate tiêu thụ**: Gate 4 (IaC scanning) mở rộng dạng job theo lịch
  (scheduled drift check) · **Bằng chứng**: `drift-report`.

**Kiểm soát nào** (ánh xạ tham chiếu): SOC 2 CC7.1 (cấu hình chuẩn)
và CC7.2 (phát hiện thay đổi trái phép/không khai báo); ISO 27001
A.8.9 (quản lý cấu hình) ở mức tham chiếu.

**Vì sao**: IaC đúng tại thời điểm merge chưa đủ — thay đổi tay trên
console làm hệ thống lệch dần khỏi trạng thái đã duyệt, và chính các
lệch kiểu security group/IAM là cửa ngõ sự cố. Drift phải có chủ, có
ticket, có hạn — không phải một danh sách để nhìn.

**Vi phạm thì sửa thế nào**: hoặc đưa trạng thái thực về đúng IaC
(áp lại plan đã duyệt), hoặc khai báo thay đổi vào IaC qua PR như một
thay đổi thường; acknowledge bắt buộc kèm ticket và vẫn bị chặn nếu
quá SLA cấu hình (mặc định 7 ngày cho nhóm network/iam/storage).
