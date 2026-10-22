# Đa môi trường: cloud + on-prem

> **Trạng thái (M1)**: tài liệu thiết kế. Mẫu tham chiếu cloud chạy trên
> workload mẫu (`examples/payments-sample/*/infra/` — Terraform AWS dạng
> file tĩnh ở M1; việc `terraform apply` thật không thuộc phạm vi M1).

## 1. Nguyên tắc

**Cùng một policy pack áp cho mọi môi trường.** Khác biệt giữa cloud và
on-prem khai báo bằng file giá trị (values) riêng cho từng môi trường —
không fork policy, không sửa luật theo môi trường. Nếu một kiểm soát không
thể thực thi ở một môi trường, đó là một *ngoại lệ được ghi lại trong bằng
chứng*, không phải một bản policy lặng lẽ yếu hơn.

## 2. Cloud (tham chiếu: AWS)

- Hạ tầng khai báo bằng Terraform (mẫu trong workload: VPC, ECS Fargate,
  ALB, IAM role theo OIDC federation — xem `identity-and-access.md`).
- Pipeline chạy trên GitHub-hosted runner hoặc self-hosted runner trong
  VPC của tổ chức; workload nhận danh tính qua OIDC, không qua access key.
- Evidence store đặt trong hạ tầng của tổ chức (ví dụ bucket S3 có versioning
  + khoá mã hoá + Object Lock nếu tổ chức yêu cầu bất biến).

## 3. On-prem

- Kubernetes tự quản + **self-hosted runner** là đường triển khai on-prem
  của pha 1: bộ gates chạy như trên cloud, chỉ khác nơi thực thi.
- Admission bằng Kyverno trên cluster tự quản, dùng cùng policy đã biên
  dịch từ pack (xem mẫu `docs/examples/kyverno-verify-images.yaml`).
- Môi trường không có Internet: các công cụ quét và feed dữ liệu (CISA KEV,
  EPSS) phải được mirror vào trong (cập nhật feed theo lịch qua một điểm
  trung chuyển có kiểm soát) — đây là yêu cầu thiết kế ghi nhận ở M1; cơ
  chế mirror cụ thể thuộc mốc cài đặt gates (M3) và sẽ được ghi rõ giới hạn
  khi đó.

## 4. Bảng khác biệt được phép (values), ví dụ

| Hạng mục | Cloud (AWS) | On-prem |
|---|---|---|
| Nơi chạy gates | GitHub-hosted hoặc self-hosted runner | Self-hosted runner trong DC |
| Danh tính workload | GitHub OIDC → IAM role | OIDC của cluster / SPIFFE (thiết kế pha sau) |
| Registry | ECR của tổ chức | Registry nội bộ (Harbor…) |
| Evidence store | S3 (versioning + SSE) | Object storage nội bộ tương đương |
| Feed KEV/EPSS | Tải trực tiếp từ CISA/FIRST | Qua mirror nội bộ |

Những hạng mục **không** được khác theo môi trường: danh mục gates đang
bật, ngưỡng chặn đã hiệu chuẩn, định dạng bằng chứng và yêu cầu toàn vẹn
(SHA-256 manifest).
