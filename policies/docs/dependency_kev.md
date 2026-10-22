# dependency_kev — chặn dependency dính CISA KEV / EPSS cao

- **Mã**: `devsecops.dependency_kev` · **Cơ chế**: OPA/Rego trên danh
  sách dependency + dữ liệu lỗ hổng (OSV) hợp nhất với feed CISA KEV và
  điểm EPSS (FIRST) · **Gate tiêu thụ**: Gate 3 (SCA) sinh dữ liệu,
  Gate 8 (KEV/EPSS) tiêu thụ policy này để quyết định chặn · **Bằng
  chứng**: `vuln-risk-ranking` + `policy-decision`.

**Kiểm soát nào** (ánh xạ tham chiếu): SSDF RV.1/RV.2 (xác định và
phân tích lỗ hổng); PCI DSS 4.0 Yêu cầu 11 (quét lỗ hổng định kỳ) và
6.3 (giữ phần mềm được hỗ trợ/vá); ISO 27001 A.8.8 (quản lý lỗ hổng kỹ
thuật); CPS 234 (quản lý lỗ hổng theo vòng đời).

**Vì sao**: chặn theo CVSS thô tạo alert fatigue khiến đội ngũ tắt
gate (bài học flagship #1). KEV là bằng chứng khai thác thật, EPSS là
xác suất bị khai thác — chặn theo hai tín hiệu này giữ tỉ lệ chặn đúng
cao. Lỗi gài #2 (starlette 1.0.0 / CVE-2026-48710 trong KEV) bị chặn
bởi chính policy này.

**Vi phạm thì sửa thế nào**: nâng dependency tới bản đã vá đầu tiên ghi
trong dữ liệu lỗ hổng (starlette ≥ 1.0.1); nếu chưa nâng được, mở issue
kèm hạn xử lý theo mức KEV/EPSS — pack v1 không có allowlist im lặng
cho CVE thuộc KEV.
