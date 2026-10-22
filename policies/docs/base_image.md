# base_image — base image EOL/đóng băng hoặc tag `latest` thì chặn

- **Mã**: `devsecops.base_image` · **Cơ chế**: OPA/Rego trên danh sách
  FROM của Dockerfile + dữ liệu EOL đóng gói trong pack · **Gate tiêu
  thụ**: Gate 5 (container scanning) ở bước tiền kiểm (trước khi quét
  CVE bằng Trivy/Grype) · **Bằng chứng**: `policy-decision` + báo cáo
  quét của gate 5 (`sarif-report`).

**Kiểm soát nào** (ánh xạ tham chiếu): PCI DSS 4.0 Yêu cầu 6.3 (chỉ
dùng phần mềm còn được hỗ trợ) và Yêu cầu 11 (quét định kỳ); SSDF
PS.3/PW.9; ISO 27001 A.8.8/A.8.9.

**Vì sao**: base image ghim ở patch-level cũ (lỗi gài #4:
`python:3.10.4-slim-bullseye`, ảnh chụp 4/2022) không bao giờ nhận bản
vá — mang theo CVE đã sửa ở nơi khác (OpenSSL 1.1.1n, CPython <3.10.9)
và hệ điều hành nền đã hết hỗ trợ. Scanner báo CVE; policy này chặn
mẫu rủi ro cấu trúc ngay cả khi chưa quét.

**Vi phạm thì sửa thế nào**: chuyển sang dòng image còn được duy trì
(bản clean dùng `python:3.13-slim`), ghim tag cụ thể hoặc digest; cập
nhật dữ liệu EOL trong pack khi nhà phát hành công bố lịch EOL mới.
