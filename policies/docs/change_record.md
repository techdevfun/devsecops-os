# change_record — release phải có phê duyệt, gate đạt, bằng chứng

- **Mã**: `devsecops.change_record` · **Cơ chế**: OPA/Rego trên hồ sơ
  thay đổi chuẩn hoá (M4 collector sinh từ PR + kết quả gate) · **Gate
  tiêu thụ**: toàn bộ bộ gates (kết quả), thực thi tại bước merge vào
  nhánh bảo vệ / tạo release — lớp quyết định cuối trước phát hành ·
  **Bằng chứng**: `change-record`.

**Kiểm soát nào** (ánh xạ tham chiếu): ISO 27001 A.8.32 (quản lý thay
đổi) và A.8.9 (quản lý cấu hình); PCI DSS 4.0 Yêu cầu 6.5 (quản lý
thay đổi phần mềm); SOC 2 CC8.1 (thay đổi được phê duyệt và kiểm thử
trước khi triển khai); CPS 234 (duy trì kiểm soát có hệ thống).

**Vì sao**: ba hàng khung khác nhau cùng đòi một thứ — thay đổi vào
môi trường quan trọng phải truy được ai duyệt, kiểm tra gì đã chạy,
bằng chứng ở đâu. Policy gộp ba đòi hỏi đó thành một quyết định máy
đọc được, gồm cả cấm tự phê duyệt (self-approval) — điểm hay bị bỏ qua
khi chỉ dựa vào cài đặt mặc định của nền tảng.

**Vi phạm thì sửa thế nào**: xin review từ người khác tác giả; chạy
lại/sửa các gate chưa đạt thay vì xin ngoại lệ; nếu buộc phải ngoại
lệ, ghi ngoại lệ có hạn dùng trong hồ sơ — hết hạn policy tự chặn lại.
