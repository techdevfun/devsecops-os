# payments-sample — workload mẫu của devsecops-os (M1)

Ứng dụng thanh toán tối giản, tự chứa, dùng làm **workload kiểm chứng** cho
bộ gates của devsecops-os: bản `clean/` kỳ vọng qua mọi gate, bản `planted/`
gài đúng 4 lỗi có chủ đích kỳ vọng bị chặn ở đúng gate tương ứng (tiêu chí
nghiệm thu số 2 của blueprint mục 3.2 — kết luận chặn/không thuộc M3/M5 khi
gates chạy thật; ở M1 workload chỉ cần *tồn tại đúng thiết kế và chạy được*).

## Cấu trúc mỗi biến thể

```
clean/  (planted/ tương tự)
├── backend/     API Python (Starlette + uvicorn): /health, GET/POST /api/payments
├── frontend/    Trang tĩnh tối thiểu (index.html + app.js + style.css)
├── infra/       Terraform AWS tối giản: VPC + ALB + ECS Fargate + IAM + S3
├── Dockerfile   Đóng gói backend
└── k8s/         Manifest Kubernetes tối giản (Deployment + Service)
```

## Chạy backend local (cả hai biến thể)

```bash
cd clean/backend            # hoặc planted/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
PORT=8000 python app.py
```

Kiểm tra nhanh:

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok","service":"payments-sample"}

curl http://127.0.0.1:8000/api/payments
curl -X POST http://127.0.0.1:8000/api/payments \
  -H 'Content-Type: application/json' \
  -d '{"amount": 50000, "currency": "VND", "description": "Invoice INV-1002"}'
```

Frontend: mở `frontend/index.html` bằng một static server bất kỳ (ví dụ
`python3 -m http.server 3000 --directory frontend`); trang gọi API tại
`http://localhost:8000` theo cấu hình mặc định trong `app.js` (backend đã
bật CORS cho origin localhost phục vụ demo local; khi triển khai sau ALB,
frontend và API cùng origin — xem ghi chú trong `app.js`).

## Infra / Docker / Kubernetes ở M1

- `infra/*.tf` không được `terraform apply` vào tài khoản AWS thật
  (workload mẫu chỉ phục vụ kiểm chứng gates). Từ M3 chúng được kiểm
  chứng bằng terraform thật trong gate 4; từ M5 (refactor rule security
  group sang tài nguyên riêng) `terraform fmt -check` và
  `terraform validate` đều PASS trên cả hai biến thể — kết quả từng lần
  chạy nằm trong `gates/verification/results.md` và `validate.json` của
  gate 4. `terraform plan` vẫn cần AWS API thật (data source
  availability zones) nên chưa sinh được trong môi trường kiểm chứng.
- `Dockerfile` và `k8s/` là hiện vật triển khai để gate container (M3) và
  kiểm tra manifest (M2/M3) quét ở các mốc sau; đường chạy được ở M1 là
  venv local ở trên.

## Khác biệt giữa hai biến thể

Chỉ đúng 4 điểm — đều nằm trong `planted/PLANTED.md`:

| # | Điểm khác | File (bản planted) |
|---|---|---|
| 1 | Secret giả hardcode làm giá trị dự phòng | `backend/config.py` |
| 2 | `starlette==1.0.0` — dính CVE-2026-48710 (CISA KEV) | `backend/requirements.txt` |
| 3 | Security group mở `0.0.0.0/0` (cổng app + SSH) | `infra/main.tf` |
| 4 | Base image đóng băng từ 2022 (`python:3.10.4-slim-bullseye`) | `Dockerfile` |

Mọi file còn lại giống hệt bản `clean/` để phép đối chiếu ở M3/M5 sạch:
gates chặn bản planted thì chỉ có thể là vì 4 lỗi này.
