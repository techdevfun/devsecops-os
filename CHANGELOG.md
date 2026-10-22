# Nhật ký thay đổi (CHANGELOG)

Mọi thay đổi đáng chú ý của devsecops-os được ghi tại đây. Định dạng
theo [Keep a Changelog](https://keepachangelog.com/), phiên bản theo
[SemVer](https://semver.org/). Dự án **chưa phát hành công khai**
— các mục dưới đây là mốc hoàn thiện cục bộ của pha 1, phục vụ hồ sơ
phát hành (`release/RELEASE-DOSSIER.md`).

## [Chưa phát hành] — vòng hoàn thiện cục bộ M5-A3 (2026-10-22)

### Thêm

- **Bộ sinh bằng chứng quyết định/định kỳ** `evidence/generators.py`
  (chỉ thư viện chuẩn): sinh 4 loại record còn thiếu của bản đồ pha 1
  từ dữ liệu thật — `change-record` (từ kết quả các cổng của một lần
  chạy, kèm quyết định policy `change_record` chạy thật bằng OPA),
  `drift-report` (chênh lệch cấu hình IaC so với baseline đã khai,
  kèm quyết định `drift_control`), `access-review-report` (rà soát
  quyền của chính các workflow trong cây) và
  `config-baseline-report` (đánh giá các policy IaC trên cấu hình
  hiện tại). Baseline drift được khai tại
  `evidence/baselines/payments-sample.tf-normalized.json`.
- Collector (`evidence/bundle_tool.py` 1.2.0): quét thêm thư mục
  `supplementary-records/` của lần chạy (kiểm schema như record của
  cổng) và **tự phát hành record `ci-log`** — đóng gói toàn bộ log
  của lần chạy thành artefact zip tất định kèm SHA-256; bước verify
  đối chiếu chéo hash khai trong record với artefact trong bundle.
  Truy vết bản đồ pha 1 đạt **13/14 hàng đầy đủ** (còn `row-05` một
  phần vì cổng 10 tắt theo thiết kế).
- Kiểm thử: `evidence/tests/test_generators.py` (15 test: bộ sinh +
  mở rộng collector) và `gates/local/tests/test_adapters.py`
  (13 test cho các adapter của cổng, gồm chuỗi SBOM + ký Cosign thật
  trên workload tối thiểu).
- `CONTRIBUTING.md`, mẫu issue trong `.github/ISSUE_TEMPLATE/`,
  mục xử lý sự cố lộ secret trong `SECURITY.md`.
- Bản nháp bài giới thiệu dev.to (`release/devto-article-draft.md`)
  — chưa đăng, chờ cổng phát hành.

### Sửa

- `examples/checkout-sample/.github/workflows/ci.yml`: sửa tham
  chiếu reusable workflow cổng 10 thành đúng tên file
  `gate-10-ai-pr-review.yml`.
- Truy vết trong `evidence/README.md` và nội dung landing cập nhật
  theo trạng thái 13/14.

## [M5-A2] — 2026-10-22

### Thêm

- Ký Cosign cho bundle bằng chứng (`collect --sign`): chữ ký trên
  `bundle.sha256`, verify bắt buộc khi manifest đã khai chữ ký
  (fail-closed, kể cả khi thiếu binary cosign ở máy kiểm chứng).
- Unit test cho `bundle_tool.py` (`evidence/tests/`, 8 test gồm các
  ca giả mạo: sửa record + tính lại hash vẫn bị bắt ở lớp chữ ký).

## [M5-A] — 2026-10-22

### Thêm

- Golden path: `templates/api-service/` và workload dogfood
  `examples/checkout-sample/` dựng từ chính template — chạy trọn
  pipeline cục bộ (10 cổng + bundle + verify) xanh ngay lần đầu.
- Demo (`release/demo/`), nội dung landing, quét rủi ro trước phát
  hành, hồ sơ phát hành `release/RELEASE-DOSSIER.md`.

### Sửa

- Terraform workload mẫu: tách rule inline của security group thành
  tài nguyên `aws_vpc_security_group_*_rule` riêng — hết vòng tham
  chiếu, `terraform validate` đạt trên cả hai biến thể.
- Bỏ job gom artefact dùng `merge-multiple: true` trong workflow CI
  (ghi đè các record trùng tên giữa các cổng).

## [M4] — 2026-10-22

### Thêm

- Tự động hoá bằng chứng: `evidence/bundle_tool.py` — thu thập
  record từ một lần chạy, kiểm schema M2, đóng bundle kèm manifest
  SHA-256 và kiểm chứng một lệnh (`evidence/verify_bundle.py`).

## [M3] — 2026-10-22

### Thêm

- 10 cổng CI dạng reusable workflow, dùng chung script với bản chạy
  cục bộ (`gates/local/gate-NN.sh`) — CI và cục bộ là cùng một mã.
  Cổng 10 (AI PR review) mặc định TẮT; pipeline chính hoàn thành khi
  cổng 10 tắt.

## [M2] — 2026-10-22

### Thêm

- Gói policy v1: 14 policy (12 Rego + 2 Kyverno) và 14 schema bằng
  chứng phủ đủ 14 hàng bản đồ kiểm soát pha 1; bộ kiểm chứng
  `opa test` 48 test và harness đối chiếu workload mẫu.

## [M1] — 2026-10-22

### Thêm

- Khung repo: tài liệu kiến trúc tham chiếu, cấu hình mẫu tĩnh,
  workload demo `examples/payments-sample/` (biến thể sạch + biến
  thể cài 4 lỗi có chủ đích, mỗi lỗi ánh xạ tới cổng sẽ chặn nó).
