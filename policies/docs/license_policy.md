# license_policy — license cấm trong SBOM thì chặn

- **Mã**: `devsecops.license_policy` · **Cơ chế**: OPA/Rego trên danh
  sách component + license đọc từ SBOM · **Gate tiêu thụ**: Gate 7
  (license compliance), chạy sau Gate 6 (SBOM) · **Bằng chứng**:
  `sbom` + `policy-decision`.

**Kiểm soát nào** (ánh xạ tham chiếu): ISO 27001 A.5.19–A.5.22 (quan
hệ nhà cung cấp — điều kiện sử dụng phần mềm bên thứ ba); SSDF PS.3/
PW.4 (bảo vệ và tái sử dụng phần mềm an toàn); SOC 2 CC6.1 (kiểm soát
thành phần đưa vào hệ thống) ở mức tham chiếu.

**Vì sao**: license copyleft mạnh (AGPL/GPL) lọt vào sản phẩm phân phối
có thể kéo theo nghĩa vụ công bố mã nguồn ngoài ý muốn; license không
xác định được (NOASSERTION) là điểm mù pháp lý phải rà soát tay.

**Vi phạm thì sửa thế nào**: thay component bằng phương án license
cho phép, hoặc xin phê duyệt ngoại lệ của tổ chức và ghi vào cấu hình
`denied_licenses`/allowlist của repo; license NOASSERTION thì xác minh
thủ công từ trang dự án gốc rồi khai báo lại trong SBOM.
