# Nội dung trang giới thiệu devsecops-os cho techdev.fun — BẢN SOẠN SẴN (M5-A)

> Trạng thái: **đã soạn, CHƯA deploy**. File này là nguồn nội dung để
> Tổng quản/chủ sở hữu duyệt và đưa lên techdev.fun ở mốc phát hành
> (M5-B) sau khi repo qua cổng 99/100. Mọi con số dưới đây lấy từ bằng
> chứng kiểm chứng trong repo và được ghi nhãn "cục bộ" khi chưa có số
> đo trên GitHub Actions thật — không sửa các nhãn này khi đăng.

---

## [Hero]

# devsecops-os

**Lớp điều hành DevSecOps + AI SecOps mã nguồn mở cho tổ chức bị quản
chế.** Policy-as-code ánh xạ sẵn tới ISO 27001:2022, NIST CSF/SSDF,
PCI DSS 4.0 và APRA CPS 234/230 — chạy trong CI của chính bạn, bằng
chứng kiểm toán tự sinh từ mỗi lần chạy pipeline. Không server trung
gian, không dữ liệu nào rời hạ tầng của tổ chức.

[Demo GIF — release/demo/demo-terminal.gif: bộ gates chạy thật trên
workload mẫu hai biến thể + kiểm chứng evidence bundle]

**Ai đang đau:** CISO và đội platform ở ngân hàng/tài chính/bảo hiểm —
nơi mỗi đội tự lắp pipeline bảo mật một kiểu, chính sách tuân thủ nằm
trong tài liệu Word, và đến mùa kiểm toán thì cả tổ chức đi gom bằng
chứng thủ công. devsecops-os làm đúng phần còn thiếu đó: một "đường
chuẩn" (golden path) để service mới sinh ra đã đạt kiểm soát, chính sách
dạng mã nằm trong repo của chính tổ chức, và bằng chứng là sản phẩm phụ
tự động của vận hành — pipeline không chỉ chặn lỗi, nó tự chứng minh nó
đã chặn.

## [Cách nó hoạt động]

1. **10 CI gates** trên mọi pull request: quét secret, SAST, SCA, IaC,
   container, SBOM + attestation, giấy phép, ưu tiên lỗ hổng theo
   CISA KEV/EPSS, vệ sinh pipeline, và một gate review AI tuỳ chọn
   (mặc định tắt).
2. **Policy ở trung tâm**: 14 policy (OPA/Rego + Kyverno) ánh xạ tới các
   khung kiểm soát — ánh xạ *tham chiếu* phục vụ chuẩn bị kiểm toán,
   không phải chứng nhận tuân thủ.
3. **Evidence bundle**: mỗi lần chạy đóng thành một gói có manifest
   SHA-256, kiểm chứng toàn vẹn bằng **một lệnh** — kể cả phát hiện sửa
   đổi 1 byte.
4. **Golden path**: template service (API + IaC + manifest + CI) để đội
   ngũ onboard trong vài phút thay vì tự lắp ráp nhiều tuần.

## [Bằng chứng, không lời hứa]

- Workload mẫu hai biến thể chạy thật: bản sạch qua cả 10 gate; bản gài
  đúng 4 lỗi có chủ đích (secret giả, dependency dính CVE thuộc CISA
  KEV, security group mở 0.0.0.0/0, base image đóng băng từ 2022) bị
  chặn ở **đúng 4 gate tương ứng**, không chặn nhầm, không lọt lỗi nào.
- Policy harness: 34/34 kiểm tra đạt. Evidence bundle: kiểm chứng đạt
  trên cả hai biến thể; thử sửa 1 byte → kiểm chứng FAIL và chỉ đúng
  file bị sửa.
- Golden path đã dogfood: dựng service thứ hai từ template, toàn bộ
  pipeline cục bộ xanh ngay lần chạy đầu trong ~100 giây.

*(Số đo trên là số đo cục bộ trên máy kiểm chứng của dự án. Thời gian
workflow trên GitHub Actions thật sẽ được công bố sau nghiệm thu phát
hành — trang này không đăng con số chưa đo.)*

## [Giới hạn đã biết — nói thẳng]

- Đây là **pha 1**: GitHub Actions là nền CI được cài đặt; GitLab/
  Jenkins/on-prem là điểm tích hợp đã thiết kế, chưa cài đặt.
- Bằng chứng dạng quyết định/định kỳ (biên bản thay đổi, báo cáo
  drift, rà soát quyền truy cập, đường cơ sở cấu hình) **đã có bộ
  sinh tự động** chạy trên dữ liệu của lần chạy/cây (vòng M5-A3,
  truy vết 13/14 hàng) — nhưng giá trị kiểm toán đầy đủ của chúng
  vẫn cần dữ liệu vận hành thật của tổ chức (phê duyệt PR thật,
  lịch sử drift thật), thứ chỉ có sau khi áp dụng thực tế.
- Record `change-record` ở các lần chạy cục bộ hiện bị policy
  **DENY** vì không có phê duyệt PR thật — đúng bản chất: bằng chứng
  trung thực về một thay đổi chưa qua phê duyệt, không phải lỗi.
- Evidence bundle có toàn vẹn SHA-256 và ký được bằng Cosign ở mức
  bundle — hiện mới ở mức khoá cục bộ tạm theo lần chạy (chưa gắn danh
  tính OIDC/transparency log như ký keyless trên CI).
- Hệ này **không thay thế** Harness, GitHub Advanced Security hay Snyk
  về độ sâu quét và hỗ trợ enterprise — nó là lớp quản trị + bằng chứng
  xuyên suốt nằm trên các công cụ đó.

## [Bắt đầu]

Repo GitHub và bài viết giới thiệu kỹ thuật (dev.to) sẽ được gắn tại
đây khi dự án qua cổng phát hành 99/100 của nhà máy. Mã nguồn theo giấy
phép MIT.
