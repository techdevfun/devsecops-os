# Kết quả kiểm chứng M3 — bộ CI gates chạy thật trên workload mẫu

Sinh tự động từ `results.json` (đầu ra thật của các gate) bằng
`render_results_md.py`. Log thô từng gate: `gates/verification/logs/`.
Bằng chứng từng lần chạy: `evidence/output/local-<biến thể>/`.

Quy ước mã thoát: 0 = qua; 1 = bị chặn theo điều kiện chặn mặc
định của blueprint; 2 = lỗi hạ tầng (kèm scan-error.json).

| Gate | Clean — kết quả (mã thoát, giây) | Planted — kết quả (mã thoát, giây) |
|---|---|---|
| 01 Secret scanning | exit 0, 6.67s — policy pass (0 vi phạm) | exit 1, 4.88s — policy deny (1 vi phạm) |
| 02 SAST | exit 0, 37.82s — 0 finding  — report-only | exit 0, 25.6s — 0 finding  — report-only |
| 03 SCA | exit 0, 18.63s — 4 lỗ hổng: CVE-2026-64847, CVE-2026-63374, CVE-2025-43859, CVE-2026-45409 | exit 0, 16.81s — 9 lỗ hổng: CVE-2026-48710, CVE-2026-48817, CVE-2026-48818, CVE-2026-54282, CVE-2026-54283, CVE-2026-64847, CVE-2026-63374, CVE-2025-43859, CVE-2026-45409 |
| 04 IaC scanning | exit 0, 49.62s — validate=PASS; network_exposure=pass(0); storage_encryption=pass(0); iam_least_privilege=pass(0); trivy-config=8 misconfig | exit 1, 68.79s — validate=PASS; network_exposure=deny(2); storage_encryption=pass(0); iam_least_privilege=pass(0); trivy-config=9 misconfig |
| 05 Container scanning | exit 0, 13.72s — image 170 CVE {'LOW': 61, 'HIGH': 48, 'MEDIUM': 60, 'UNKNOWN': 1}; nhóm chặn KEV=0; base_image=pass(0) | exit 1, 14.85s — image 621 CVE {'LOW': 184, 'HIGH': 166, 'MEDIUM': 245, 'UNKNOWN': 9, 'CRITICAL': 17}; nhóm chặn KEV=0; base_image=deny(2) |
| 06 SBOM + attestation | exit 0, 8.74s — provenance pass; SBOM 3 components, signed=True | exit 0, 7.5s — provenance pass; SBOM 3 components, signed=True |
| 07 License compliance | exit 0, 0.32s — license_policy pass (0 vi phạm) | exit 0, 0.31s — license_policy pass (0 vi phạm) |
| 08 EPSS/CISA KEV | exit 0, 4.11s — dependency_kev pass (0 vi phạm); 174 mục xếp hạng, block: — | exit 1, 2.15s — dependency_kev deny (1 vi phạm); 630 mục xếp hạng, block: ['CVE-2026-48710', 'CVE-2023-4911', 'CVE-2024-2961', 'CVE-2023-4911', 'CVE-2024-2961', 'CVE-2011-3389', 'CVE-2025-6965', 'CVE-2022-2068', 'CVE-2023-0286', 'CVE-2023-2650', 'CVE-2024-2511', 'CVE-2023-50387', 'CVE-2023-50868', 'CVE-2023-50387', 'CVE-2023-50868', 'CVE-2022-2068', 'CVE-2023-0286', 'CVE-2023-2650', 'CVE-2024-2511'] |
| 09 Vệ sinh pipeline | exit 0, 1.45s — pipeline_policy pass (0 vi phạm) | exit 0, 0.47s — pipeline_policy pass (0 vi phạm) |
| 10 AI PR Review Gate | exit 0, 0.05s — disabled (mặc định pha 1) | exit 0, 0.02s — disabled (mặc định pha 1) |

Tổng thời gian chạy tuần tự (cục bộ, cache đã ấm): clean 141.13s, planted 141.38s. Gate lâu nhất: 68.79s.

## Đối chiếu kỳ vọng bắt buộc của M3

- Clean qua mọi gate (mọi mã thoát = 0): **ĐẠT**
- Planted bị chặn ở gate 01 (mã thoát 1): **ĐẠT**
- Planted bị chặn ở gate 04 (mã thoát 1): **ĐẠT**
- Planted bị chặn ở gate 05 (mã thoát 1): **ĐẠT**
- Planted bị chặn ở gate 08 (mã thoát 1): **ĐẠT**
- Planted KHÔNG bị chặn ở gate 02 (mã thoát 0): **ĐẠT**
- Planted KHÔNG bị chặn ở gate 03 (mã thoát 0): **ĐẠT**
- Planted KHÔNG bị chặn ở gate 06 (mã thoát 0): **ĐẠT**
- Planted KHÔNG bị chặn ở gate 07 (mã thoát 0): **ĐẠT**
- Planted KHÔNG bị chặn ở gate 09 (mã thoát 0): **ĐẠT**
- Planted KHÔNG bị chặn ở gate 10 (mã thoát 0): **ĐẠT**
- Gate 3 planted phát hiện CVE-2026-48710: **ĐẠT**
- Gate 8 planted xếp CVE-2026-48710 vào nhóm block (KEV): **ĐẠT**
- Gate 4 cả hai biến thể: terraform validate = PASS (clean) / PASS (planted) — sau refactor M5 tách rule security group sang tài nguyên riêng, vòng tham chiếu đã hết; chi tiết trong validate.json của từng lần chạy. terraform plan JSON vẫn chưa sinh được tại chỗ vì plan cần gọi AWS API thật (data source aws_availability_zones).

