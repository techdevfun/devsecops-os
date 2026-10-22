# devsecops-os

**Lớp điều hành (operating layer) mã nguồn mở, vendor-neutral cho DevSecOps +
AI SecOps trong tổ chức bị quản chế** (ngân hàng, tài chính, bảo hiểm): kiến
trúc tham chiếu chạy được, policy-as-code packs ánh xạ sẵn tới các khung kiểm
soát (ISO 27001:2022, NIST CSF 2.0/SSDF, PCI DSS 4.0, APRA CPS 234, APRA
CPS 230, SOC 2), bộ CI security gates tái dùng, và tự động hoá thu thập bằng
chứng kiểm toán. Nó **tích hợp với** GitHub/GitLab/Harness chứ không thay thế
họ, và không phải thêm một scanner nữa.

> ## Trạng thái: PHA 1 — ĐÃ KIỂM CHỨNG TRÊN GITHUB ACTIONS THẬT
>
> Các mốc M1–M5 đã xong: policy pack chạy được (14 policy + harness
> 34/34), 10 CI gates chạy thật trên workload mẫu với ma trận kết quả
> đầy đủ (bản sạch qua hết, bản gài lỗi bị chặn đúng 4 gate), evidence
> bundle đóng gói + kiểm chứng một lệnh đã kiểm chứng cả chiều xuôi lẫn
> chiều phá hoại (sửa 1 byte → FAIL), golden path đã có template và đã
> dogfood một service thứ hai. **Số đo trên GitHub Actions thật** (repo
> này, nhánh main): workflow tổng chạy 3 lần — 54, 66, 58 giây, **trung
> vị 58 giây** (trần nghiệm thu 15 phút); biến thể gài lỗi bị chặn ở
> đúng các gate 1, 4, 5, 8 trên CI; golden path dựng service từ template
> và CI xanh **ngay lần chạy đầu**, tổng dựng + CI 5 phút 42 giây (trần
> 30 phút); evidence bundle của mỗi lần chạy CI được **ký keyless bằng
> Cosign qua OIDC** và tự xác minh ngay trong job. Hồ sơ phát hành chi
> tiết: [`release/RELEASE-DOSSIER.md`](release/RELEASE-DOSSIER.md).
> Không dùng repo này để tuyên bố tuân thủ bất kỳ khung kiểm soát nào:
> các ánh xạ trong tài liệu là **ánh xạ tham chiếu phục vụ chuẩn bị
> kiểm toán, không phải chứng nhận tuân thủ**.

## Demo (từ lần chạy thật)

![Demo: gates chạy thật trên hai biến thể + kiểm chứng evidence bundle](release/demo/demo-terminal.gif)

Bản ghi terminal dạng chữ và script tái hiện cùng lần chạy:
[`release/demo/demo-transcript.txt`](release/demo/demo-transcript.txt),
[`release/demo/replay.sh`](release/demo/replay.sh). Demo dựng từ output
thật của bộ gates + kiểm chứng bundle trên hai biến thể của workload mẫu
— không cảnh dàn dựng.

## Ai đau, hệ này làm gì

- **CISO / đội platform của tổ chức bị quản chế** đau ở ba chỗ: (1) mỗi đội
  tự lắp pipeline bảo mật một kiểu, không có "đường chuẩn" để đi theo là đạt
  kiểm soát; (2) chính sách tuân thủ nằm trong tài liệu Word/PDF, đến mùa
  kiểm toán mới dịch thủ công thành cấu hình và đi gom bằng chứng khắp nơi;
  (3) kết quả quét của các vendor (Harness, GitHub Advanced Security, Snyk…)
  nằm trong hệ kín của từng vendor — lớp quản trị + bằng chứng xuyên suốt
  theo khung quản chế cụ thể (CPS 234/230, PCI DSS…) vẫn phải tự xây.
- Hệ này làm đúng phần còn thiếu đó: **policy-as-code nằm trong repo của
  chính tổ chức** (không có server của bên thứ ba giữ dữ liệu), **CI gates**
  chặn ở các điểm đã hiệu chuẩn, và **bằng chứng kiểm toán sinh tự động** từ
  chính các lần chạy pipeline — pipeline không chỉ chặn lỗi, nó tự chứng
  minh nó đã chặn.

## Nguyên tắc thiết kế (tóm tắt — chi tiết ở `docs/architecture.md`)

1. **Vendor-neutral theo cấu trúc**: scanner/connector giao tiếp qua định
   dạng mở (SARIF, CycloneDX/SPDX, Sigstore, SLSA) — thay công cụ quét không
   được phép làm gãy policy hay bằng chứng.
2. **Identity-first**: không credential tĩnh dài hạn trong pipeline; con
   người qua SSO/OIDC, workload qua OIDC federation nhận token ngắn hạn,
   artefact được ký (Cosign) kèm SLSA provenance.
3. **Policy ở trung tâm, thực thi ở nhiều điểm**: cùng một ý định kiểm soát
   biên dịch xuống OPA/Rego, Kyverno và GitHub Actions gate.
4. **Bằng chứng là sản phẩm phụ tự động của vận hành**, không phải việc làm
   thêm mùa kiểm toán.
5. **Không dữ liệu nào rời hạ tầng người dùng**: mọi thành phần chạy trong
   CI/runner/cluster của chính tổ chức.

## Cấu trúc repo

| Thư mục | Nội dung | Mốc |
|---|---|---|
| `docs/` | Kiến trúc tham chiếu + hướng dẫn (gồm golden paths) | M1 ✓ |
| `examples/payments-sample/` | Workload mẫu hai biến thể (sạch / gài lỗi) để kiểm chứng gates | M1 ✓ |
| `examples/checkout-sample/` | Service thứ hai, dựng từ golden path (dogfood) | M5 ✓ |
| `policies/` | Policy packs ánh xạ khung kiểm soát (14 policy, harness 34/34) | M2 ✓ |
| `gates/` | Bộ 10 CI security gates dạng reusable workflows + script cục bộ | M3 ✓ |
| `evidence/` | Evidence collector + bundle có manifest SHA-256 + verify một lệnh | M4 ✓ |
| `templates/` | Golden-path service templates (`api-service`) | M5 ✓ |
| `release/` | Hồ sơ phát hành, biên bản dogfood, demo, nội dung landing | M5 |

## Chạy thử ngay (cục bộ, cùng script mà CI gọi)

```bash
# 1) Tải bộ công cụ đã ghim phiên bản + SHA-256
bash gates/local/fetch_tools.sh            # TOOLS_DIR mặc định: ~/workspace/tools

# 2) Chạy toàn bộ kiểm chứng trên hai biến thể workload mẫu
bash gates/verification/run_verification.sh all
#    -> ma trận kết quả: gates/verification/results.md

# 3) Đóng + kiểm chứng evidence bundle của một lần chạy (một lệnh verify)
python3 evidence/bundle_tool.py collect evidence/output/local-clean \
    --run-id local-clean --out-dir evidence/bundles/local-clean
python3 evidence/verify_bundle.py evidence/bundles/local-clean
```

Kỳ vọng (đã kiểm chứng tại M3–M5): bản `clean` qua cả 10 gate; bản
`planted` bị chặn đúng ở gate 1 (secret), gate 4 (IaC — security group mở
Internet), gate 5 (base image hết hạn) và gate 8 (dependency thuộc CISA
KEV), không chặn nhầm ở gate nào khác.

## Workload mẫu

`examples/payments-sample/` chứa một ứng dụng thanh toán tối giản (API
backend Python/Starlette, frontend tĩnh, Terraform AWS, Dockerfile, manifest
Kubernetes) ở hai biến thể song song:

- `clean/` — cấu hình đúng chuẩn, kỳ vọng qua mọi gate.
- `planted/` — gài đúng 4 lỗi có chủ đích (secret giả, dependency dính
  CVE-2026-48710 thuộc CISA KEV, security group mở 0.0.0.0/0, base image cũ
  đóng băng từ 2022) để kiểm chứng gate chặn đúng chỗ. Chi tiết từng lỗi và
  gate kỳ vọng tương ứng: `examples/payments-sample/planted/PLANTED.md`.

## Tài liệu

- [Kiến trúc tham chiếu](docs/architecture.md)
- [Định danh & attestation (identity-first)](docs/identity-and-access.md)
- [Golden paths](docs/golden-paths.md) + [template](templates/README.md)
- [Đa môi trường: cloud + on-prem](docs/environments.md)
- [Điểm tích hợp GitHub / Harness / GitLab](docs/integration-points.md)
- [Ma trận kết quả kiểm chứng gates](gates/verification/results.md)
- [Hồ sơ phát hành + bảng điểm hội đồng](release/RELEASE-DOSSIER.md)

## Ranh giới trung thực

- Không tuyên bố "bank-grade", "NAB-grade" hay "được tổ chức nào sử dụng" —
  đây là blueprint + reference implementation chạy được trên workload mẫu.
- Đối thủ thương mại (Harness, GitHub Advanced Security, Snyk) hơn hẳn hệ
  này về độ sâu quét, hỗ trợ enterprise và chứng chỉ của chính vendor; hệ
  này không tuyên bố thay thế họ (xem phân tích đối thủ trong blueprint của
  dự án).
- Gate AI PR Review Gate (flagship #1 của nhà máy) là một gate *tuỳ chọn*,
  mặc định **tắt** trong pha 1, và chỉ được bật khi flagship #1 qua cổng
  publish riêng của nó.

## License

MIT — xem `LICENSE`.
