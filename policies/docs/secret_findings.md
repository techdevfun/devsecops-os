# secret_findings — finding secret chưa allowlist thì chặn

- **Mã**: `devsecops.secret_findings` · **Cơ chế**: policy quyết định
  (Rego) trên kết quả quét của scanner — **lý do không viết lại scanner**:
  phát hiện secret là việc của gitleaks (gate 1) với tập rule được cộng
  đồng duy trì; pack chỉ giữ lớp quyết định (chặn / allowlist có hạn) để
  thay scanner không đổi chính sách · **Gate tiêu thụ**: Gate 1 (secret
  scanning) ở bước quyết định sau quét · **Bằng chứng**: `sarif-report`
  (kết quả quét) + `policy-decision`.

**Kiểm soát nào** (ánh xạ tham chiếu): ISO 27001 A.8.28 (coding an
toàn — không nhúng bí mật vào mã); SSDF PW.6/PW.9 (cấu hình môi trường
build an toàn); PCI DSS 4.0 Yêu cầu 6.2/8 (không hardcode credential);
SOC 2 CC6.1/CC7.1.

**Vì sao**: secret đã commit thì coi như đã lộ (mọi bản sao của repo đều
mang theo) — lỗi gài #1 của payments-sample (khoá `sk_live_` dự phòng
trong `config.py`).

**Vi phạm thì sửa thế nào**: xoá secret khỏi code (đọc từ biến môi
trường/secret manager như bản clean), **xoay vòng credential ngay** vì
xoá khỏi HEAD không xoá khỏi lịch sử git; nếu là dương tính giả có lý
do, xin allowlist kèm hạn dùng — hết hạn là chặn lại.
