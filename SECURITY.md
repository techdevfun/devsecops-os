# Chính sách bảo mật

## Báo cáo lỗ hổng

Nếu bạn phát hiện lỗ hổng bảo mật trong devsecops-os (policy, gate,
evidence tooling hoặc template), vui lòng **không** mở issue công khai.
Hãy báo cáo riêng qua kênh liên hệ của chủ sở hữu dự án (trang
techdev.fun) kèm:

- mô tả lỗ hổng và thành phần bị ảnh hưởng (file/gate/policy),
- các bước tái hiện tối thiểu,
- đánh giá tác động theo góc nhìn của bạn.

Dự án sẽ xác nhận đã nhận báo cáo và phối hợp khắc phục trước khi công
bố chi tiết. Đây là dự án mã nguồn mở do một nhóm nhỏ duy trì — thời
gian phản hồi là nỗ lực tốt nhất (best effort), không phải SLA.

## Xử lý sự cố: nghi ngờ lộ secret hoặc khoá ký

Nếu bạn phát hiện (hoặc nghi ngờ) một secret, token hay khoá riêng
bị lộ trong repo này, trong một bundle bằng chứng, hoặc qua một lần
chạy cổng:

1. **Thu hồi/xoay vòng ngay lập tức** — coi như đã bị lộ: token thì
   revoke và cấp mới, khoá ký Cosign thì sinh cặp khoá mới và tuyên
   bố fingerprint cũ không còn hiệu lực. Đừng chờ xác minh "đã bị
   khai thác hay chưa" mới thu hồi.
2. **Xoá khỏi cây hiện tại** và ghi rõ trong `CHANGELOG.md` (mục
   Bảo mật) rằng đã có sự cố + đã xoay vòng — nhưng hiểu rằng xoá
   file **không** xoá được lịch sử git hay các bundle đã phát tán;
   bước 1 mới là biện pháp hiệu lực.
3. **Thông báo cho người duy trì** qua kênh riêng ở trên, kèm: loại
   secret, vị trí phát hiện (file/bundle/lần chạy), thời điểm nghi
   lộ. Không gửi chính giá trị secret trong thông báo.
4. Với bundle bằng chứng đã ký chứa dữ liệu nhạy cảm: phát hành lại
   bundle đã làm sạch, ký bằng khoá mới, và ghi fingerprint khoá bị
   thu hồi vào file này để bên kiểm chứng loại bỏ.

## Phạm vi

- Các secret xuất hiện trong `examples/payments-sample/planted/` là
  **giá trị giả được cài có chủ đích** để kiểm chứng gate quét secret —
  không phải rò rỉ thật; xin đừng báo cáo chúng như sự cố.
- Khoá Cosign dùng trong các lần chạy kiểm chứng cục bộ là khoá tạm
  sinh theo từng lần chạy trong thư mục đầu ra (đã gitignore), không
  dùng cho bất kỳ artefact phát hành nào.
