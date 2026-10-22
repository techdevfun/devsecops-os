# Golden paths

> **Trạng thái (cập nhật M5-A)**: template thật đã có tại
> `templates/api-service/` và đã dogfood tại chỗ bằng service thứ hai
> `examples/checkout-sample/` — toàn bộ pipeline cục bộ (10 gates +
> evidence bundle + verify) xanh ngay lần chạy đầu, tổng ~100 giây (biên
> bản: `release/dogfood-checkout-sample.md`). Phần "CI xanh trên GitHub
> Actions thật" của tiêu chí nghiệm thu vẫn **UNVERIFIED**, chờ mốc
> phát hành M5-B. Phần dưới đây là tài liệu thiết kế gốc (M1) được giữ
> nguyên làm cơ sở đối chiếu.

## 1. Ý tưởng

Golden path là "đường mòn đã lát sẵn": một template repo theo loại service
(API, worker, frontend) mà khi đội ngũ đi theo nó, các kiểm soát bảo mật là
**mặc định có sẵn** thay vì việc phải tự lắp. Tuân thủ trở thành đường ít
ma sát nhất, không phải nỗ lực cộng thêm.

## 2. Một golden-path template gồm gì (thiết kế)

- Mã nguồn khung tối thiểu của loại service (ví dụ API Python như workload
  mẫu `examples/payments-sample/clean/` — workload này chính là hạt nhân
  tham chiếu cho template API ở M5).
- `Dockerfile` theo chuẩn: base image hiện hành, chạy non-root, có
  healthcheck, ghim phiên bản.
- Manifest Kubernetes theo chuẩn: resource requests/limits, probes, security
  context tối thiểu (non-root, không leo quyền).
- Pipeline CI đã cài đủ các gate của hệ (M3) ở chế độ mặc định an toàn:
  report-only khi mới lắp, chuyển sang chặn sau hiệu chuẩn (xem
  `gates/README.md`).
- File cấu hình của hệ (`devsecops-os.yml` — mẫu ở
  `docs/examples/devsecops-os.sample.yml`): chọn policy pack, ngưỡng gate,
  nơi lưu bằng chứng.
- `CODEOWNERS`, branch protection-as-code, `.gitignore` đúng chuẩn (không
  commit secret/tfstate).
- README của service có sẵn mục vận hành: chạy local, biến môi trường, nơi
  xem bằng chứng của service mình.

## 3. Vòng đời

1. Tạo service từ template (GitHub template repository / công cụ sinh repo
   của tổ chức).
2. CI chạy lần đầu: kỳ vọng **xanh ngay** trên mã khung (đây là tiêu chí
   nghiệm thu đo được của pha 1, không phải khẩu hiệu).
3. Đội ngũ phát triển tính năng trên đường mòn đó; khi cần đi ra ngoài
   đường mòn (tắt một gate, nới một policy), thao tác đó là một thay đổi
   cấu hình có review và để lại dấu vết trong bằng chứng — không cấm, nhưng
   không im lặng.

## 4. An toàn của chính template (rủi ro R7 của blueprint)

Template bị lỗi (quyền thừa, cấu hình yếu) sẽ nhân rộng lỗi đó ra mọi
service sinh ra từ nó. Vì vậy khi M5 cài đặt:

- Template phải **tự qua chính bộ gates của hệ** trong CI của repo này
  (dogfood bắt buộc).
- Mọi action bên thứ ba dùng trong template phải ghim full commit SHA.
- Phát hiện cấu hình nguy hiểm đã phát hành trong template → sửa + phát
  hành bản vá + ghi chú công khai trong CHANGELOG trong 48 giờ (điều kiện
  dừng đã ghi trong sổ rủi ro của blueprint).
