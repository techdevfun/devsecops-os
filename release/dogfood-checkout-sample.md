# Biên bản dogfood golden path — service checkout-sample (M5-A)

**Ngày chạy:** 2026-10-22 (giờ hệ thống UTC; máy kiểm chứng cục bộ của
nhà máy). **Người chạy:** worker M5-A. **Môi trường:** cục bộ — cùng các
script `gates/local/gate-*.sh` mà GitHub Actions gọi (xem
`gates/README.md`). Phần chạy trên GitHub Actions thật: **UNVERIFIED**,
thuộc mốc M5-B.

## Cách service được tạo (đúng quy trình golden path)

1. Sao chép nguyên cây `templates/api-service/` →
   `examples/checkout-sample/` (không sao chép từ payments-sample).
2. Đổi tên `example-service` → `checkout-sample` và `EXAMPLE_API_KEY` →
   `CHECKOUT_API_KEY` trên toàn bộ file (mã nguồn, IaC, manifest, docs).
3. Điền README của service (mục đích, mức nhạy cảm dữ liệu: internal;
   mục vận hành ghi "không áp dụng — service mẫu dogfood").
4. Chạy toàn bộ pipeline cục bộ như bước 6 của `templates/README.md`.

## Kết quả từng bước (lần chạy đầu tiên, không chạy lại)

| Bước | Kết quả | Thời lượng |
|---|---|---|
| Smoke: cài dependencies vào venv sạch + chạy backend thật + gọi `GET /health` | ✅ `{"status":"ok","service":"checkout-sample"}` | (gộp với gate 01 ≈ 20 giây đầu) |
| Gate 01 — secret scanning | ✅ PASS, 0 vi phạm | ~5 giây |
| Gate 02 — SAST (report-only) | ✅ exit 0, 0 finding chặn | ~17 giây |
| Gate 03 — SCA (report-only) | ✅ exit 0 | ~10 giây |
| Gate 04 — IaC | ✅ terraform validate PASS; network_exposure / storage_encryption / iam_least_privilege đều PASS | ~33 giây |
| Gate 05 — container | ✅ base_image PASS | ~12 giây |
| Gate 06 — SBOM + attestation | ✅ provenance PASS, SBOM đã ký (khoá tạm của lần chạy) | ~6 giây |
| Gate 07 — license | ✅ PASS | <1 giây |
| Gate 08 — KEV/EPSS | ✅ dependency_kev PASS | ~2 giây |
| Gate 09 — vệ sinh pipeline | ✅ PASS | <1 giây |
| Gate 10 — AI PR review | ✅ hoàn thành ở trạng thái tắt mặc định (pha 1) | <1 giây |
| Đóng evidence bundle | ✅ `evidence/bundles/local-checkout-sample/` | <1 giây |
| Kiểm chứng bundle (một lệnh) | ✅ "PASS — mọi hash khớp manifest, mọi record khớp schema M2" | <1 giây |
| **TỔNG** | **Mọi bước exit 0 ngay lần chạy đầu** | **100 giây** (đo bằng đồng hồ treo tường của script chạy) |

Thời lượng từng bước khôi phục từ dấu thời gian file đầu ra (sai số ±2
giây) vì tiện ích `bc` không có trên máy chạy nên bộ đo lẻ của script
ghi 0.00 — tổng 100 giây là số đo trực tiếp, không suy diễn. Log thô:
`release/dogfood-run.log`; bảng mã thoát từng bước:
`release/dogfood-timings.tsv`.

## Đối chiếu tiêu chí nghiệm thu 5 của blueprint

"Golden path ≤ 30 phút, CI xanh ngay lần chạy đầu":

- **Phần cục bộ: ĐẠT** — từ lúc có cây service tới khi bundle kiểm chứng
  xong: ~100 giây cho pipeline (cộng vài phút thao tác sao chép/đổi tên
  thủ công theo hướng dẫn), mọi bước xanh ngay lần đầu, không sửa lỗi
  giữa chừng.
- **Phần trên GitHub Actions thật: UNVERIFIED** — repo chưa được công
  bố; việc tạo service từ template trong một repo GitHub thật và CI
  xanh ở lần chạy đầu trên Actions thuộc nghiệm thu M5-B sau khi chủ sở
  hữu duyệt phát hành.

## Ghi chú trung thực

- Gate 02/03 ở chế độ report-only theo mặc định pha 1: "xanh" nghĩa là
  hoàn thành và không có finding thuộc diện chặn; với checkout-sample,
  gate 03 vẫn thấy các CVE mức thấp của chính các dependency đã ghim
  (cùng nhóm với bản clean của payments-sample) — ghi trong bundle.
- Checkout-sample dùng chung phiên bản dependency/IaC với template nên
  kết quả này kiểm chứng template, không phải một hệ sinh thái khác.
