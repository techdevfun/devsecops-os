# Policy pack v1 — bản đồ pack (M2)

Thư mục này chứa **policy pack v1** của devsecops-os: mọi hàng đánh dấu
"pha 1" trong bảng ánh xạ mục 4 của blueprint đều có đủ ba thứ:

1. **mã policy chạy được** — OPA/Rego (`rego/`), Kyverno (`kyverno/`),
   hoặc policy quyết định trên đầu ra của scanner khi bản chất kiểm
   soát không phải policy (ghi rõ lý do trong tài liệu của policy đó);
2. **khai báo cơ chế thực thi** — gate nào trong mục 5 của blueprint
   tiêu thụ policy và ở bước nào (wiring workflow thuộc M3);
3. **định nghĩa loại bằng chứng** — schema JSON tại
   `evidence-schemas/` (14 loại), để M4 collector thu thập theo đúng
   hợp đồng trong `../evidence/README.md`.

Mỗi policy có tài liệu riêng trong `docs/`: kiểm soát nào, vì sao,
vi phạm thì sửa thế nào (tiêu chí nghiệm thu 6 của blueprint).

> **Mọi ánh xạ trong pack là ánh xạ tham chiếu phục vụ chuẩn bị kiểm
> toán, không phải chứng nhận tuân thủ** dưới bất kỳ khung nào. Metadata
> pack, nguồn đối chiếu và ngày rà soát: `pack.yaml` (quá 12 tháng
> chưa rà soát → pack bị đánh dấu "stale", rủi ro R4 của blueprint).

## Kiểm chứng cục bộ (chạy lại được)

```bash
# OPA: unit test từng policy + fixture tĩnh + đối chiếu planted-vs-clean
python3 policies/harness/run_checks.py
# Kyverno: cần kyverno CLI (~/workspace/tools/kyverno hoặc PATH)
bash policies/harness/kyverno_check.sh
```

- `harness/build_workload_fixtures.py` sinh input từ **file thật** của
  `examples/payments-sample` (SG trong `main.tf`, secret trong
  `config.py`, pin trong `requirements.txt`, FROM trong `Dockerfile`)
  — đối chiếu bắt buộc của M2: 4 lỗi gài của biến thể planted phải cho
  verdict **deny**, biến thể clean phải **pass**.
- Kết quả đo thật được ghi trong báo cáo mốc M2 (không ghi trong file
  này để tránh tài liệu đi trước số đo).

## Bản đồ pack v1: hàng pha 1 → policy → gate → bằng chứng

Gate đánh số theo mục 5 của blueprint: 1 secret · 2 SAST · 3 SCA ·
4 IaC · 5 container · 6 SBOM+attestation · 7 license · 8 KEV/EPSS ·
9 vệ sinh pipeline · 10 AI PR Review Gate (mặc định TẮT ở pha 1) ·
cuối: evidence collector (M4).

| # | Hàng blueprint (khung — nhóm kiểm soát) | Policy (mã/file) | Gate tiêu thụ & bước | Loại bằng chứng |
|---|---|---|---|---|
| 1 | ISO 27001 A.8.25–A.8.28 — vòng đời phát triển an toàn, coding an toàn | `devsecops.pipeline_policy` (`rego/pipeline_policy.rego`, phần "đủ gate bắt buộc") + `devsecops.secret_findings` | Gates 1/2/3/4 sinh dữ liệu tại PR; pipeline_policy quyết định đủ-gate ở bước tổng hợp | `sarif-report`, `pipeline-config-verification`, `policy-decision` |
| 2 | ISO 27001 A.8.9 + A.8.32 — quản lý cấu hình, quản lý thay đổi | `devsecops.change_record` + Kyverno `workload-baseline` | Lớp quyết định khi merge vào nhánh bảo vệ; Kyverno thực thi cấu hình ở admission | `change-record`, `policy-decision` |
| 3 | ISO 27001 A.8.15–A.8.16 — ghi log & giám sát | `devsecops.evidence_completeness` (bắt buộc loại `ci-log` có hash) | "Gate cuối" — M4 collector đánh giá manifest bundle sau mọi gate | `ci-log`, `control-evidence-index` |
| 4 | ISO 27001 A.5.19–A.5.22 — quan hệ nhà cung cấp | `devsecops.dependency_kev` + `devsecops.license_policy` (trên SBOM) | Gate 3/8 (lỗ hổng) và Gate 7 (license) sau khi Gate 6 sinh SBOM | `sbom`, `vuln-risk-ranking`, `policy-decision` |
| 5 | NIST SSDF PW.7 + PW.9 — review code, cấu hình build an toàn | `devsecops.pipeline_policy` (toàn bộ: permissions, ghim SHA, OIDC, đủ gate review/SAST) | Gate 9 + Gate 2 tại PR; Gate 10 cắm cùng vị trí khi flagship #1 qua cổng publish của nó | `pipeline-config-verification`, `pr-review-report` (chỉ khi gate 10 bật) |
| 6 | NIST SSDF PS.3 + RV.1–RV.2 — bảo vệ artefact/provenance, phân tích lỗ hổng | `devsecops.provenance` + `devsecops.dependency_kev` + Kyverno `verify-image-signatures` | Gate 6 sinh SBOM/ký/provenance; provenance.rego quyết định trước triển khai; Kyverno chặn ở admission đích | `provenance-attestation`, `sbom`, `vuln-risk-ranking` |
| 7 | NIST CSF PR.DS + ID.RA — bảo vệ dữ liệu, đánh giá rủi ro IaC | `devsecops.network_exposure` + `devsecops.storage_encryption` | Gate 4 — OPA trên Terraform plan trước apply | `iac-assessment`, `policy-decision` |
| 8 | PCI DSS 4.0 Req 6 — phát triển an toàn + quản lý thay đổi (6.5) | `devsecops.change_record` (gate_results bao quát toàn bộ bộ gates) | Lớp quyết định tại release; mọi gate 1–9 cấp kết quả vào hồ sơ | `change-record` |
| 9 | PCI DSS 4.0 Req 2 + Req 8 — không cấu hình mặc định, định danh/MFA | `devsecops.network_exposure` + `devsecops.iam_least_privilege` + `devsecops.pipeline_policy` (phần OIDC/secret tĩnh) | Gate 4 (IaC: IAM/SG) + Gate 9 (định danh workload trong CI) | `config-baseline-report`, `access-review-report`, `iac-assessment` |
| 10 | PCI DSS 4.0 Req 11 — kiểm tra an toàn định kỳ | `devsecops.dependency_kev` (chạy theo lịch trên SBOM hiện hành) | Gate 3/5 chạy scheduled + Gate 8 xếp hạng/leo thang KEV | `vuln-risk-ranking` |
| 11 | APRA CPS 234 — duy trì & kiểm tra kiểm soát có hệ thống, bằng chứng liên tục | `devsecops.evidence_completeness` (đánh giá chỉ mục bằng chứng theo quý) + toàn bộ policy của pack làm nguồn quyết định | "Gate cuối" theo kỳ — collector tổng hợp gói bằng chứng quý | `control-evidence-index` |
| 12 | SOC 2 CC8.1 — quản lý thay đổi | `devsecops.change_record` | Lớp quyết định tại merge/release (chung với hàng 2/8) | `change-record` |
| 13 | SOC 2 CC7.1–CC7.2 — vận hành hệ thống, phát hiện thay đổi trái phép | `devsecops.drift_control` (trên nền `network_exposure`/`storage_encryption` đánh giá lại trạng thái thực) | Gate 4 mở rộng dạng scheduled drift check | `drift-report` |
| 14 | SOC 2 CC6.1 + CC6.6 — truy cập logic & ranh giới hệ thống | `devsecops.iam_least_privilege` + `devsecops.network_exposure` + `devsecops.pipeline_policy` (OIDC/least-privilege của workflow) | Gate 4 (IAM/SG trên plan) + Gate 9 (quyền workflow), báo cáo theo kỳ | `access-review-report`, `config-baseline-report` |

Hàng pha 2 (không thuộc pack v1, ghi để không hiểu nhầm): CPS 234
thông báo sự cố cho APRA; CPS 230 rủi ro vận hành/nhà cung cấp trọng
yếu — xem lộ trình pha 2 trong blueprint mục 3.3.

## Danh mục policy

| Policy | Loại | File | Tài liệu |
|---|---|---|---|
| network_exposure | Rego | `rego/network_exposure.rego` | `docs/network_exposure.md` |
| storage_encryption | Rego | `rego/storage_encryption.rego` | `docs/storage_encryption.md` |
| iam_least_privilege | Rego | `rego/iam_least_privilege.rego` | `docs/iam_least_privilege.md` |
| secret_findings | Rego (quyết định trên kết quả gitleaks) | `rego/secret_findings.rego` | `docs/secret_findings.md` |
| dependency_kev | Rego (trên OSV + KEV/EPSS) | `rego/dependency_kev.rego` | `docs/dependency_kev.md` |
| license_policy | Rego (trên SBOM) | `rego/license_policy.rego` | `docs/license_policy.md` |
| base_image | Rego (tiền kiểm cho container scan) | `rego/base_image.rego` | `docs/base_image.md` |
| pipeline_policy | Rego | `rego/pipeline_policy.rego` | `docs/pipeline_policy.md` |
| change_record | Rego | `rego/change_record.rego` | `docs/change_record.md` |
| provenance | Rego | `rego/provenance.rego` | `docs/provenance.md` |
| evidence_completeness | Rego | `rego/evidence_completeness.rego` | `docs/evidence_completeness.md` |
| drift_control | Rego | `rego/drift_control.rego` | `docs/drift_control.md` |
| workload-baseline | Kyverno ClusterPolicy | `kyverno/workload-baseline.yaml` | `docs/kyverno_workload_baseline.md` |
| verify-image-signatures | Kyverno ClusterPolicy (verifyImages) | `kyverno/verify-image-signatures.yaml` | `docs/kyverno_verify_image_signatures.md` |

Mỗi policy Rego có file `*_test.rego` đi kèm (test bằng `opa test`) và
cặp fixture `fixtures/<tên>.pass.json` / `.fail.json`. Fixture cho
Kyverno baseline: manifest clean của workload (pass) và
`fixtures/k8s-bad-pod.yaml` (fail).
