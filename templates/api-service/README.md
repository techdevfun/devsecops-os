# example-service — service sinh ra từ golden path (template README)

> Đây là README khung của một service dùng golden path `api-service`.
> Khi tạo service thật: đổi tên `example-service` ở mọi file, xoá phần
> khung này và điền các mục TODO.

## Service này làm gì

TODO: một đoạn ngắn — nghiệp vụ, người dùng, dữ liệu nó chạm tới, mức độ
nhạy cảm của dữ liệu (public / internal / confidential). Mức nhạy cảm
quyết định policy pack áp dụng (xem `devsecops-os.yml`).

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
  `EXAMPLE_API_KEY` (đổi tên theo provider thật của service).

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

- **Deploy**: TODO — môi trường, lệnh/đường ống, cửa sổ triển khai.
- **Rollback**: TODO — cách quay lại bản trước trong <15 phút.
- **On-call / liên hệ sự cố**: TODO — kênh, người phụ trách (xem
  CODEOWNERS cho quyền sở hữu code).
- **Nhật ký & bằng chứng**: bundle bằng chứng của từng lần chạy nằm ở
  artefact CI / kho bằng chứng của tổ chức (cấu hình trong
  `devsecops-os.yml`, mục `evidence`).
