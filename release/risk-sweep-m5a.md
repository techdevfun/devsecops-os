# Quét rủi ro trước phát hành — devsecops-os (M5-A, LUẬT ĐỨNG 5)

Ngày quét: 2026-10-22. Phạm vi: toàn bộ cây repo tại thời điểm cuối
M5-A. Phương pháp: gitleaks (filesystem scan toàn cây), rà thủ công theo
lớp rủi ro, đối chiếu tài liệu với bằng chứng chạy thật.

*Cập nhật M5-A2 (2026-10-22): mục R1 đã thay đổi trạng thái nhờ ký
Cosign cho evidence bundle — xem dòng R1 ở mục 6 và câu giới hạn ở
mục 4 đã sửa. Phần còn lại của bản quét giữ nguyên.*

## 1. Secret trong cây / lịch sử

- Gitleaks quét toàn cây: 16 finding, phân loại như sau:
  - **1 finding trong mã nguồn**: secret Stripe giả trong
    `examples/payments-sample/planted/backend/config.py` — giá trị giả
    được cài CÓ CHỦ ĐÍCH làm lỗi kiểm chứng số 1 (ghi rõ trong
    PLANTED.md), không phải credential thật. Các bản sao của nó trong
    đầu ra của gate 1 và trong bundle của bản planted là hệ quả đúng
    thiết kế (gate phát hiện và ghi lại).
  - **6 finding `private-key`**: các file `cosign.key` trong thư mục đầu
    ra của các lần chạy gate 6 (`evidence/output/**`) — khoá tạm sinh
    theo từng lần chạy, thư mục đã gitignore. **ĐÃ XOÁ cả 3 file tại
    chỗ**; công cụ của gate tự sinh khoá mới mỗi lần chạy nên việc xoá
    không ảnh hưởng gì. Kiểm tra lại: không còn file `.key`/`.pem`/
    chuỗi `PRIVATE KEY` nào trong cây và trong các bundle.
  - **6 finding `generic-api-key`** trong `trivy-image.json`: đầu ra của
    Trivy khi quét base image công khai (báo cáo của scanner về nội
    dung image), không phải secret của dự án; nằm trong thư mục đầu ra
    đã gitignore.
- **Lịch sử**: cây hiện tại không phải git repository (chưa có `.git`)
  nên không tồn tại lịch sử commit để quét — khi tạo repo ở M5-B, lần
  commit đầu tiên chính là cây đã quét này.
- Bundle chỉ chứa `cosign.pub` (khoá công khai) — đúng thiết kế.

## 2. File rác / hiện vật tạm — ĐÃ DỌN TẠI CHỖ

- Xoá 3 `cosign.key` (như trên) và 3 thư mục `__pycache__` (gồm 1 thư
  mục do lần chạy smoke của chính M5-A tạo trong checkout-sample).
- `.gitignore` đã bao phủ đúng các lớp: `*.key`/`*.pem`,
  `__pycache__/`, `.terraform/`, tfstate, `evidence/output/` (gồm cả
  tf-sandbox và log của từng lần chạy), `evidence/bundles/`,
  `gates/verification/logs/`. Ngược lại, `gates/verification/results.*`
  và bản ghi demo trong `release/demo/` được giữ có chủ đích làm bằng
  chứng phát hành.
- Thư mục đầu ra còn ~24MB (`evidence/output`) + ~5.9MB
  (`evidence/bundles`) — toàn bộ đều gitignored, không đi vào repo khi
  phát hành; giữ lại tại chỗ làm bằng chứng kiểm chứng.

## 3. Giấy phép

- Repo có `LICENSE` (MIT) và `SECURITY.md` (bổ sung tại M5-A — trước
  đó thiếu).
- Mã trong repo là mã gốc của dự án; các công cụ ngoài (gitleaks,
  Semgrep, Trivy, Syft, Cosign, OPA/conftest, Kyverno, osv-scanner,
  Starlette…) chỉ được *gọi* khi chạy, không nhúng mã của chúng vào
  repo; tên công cụ được ghi công trong tài liệu. Không có asset
  (ảnh/font/mã) của bên thứ ba được sao chép vào cây — font trong GIF
  demo là DejaVu Sans Mono của hệ thống, chỉ dùng lúc dựng ảnh.
- Gate 7 (license compliance) áp lên workload: PASS cả hai biến thể.

## 4. Khẳng định quá mức so với bằng chứng — ĐÃ SỬA TẠI CHỖ

- README gốc còn banner "đang ở mốc M1, chưa có policy/gate/evidence"
  — sai sự thật sau M2–M4. **Đã viết lại** banner trạng thái + bảng cấu
  trúc + mục chạy thử theo đúng trạng thái M5-A, kèm nhãn UNVERIFIED
  cho phần GitHub Actions.
- `examples/payments-sample/README.md` còn ghi "chưa được kiểm chứng
  bằng terraform" — **đã sửa** (fmt + validate PASS từ M3/M5; plan vẫn
  cần AWS API thật, ghi rõ).
- `docs/golden-paths.md` còn header "trạng thái M1" — **đã cập nhật**
  trạng thái M5-A, giữ nguyên phần thiết kế gốc bên dưới.
- `gates/verification/render_results_md.py` ghi cứng câu "lỗi cycle
  security-group" — **đã sửa** để câu chữ đi theo kết quả validate thật;
  results.md đã render lại: validate=PASS cả hai biến thể.
- Rà từ ngữ rủi ro toàn cây ("bank-grade", "chứng nhận tuân thủ", "đảm
  bảo"…): chỉ còn xuất hiện trong câu phủ định/ràng buộc trung thực.
- Giới hạn đã biết vẫn được công khai trong README/landing: truy vết
  bằng chứng 6/14 đầy đủ (4 một phần, 4 chưa có — đều là bằng chứng
  dạng quyết định/định kỳ cần dữ liệu vận hành thật), chữ ký bundle
  mới ở mức khoá cục bộ tạm theo lần chạy (chưa keyless OIDC/Rekor —
  cập nhật M5-A2), terraform plan cần AWS API thật.

## 5. Phụ thuộc chưa ghim phiên bản

- Công cụ của gates: ghim phiên bản + SHA-256 trong
  `gates/local/fetch_tools.sh` (kiểm tra hash khi tải).
- GitHub Actions trong mọi workflow: ghim full commit SHA (gate 9 thực
  thi — PASS sau khi gỡ job `collect-gate-outputs` ở M5-A).
- Dependency của workload/template: ghim chính xác bằng `==` trong
  requirements.txt. Python tooling nội bộ chỉ dùng thư viện chuẩn.
- Terraform provider: `versions.tf` khoá `hashicorp/aws ~> 5.x` (khoảng
  tương thích, không ghim patch) — mức độ **thấp**, chấp nhận được cho
  workload tham chiếu; ghi nhận tại đây.

## 6. Còn tồn (không sửa tại chỗ được)

| # | Hạng mục | Mức độ | Xử lý |
|---|---|---|---|
| R1 | ~~Bundle chưa ký mật mã (chỉ toàn vẹn SHA-256)~~ — ĐÃ GIẢM NHẸ TẠI M5-A2: bundle đóng bằng `--sign` được ký Cosign trên `bundle.sha256` (khoá tạm theo lần chạy, sinh ngoài cây và huỷ ngay; verify một lệnh kiểm thêm chữ ký; đã kiểm chứng: ký → PASS, sửa 1 byte → FAIL, thay chữ ký của bundle khác → FAIL, sửa kèm tính lại hash nhất quán → FAIL ở lớp chữ ký). Phần còn lại: danh tính chữ ký chưa gắn OIDC và không có transparency log (Rekor) — neo tin cậy đầy đủ cần đối chiếu vân tay khoá công khai với bản ghi ngoài bundle, hoặc ký keyless trên CI | Thấp (phần còn lại) | Phần còn lại thuộc M5-B (ký keyless/OIDC trên CI) — M5-B đang đóng băng theo quyết định chủ sở hữu 2026-10-22; giới hạn hiện tại đã công khai trong `evidence/README.md` + landing. |
| R2 | ~~4/14 hàng truy vết bằng chứng chưa tự động sinh (quyết định/định kỳ)~~ — ĐÃ ĐÓNG TẠI M5-A3: cả 4 loại (`change-record`, `drift-report`, `access-review-report`, `config-baseline-report`) + `ci-log` đều có bộ sinh tự động chạy trên dữ liệu thật của lần chạy/cây (`evidence/generators.py` + collector phát hành ci-log kèm đối chiếu chéo hash ở verify); chứng minh bằng bundle `local-clean-m5a3` verify PASS, truy vết **13/14 đầy đủ**. Phần còn lại (không phải lỗi kỹ thuật): giá trị kiểm toán đầy đủ của các record quyết định vẫn cần dữ liệu vận hành thật (phê duyệt PR thật — record change-record cục bộ bị policy DENY đúng vì chưa có phê duyệt) và hàng row-05 (`pr-review-report`) vẫn một phần vì gate 10 TẮT theo thiết kế pha 1 | Thấp (phần còn lại) | Đã công khai trong `evidence/README.md` + landing (bản cập nhật M5-A3). |
| R6 (mới, M5-A3) | Quét gitleaks toàn cây cuối vòng M5-A3: sau khi xoá 2 khoá `cosign.key` sót trong thư mục đầu ra các lần chạy cũ và sửa chuỗi secret mẫu trong fixture test (tránh mẫu `sk_live_…` dù là giả), 12 finding còn lại đều thuộc diện đã biết: secret giả cài sẵn của biến thể `planted/` (kèm báo cáo gate 1 của chính nó trong artefact) và nhiễu generic-api-key trong JSON đầu ra của Trivy ở thư mục lần chạy (đã gitignore toàn bộ `evidence/output/`) | Thấp | Không còn finding nào trong mã nguồn/tài liệu của cây. Việc chuyển gate 6 sang keyless thuộc R5. |
| R3 | terraform plan JSON chưa sinh được tại chỗ (cần AWS API thật) | Thấp | Gate đã thiết kế quanh conftest parse + validate; ghi rõ lý do thật. |
| R4 | Thời gian workflow trên GitHub Actions + golden path trên CI thật chưa đo | Cao (với cổng phát hành) | UNVERIFIED — thuộc M5-B sau khi chủ sở hữu duyệt tạo repo. |
| R5 | Khoá Cosign tạm của gate 6 nằm trong thư mục đầu ra mỗi lần chạy (dù gitignore) | Thấp | Đã xoá bản hiện có; về lâu dài nên chuyển sang keyless/OIDC — ghi nhận, không chặn pha 1. |

Kết luận quét: không còn rủi ro nào thuộc diện chặn phát hành ở lớp
cục bộ ngoài các UNVERIFIED của M5-B (R4) — cổng phát hành quyết bởi
bảng điểm hội đồng trong `RELEASE-DOSSIER.md`.
