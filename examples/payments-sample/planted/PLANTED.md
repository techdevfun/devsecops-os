# PLANTED — 4 lỗi gài có chủ đích trong biến thể này

Biến thể `planted/` giống hệt `clean/` ngoại trừ **đúng 4 lỗi** dưới đây.
Mục đích: kiểm chứng bộ gates của devsecops-os chặn đúng chỗ (tiêu chí
nghiệm thu số 2 của blueprint mục 3.2 — mỗi lỗi phải bị chặn ở đúng gate
kỳ vọng, và bản `clean/` không được có chặn oan nào). Việc gates có thực
sự chặn được hay không được kết luận ở M3/M5 khi gates chạy thật; tài liệu
này là *đặc tả kỳ vọng*, không phải kết quả đo.

> **An toàn**: mọi "bí mật" trong biến thể này đều là chuỗi GIẢ dạng ví dụ,
> không dùng được ở bất kỳ đâu. Không bao giờ gài credential thật vào
> workload mẫu.

## Lỗi 1 — Secret giả hardcode trong code

- **Ở đâu**: `backend/config.py` — `PAYMENT_PROVIDER_API_KEY` có giá trị
  dự phòng hardcode dạng `sk_live_FAKENOTREAL…` khi biến môi trường không
  được đặt.
- **Bản chất**: API key của nhà cung cấp thanh toán bị commit thẳng vào
  mã nguồn — rò rỉ theo mọi bản sao của repo.
- **Gate kỳ vọng chặn**: **Gate 1 — Secret scanning** (gitleaks; blueprint
  mục 5.1). Điều kiện chặn mặc định của gate 1: phát hiện secret có vẻ
  thật. Chuỗi gài dùng định dạng khoá live (`sk_live_` + hậu tố chữ-số dài)
  để scanner nhận diện được theo mẫu, nhưng chứa dấu hiệu giả rõ ràng
  (`FAKENOTREAL`) với con người.
- **Cách gỡ**: xoá giá trị dự phòng, chỉ đọc từ môi trường — đúng như
  `clean/backend/config.py`.

## Lỗi 2 — Dependency dính CVE thuộc CISA KEV

- **Ở đâu**: `backend/requirements.txt` — `starlette==1.0.0`.
- **CVE**: **CVE-2026-48710** ("BadHost", GHSA-86qp-5c8j-p5mr) — Starlette
  không kiểm chứng header `Host` khi tái dựng `request.url`, cho phép
  chèn đường dẫn vào phần host và qua mặt các kiểm tra phân quyền dựa trên
  `request.url.path` (HTTP request smuggling / inconsistent interpretation,
  CWE-444).
- **Phạm vi bị ảnh hưởng**: Starlette `>= 0.8.3, < 1.0.1`; bản vá đầu tiên
  là **1.0.1** (phát hành 2026-05-21). Bản gài dùng `1.0.0` — bản cuối cùng
  còn dính lỗi. Bản `clean/` dùng `1.9.0` (đã qua bản vá).
- **Nguồn kiểm chứng** (đã đối chiếu ngày 2026-10-22):
  - CISA Known Exploited Vulnerabilities catalog (bản JSON chính thức,
    catalogVersion 2026.10.21): CVE-2026-48710 có mặt trong catalog,
    `dateAdded: 2026-09-02`, nhà cung cấp/sản phẩm ghi "Kludex / Starlette".
  - GitHub Security Advisory **GHSA-86qp-5c8j-p5mr** (repo Kludex/starlette):
    mô tả cơ chế lỗi và hướng khắc phục "nâng cấp lên bản đã vá".
  - Advisory **X41-2026-002** của X41 D-Sec (đơn vị phát hiện): ghi rõ
    "Confirmed Affected Versions: starlette >= 0.8.3, < 1.0.1" và
    "Confirmed Patched Versions: starlette 1.0.1".
- **Gate kỳ vọng chặn**: **Gate 3 — SCA** (osv-scanner/Trivy quét
  `requirements.txt`/SBOM và báo CVE-2026-48710) kết hợp **Gate 8 — Ưu tiên
  EPSS/CISA KEV**: vì CVE nằm trong KEV, gate 8 xếp nó vào nhóm chặn đầu
  tiên khi hết giai đoạn report-only (đây là cơ chế chống alert fatigue
  của hệ: không chặn theo CVSS thô, chặn theo bằng chứng khai thác thật).
- **Cách gỡ**: nâng `starlette` lên `>= 1.0.1` (bản clean dùng `1.9.0`).

## Lỗi 3 — IaC mở public: security group 0.0.0.0/0

- **Ở đâu**: `infra/main.tf` — hai tài nguyên rule ingress riêng cộng
  thêm gắn vào `aws_security_group.app` (`app_world_app_port` và
  `app_world_ssh`, có chú thích `PLANTED:` ngay trong file): cổng ứng
  dụng (`var.app_port`, mặc định 8000) và cổng SSH (22) mở từ
  `0.0.0.0/0`. (Từ M5, toàn bộ rule của workload dùng dạng tài nguyên
  `aws_vpc_security_group_*_rule` riêng thay cho rule inline — bản chất
  lỗi không đổi.)
- **Bản chất**: task ECS lẽ ra chỉ nhận traffic từ ALB (rule gốc vẫn còn),
  nhưng hai rule gài cho phép bất kỳ địa chỉ Internet nào nối thẳng tới
  task, qua mặt ALB và mọi kiểm soát ở tầng load balancer.
- **Gate kỳ vọng chặn**: **Gate 4 — IaC scanning** (Trivy/Checkov quét
  Terraform + OPA trên plan): rule security group mở `0.0.0.0/0` vào cổng
  quản trị/ứng dụng vi phạm trực tiếp nhóm kiểm soát ranh giới hệ thống
  trong các pack pha 1 (ví dụ SOC 2 CC6.6, PCI DSS yêu cầu 2 trong bảng
  ánh xạ mục 4 của blueprint).
- **Cách gỡ**: xoá hai tài nguyên rule có chú thích `PLANTED:` — file
  trở thành giống hệt `clean/infra/main.tf`.

## Lỗi 4 — Base image cũ đóng băng, có lỗ hổng đã biết

- **Ở đâu**: `Dockerfile` — `FROM python:3.10.4-slim-bullseye`.
- **Bản chất**: ảnh chụp đóng băng tháng 4/2022: CPython 3.10.4 trên Debian
  bullseye với OpenSSL 1.1.1n. Tag cố định theo patch level nghĩa là image
  không bao giờ nhận bản vá: nó mang theo các lỗ hổng đã được sửa ở nơi
  khác, ví dụ CVE-2022-1292 (OpenSSL 1.1.1n, sửa ở 1.1.1o) và
  CVE-2022-45061 (CPython < 3.10.9). Debian bullseye cũng đã hết vòng đời
  hỗ trợ thường. (Hai CVE nêu ở đây thuộc về *thành phần bên trong image*,
  độc lập với CVE-2026-48710 của lỗi 2.)
- **Gate kỳ vọng chặn**: **Gate 5 — Container scanning** (Trivy/Grype quét
  image theo layer): kỳ vọng báo nhiều lỗ hổng mức cao/nghiêm trọng trong
  các gói hệ điều hành và thư viện của image, trái ngược với image hiện
  hành của bản `clean/` (`python:3.13-slim`).
- **Lưu ý trung thực**: ở M1 chưa có lần chạy Trivy/Grype nào trên hai
  image này — danh sách lỗ hổng cụ thể và việc gate 5 chặn ở ngưỡng nào
  là kết quả đo của M3, không được suy diễn trước từ tài liệu này. Đường
  chạy local ở M1 là venv trên Python của máy (xem README của workload),
  không phải build image này.
- **Cách gỡ**: dùng base image hiện hành được duy trì — đúng như
  `clean/Dockerfile`.

## Bảng tóm tắt kỳ vọng cho M3/M5

| # | Lỗi gài | File | Gate kỳ vọng (blueprint mục 5) |
|---|---|---|---|
| 1 | Secret giả hardcode | `backend/config.py` | 1 — Secret scanning |
| 2 | `starlette==1.0.0` dính CVE-2026-48710 (KEV) | `backend/requirements.txt` | 3 — SCA, leo thang bởi 8 — KEV/EPSS |
| 3 | SG mở `0.0.0.0/0` (app + SSH) | `infra/main.tf` | 4 — IaC scanning |
| 4 | Base image `python:3.10.4-slim-bullseye` (2022) | `Dockerfile` | 5 — Container scanning |

Và chiều ngược lại bắt buộc: **bản `clean/` phải qua 100% gates** — một
lần chặn oan trên bản clean cũng tính là không đạt, ngang với một lần sót
lỗi trên bản planted.
