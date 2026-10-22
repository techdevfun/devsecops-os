# CI security gates — M3 (đã cài đặt, kiểm chứng cục bộ)

Bộ 10 gates của mục 5 blueprint đã được cài đặt ở M3 và kiểm chứng
bằng công cụ thật trên cả hai biến thể workload mẫu. Kết quả đo:
`gates/verification/results.md` (log thô: `gates/verification/logs/`).

## Cấu trúc — vì sao gates nằm ở hai nơi

GitHub chỉ nạp reusable workflow từ `.github/workflows/` của repo,
nên 11 file YAML (10 gate + `all-gates.yml`) nằm ở đó. Nhưng mã chạy
thật của mỗi gate là MỘT script `gates/local/gate-NN.sh` — workflow
chỉ checkout, tải công cụ đã ghim (phiên bản + sha256 trong
`gates/local/fetch_tools.sh`) rồi gọi đúng script đó. Nhờ vậy bản chạy
trên GitHub và bản chạy kiểm chứng cục bộ là **cùng một mã**, không
có chuyện "CI một đằng, máy dev một nẻo".

| Thư mục/file | Vai trò |
|---|---|
| `.github/workflows/gate-NN-*.yml` | Reusable workflow (`workflow_call`) cho từng gate |
| `.github/workflows/all-gates.yml` | Workflow tổng: chạy cả 10 gate trên một biến thể workload + gom artefact (collector thật là M4) |
| `gates/local/gate-NN.sh` | Mã chạy thật của gate (dùng chung CI + cục bộ) |
| `gates/local/lib.sh` | Thư viện chung: định danh lần chạy, ghi evidence record, gọi OPA |
| `gates/local/adapters/*.py` | Bộ chuyển đổi đầu ra scanner → input của policy pack / evidence record |
| `gates/local/fetch_tools.sh` | Tải công cụ đã ghim phiên bản + kiểm sha256 |
| `gates/verification/` | Runner + kết quả kiểm chứng cục bộ M3 |

## 10 gates ↔ công cụ ↔ policy ↔ bằng chứng

| # | Gate | Công cụ thật (phiên bản khi kiểm chứng) | Policy của pack (M2) | Bằng chứng sinh ra |
|---|---|---|---|---|
| 1 | Secret scanning | gitleaks 8.30.1 | `devsecops.secret_findings` | SARIF + `policy-decision` |
| 2 | SAST | Semgrep 1.182.1 (p/security-audit, p/python) — report-only | — (chưa có policy ở pha 1) | SARIF + tóm tắt theo severity |
| 3 | SCA | osv-scanner 2.7.0 | (phát hiện; quyết định ở gate 8) | SARIF + bản chuẩn hoá lỗ hổng |
| 4 | IaC scanning | Terraform 1.17.0 (validate) + Trivy 0.76.1 (config) + OPA 1.21.3 trên parse HCL2 của conftest 0.71.1 | `network_exposure`, `storage_encryption`, `iam_least_privilege` | SARIF + `policy-decision` ×3 + `iac-assessment` |
| 5 | Container scanning | Trivy 0.76.1 (image) + đối chiếu KEV | `devsecops.base_image` | SARIF + `policy-decision` + tóm tắt CVE |
| 6 | SBOM + attestation | Syft 1.55.0 + Cosign 3.1.4 | `devsecops.provenance` | `sbom` (CycloneDX, đã ký bundle) + `provenance-attestation` + `policy-decision` |
| 7 | License compliance | Đọc từ SBOM CycloneDX | `devsecops.license_policy` | `policy-decision` |
| 8 | EPSS/CISA KEV | Feed CISA KEV + FIRST EPSS tải tại thời điểm chạy | `devsecops.dependency_kev` | `vuln-risk-ranking` + `policy-decision` |
| 9 | Vệ sinh pipeline | Quét chính `.github/workflows/` của repo | `devsecops.pipeline_policy` | `pipeline-config-verification` + `policy-decision` |
| 10 | AI PR Review Gate | Flagship #1 — **chưa publish** | (khi bật: `pr-review-report`) | Tắt: chỉ ghi nhận trạng thái, không sinh evidence |

Gate 10 **mặc định TẮT** ở pha 1 (input `enabled`/`enable_ai_pr_review`
mặc định `false`, biến `ENABLE_AI_PR_REVIEW` khi chạy cục bộ): wiring ở
tầng PR đã có, workflow tổng chạy hoàn chỉnh khi nó tắt, và nghiệm thu
pha 1 không phụ thuộc vào nó. Chỉ bật khi flagship #1 qua cổng publish
riêng của nó.

## Cách chạy cục bộ

```bash
# chạy toàn bộ kiểm chứng (cả hai biến thể, có đo thời gian):
bash gates/verification/run_verification.sh

# chạy một gate lẻ:
REPO_ROOT=$PWD WORKLOAD=$PWD/examples/payments-sample/planted \
OUT_ROOT=$PWD/evidence/output/thu COMMIT_SHA=thu-1 \
  bash gates/local/gate-01.sh
```

Mã thoát của gate: `0` = qua (không chặn), `1` = **bị chặn** theo điều
kiện chặn mặc định của blueprint, `2` = lỗi hạ tầng/quét không hoàn
tất (kèm `scan-error.json` — không bao giờ ngụy trang thành "sạch").
Bằng chứng của mỗi lần chạy nằm ở `evidence/output/<lần chạy>/gate-NN-*/`
đúng hợp đồng thư mục của M4 (xem `evidence/README.md`); M4 collector
sẽ thu các `*.record.json` + artefact tại đó.

## Nguyên tắc vận hành (thừa hưởng bài học của flagship #1)

- Mặc định **report-only khi mới lắp** tại tổ chức áp dụng (cấu hình
  `gates.<id>.mode` trong `docs/examples/devsecops-os.sample.yml`);
  chỉ chuyển sang chặn sau khi chạy hiệu chuẩn trên lịch sử của chính
  repo đó. Riêng lần kiểm chứng M3 dùng điều kiện chặn mặc định của
  blueprint để chứng minh khả năng chặn.
- Mọi lần quét bị cắt ngắn/lỗi dữ liệu phải **báo ồn ào** — gate 3 thử
  lại khi osv-scanner lỗi phân giải và thoát 2 nếu vẫn không quét
  được dependency nào; gate 5 ghi `scan-error.json` khi trivy lỗi.
- Mỗi gate có đường tắt có kiểm soát và mọi lần dùng đường tắt đều ghi
  lại trong bằng chứng (allowlist của gate 1 có hạn dùng; exception của
  pack có ngày hết hạn trong policy `change_record`).
- Evidence collector là "gate cuối" (M4): thiếu bằng chứng bắt buộc
  của các gate đã bật → lần chạy bị gắn cờ `evidence incomplete`.

## Giới hạn đã biết (đo được ở M3, không che giấu)

- **Terraform plan JSON chưa sinh được**: workload mẫu có lỗi vòng
  tham chiếu thật giữa hai security group (`aws_security_group.alb` ↔
  `aws_security_group.app` tham chiếu lẫn nhau trong rule inline) nên
  cả `terraform validate` lẫn `plan` đều lỗi trên CẢ HAI biến thể.
  Gate 4 vì thế dùng parse HCL2 chuẩn (`conftest parse`) làm đầu vào
  cho 3 policy hạ tầng — thay cho bộ trích regex của harness M2 —
  và ghi kết quả validate riêng trong bằng chứng. Muốn có plan JSON
  phải refactor workload sang `aws_vpc_security_group_*_rule` riêng:
  để lại cho M5 quyết (xem `gates/verification/results.md`).
- Trên GitHub Actions mỗi job chạy độc lập: gate 7/8 tự sinh lại
  SBOM/quét lại dependency khi không thấy đầu ra của gate 6/3 trong
  cùng job (chạy cục bộ theo chuỗi thì dùng lại đầu ra có sẵn).
- Gate 6 ở cục bộ đạt SLSA Build L1 (builder thường + khoá ký tạm
  thời); mức cao hơn nhờ `slsa-github-generator` chỉ có khi chạy trên
  GitHub Actions — triển khai ở M5.
- Kyverno (2 policy phía cluster của pack) không thuộc 10 gate CI này;
  chúng áp ở tầng admission của cluster theo tài liệu kiến trúc.
