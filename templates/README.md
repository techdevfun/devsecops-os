# Golden Path — mẫu paved road (M5)

Golden path là "đường đã lát": một service mới bắt đầu từ template này
thì **mặc định đã an toàn** — 10 CI gates, policy mặc định, bằng chứng tự
sinh — mà không cần đội ngũ tự lắp ráp. Thiết kế gốc: mục 6 của
[`../docs/blueprint.md`](../docs/blueprint.md), chi tiết ở
[`../docs/golden-paths.md`](../docs/golden-paths.md).

## Template hiện có

| Template | Dùng cho | Trạng thái |
|---|---|---|
| [`api-service/`](api-service/) | API backend (Python/Starlette) + frontend tĩnh + IaC AWS tối thiểu + manifest K8s | Đã dogfood tại M5 (xem dưới) |

Template gồm: khung mã nguồn (backend/frontend), Dockerfile chuẩn (base
image đang được duy trì, non-root, healthcheck), IaC chuẩn (mã hoá mặc
định, security group không mở ra Internet ở cổng ứng dụng/SSH — rule dạng
tài nguyên `aws_vpc_security_group_*_rule` riêng), manifest K8s chuẩn
(non-root, drop ALL capabilities, probes, secret qua tham chiếu), CI gọi
10 gates (`.github/workflows/ci.yml`), cấu hình `devsecops-os.yml` mặc
định an toàn, CODEOWNERS và `branch-protection.json` (protection-as-code
tham chiếu).

## Tạo một service mới từ template (từng bước)

1. **Sao chép** toàn bộ thư mục `api-service/` thành thư mục/repo của
   service mới. (Khi tổ chức tách repo riêng: giữ nguyên cây này, trỏ
   `uses:` trong workflow sang repo hệ thống — xem chú thích đầu file
   `.github/workflows/ci.yml`.)
2. **Đổi tên**: thay `example-service` bằng tên service ở mọi file
   (app, IaC, manifest, README của service), đổi tên secret mẫu
   `EXAMPLE_API_KEY` theo provider thật.
3. **Điền README của service**: mục "Service này làm gì" + mức nhạy cảm
   dữ liệu; mục Vận hành (deploy/rollback/on-call).
4. **Cấu hình**: rà `devsecops-os.yml` — giữ nguyên tắc mặc định (gate 1
   và gate 9 chặn; còn lại report-only) cho tới khi hiệu chuẩn xong trên
   lịch sử của chính service.
5. **CODEOWNERS**: thay `@your-org/...` bằng team thật; áp
   `branch-protection.json` cho nhánh chính bằng công cụ quản trị của tổ
   chức.
6. **Chạy thử toàn bộ pipeline tại chỗ trước PR đầu tiên** (đúng các
   script mà CI sẽ gọi):
   ```bash
   export REPO_ROOT=<repo-he-thong> WORKLOAD=<thu-muc-service> \
          OUT_ROOT=evidence/output/local-<service> \
          COMMIT_SHA=local-dogfood TOOLS_DIR=~/workspace/tools
   for g in gates/local/gate-*.sh; do bash "$g"; done
   python3 evidence/bundle_tool.py collect "$OUT_ROOT" \
       --run-id local-<service> --out-dir evidence/bundles/local-<service>
   python3 evidence/verify_bundle.py evidence/bundles/local-<service>
   ```
   Kỳ vọng: mọi gate PASS (gate 10 tắt mặc định — job hoàn thành, không
   chặn), kiểm chứng báo `bundle OK`.
7. **Mở PR đầu tiên** — trên GitHub Actions, cùng bộ workflow phải xanh
   ngay lần chạy đầu (tiêu chí nghiệm thu 5; phần Actions thật kiểm
   chứng ở mốc phát hành M5-B).

Điều kiện an toàn R7 (blueprint mục 7): template **tự nó phải qua được bộ
gates của chính hệ** — đó là lý do có dogfood dưới đây, và mọi thay đổi
vào template phải chạy lại dogfood trước khi được nhận.

## Dogfood (bằng chứng tại chỗ)

Tại M5, service mẫu [`../examples/checkout-sample/`](../examples/checkout-sample/)
được dựng **từ chính template này** (không sao chép từ payments-sample) và
chạy toàn bộ pipeline cục bộ: 10 gates, bó bằng chứng, kiểm chứng một
lệnh. Biên bản đầy đủ (thời gian và kết quả từng bước):
[`../release/dogfood-checkout-sample.md`](../release/dogfood-checkout-sample.md).
Phần "CI xanh trên GitHub Actions thật" thuộc nghiệm thu M5-B —
**UNVERIFIED** tại thời điểm viết.
