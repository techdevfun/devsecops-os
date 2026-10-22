# Điểm tích hợp: GitHub / Harness / GitLab

> **Trạng thái (M1)**: tài liệu thiết kế điểm nối. Định vị bất biến của hệ:
> **tích hợp với các nền tảng tổ chức đã có, không đối đầu trực diện với họ
> ở mảng quét pipeline** (phân tích đối thủ đầy đủ nằm trong blueprint của
> dự án).

## 1. GitHub (nền chính của pha 1)

- **Actions**: nơi các gate chạy (reusable workflows — M3).
- **Code scanning**: mọi scanner bắt buộc xuất SARIF để kết quả lên GitHub
  code scanning — bề mặt xem finding chung cho cả đội, không phụ thuộc
  công cụ quét cụ thể.
- **Attestation store của GitHub**: nơi đính kèm SLSA provenance cho
  artefact build trong Actions (bên cạnh chữ ký Cosign).
- **Tính năng gốc của nền tảng được dùng lại, không viết lại**: Dependabot,
  secret scanning/push protection của GitHub được khuyến nghị bật khi tổ
  chức có giấy phép; gates của hệ này bổ sung lớp policy + bằng chứng phía
  trên, không nhân đôi chức năng nền tảng đã có.

## 2. Harness (tuỳ chọn, hai chiều)

Nếu tổ chức đã dùng Harness STO:

- **Chiều đẩy sang Harness**: kết quả quét và trạng thái gate của hệ này
  đẩy sang Harness qua API/webhook (định dạng SARIF/JSON), để Harness tiếp
  tục là nơi điều phối và khử trùng finding của họ.
- **Chiều độc lập**: policy pack + evidence của hệ này vẫn chạy và có giá
  trị đầy đủ khi *không có* Harness — lớp quản trị + bằng chứng nằm trong
  hạ tầng người dùng là phần hệ này đóng góp, không phụ thuộc vendor.
- Hệ này không thay thế Harness STO, không cạnh tranh mảng điều phối
  scanner; và ngược lại, sự hiện diện của Harness không làm mất lý do tồn
  tại của lớp policy/bằng chứng mở.

## 3. GitLab (pha 3 — chỉ ghi nhận điểm nối ở pha 1)

- Policy pack (OPA/Rego) là tài sản dùng chung; khi port sang GitLab CI
  (pha 3) chỉ thay lớp thực thi (CI template), không viết lại policy.
- **Giới hạn trung thực**: chưa có kiểm chứng nào trên GitLab instance thật
  ở thời điểm này (kể cả mẫu GitLab sẵn có của flagship #1 vẫn mang nhãn
  "chưa kiểm chứng live"). Mọi nội dung GitLab trong tài liệu của pha 1 là
  ý định thiết kế, không phải cam kết tương thích.

## 4. Các điểm nối khác (thiết kế)

- **SIEM/SOC của tổ chức**: evidence store xuất báo cáo và (pha 2) sự kiện
  sang hệ SOC hiện hữu qua API/webhook; lớp AI SecOps pha 2 nối sang
  Vigil/Wazuh/Shuffle theo cùng nguyên tắc "đối tác tích hợp, không thay
  thế".
- **Issue tracker**: pha 1 chỉ dùng bề mặt GitHub (issue/PR comment); tích
  hợp Jira/Linear là roadmap pha 2–3.
