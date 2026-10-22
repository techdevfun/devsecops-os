# evidence_completeness — bundle thiếu bằng chứng bắt buộc là chưa xong

- **Mã**: `devsecops.evidence_completeness` · **Cơ chế**: OPA/Rego trên
  manifest của evidence bundle · **Gate tiêu thụ**: "gate cuối"
  (blueprint 5.2) do M4 collector chạy sau mọi gate khác · **Bằng
  chứng**: `control-evidence-index` (chỉ mục theo kỳ) — policy này là
  bộ đánh giá độ đầy đủ của chính hệ bằng chứng.

**Kiểm soát nào** (ánh xạ tham chiếu): ISO 27001 A.8.15–A.8.16 (ghi
log và giám sát hoạt động — bằng chứng log CI bắt buộc có mặt, có
hash); APRA CPS 234 (duy trì và kiểm tra kiểm soát có hệ thống —
bằng chứng kiểm soát liên tục theo kỳ); SOC 2 CC7.2 ở mức tham chiếu.

**Vì sao**: pipeline chặn lỗi mà không để lại bằng chứng thì mùa kiểm
toán vẫn phải làm lại bằng tay — đúng nỗi đau mà flagship này tồn tại
để xoá. "Evidence incomplete" phải là trạng thái nhìn thấy được, không
phải im lặng coi như đạt.

**Vi phạm thì sửa thế nào**: bật gate đang thiếu loại bằng chứng
tương ứng; sửa collector nếu bằng chứng có sinh ra nhưng không vào
bundle; không sửa tay manifest — bundle phải tái sinh từ lần chạy.
