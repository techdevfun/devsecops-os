# Đóng góp cho devsecops-os

Cảm ơn bạn quan tâm tới dự án. devsecops-os là lớp vận hành DevSecOps
mã nguồn mở, trung lập nhà cung cấp: kiến trúc tham chiếu + gói
policy-as-code + 10 cổng CI + tự động hoá bằng chứng kiểm toán. Mọi
đóng góp đều đi qua cùng một chuẩn kiểm chứng mà dự án áp lên chính
mình: **không tuyên bố điều chưa chạy thật**.

## Trước khi bắt đầu

- Đọc `README.md` (kiến trúc, 10 cổng, cách chạy cục bộ) và
  `docs/` (kiến trúc tham chiếu, bản đồ kiểm soát).
- Vấn đề bảo mật: KHÔNG mở issue công khai — xem `SECURITY.md`.

## Môi trường phát triển

Các công cụ của pipeline được ghim phiên bản và đặt trong
`~/workspace/tools` ở máy phát triển của dự án (xem
`gates/local/README.md` để biết danh sách + phiên bản): OPA,
conftest, gitleaks, Semgrep, osv-scanner, Trivy, Terraform, Syft,
Cosign, Kyverno CLI. Toàn bộ kiểm thử chạy được **cục bộ, không cần
tài khoản cloud**:

```bash
# Kiểm thử gói policy (OPA + harness + Kyverno)
~/workspace/tools/opa test policies/rego/
python3 policies/harness/run_checks.py
bash policies/harness/kyverno_check.sh

# Kiểm thử bằng chứng (collector + bộ sinh)
python3 -m unittest discover -s evidence/tests

# Kiểm thử adapter của các cổng
python3 -m unittest discover -s gates/local/tests
```

## Quy tắc đóng góp

1. **Policy mới/sửa phải có đủ 4 thứ**: file Rego (hoặc Kyverno),
   schema bằng chứng tương ứng trong `policies/evidence-schemas/`,
   fixture pass + fail trong `policies/fixtures/`, và mục tài liệu
   trong `policies/docs/`. Thiếu một trong bốn, PR chưa sẵn sàng.
2. **Mọi thay đổi hành vi phải có test chạy đỏ trước, xanh sau**
   (red-first): test mới phải fail trên code cũ và pass trên code
   mới. Ghi lệnh chạy + kết quả vào mô tả PR.
3. **Không nới lỏng cổng để "cho qua"**: không hạ severity, không
   thêm ngoại lệ không hạn, không tắt gate trong `all-gates.yml`
   nếu không có quyết định ghi trong `CHANGELOG.md` kèm lý do.
4. **Bằng chứng phải sinh từ dữ liệu thật**: record mẫu trong tài
   liệu/test phải do chính công cụ của dự án sinh ra trên dữ liệu
   trong cây — không viết tay record "trông giống thật".
5. **Không commit secret, khoá riêng hay dữ liệu khách hàng** —
   kể cả trong fixture. Fixture chứa secret giả phải ghi rõ là giả
   (ví dụ hậu tố `FAKENOTREAL`) và chỉ nằm trong biến thể `planted/`.
6. Cập nhật `CHANGELOG.md` cho mọi thay đổi người dùng nhìn thấy
   được (policy, cổng, schema, hành vi collector).

## Quy trình PR

1. Fork/nhánh từ `main`, một PR một mục đích.
2. Chạy đủ 5 bộ kiểm thử ở trên; dán kết quả vào PR.
3. PR vào nhánh được bảo vệ cần ít nhất 1 phê duyệt của người khác
   tác giả (đây cũng là điều kiện policy `change_record` kiểm tra
   trong bằng chứng thay đổi).
4. CI phải xanh toàn bộ 10 cổng áp dụng cho thay đổi đó; cổng chặn
   (blocking) không được bỏ qua bằng nhãn.

## Phong cách

- Tài liệu: tiếng Việt có dấu cho tài liệu vận hành nội bộ, tiếng
  Anh cho README/schema/tên kỹ thuật; giữ nhất quán với file lân cận.
- Code Python trong `evidence/` và `gates/local/adapters/` chỉ dùng
  thư viện chuẩn (ngoại trừ adapter đã khai báo phụ thuộc, ví dụ
  `workflow_input.py` dùng PyYAML) — để công cụ chạy được ở mọi
  runner không cần bước cài đặt thêm.
- Rego: viết theo cú pháp OPA v1 (`import rego.v1` không cần; dùng
  `if`/`contains` như các policy hiện có trong `policies/rego/`).
