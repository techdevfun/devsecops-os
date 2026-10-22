# checkout-sample — service sinh ra từ golden path (template README)

> Service mẫu thứ hai của devsecops-os, dựng **từ golden path
> `templates/api-service`** tại M5 (không sao chép từ payments-sample) để
> kiểm chứng tiêu chí "service mới onboard bằng đường đã lát". Biên bản
> dogfood (thời gian + kết quả từng bước của pipeline):
> [`../../release/dogfood-checkout-sample.md`](../../release/dogfood-checkout-sample.md).

## Service này làm gì

API giỏ hàng/checkout tối thiểu cho mục đích dogfood: `/health` và
resource mẫu `items` (in-memory). Dữ liệu: không dữ liệu thật, không
thông tin thanh toán — mức nhạy cảm **internal**. Nó tồn tại để chứng
minh template tự qua được bộ gates của chính hệ (điều kiện R7 của
blueprint); nghiệp vụ checkout thật nằm ngoài phạm vi pha 1.

## Chạy local

```bash
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
PORT=8000 python app.py
curl http://127.0.0.1:8000/health
```

Frontend tĩnh: `python3 -m http.server 3000 --directory frontend`.

## Cấu hình & secret

- Mọi cấu hình qua biến môi trường (`backend/config.py`). Secret CHỈ đến
  từ secret store của nền tảng lúc triển khai — không giá trị dự phòng
  ghi cứng, không secret trong manifest (k8s dùng `secretKeyRef`).
- Danh sách biến môi trường: `SERVICE_NAME`, `ENVIRONMENT`,
  `CHECKOUT_API_KEY` (đổi tên theo provider thật của service).

## Kiểm soát bảo mật có sẵn (từ template)

- 10 CI gates của devsecops-os chạy trên mọi PR (`.github/workflows/`),
  mặc định an toàn: gate 1 (secret) và gate 9 (vệ sinh pipeline) ở chế độ
  **chặn**; các gate còn lại **report-only** cho tới khi hiệu chuẩn xong
  trên lịch sử của chính service (nguyên tắc blueprint: backtest →
  report-only → enforce).
- Policy mặc định: pack pha 1 (ISO 27001:2022 / NIST CSF+SSDF / PCI DSS 4
  ánh xạ tham chiếu) qua `devsecops-os.yml`.
- Dockerfile chuẩn: base image đang được duy trì, non-root, healthcheck.
- Manifest K8s chuẩn: `runAsNonRoot`, drop ALL capabilities, resource
  limits, probes, secret qua tham chiếu.
- IaC chuẩn: mã hoá mặc định, security group không mở ra Internet ở cổng
  ứng dụng/SSH (rule dạng tài nguyên riêng `aws_vpc_security_group_*_rule`).
- Bằng chứng: mỗi lần CI chạy sinh evidence bundle có SHA-256 manifest,
  kiểm chứng bằng một lệnh (`evidence/verify_bundle.py` ở repo hệ thống).

## Vận hành

- **Deploy**: không áp dụng — service mẫu dogfood, không triển khai thật.
- **Rollback**: không áp dụng (như trên).
- **On-call / liên hệ sự cố**: không áp dụng (như trên); quyền sở hữu code xem CODEOWNERS.
  CODEOWNERS cho quyền sở hữu code).
- **Nhật ký & bằng chứng**: bundle bằng chứng của từng lần chạy nằm ở
  artefact CI / kho bằng chứng của tổ chức (cấu hình trong
  `devsecops-os.yml`, mục `evidence`).
