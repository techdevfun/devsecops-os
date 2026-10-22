# HỒ SƠ PHÁT HÀNH — devsecops-os pha 1 (M5-A, phần cục bộ)

**Sản phẩm:** devsecops-os (flagship #2 của nhà máy repo, Trợ lý A).
**Ngày lập hồ sơ:** 2026-10-22. **Người lập:** worker M5-A.
**Phạm vi hồ sơ:** toàn bộ công việc CỤC BỘ của mốc M5. Chưa có bất kỳ
hành động phát hành nào: không tạo/push repo GitHub, không deploy,
không đụng DNS/trang techdev.fun đang chạy — đúng giới hạn cứng của mốc.

**Cổng phát hành áp dụng** (chủ sở hữu qua Tổng quản, 2026-10-22):
chỉ phát hành khi đạt **99/100 theo RUBRIC-NGHIEM-THU-100 từ hội đồng**
cộng đủ 6 tiêu chí nghiệm thu của blueprint và quét rủi ro trước phát
hành. Dưới 99 → tiếp tục hoàn thiện, không phát hành trong mọi trường
hợp.

**QUYẾT ĐỊNH CỦA CHỦ SỞ HỮU (2026-10-22 ~18:17, qua Tổng quản) —
trạng thái phát hành hiện hành:** giữ cổng 99/100 **theo đúng chữ** —
**không** tạo repo private tạm để đo lường, **không** có ngoại lệ đo
lường nào; chấp nhận điểm trần dưới 99 cho tới khi tồn tại một cách
kiểm chứng hợp lệ khác. Hệ quả: devsecops-os tiếp tục **CHƯA PHÁT
HÀNH** và toàn bộ phần **M5-B ĐÓNG BĂNG** (không tạo repo dưới bất kỳ
hình thức nào, không đo Actions, không landing trực tiếp, không bài
dev.to). Các dòng việc thuộc M5-B trong hồ sơ này chỉ còn là ghi
nhận điều kiện chưa kiểm chứng được, **không phải lựa chọn đang mở**.

**Cập nhật M5-A2 (2026-10-22, worker M5-A2):** hai điểm trừ kỹ thuật
cục bộ của hạng mục 3 đã xử lý trong phạm vi cục bộ — ký Cosign cho
evidence bundle (mức khoá cục bộ tạm theo lần chạy) và bộ unit test
riêng cho bundle_tool — và đã chấm lại đúng các dòng bị ảnh hưởng
(mục 1, 3, 5). Mọi dòng điểm thuộc M5-B/UNVERIFIED giữ nguyên.

**Cập nhật M5-A3 (2026-10-22, worker M5-A3, theo lệnh chủ sở hữu
"làm liên tục cho tới khi xong phần làm được mới dừng"):** vòng vét
cạn cục bộ — đóng 4 hàng bằng chứng còn thiếu của bản đồ pha 1 cộng
ci-log (truy vết 6/14 → **13/14 đầy đủ**, chứng minh bằng bundle mới
verify PASS); quét toàn bộ 210 mục checklist nhà máy (119 đạt, 4 đã
sửa trong vòng, 67 không áp dụng có lý do, 20 bị khoá phát hành —
`release/checklist-sweep-m5a3.md`); tăng unit test Python 8 → 36;
soạn sẵn bản nháp bài dev.to (chưa đăng). Chấm lại: hạng mục 6 từ 0
→ 2 (bản nháp hoàn chỉnh đã kiểm chứng), **tổng 69,5/100 — đây là
TRẦN CỤC BỘ**: toàn bộ 30,5 điểm còn lại đều khoá ở phía phát hành/
người dùng thật (phân rã ở mục 5). Mọi dòng đóng băng giữ nguyên.

## KẾT LUẬN CỦA HỒ SƠ

**Tổng điểm hội đồng: 69,5/100 — CHƯA ĐẠT CỔNG 99. KHÔNG PHÁT HÀNH.**
(66/100 tại M5-A; +1,5 tại M5-A2 từ hai điểm trừ kỹ thuật cục bộ của
hạng mục 3 đã xử lý xong và kiểm chứng thật; +2 tại M5-A3 từ bản nháp
bài dev.to hoàn chỉnh của hạng mục 6 — xem mục 3 và 5. **69,5 là
trần cục bộ**: sau vòng M5-A3 không còn điểm trừ nào gỡ được tại
chỗ; 30,5 điểm còn lại đều cần repo/CI thật, hành động publish,
hoặc người dùng thật.)

Phần lớn điểm chưa đạt nằm ở các hạng mục *về bản chất* chỉ kiểm chứng
được khi phát hành thật (GitHub Actions, phân phối, bài dev.to) — chúng
được ghi UNVERIFIED và **không** được cộng điểm theo đúng quy tắc của
mốc. Theo quyết định của chủ sở hữu (2026-10-22 ~18:17, ghi ở đầu hồ
sơ), các hạng mục này **không** được mở khoá bằng repo tạm hay bất kỳ
ngoại lệ đo lường nào: điểm trần dưới 99 được chấp nhận cho tới khi có
cách kiểm chứng hợp lệ khác, và M5-B giữ trạng thái đóng băng. Chi
tiết từng điểm bị trừ ở mục 4–5. Đây là kết quả kỳ vọng của một hồ sơ
trung thực, không phải thất bại kỹ thuật: toàn bộ phần cục bộ có thể
kiểm chứng đã đạt (mục 1–2).

---

## 1. Việc đã làm tại M5-A (nhiệm vụ 1–6) và bằng chứng

| # | Hạng mục | Kết quả | Bằng chứng trong cây |
|---|---|---|---|
| 1 | Mở khoá terraform plan/validate | Refactor rule SG inline → tài nguyên `aws_vpc_security_group_*_rule` riêng, nhất quán 2 biến thể; vẫn đúng 4 file khác biệt của planted, bản chất 4 lỗi không đổi. `terraform validate` **PASS cả hai biến thể** (trước: FAIL vì cycle); `terraform fmt -check` PASS. Chạy lại toàn bộ kiểm chứng: ma trận không đổi (clean qua hết; planted DENY đúng gate 1/4/5/8, network_exposure DENY ×2). Harness policy vẫn 34/34. **terraform plan vẫn chưa sinh được tại chỗ** — lý do thật: plan cần gọi AWS API cho data source `aws_availability_zones`; thử plan với credential giả treo đúng ở data source này (đã ghi vào gate-04.sh + record). Gate tiếp tục dùng conftest parse HCL2 + validate. | `examples/payments-sample/{clean,planted}/infra/main.tf`, `evidence/output/local-*/gate-04-iac/validate.json` (passed=true), `gates/verification/results.md` (đã render lại) |
| 2 | Dọn workflow | Đã gỡ hẳn job `collect-gate-outputs` (gộp artefact `merge-multiple` gây ghi đè record) khỏi `all-gates.yml`; job `evidence-bundle` là đường gom duy nhất. Cả 12 file workflow YAML hợp lệ; gate 9 chạy lại: PASS cả hai biến thể. | `.github/workflows/all-gates.yml` |
| 3 | Golden path + dogfood | Template hoàn thiện tại `templates/api-service/` (khung service + Dockerfile/IaC/K8s chuẩn + CI 10 gates + `devsecops-os.yml` + CODEOWNERS + branch-protection-as-code + hướng dẫn từng bước). Dogfood: dựng `examples/checkout-sample/` **từ chính template**, chạy toàn pipeline cục bộ (smoke backend thật + 10 gates + bundle + verify): **mọi bước exit 0 ngay lần chạy đầu, tổng 100 giây** (ngân sách 30 phút). Phần CI thật: UNVERIFIED. | `templates/`, `examples/checkout-sample/`, `release/dogfood-checkout-sample.md`, `release/dogfood-run.log` |
| 4 | Demo | GIF 30 giây dựng từ output của phiên chạy THẬT (`script` ghi lại, 91 giây chạy thật: gates trên 2 biến thể + bundle verify + thử sửa 1 byte → FAIL đúng file). Kèm transcript dạng chữ + script tái hiện. GIF là bản diễn lại dạng chữ của các dòng output thật (nén thời gian chờ, nội dung không đổi — ghi rõ trong transcript). | `release/demo/demo-terminal.gif`, `demo-transcript.txt`, `replay.sh`, `demo-raw.typescript` |
| 5 | Nội dung landing | Đã soạn sẵn nội dung trang techdev.fun (hero "ai đau/làm gì", cách hoạt động, bằng chứng có nhãn cục bộ, giới hạn đã biết) — **chưa deploy**. README repo đã có demo + "ai đau, hệ làm gì" ở phần đầu trang và banner trạng thái đúng sự thật M5-A. | `release/landing-techdev-fun.md`, `README.md` |
| 6 | Quét rủi ro | Gitleaks toàn cây + rà 5 lớp rủi ro. Sửa tại chỗ: xoá 3 cosign.key tạm + 3 `__pycache__`, bổ sung SECURITY.md, sửa 4 điểm tài liệu sai/lỗi thời (README, payments-sample README, golden-paths.md, câu ghi cứng trong render_results_md.py). Còn tồn 5 mục R1–R5, cao nhất là R4 (chưa đo trên Actions). | `release/risk-sweep-m5a.md` |
| 7 | (M5-A2) Ký bundle + unit test bundle_tool | `collect --sign`: ký Cosign trên `bundle.sha256` bằng khoá tạm sinh ngoài cây, huỷ ngay sau khi ký (khoá riêng không vào bundle, không nằm lại trong cây); khai báo chữ ký + vân tay khoá công khai nằm trong manifest/bundle.json; `verify` một lệnh kiểm thêm chữ ký và FAIL ồn ào khi thiếu/sai/không kiểm được. Kiểm chứng thật trên dữ liệu lần chạy `local-clean`: bundle ký → verify PASS cả hash + chữ ký; sửa 1 byte → FAIL nêu đúng file; thay chữ ký bằng chữ ký của bundle planted → FAIL "invalid signature"; sửa record kèm tính lại hash nhất quán (test tự động) → FAIL ở lớp chữ ký; bundle có khai báo chữ ký nhưng máy không có cosign → FAIL. Unit test: **8 test, toàn bộ xanh** (`python3 -m unittest discover -s evidence/tests`, 15,3 giây) phủ collect/verify/schema nghiêm + allow-incomplete/gate 10 disabled/sửa 1 byte/3 ca chữ ký. Giới hạn đã ghi trong `evidence/README.md`: khoá cục bộ tạm thời, không tlog, không gắn danh tính OIDC — keyless trên CI thuộc M5-B (đang đóng băng). | `evidence/bundle_tool.py` (v1.1.0), `evidence/verify_bundle.py`, `evidence/tests/test_bundle_tool.py`, `evidence/README.md` |
| 8 | (M5-A3) Đóng bằng chứng quyết định/định kỳ + vét cạn cục bộ | **Bộ sinh bằng chứng** `evidence/generators.py` (stdlib-only): `change-record` sinh từ kết quả gates thật của một lần chạy (quyết định do policy `change_record` chạy thật bằng OPA — DENY đúng vì lần chạy cục bộ không có phê duyệt PR), `drift-report` từ so cấu hình IaC với baseline đã khai (phát hiện đúng +2 rule mở trên planted, 0 mục trên clean), `access-review-report` rà 13 workflow trong cây (0 finding mức cao), `config-baseline-report` đánh giá 3 policy IaC trên cấu hình hiện tại (planted: network_exposure DENY). Collector (`bundle_tool.py` v1.2.0) quét thêm thư mục `supplementary-records/` và **tự phát hành record `ci-log`** (đóng gói log lần chạy thành zip tất định kèm SHA-256; verify đối chiếu chéo hash record ↔ artefact — test giả mạo bị bắt). Chứng minh: bundle `local-clean-m5a3` đóng ở chế độ nghiêm + verify **PASS** (66 file hash, 27 record khớp schema), truy vết **13/14 đầy đủ** (còn row-05 vì gate 10 tắt theo thiết kế). Kèm theo: quét 210 mục checklist (4 mục sửa tại chỗ: CHANGELOG.md, CONTRIBUTING.md, ISSUE_TEMPLATE, quy trình lộ secret trong SECURITY.md; sửa tham chiếu workflow gate-10 sai tên ở template + dogfood; xoá 2 khoá cosign sót trong thư mục lần chạy); **28 unit test mới** (15 cho bộ sinh + mở rộng collector, 13 cho adapters của gates — gồm chuỗi Syft+Cosign thật); bản nháp bài dev.to `release/devto-article-draft.md` (chưa đăng). | `evidence/generators.py`, `evidence/baselines/`, `evidence/bundles/local-clean-m5a3-*`, `evidence/tests/test_generators.py`, `gates/local/tests/test_adapters.py`, `release/checklist-sweep-m5a3.md`, `release/devto-article-draft.md`, `CHANGELOG.md`, `CONTRIBUTING.md` |

## 2. Đối chiếu 6 tiêu chí nghiệm thu của blueprint

| # | Tiêu chí | Kết luận tại M5-A |
|---|---|---|
| 1 | Master workflow ≤ 15 phút, trung vị 3 lần chạy trên GitHub Actions | **UNVERIFIED** — chưa có repo/Actions. Ước lượng cục bộ: bộ gates chạy tuần tự ~141 giây/biến thể (máy kiểm chứng, cache ấm); trên Actions các gate chạy song song theo job. Số chính thức chỉ có ở M5-B. |
| 2 | Clean qua 100%; planted bị chặn đúng gate; 0 chặn nhầm / 0 lọt | **ĐẠT (cục bộ)** — kiểm chứng lại đầy đủ tại M5-A sau refactor: đúng ma trận tuyệt đối ở `gates/verification/results.md`. |
| 3 | Mọi hàng ánh xạ pha 1 có policy + thực thi + bằng chứng tự sinh | **ĐẠT (13/14 hàng đầy đủ)** — tại M4/M5-A: 6/14 đầy đủ, 4 một phần, 4 chưa có. Tại M5-A3: bộ sinh bằng chứng + ci-log của collector đóng nốt các hàng 02, 03, 08, 09, 12, 13, 14 (bundle chứng minh `local-clean-m5a3`, verify PASS). Hàng duy nhất còn một phần là row-05 (`pr-review-report`) — chỉ sinh khi gate 10 bật, mà gate 10 TẮT là điều kiện thiết kế của pha 1, nên trạng thái này là đúng nghiệm thu chứ không phải thiếu sót. |
| 4 | Evidence bundle có manifest SHA-256, kiểm chứng một lệnh | **ĐẠT (cục bộ)** — verify PASS cả hai biến thể + bản dogfood; sửa 1 byte → FAIL chỉ đúng file (kiểm chứng lại ngay trong phiên demo M5-A). Từ M5-A2: bundle đóng bằng `--sign` còn có chữ ký Cosign trên `bundle.sha256` và cùng một lệnh verify kiểm thêm chữ ký (3 ca kiểm chứng tại mục 1 dòng 7). |
| 5 | Golden path ≤ 30 phút, CI xanh ngay lần chạy đầu | **ĐẠT phần cục bộ** (100 giây, xanh lần đầu — biên bản dogfood); **UNVERIFIED phần GitHub Actions** (chờ M5-B). |
| 6 | Tài liệu từng policy + README có demo/"ai đau" ở đầu trang | **ĐẠT** — `policies/README.md` + tài liệu từng policy; README đầu trang có demo GIF + mục "Ai đau, hệ này làm gì" + trạng thái trung thực. |

## 3. Bảng điểm hội đồng (RUBRIC-NGHIEM-THU-100)

Thang gốc của rubric giữ nguyên. Ban 5 (Hội đồng phản biện & người dùng
thử) là ban chấm chính mọi hạng mục; các ban xác nhận chéo ghi ý kiến
riêng. Phần phụ thuộc môi trường thật (GitHub Actions/phát hành) ghi
UNVERIFIED và không cộng điểm.

| Hạng mục | Tối đa | Điểm | Ban chấm / xác nhận | Căn cứ & điểm trừ |
|---|---|---|---|---|
| 1. Vừa pain & khác biệt | 20 | **18** | Ban 5 chấm; Ban 1 (chiến lược) xác nhận | Pain rõ và có tên người đau cụ thể trong README/landing; khác biệt với Harness/GHAS/Snyk có phân tích nguồn từ blueprint. −2: chưa có kiểm chứng từ người dùng thật/tổ chức thật nào; khác biệt chưa được đo trên đối thủ bằng tay. |
| 2. Chạy thật & e2e | 20 | **12** | Ban 5 | Cục bộ đạt mức tối đa có thể: ma trận gates tuyệt đối trên 2 biến thể + dogfood lần đầu xanh + bundle verify hai chiều. −8: tiêu chí gốc yêu cầu chạy thật *trong môi trường đích* — master workflow trên GitHub Actions (trung vị 3 lần) và golden path trên CI thật đều UNVERIFIED (toàn bộ phần này chờ M5-B). |
| 3. Chất lượng mã & kiểm thử | 15 | **14,5** | Ban 5; Ban 3 (kỹ thuật) xác nhận | Toolchain ghim phiên bản + SHA-256; OPA test 48/48; harness 34/34; Kyverno đạt; tooling nội bộ stdlib-only; template được dogfood thật. Tại M5-A2: unit test riêng cho bundle_tool đã có (**8 test, xanh toàn bộ** — cộng lại +1); bundle đã ký Cosign và kiểm chứng 3 ca thật, nhưng mới ở mức khoá cục bộ tạm thời (không tlog, không gắn danh tính OIDC) nên chỉ cộng +0,5 — còn −0,5 cho phần chứng thực đầy đủ (keyless/OIDC + Rekor trên CI, thuộc M5-B đang đóng băng). |
| 4. Demo + README đầu trang | 15 | **13** | Ban 5; Ban 9 (trình bày) xác nhận | GIF ~30 giây từ phiên chạy thật + transcript + script tái hiện; README đầu trang đủ demo + "ai đau" + trạng thái trung thực. −1: GIF là bản diễn lại dạng chữ của output thật (đã ghi nhãn) thay vì quay màn hình trực tiếp; −1: ảnh demo chỉ hiển thị được sau khi repo công bố (liên kết tương đối trong repo). |
| 5. Sẵn sàng phân phối | 15 | **5** | Ban 5; Ban 2 (tăng trưởng) + Ban 7 (vận hành phát hành) xác nhận | Đã có: LICENSE, SECURITY.md, nội dung landing soạn sẵn, hồ sơ phát hành, cây repo sạch sau quét rủi ro. −10: repo chưa tồn tại trên GitHub (đúng giới hạn M5-A), chưa topics/release/trang landing trực tiếp, chưa kênh phân phối nào hoạt động — hạng mục này về bản chất thuộc M5-B. |
| 6. Bài dev.to | 10 | **2** | Ban 5; Ban 6 (nội dung) xác nhận | Tại M5-A: 0 (chưa có bài viết). Tại M5-A3: **bản nháp bài kỹ thuật hoàn chỉnh đã soạn và kiểm chứng** tại `release/devto-article-draft.md` — cấu trúc vấn đề → cách làm → demo → repo, bảng so sánh đối thủ có nguồn + mục "điểm đối thủ hơn ta", chỉ tuyên bố đã kiểm chứng, trục nội dung là biên bản dogfood + ma trận planted (đúng đề xuất của Ban 6 ở M5-A) — cộng +2 cho phần nội dung sẵn sàng đăng. −8 còn lại: bài **chưa đăng** (chưa có id/link, chưa gắn canonical hai chiều với repo) — thuộc M5-B đóng băng. |
| 7. An toàn & tuân thủ | 5 | **5** | Ban 5; Ban 8 (an toàn) xác nhận chéo — không dùng quyền phủ quyết | Quét gitleaks: mã nguồn chỉ có secret giả cài có chủ đích đã tài liệu hoá; khoá tạm đã xoá; LICENSE MIT đầy đủ; không nội dung vi phạm bản quyền; không tương tác giả. Xem `risk-sweep-m5a.md`. |
| **TỔNG** | **100** | **69,5** | | (66 tại M5-A; 67,5 sau chấm lại M5-A2; 69,5 sau M5-A3 — chỉ hạng mục 6 thay đổi ở vòng này) |

### Ý kiến từng ban (tóm tắt)

- **Ban 1 — Chiến lược & định vị:** xác nhận hạng mục 1; định vị
  "lớp quản trị + bằng chứng trên các scanner" là khác biệt có thật,
  không trùng tuyên bố của đối thủ lớn.
- **Ban 2 — Tăng trưởng & phân phối:** hạng mục 5 chưa thể cao hơn khi
  chưa có mặt trên GitHub; landing đã soạn là đầu vào tốt cho M5-B.
- **Ban 3 — Kỹ thuật & kiến trúc:** xác nhận hạng mục 3; ghi nhận
  refactor SG đúng chuẩn tài nguyên riêng và adapter/harness đã được mở
  rộng tương ứng mà không đổi kỳ vọng kiểm chứng. (M5-A2: xác nhận bổ
  sung ký Cosign cho bundle + 8 unit test của bundle_tool — điểm hạng
  mục 3 tăng 13 → 14,5 theo đúng phần đã kiểm chứng, phần keyless/OIDC
  chưa chấm.) (M5-A3: xác nhận bộ sinh bằng chứng + 28 unit test mới
  đều kiểm chứng thật — điểm hạng mục 3 **không đổi** vì điểm trừ còn
  lại của nó chỉ là chứng thực danh tính chữ ký (OIDC/Rekor), không
  phải độ phủ test.)
- **Ban 4 — Sản phẩm & trải nghiệm:** README đầu trang đạt yêu cầu
  "hiểu trong 30 giây"; đường chạy thử cục bộ rõ ràng.
- **Ban 5 — Hội đồng phản biện & người dùng thử:** giữ nguyên tắc
  không điểm cho UNVERIFIED; tổng 69,5 (sau M5-A3) phản ánh đúng
  khoảng cách tới phát hành, không phải chất lượng phần đã kiểm chứng.
- **Ban 6 — Nội dung & dev.to:** tại M5-A: 0 điểm hạng mục 6; đề xuất
  bài viết dùng chính biên bản dogfood + ma trận planted làm trục nội
  dung. (M5-A3: bản nháp theo đúng trục đó đã hoàn thành và tự kiểm
  chứng theo checklist Ban 6 — chấm 2/10 cho phần nội dung sẵn sàng;
  8 điểm còn lại gắn với hành động đăng.)
- **Ban 7 — Vận hành & bàn giao:** hồ sơ + biên bản + script tái hiện
  đủ để bàn giao M5-B; lưu ý R5 (khoá tạm gate 6) cho pha sau.
- **Ban 8 — An toàn & pháp lý:** không phủ quyết; 5 điều kiện cứng đều
  qua (mục 4). Nhắc: khi tạo repo ở M5-B phải commit đúng cây đã quét.
- **Ban 9 — Trình bày & tài liệu:** xác nhận hạng mục 4; GIF rõ, tiếng
  Việt hiển thị đúng, nhãn trung thực về cách dựng demo.
- **Ban 10 — Kiểm chứng độc lập:** đã đối chiếu độc lập các số trong hồ
  sơ này với `gates/verification/results.md`, `validate.json`,
  `release/dogfood-timings.tsv` và log phiên demo — khớp.

## 4. Năm điều kiện cứng (rubric — vi phạm bất kỳ = FAIL bất kể điểm)

| Điều kiện | Kết quả |
|---|---|
| Mã chạy được / e2e đạt | ✅ Qua ở cục bộ (toàn bộ pipeline chạy thật; phần Actions là UNVERIFIED chứ không phải FAIL) |
| Không chứa secret | ✅ Qua (duy nhất secret giả cài có chủ đích, đã tài liệu hoá là fixture kiểm chứng) |
| Không vi phạm bản quyền | ✅ Qua (mã gốc; công cụ ngoài chỉ được gọi, không nhúng) |
| Có LICENSE | ✅ Qua (MIT) |
| Không tương tác giả | ✅ Qua (chưa phát hành; không star/issue/comment giả nào tồn tại) |

## 5. Các điểm bị trừ và đường lên 99

Tổng bị trừ: **30,5 điểm** (34 tại M5-A; giảm 1,5 tại M5-A2; giảm
thêm 2 tại M5-A3). Phân rã chính xác:

| Khối điểm trừ | Điểm | Muốn lấy lại phải làm gì | Mốc |
|---|---|---|---|
| Hạng mục 2 — e2e trên môi trường đích chưa kiểm chứng | −8 | Chạy master workflow trên GitHub Actions ≥3 lần, lấy trung vị ≤15 phút; chạy golden path trên CI thật xanh lần đầu; ghi số vào hồ sơ và chấm lại | M5-B — **ĐÓNG BĂNG** (quyết định chủ sở hữu 22/10/2026) |
| Hạng mục 5 — phân phối chưa tồn tại | −10 | Công bố repo đúng cây đã duyệt (topics, mô tả, release), đưa landing lên techdev.fun từ file đã soạn, kiểm tra hiển thị thật | M5-B — **ĐÓNG BĂNG** |
| Hạng mục 6 — bài dev.to chưa đăng | −8 | ĐÃ XỬ LÝ MỘT PHẦN TẠI M5-A3: bản nháp hoàn chỉnh đã soạn + kiểm chứng (+2). Phần còn lại: đăng bài sau khi repo công bố, gắn liên kết hai chiều repo ↔ bài, ghi id/link vào hồ sơ | M5-B — **ĐÓNG BĂNG** |
| Hạng mục 1 — chưa có kiểm chứng người dùng thật | −2 | Có phản hồi/bằng chứng dùng thử từ ít nhất một đội ngũ thật, hoặc đối chiếu tay với đối thủ trên cùng workload và công bố kết quả đo | Sau phát hành |
| Hạng mục 3 — phần chứng thực đầy đủ của chữ ký bundle | −0,5 | ĐÃ XỬ LÝ TẠI M5-A2: unit test bundle_tool (+1) và ký Cosign mức khoá cục bộ (+0,5). Phần còn lại: chữ ký keyless/OIDC + Rekor trên CI để danh tính chữ ký gắn với workflow | M5-B — **ĐÓNG BĂNG** |
| Hạng mục 4 — demo diễn lại dạng chữ; liên kết demo chờ repo | −2 | Sau khi repo công bố: kiểm tra GIF hiển thị thật trên trang repo; cân nhắc quay capture trực tiếp bổ sung nếu hội đồng yêu cầu | M5-B — **ĐÓNG BĂNG** |

**Nhận định thẳng:** các khối M5-B ở trên hiện **đóng băng theo quyết
định của chủ sở hữu** (không tạo repo dưới bất kỳ hình thức nào để
đo) — chúng được ghi lại thuần tuý để hồ sơ trung thực về điều kiện
chưa kiểm chứng, không phải đường đi đang mở. Ngay cả trong giả
thuyết M5-B được mở lại và làm trọn, điểm dự kiến đạt ~97–99 — cổng
99 đòi hỏi hội đồng chấm lại trên bằng chứng thật và gần như không
còn điểm trừ nào, kể cả các điểm trừ nhỏ ở hạng mục 1/3/4. Hồ sơ này
không làm tròn số và không hứa trước kết quả chấm lại.

**TRẦN CỤC BỘ = 69,5/100 (chốt tại M5-A3).** Sau vòng vét cạn
M5-A3, cả 6 khối điểm trừ còn lại đều nằm ngoài tầm cục bộ, từng
khối một: −8 (hạng mục 2) cần GitHub Actions thật — không tồn tại
khi chưa có repo; −10 (hạng mục 5) là chính hành động công bố repo/
landing — bị đóng băng; −8 (hạng mục 6) là hành động đăng bài —
đi cùng publish; −2 (hạng mục 1) cần người dùng/tổ chức thật dùng
thử — không thể tự tạo mà không thành tương tác giả (điều kiện
cứng cấm); −0,5 (hạng mục 3) cần danh tính OIDC/Rekor của CI thật;
−2 (hạng mục 4) gồm liên kết hiển thị trên repo công khai và yêu
cầu capture trực tiếp được hội đồng nghiệm thu trên bản công khai.
Không còn điểm trừ nào trong tầm cục bộ đang mở.

## 6. Trạng thái quyết định (đã chốt — không còn khuyến nghị mở)

1. **Không phát hành ở trạng thái hiện tại** (69,5/100 < 99) — đúng
   quy tắc cổng đã đặt.
2. **Chủ sở hữu đã quyết định (2026-10-22 ~18:17, qua Tổng quản):**
   giữ cổng 99/100 theo đúng chữ; **không tạo repo private tạm để
   đo, không ngoại lệ đo lường**; chấp nhận điểm trần dưới 99 cho
   tới khi có cách kiểm chứng hợp lệ khác. M5-B **đóng băng**:
   không tạo repo (công khai hay riêng tư), không đo GitHub Actions,
   không đưa landing lên trực tiếp, không viết/đăng bài dev.to.
   Hồ sơ này không đề xuất lại các đường đo qua repo tạm như một
   lựa chọn — quyết định đã chốt.
3. Hai điểm trừ kỹ thuật cục bộ được nêu ở bản M5-A của mục này
   (ký bundle, unit test bundle_tool) **đã hoàn thiện tại M5-A2**
   (mục 1 dòng 7); vòng **M5-A3** đã vét cạn phần cục bộ còn lại
   (mục 1 dòng 8): bằng chứng quyết định/định kỳ, độ phủ kiểm thử,
   quét checklist toàn diện, bản nháp dev.to. **Trần cục bộ chốt ở
   69,5/100** — phần còn mở chỉ gồm các UNVERIFIED thuộc M5-B đóng
   băng và hạng mục 1 (kiểm chứng người dùng thật — sau phát hành).

---

## 7. M5-B LIVE — BỔ SUNG NGHIỆM THU TRÊN GITHUB THẬT (đêm 2026-10-22)

Chủ sở hữu đã **mở khoá đo lường** (2026-10-22 ~23:02) và lệnh tạo
repo ngay trong đêm (~23:17, chủ sở hữu tự ghi đè khung giờ tạo repo
08:00–22:00 cho lần này). Toàn bộ số đo dưới đây là bằng chứng thật
trên GitHub, kiểm chứng lại qua API:

- Repo `techdevfun/devsecops-os` (id 1430021492) tạo **PRIVATE**;
  cây 235 file đẩy qua Git Data API, mọi blob khớp SHA với bản cục
  bộ. Commit ứng viên phát hành: `1b4d1f87`.
- **Workflow tổng trên Actions (3 lần liên tiếp, workload sạch):**
  run 39818433394 = 54 giây, run 39818602558 = 66 giây,
  run 39818765418 = 58 giây — cả 3 `success`, 11/11 job xanh.
  **Trung vị 58 giây** (tiêu chí ≤ 15 phút → ĐẠT, vượt xa).
- **Biến thể gài lỗi trên CI:** run 39818945487 `failure` đúng thiết
  kế — fail ở đúng gate-01, gate-04, gate-05, gate-08; 7 job còn lại
  success. Ma trận gate khớp 100% với nghiệm thu cục bộ.
- **Golden path trên CI thật:** repo scratch riêng
  `techdevfun/devsecops-os-goldenpath-ci` (id 1430031722, private)
  dựng từ template; run 39819226621 `success` **ngay lần chạy đầu**,
  11/11 job xanh; tổng dựng + đẩy + CI **5 phút 42 giây**
  (tiêu chí ≤ 30 phút → ĐẠT).
- **Ký keyless (OIDC) cho evidence bundle trên CI:** commit ứng viên
  nối Cosign sign-blob + verify-blob vào job evidence-bundle
  (cosign v3.1.4 ghim sha256; chỉ thêm quyền `id-token: write` cho
  job đó). Run xác nhận 39820512697 `success` 69 giây; bước ký +
  tự xác minh **success**. Phần trừ keyless của hạng mục 3 tại
  M5-A2 nay đã gỡ.
- Repo đã có: mô tả, 12 topics, release `v1.0.0-phase1`
  (prerelease, id 420992051) trỏ đúng commit ứng viên.
- Sự cố kỹ thuật trong đêm (đã xử lý, không ảnh hưởng sản phẩm):
  Git Data API trả 409 trên repo rỗng → khởi tạo bằng Contents API
  rồi đẩy tiếp; POST cây 235 mục bị GitHub timeout 422 → dựng cây
  tăng dần theo thư mục (đúng gợi ý trong thông báo lỗi của GitHub).

### Bảng điểm hội đồng sau M5-B (chấm trên bằng chứng thật)

| # | Hạng mục | Tối đa | Điểm | Căn cứ |
|---|----------|-------:|-----:|--------|
| 1 | Vấn đề thật & khác biệt | 20 | **18** | Không đổi: chưa có kiểm chứng người dùng ngoài thật — theo tính chất chỉ có sau phát hành. |
| 2 | Chạy thật & e2e | 20 | **20** | CI thật trên đúng commit ứng viên: 3 run success, trung vị 58 giây; planted chặn đúng 4 gate trên CI; golden path xanh lần đầu 5 phút 42 giây; toàn bộ test cục bộ xanh (OPA 48/48, harness 34/34, evidence 23 test, adapters 13 test). |
| 3 | Chất lượng mã & kiểm thử | 15 | **15** | Ký keyless OIDC/Rekor cho bundle CI đã nối và kiểm chứng tại run 39820512697 — gỡ nốt phần trừ cuối của M5-A2. |
| 4 | Demo & README | 15 | **14** | Đã chấm lại 2026-10-23 (§8): GIF thay bằng bản QUAY THÔ terminal thật — phiên `script` chạy `replay.sh`, dựng frame-theo-frame từ bản ghi thô bằng giả lập VT, tốc độ thực 1.0×, không gõ lại/sửa output — gỡ điểm trừ "dựng lại dạng chữ". −1 còn lại: kiểm chứng hiển thị trên repo công khai — hoàn thành bởi chính hành động phát hành. |
| 5 | Sẵn sàng phân phối | 15 | **11** | Repo + mô tả + topics + release ứng viên đã có; −4: landing chưa lên sóng và repo chưa công khai — cả hai là hành động phát hành. |
| 6 | Bài dev.to | 10 | **2** | Bản nháp hoàn chỉnh đã kiểm chứng (M5-A3); −8 bài chưa đăng — đăng bài là hành động phát hành (canonical phải trỏ repo công khai). |
| 7 | An toàn & tuân thủ | 5 | **5** | 5 điều kiện cứng đạt cả 5 (xem dưới). |
| | **TỔNG** | **100** | **85** | |

**5 điều kiện cứng: ĐẠT CẢ 5** — mã chạy + e2e CI pass trên commit
ứng viên; không secret thật trong cây đẩy (quét gitleaks lúc đóng
băng: chỉ 2 fixture giả đã ghi chú); không vi phạm bản quyền (công
cụ bên thứ ba tải lúc chạy, không đóng gói lại); có LICENSE (MIT);
không tương tác giả.

### Kết luận M5-B theo đúng chữ của cổng (GĐ8)

**84/100 < 99 → KHÔNG PHÁT HÀNH trong lượt này.** Repo giữ PRIVATE.
Phân rã 16 điểm trừ còn lại: **15 điểm bị khoá bởi chính hành động
phát hành** (hạng mục 1: −2 kiểm chứng người dùng sau phát hành;
hạng mục 4: −1 hiển thị công khai; hạng mục 5: −4 landing + công
khai; hạng mục 6: −8 đăng bài dev.to) và 1 điểm ở dạng demo (GIF
dựng lại dạng chữ, đã ghi chú trung thực — lựa chọn giữ nguyên của
hội đồng). Nói cách khác: **mọi tiêu chí đo được trước phát hành
đều đã đạt tối đa hoặc gần tối đa** (hạng mục 2 và 3 đạt điểm tuyệt
đối trên bằng chứng CI thật); điểm 99 theo đúng chữ chỉ có thể
chấm SAU khi các hành động phát hành đã thực hiện — cổng hiện tại
yêu cầu điểm trước, hành động sau, nên lượt này dừng ở GĐ8 và chờ
quyết định của chủ sở hữu: (a) chấp nhận phát hành ở mức bằng chứng
hiện tại rồi chấm lại sau phát hành, hoặc (b) giữ cổng nguyên văn
và giữ repo private.

## 8. CHẤM LẠI THEO CỔNG KHẢ THI — quyết định chủ sở hữu 2026-10-23 00:33

**Quyết định của chủ sở hữu (2026-10-23 00:33, thay thế điều kiện
"≥99 mới lật public" ở §6–§7 và mọi tài liệu trước):** áp **CỔNG PHÁT
HÀNH KHẢ THI** cho cả hai flagship, rút bài học từ cổng giọng văn
LinkedIn (thang tuyệt đối vận hành không nổi → trung vị cao + sàn từng
ban + ghi đè có ghi chép). Cách chấm mới: **điểm CHẤT LƯỢNG** = tổng
hạng mục 1+2+3+4+7 (tối đa 75) chuẩn hoá /100; **điểm PHÂN PHỐI** =
hạng mục 5+6 (tối đa 25) theo dõi riêng và được hoàn thành BỞI hành
động phát hành. Điều kiện lật public: chất lượng ≥ 95/100 VÀ sàn từng
ban (HM1 ≥ 18/20, HM2 ≥ 18/20, HM3 ≥ 13,5/15, HM4 ≥ 13,5/15,
HM7 = 5/5) VÀ 5 điều kiện cứng qua VÀ 0 rủi ro cao chưa xử lý.
99/100 từ nay là **đích trau chuốt SAU phát hành**, không phải điều
kiện phát hành. Kết luận GĐ8 ở §7 (dừng vì 84 < 99 theo cổng cũ) được
thay thế bởi mục này.

### Việc đã làm trong vòng chấm lại (2026-10-23)

Điểm trừ cục bộ duy nhất còn sửa được là ở hạng mục 4: GIF demo là bản
dựng lại dạng chữ từ output thật (−1). Đã làm lại bằng **quay thô
terminal thật**, đúng kỹ thuật vừa đưa flagship #1
(ai-pr-review-gate 0.4.3) lên 15/15 ở hạng mục tương ứng:

- Phiên terminal thật chạy `bash release/demo/replay.sh` (gates 1/4/8
  trên cả hai biến thể clean/planted + đóng gói & kiểm chứng evidence
  bundle + ca sửa 1 byte → kiểm chứng FAIL đúng tệp), ghi nguyên bản
  bằng `script` (util-linux) ngày 2026-10-23 00:57 giờ Việt Nam
  (17:57:13–17:57:46 UTC, mã thoát phiên 0). Kết quả trong phiên khớp
  kịch bản: clean qua cả 3 gate; planted bị DENY đúng gate 1 (secret),
  gate 4 (network_exposure), gate 8 (CVE-2026-48710); bundle verify
  PASS (58 tệp khớp hash, 21 record khớp schema); bản sửa 1 byte
  (`ci-log.record.json`) → verify FAIL chỉ đúng tệp đó.
- GIF dựng frame-theo-frame từ chính bản ghi thô
  (`release/demo/demo-raw.typescript` + `demo-raw.timing` đi kèm) bằng
  trình giả lập VT tối thiểu — không gõ lại lệnh, không sửa một dòng
  output nào, không chèn chữ trình bày vào khung hình; giữ nguyên wrap
  dòng và màu thật của terminal; phát lại tốc độ thực 1.0× (bản ghi
  33,3 giây → GIF 34,5 giây, 24 frame, 774 KB). Transcript và ghi chú
  trong README đã sửa cho khớp bản chất mới.
- **Chấm lại bảo thủ, chỉ hạng mục 4: 13 → 14/15** (+1 — điểm trừ
  "dựng lại dạng chữ" đã gỡ hẳn). Điểm trừ còn lại của hạng mục 4
  (−1, kiểm chứng hiển thị trên repo công khai) thuộc diện hoàn thành
  bởi hành động phát hành, không tự cộng trước.

### Bảng điểm theo cổng khả thi

| Hạng mục | Điểm | Sàn | Đạt sàn |
|----------|-----:|----:|:-------:|
| 1. Vấn đề thật & khác biệt | 18/20 | ≥ 18 | ✓ |
| 2. Chạy thật & e2e | 20/20 | ≥ 18 | ✓ |
| 3. Chất lượng mã & kiểm thử | 15/15 | ≥ 13,5 | ✓ |
| 4. Demo & README | 14/15 | ≥ 13,5 | ✓ |
| 7. An toàn & tuân thủ | 5/5 | = 5 | ✓ |
| **CHẤT LƯỢNG (HM 1+2+3+4+7)** | **72/75 = 96,0/100** | **≥ 95** | **✓** |
| 5. Sẵn sàng phân phối | 11/15 | — (theo dõi riêng) | |
| 6. Bài dev.to | 2/10 | — (theo dõi riêng) | |
| **PHÂN PHỐI (HM 5+6)** | **13/25** | hoàn thành bởi phát hành | |

- **5 điều kiện cứng: ĐẠT CẢ 5** (không đổi từ §7 — thay đổi vòng này
  chỉ là tệp demo/tài liệu, không đụng mã hay cây phát hành).
- **Rủi ro cao chưa xử lý: 0** (quét rủi ro trước phát hành ở M5-B;
  vòng này không phát sinh rủi ro mới).
- Tổng theo rubric 100 cũ (tham chiếu): **85/100**.

### Kết luận theo cổng khả thi

**ĐẠT CỔNG KHẢ THI — đủ điều kiện phát hành:** chất lượng 96,0/100
≥ 95, mọi điểm sàn đều qua, 5 điều kiện cứng đạt, 0 rủi ro cao chưa
xử lý. Các bước phát hành còn lại theo đúng trình tự kỷ luật: gửi
bảng điểm này về Tổng quản TRƯỚC → lật public → đăng bài dev.to →
landing techdev.fun → dispatch backup → kiểm chứng trực tiếp từng
đích. (Vòng chấm lại này chỉ đẩy các tệp demo/hồ sơ lên repo private;
không tự lật public.)
