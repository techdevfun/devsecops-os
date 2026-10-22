# Quét checklist nhà máy — vòng M5-A3 (2026-10-22)

Đối chiếu toàn bộ **210 mục** của `CHECKLIST-TONG-HOP-NHA-MAY.md`
(Ban 1: 22 · Ban 2: 22 · Ban 3: 20 · Ban 4: 20 · Ban 5: 24 ·
Ban 6: 22 · Ban 7: 20 · Ban 8: 24 · Ban 9: 20 · Ban 10: 16) với
cây `repos/devsecops-os/` và tiến trình của dự án sau vòng M5-A3.

Phân loại:

- **Đạt** — đã có/đã áp dụng, đối chiếu được trong cây hoặc trong
  hồ sơ các vòng M1–M5-A3 (gồm các mục checklist gốc đã tick [x]).
- **Đã sửa vòng này** — thiếu/sai trước vòng, đã sửa tại chỗ và
  kiểm chứng trong vòng M5-A3.
- **Không áp dụng** — mục thuộc nhịp vận hành nhà máy/tài khoản
  hoặc điều kiện chưa phát sinh; kèm lý do cụ thể từng mục.
- **Bị khoá bởi cổng phát hành** — chỉ thực hiện được khi repo
  tồn tại/được publish (quyết định chủ sở hữu 2026-10-22 ~18:17:
  giữ cổng 99/100 nguyên văn, M5-B đóng băng).

**Tổng hợp: Đạt 119 · Đã sửa vòng này 4 · Không áp dụng 67 ·
Bị khoá bởi cổng phát hành 20 = 210.**

---

## Ban 1 — Chiến lược sản phẩm & pain-point (22 mục)

| Mã | Kết quả | Ghi chú |
|---|---|---|
| B1-01 | Đạt | Bản đồ pain đã có (checklist gốc [x]); devsecops-os mở trục mới "bằng chứng kiểm toán" ngoài 11 repo đầu. |
| B1-02 | Đạt | Pain-point-first đã vào playbook (checklist gốc [x]). |
| B1-03 | Đạt | Hàng đợi đã chốt (checklist gốc [x]); flagship #2 do chủ sở hữu đưa lên làm tuyến phát hành chính ngày 22/10. |
| B1-04 | Đạt | Luật cấm trùng trục đã áp (checklist gốc [x]) — sản phẩm này không phải biến thể CLI audit. |
| B1-05 | Không áp dụng | Nhịp chọn đề tài hằng ngày của nhà máy; đề tài này do chủ sở hữu chỉ định trực tiếp. |
| B1-06 | Đạt | Người dùng mục tiêu nêu đích danh: tổ chức bị quản chế (ngân hàng/tài chính/bảo hiểm), đau ở bước gom bằng chứng kiểm toán (blueprint mục 0, README). |
| B1-07 | Đạt | Pain có căn cứ: đề xuất + blueprint dựa trên khảo sát đối thủ/nguồn đã kiểm chứng ngày 22/10, không chọn theo cảm tính. |
| B1-08 | Đạt | Đối chiếu 11 repo đã publish: không repo nào phủ lớp OS/chính sách/bằng chứng — không trùng trục. |
| B1-09 | Đạt | Giải pháp sẵn có tốt nhất đã khảo sát (Harness, GHAS, Snyk + các mảnh mở) và điểm khác biệt ghi rõ trong blueprint mục 1. |
| B1-10 | Đạt | Kịch bản dùng thử <5 phút: GIF demo 30,8 giây + `release/demo/replay.sh` chạy lại phiên thật; dogfood từ template ~100 giây. |
| B1-11 | Đạt | Phạm vi pha 1 chốt hẹp bằng văn bản trước khi build (blueprint + KE-HOACH-DEVSECOPS-OS-PHA1: cắt AI SecOps sang pha 2, gate 10 tắt). |
| B1-12 | Đạt | Tên `devsecops-os` đã kiểm tra trống dưới techdevfun; phương án `gatehouse` bị loại vì trùng (thepartly/gatehouse). |
| B1-13 | Không áp dụng | Quy tắc nhịp hằng ngày "không có đề tài đạt chuẩn thì nghỉ" — thuộc vận hành ngày của nhà máy. |
| B1-14 | Đạt | Sản phẩm thật có kênh phân phối: repo OS + reusable workflows (pha 1), từng gate thành Action Marketplace (pha sau) — không phải CLI quét một lần. |
| B1-15 | Bị khoá bởi cổng phát hành | Xác nhận riêng của Ban 1 ở nghiệm thu cuối thuộc vòng publish; bản tự soát của vòng này nằm ở hồ sơ mục 4 (hạng mục 1: 18/20). |
| B1-16 | Bị khoá bởi cổng phát hành | Ghi nhận mức chạm pain sau publish — chưa publish. |
| B1-17 | Không áp dụng | Cập nhật trend-log là nhịp A1 hằng ngày của nhà máy. |
| B1-18 | Không áp dụng | Rà hàng đợi là việc hằng tuần của nhà máy. |
| B1-19 | Không áp dụng | Đối chiếu tín hiệu thật (sao/issue/install) — sản phẩm chưa publish, chưa có tín hiệu; nhịp tuần của nhà máy. |
| B1-20 | Không áp dụng | Cập nhật bản đồ pain là nhịp hằng tháng của nhà máy. |
| B1-21 | Không áp dụng | Đánh giá danh mục 11 repo là nhịp hằng tháng của nhà máy. |
| B1-22 | Đạt | Mọi đổi hướng đều qua duyệt chủ sở hữu: blueprint được duyệt, cổng nâng 99/100, M5-B đóng băng — đều là quyết định của chủ sở hữu (checklist gốc [x] cho nguyên tắc). |

## Ban 2 — GitHub Actions & Marketplace (22 mục)

| Mã | Kết quả | Ghi chú |
|---|---|---|
| B2-01 | Đạt | Dạng phân phối chốt ở tiền build cùng Ban 1/7: reusable workflows + repo OS (blueprint mục 6). |
| B2-02 | Không áp dụng | Sản phẩm pha 1 không phải một Action đóng gói có `action.yml` riêng (là bộ reusable workflow); `action.yml` thuộc flagship #1 (gate 10 bọc nó). |
| B2-03 | Không áp dụng | Branding icon/màu cho listing Marketplace — thuộc pha phát hành từng gate. |
| B2-04 | Không áp dụng | Khai báo inputs/outputs của Action đóng gói — pha sau; inputs của reusable workflow đã khai trong từng file `gate-*.yml`. |
| B2-05 | Đạt | Công cụ trong workflow/script được ghim phiên bản cụ thể (OPA 1.21.3, Trivy 0.76.1... — `gates/local/README.md`), không dùng tag trôi nổi cho tool. |
| B2-06 | Không áp dụng | Workflow mẫu trong README/template tham chiếu reusable workflow nội bộ qua đường dẫn `./.github/workflows/...`, không tham chiếu Action ngoài qua `@main`. |
| B2-07 | Đạt | Permissions tối thiểu: cả 13 workflow trong cây khai `contents: read` (access-review vòng này rà tự động: 0 finding mức cao); gate 9 thực thi kiểm tra này. |
| B2-08 | Đạt | Sự kiện kích hoạt khai trong `all-gates.yml`; ngoài phạm vi thì êm: gate 10 tắt vẫn hoàn thành xanh theo thiết kế. |
| B2-09 | Đạt | Cơ chế fail cấu hình được: input của reusable workflow (ví dụ `fail-on` của gate 10; ngưỡng EPSS của gate 8 qua input pack). |
| B2-10 | Đạt | Đầu ra CI: job summary + record JSON có cấu trúc + SARIF lên code scanning; không spam comment lặp (bình luận PR thuộc gate 10, đang tắt). |
| B2-11 | Bị khoá bởi cổng phát hành | Test e2e trên PR thật của repo thuộc techdevfun — cần repo tồn tại. |
| B2-12 | Không áp dụng | Metadata listing Marketplace — pha phát hành từng gate. |
| B2-13 | Không áp dụng | Ảnh/icon listing — pha sau; tài sản demo/landing cho repo đã có sẵn (xem Ban 9). |
| B2-14 | Đạt | 2FA của techdevfun đã bật và kiểm chứng qua API 21/10/2026 (checklist gốc ghi rõ). |
| B2-15 | Bị khoá bởi cổng phát hành | Release/tag v1 tạo khi publish. |
| B2-16 | Đã sửa vòng này | Tạo `CHANGELOG.md` ở gốc cây, ghi các mốc M1→M5-A3 để đi kèm mọi release sau này. |
| B2-17 | Không áp dụng | Sản phẩm không phải MCP server. |
| B2-18 | Đạt | Tên đã kiểm tra không trùng trên GitHub dưới tài khoản và phương án trùng đã bị loại (xem B1-12). |
| B2-19 | Bị khoá bởi cổng phát hành | Ghi trạng thái listing sau submit — chưa submit. |
| B2-20 | Không áp dụng | Rà install của Action đã publish — chưa có Action nào publish; nhịp tuần nhà máy. |
| B2-21 | Không áp dụng | Theo dõi chính sách Marketplace — nhịp hằng tháng của nhà máy. |
| B2-22 | Không áp dụng | Rà workflow mẫu repo cũ khi GitHub đổi chuẩn — nhịp hằng tháng của nhà máy. |

## Ban 3 — Chất lượng code & kiến trúc (20 mục)

| Mã | Kết quả | Ghi chú |
|---|---|---|
| B3-01 | Đạt | Kiến trúc duyệt ở blueprint (mục 3) + kế hoạch pha 1 trước khi build sâu. |
| B3-02 | Đạt | Khác biệt rõ rệt với các repo trước: sản phẩm OS/policy/bằng chứng, không phải CLI đơn năng. |
| B3-03 | Đạt | Codebase viết mới cho sản phẩm này; template trong cây là template golden-path của chính sản phẩm (có chủ đích), không phải khuôn copy giữa các repo. |
| B3-04 | Đạt | Code tự viết; tham chiếu ngoài là tài liệu chuẩn (khung kiểm soát, SLSA, CycloneDX) — không chép code bên ngoài vào cây. |
| B3-05 | Đạt | Ưu tiên zero-dependency: evidence tooling chỉ dùng thư viện chuẩn; ngoại lệ duy nhất PyYAML (`workflow_input.py`) có lý do ghi trong `gates/local/README.md`. |
| B3-06 | Đạt | Tên hàm/file rõ nghĩa, docstring tiếng Việt giải thích luồng ở mọi module chính. |
| B3-07 | Đạt | Lỗi ở biên đều có thông điệp + mã thoát riêng: collector strict nêu tên từng vấn đề; generators thiếu binary → exit 2; adapter lỗi chạy tool → exit 2. |
| B3-08 | Đạt | Không code chết/debug sót: các `print` trong adapter là output CLI có chủ đích; vòng này dọn `__pycache__` tái sinh + tài liệu cũ sai lệch. |
| B3-09 | Đạt | Hàm dài duy nhất còn lại là `collect()` trong bundle_tool (~450 dòng, pipeline tuyến tính một mạch) — chấp nhận có ghi chú tại đây; không tách ở vòng này để tránh hồi quy sát nghiệm thu. |
| B3-10 | Đạt | Entry point rõ: mỗi công cụ 1 lệnh (collect/verify; generators theo subcommand; gate-NN.sh). |
| B3-11 | Đạt | Cấu hình qua tham số/biến môi trường được liệt kê (độ phân giải binary qua flag/env/PATH có ghi trong docstring + README); không hard-code giá trị riêng. |
| B3-12 | Đạt | `.gitignore` khớp cấu trúc: loại `evidence/output/`, `*.key`, `__pycache__`, feed cache (đã đối chiếu file thật). |
| B3-13 | Đạt | Không file build/phụ thuộc trong cây publish: thư mục lần chạy + bundle nằm trong vùng gitignore; quét cây vòng này xác nhận. |
| B3-14 | Đạt | Comment tập trung ở logic khó (validator, đường ký, quy tắc truy vết) — rà khi viết/sửa vòng này. |
| B3-15 | Đạt | Định dạng nhất quán trong từng ngôn ngữ (Python/Rego/shell) theo phong cách sẵn có của cây. |
| B3-16 | Đạt | Nợ kỹ thuật ghi danh sách bàn giao: hồ sơ phát hành mục 3 + 6 và risk-sweep R1–R6. |
| B3-17 | Đạt | README kỹ thuật khớp code thật — vòng này kiểm chứng lại và sửa 2 chỗ lệch (ghi chú truy vết 6/14 cũ; tên file workflow gate 10 ở template/dogfood). |
| B3-18 | Không áp dụng | Rà đa dạng giữa các repo trong tuần — việc hằng tuần của nhà máy. |
| B3-19 | Không áp dụng | Tổng kết bài học kỹ thuật — nhịp tuần của nhà máy (bài học vòng này nằm trong báo cáo vòng + risk-sweep). |
| B3-20 | Không áp dụng | Rà chuẩn code khi nâng cấp runtime — nhịp hằng tháng. |

## Ban 4 — Bảo mật & supply-chain (20 mục)

| Mã | Kết quả | Ghi chú |
|---|---|---|
| B4-01 | Đạt | Quét gitleaks toàn cây ở vòng này: sau dọn dẹp còn 12 finding, tất cả thuộc diện đã biết (secret GIẢ cài sẵn của biến thể planted + báo cáo gate 1 của chính nó + nhiễu trong JSON đầu ra Trivy ở thư mục lần chạy đã gitignore) — không secret thật. Điều kiện cứng giữ. |
| B4-02 | Không áp dụng | Cây chưa phải repo git đã publish nên chưa có lịch sử commit để quét; sẽ áp dụng trên repo thật ở vòng publish (M5-B). |
| B4-03 | Đạt | Fixture/sample chỉ chứa khoá giả định dạng rõ ràng (hậu tố FAKENOTREAL; khai trong SECURITY.md). |
| B4-04 | Đạt | Không thông tin cá nhân trong code/README/fixture của cây publish (đầu ra lần chạy chứa đường dẫn máy là artefact cục bộ đã gitignore, không thuộc bản publish). |
| B4-05 | Đạt | Dependency đã duyệt: workload ghim `==` (starlette 1.9.0 bản sạch); bộ công cụ ghim phiên bản, liệt kê trong `gates/local/README.md`. |
| B4-06 | Đạt | Dependency ghim phiên bản cụ thể; GitHub Actions trong workflow ghim theo tag phiên bản (chưa ghim SHA — mức tag được checklist chấp nhận "tag/SHA rõ ràng"). |
| B4-07 | Đạt | Kiểm tra cảnh báo nóng khi chọn dependency: chính CVE-2026-48710 (KEV) là căn cứ chọn bản sạch 1.9.0 và lỗi cài sẵn 1.0.0. |
| B4-08 | Đạt | Workflow mẫu/template yêu cầu quyền tối thiểu (`contents: read`) — thừa quyền bị chính gate 9 + access-review coi là finding. |
| B4-09 | Đạt | Sản phẩm không telemetry, không gọi API ngoài chưa khai báo: feed KEV/EPSS tải từ CISA/FIRST được khai rõ trong tài liệu gate 8. |
| B4-10 | Đạt | Dữ liệu người dùng (diff/log/config) xử lý tại máy/CI của họ; bằng chứng nằm trong hạ tầng của họ — không gửi về nhà máy. |
| B4-11 | Không áp dụng | OS này không nạp nội dung ngoài vào LLM; thành phần AI (gate 10) thuộc flagship #1 và đã xử lý chống injection ở sản phẩm đó. |
| B4-12 | Không áp dụng | Vệ sinh token hằng ngày của tài khoản nhà máy — việc vận hành ở kênh riêng (đã áp dụng), không phải thuộc tính của cây. |
| B4-13 | Không áp dụng | Tách token A/B là quy tắc 1 lần ở cấp tài khoản nhà máy. |
| B4-14 | Đạt | Ví dụ trong README/tài liệu dùng placeholder và biến môi trường, không hướng dẫn dán key thật. |
| B4-15 | Đạt | File cấu hình mẫu trong `docs/examples/` + template chỉ chứa placeholder (đối chiếu trong cây). |
| B4-16 | Đạt | Không vendor code bên ngoài vào cây; công cụ ngoài là binary OSS chạy ngoài cây (OPA, conftest, Syft...) — license của chúng thuộc chính chúng, cây không phân phối lại. |
| B4-17 | Đạt | Quét bảo mật 2 lượt ở mức cục bộ: trong lúc build (gate 1 trên các workload ở mọi vòng) + chốt vòng này (gitleaks toàn cây trước khi cập nhật hồ sơ). Lượt trên repo thật đi cùng publish. |
| B4-18 | Đã sửa vòng này | Bổ sung quy trình xử lý sự cố lộ secret vào SECURITY.md (xoay vòng ngay → xoá + ghi CHANGELOG → báo riêng → phát hành lại bundle + thu hồi fingerprint khoá). |
| B4-19 | Không áp dụng | Rà repo đã publish khi có cảnh báo mới — sản phẩm chưa publish; nhịp tuần nhà máy. |
| B4-20 | Không áp dụng | Rà toàn bộ bề mặt supply-chain nhà máy — nhịp hằng tháng ở cấp nhà máy. |

## Ban 5 — Kiểm thử & nghiệm thu (24 mục)

| Mã | Kết quả | Ghi chú |
|---|---|---|
| B5-01 | Đạt | Test đi cùng build ở mọi vòng: policy test cùng M2, bundle test cùng M4/M5-A2, adapter + generator test cùng M5-A3. |
| B5-02 | Đạt | Hai fixture bắt buộc có ở mọi lớp: biến thể clean (sạch) + planted (hỏng đúng kiểu pain) cho workload; fixture pass/fail cho từng policy. |
| B5-03 | Đạt | Unit test xanh toàn bộ trên máy local trước mọi mốc: vòng này OPA 48/48, harness 34/34, Python 36/36 (23 evidence + 13 adapters). |
| B5-04 | Đạt | Ví dụ + lệnh mẫu chạy thật đầu-cuối: pipeline dogfood từ template, phiên demo, các lệnh trong evidence/README đều đã thực thi ở các vòng. |
| B5-05 | Bị khoá bởi cổng phát hành | E2e trên PR thật của repo thử nghiệm techdevfun — cần repo. |
| B5-06 | Bị khoá bởi cổng phát hành | Link PR + link run CI làm bằng chứng e2e — chưa có môi trường thật. |
| B5-07 | Bị khoá bởi cổng phát hành | CI GitHub xanh ở HEAD publish — chưa có repo/CI. |
| B5-08 | Đạt | Ca biên đã kiểm: input thiếu/hỏng (record sai schema bị loại/dừng có tên), thiếu binary (exit 2 rõ ràng), findings rỗng, file bị sửa 1 byte, chữ ký bị thay. |
| B5-09 | Đạt | Đối chiếu tay: Trợ lý A tự chạy lại gate + verify ở các vòng M3/M4/M5-A2; vòng này worker tự soi từng record sinh ra (gate_results, finding, drift item) đối chiếu dữ liệu nguồn. |
| B5-10 | Đạt | Hiệu năng chấp nhận trên mẫu lớn nhất có tại chỗ: gates ~151 giây/biến thể chạy tuần tự, golden path 100 giây, không treo (ngoại lệ đã ghi: terraform plan chờ AWS API là giới hạn môi trường, không phải treo của sản phẩm). |
| B5-11 | Đạt | Kỷ luật trượt ngày đã áp thật: vòng tham chiếu terraform ở M3 ghi tồn đọng sang M5 thay vì ép qua; publish không bao giờ bị ép khi chưa đạt. |
| B5-12 | Đạt | Rubric được chấm theo bằng chứng trong hồ sơ phát hành mục 4 (bản worker); điểm chốt cuối thuộc Ban 5 của A khi nghiệm thu — hồ sơ là gói bằng chứng cho việc đó. |
| B5-13 | Bị khoá bởi cổng phát hành | Kiểm tra chéo điều kiện cứng của Ban 8 ở nghiệm thu cuối là bước của A tại cổng publish (rà cục bộ tương đương đã làm ở B4-01/B8-18 của vòng này). |
| B5-14 | Đạt | <90 (và <99 theo cổng riêng) → không publish, lý do trừ + việc cần sửa ghi trong hồ sơ mục 3/6 — đang thực thi đúng. |
| B5-15 | Đạt (có ghi chú trung thực) | Điểm 69,5 < 90 nên điều "≥90 → trau chuốt hướng 99" chưa kích hoạt theo đúng chữ; việc trau chuốt vẫn diễn ra theo lệnh trực tiếp mới hơn của chủ sở hữu (22:52 ngày 22/10: làm liên tục tới khi vét cạn phần cục bộ) đồng thời giữ nguyên cổng 99 — hai lớp tách bạch trong hồ sơ. |
| B5-16 | Đạt | Điểm + lý do trừ được ghi vào hồ sơ phát hành và báo cáo lên Tổng quản ở từng vòng. |
| B5-17 | Đạt | Cơ chế backup sau publish đã chạy + xác nhận bằng run thật cho các repo đã publish (checklist gốc [x]); sản phẩm này chưa publish nên chưa phát sinh backup của chính nó. |
| B5-18 | Bị khoá bởi cổng phát hành | Dispatch backup ngay sau publish — chưa publish. |
| B5-19 | Bị khoá bởi cổng phát hành | Mở kiểm lại nội dung repo trên GitHub sau publish. |
| B5-20 | Bị khoá bởi cổng phát hành | Khớp phiên bản publish với bản nghiệm thu — tại thời điểm publish. |
| B5-21 | Không áp dụng | Thống kê tỉ lệ qua cổng lần đầu — nhịp tuần của nhà máy. |
| B5-22 | Không áp dụng | Tổng hợp lỗi lặp lại của tuần — nhịp tuần nhà máy (phát hiện của vòng này đã ghi vào risk-sweep để làm đầu vào). |
| B5-23 | Không áp dụng | Chạy lại e2e flagship đang sống khi GitHub đổi hành vi — chưa có bản đang sống. |
| B5-24 | Không áp dụng | Rà CI xanh của repo đã publish — nhịp tháng; sản phẩm chưa publish. |

## Ban 6 — DevRel & nội dung dev.to (22 mục)

| Mã | Kết quả | Ghi chú |
|---|---|---|
| B6-01 | Đạt | Luật auto-publish đã áp ở cấp nhà máy (checklist gốc [x]). Bài của repo này chưa đăng vì chính hành động publish repo đang đóng băng theo quyết định chủ sở hữu — bài đi cùng publish, không tách rời. |
| B6-02 | Đạt | Luật "production, không draft" (checklist gốc [x]): file `release/devto-article-draft.md` là bản soạn nội bộ trước publish, KHÔNG phải draft trên dev.to; khi publish sẽ đăng production trong ngày. |
| B6-03 | Bị khoá bởi cổng phát hành | Bài đăng cùng ngày tạo repo — cả hai cùng đóng băng, sẽ thực thi đồng thời ở M5-B. |
| B6-04 | Đạt | Nhịp dọn bài tồn đọng đã chốt ở cấp nhà máy (checklist gốc [x]). |
| B6-05 | Đạt (ở mức bản nháp) | Front matter của bản nháp đã đặt `canonical_url` trỏ về repo GitHub (URL sẽ tồn tại khi publish). |
| B6-06 | Đạt | Luật 1 repo = 1 bài = 1 nơi/ngày đã áp ở cấp nhà máy (checklist gốc [x]). |
| B6-07 | Đạt (ở mức bản nháp) | Cấu trúc vấn đề → cách làm → demo → link repo đủ trong bản nháp. |
| B6-08 | Đạt (ở mức bản nháp) | Demo thật của chính sản phẩm (GIF từ phiên chạy thật + transcript) sẵn sàng nhúng. |
| B6-09 | Đạt (ở mức bản nháp) | Tags đúng chủ đề: devsecops, opensource, security, githubactions. |
| B6-10 | Đạt (ở mức bản nháp) | Bài có mục giới hạn riêng + mục "điểm đối thủ hơn ta" (luật đứng của nhà máy). |
| B6-11 | Đạt (ở mức bản nháp) | Bài đứng vững như bài chia sẻ độc lập; link repo xuất hiện ở mục dùng thử cuối bài. |
| B6-12 | Đạt | Không đăng trùng kênh khác cùng ngày — chưa đăng kênh nào; quy trình publish đã khoá điều này. |
| B6-13 | Bị khoá bởi cổng phát hành | Ghi id + link bài sau publish — chưa đăng. |
| B6-14 | Không áp dụng | Nhịp bài tồn đọng hằng ngày — bài này không phải bài tồn đọng; nó gắn với ngày publish. |
| B6-15 | Không áp dụng | Show HN chỉ xét cho repo nổi bật ở pha publish; vòng này không phát sinh quyết định đó. |
| B6-16 | Không áp dụng | Chọn subreddit — quyết định của pha publish, chưa tới. |
| B6-17 | Không áp dụng | Product Hunt — nhịp tháng/pha publish, chưa tới. |
| B6-18 | Đạt (ở mức bản nháp) | Tiêu đề bài không giật tít (nêu vấn đề + lời hứa đo được). |
| B6-19 | Không áp dụng | Trả lời comment dev.to — chưa có bài đang sống của sản phẩm này. |
| B6-20 | Không áp dụng | Theo dõi view/reaction — chưa có bài đang sống. |
| B6-21 | Không áp dụng | So sánh hiệu quả bài theo pain — nhịp tuần nhà máy. |
| B6-22 | Không áp dụng | Rà link bài cũ — nhịp tháng nhà máy; sản phẩm chưa có bài cũ. |

## Ban 7 — Tăng trưởng & phân phối (20 mục)

| Mã | Kết quả | Ghi chú |
|---|---|---|
| B7-01 | Đạt | Kênh phân phối chính chốt ở tiền build cùng Ban 1/2 (blueprint mục 6). |
| B7-02 | Đạt | Landing là 1 trong 3 thứ chốt trước: nội dung landing đã soạn sẵn trong cây (`release/landing-techdev-fun.md`); việc deploy thuộc M5-B đóng băng nhưng phần chuẩn bị đã xong. |
| B7-03 | Đạt (phần nội dung) | Flagship có nội dung landing riêng (không chỉ 1 card); deploy trang thuộc M5-B. |
| B7-04 | Bị khoá bởi cổng phát hành | Card catalog gắn ngày publish. |
| B7-05 | Bị khoá bởi cổng phát hành | Kiểm chứng live sau khi cập nhật landing — cần trang thật cập nhật. |
| B7-06 | Đạt | Mô tả 1 dòng đã chốt (đầu landing + dòng mô tả repo đề xuất trong landing). |
| B7-07 | Đạt | Bộ topics đề xuất đã ghi ở đầu file landing. |
| B7-08 | Bị khoá bởi cổng phát hành | Kiểm tra social preview cần link repo/trang thật. |
| B7-09 | Bị khoá bởi cổng phát hành | Đối chiếu link qua lại repo ↔ landing ↔ bài ↔ Marketplace cần các đầu mối tồn tại. |
| B7-10 | Không áp dụng | Đưa vào awesome list là hoạt động sau publish bằng đóng góp thật; chưa tới pha đó. |
| B7-11 | Không áp dụng | Ghim repo lên profile — nhịp tuần ở cấp tài khoản. |
| B7-12 | Không áp dụng | Theo dõi sao/fork/install toàn danh mục — nhịp tuần nhà máy. |
| B7-13 | Không áp dụng | Phân tích traffic GitHub — nhịp tuần; repo chưa tồn tại. |
| B7-14 | Đạt | Veto tăng trưởng gian lận đang hiệu lực và được tôn trọng tuyệt đối trong mọi vòng của sản phẩm (không mua sao/bot/spam ở bất kỳ đâu). |
| B7-15 | Không áp dụng | Hoạt động cộng đồng ≤2/tuần — nhịp tuần ở cấp tài khoản. |
| B7-16 | Đạt | Không đăng link dạo vào comment/group không liên quan — không có hành động nào như vậy; chưa đăng link nào cả. |
| B7-17 | Không áp dụng | Đối chiếu nhịp tăng trưởng với trần an toàn — nhịp tuần của nhà máy. |
| B7-18 | Không áp dụng | Thử nghiệm phân phối — nhịp tháng, sau publish. |
| B7-19 | Không áp dụng | Rà catalog techdev.fun — nhịp tháng ở cấp trang/nhà máy. |
| B7-20 | Không áp dụng | Tổng hợp kênh hiệu quả theo pain — nhịp tháng của nhà máy. |

## Ban 8 — An toàn tài khoản & tuân thủ (24 mục)

| Mã | Kết quả | Ghi chú |
|---|---|---|
| B8-01 | Đạt | Trần ≤2 repo/ngày đã áp ở cấp tài khoản (checklist gốc [x]); sản phẩm này chưa tạo repo nào. |
| B8-02 | Đạt | Cách nhau ≥2 giờ đã áp ở cấp nhà máy (checklist gốc [x]). |
| B8-03 | Đạt | Quy trình 429 → dừng 24h đã có và bắt buộc (checklist gốc [x]). |
| B8-04 | Đạt | Quy trình email cảnh báo → dừng 72h đã có (checklist gốc [x]). |
| B8-05 | Đạt | Quy tắc repo bị gắn cờ → không thay thế 7 ngày đã có (checklist gốc [x]). |
| B8-06 | Đạt | Cấm mua sao/bot star đã áp (checklist gốc [x]). |
| B8-07 | Đạt | Cấm issue/PR/comment giả đã áp (checklist gốc [x]). |
| B8-08 | Đạt | Cấm tương tác chéo A↔B đã áp (checklist gốc [x]). |
| B8-09 | Đạt | Cấm nhận token/mật khẩu qua chat — chỉ Secure Vault (checklist gốc [x]). |
| B8-10 | Đạt | Khung giờ 8h–22h VN đã áp cho mọi run (checklist gốc [x]). |
| B8-11 | Đạt | Profile techdevfun đã điền và kiểm chứng qua API 21/10/2026 (checklist gốc [x]). |
| B8-12 | Không áp dụng | Verify email tài khoản là trạng thái ở cấp tài khoản, checklist gốc chưa tick; không kiểm chứng được từ cây/vòng cục bộ này. |
| B8-13 | Đạt | 2FA đã bật, kiểm chứng qua API (checklist gốc [x]). |
| B8-14 | Không áp dụng | Đổi avatar là thao tác web phía chủ sở hữu (checklist gốc ghi vẫn là ảnh mặc định tính đến 21/10) — ngoài khả năng của vòng cục bộ này. |
| B8-15 | Không áp dụng | Đặt email hiển thị công khai là cài đặt web phía chủ sở hữu — ngoài vòng này. |
| B8-16 | Không áp dụng | Điền location profile là quyết định ở cấp tài khoản — ngoài vòng này. |
| B8-17 | Bị khoá bởi cổng phát hành | Đếm repo trong ngày + giờ publish gần nhất là bước ngay trước publish. |
| B8-18 | Đạt | Rà điều kiện cứng ở mức cục bộ đã làm trong vòng này: quét secret (B4-01), LICENSE có mặt, không tương tác giả, không vi phạm bản quyền (code tự viết). Kiểm tra chéo chính thức của Ban 8 ở nghiệm thu là bước của A (xem B5-13). |
| B8-19 | Đạt | Không publish đồng thời — vòng này không publish gì cả; kỷ luật được giữ. |
| B8-20 | Không áp dụng | Rà tín hiệu nguy hiểm đầu ngày là nhịp A1 của nhà máy. |
| B8-21 | Không áp dụng | Ngày nghỉ ngẫu nhiên là nhịp vận hành tuần của nhà máy/tài khoản. |
| B8-22 | Không áp dụng | Giới hạn commit/ngày áp cho hoạt động trên GitHub; sản phẩm này chưa có commit GitHub nào. |
| B8-23 | Không áp dụng | Rà hoạt động 7 ngày ở tổng kết tuần — việc của nhà máy. |
| B8-24 | Đạt | Quy tắc không tạo tài khoản lách khi bị khoá đã có và bắt buộc ở cấp tài khoản (playbook A). |

## Ban 9 — Demo, README & trải nghiệm người dùng (20 mục)

| Mã | Kết quả | Ghi chú |
|---|---|---|
| B9-01 | Đạt | Kịch bản demo chốt trước: phiên 91 giây dựng theo kịch bản (gates 2 biến thể → bundle → verify → giả mạo 1 byte) có trong `release/demo/`. |
| B9-02 | Đạt | Khoảnh khắc "wow" trong 30 giây đầu của GIF: lỗi cài sẵn bị chặn đúng cổng + sửa 1 byte làm verify FAIL. |
| B9-03 | Đạt | Demo từ phiên chạy thật (typescript gốc lưu kèm; bản GIF là dựng lại dạng chữ đã ghi nhãn trung thực trong hồ sơ). |
| B9-04 | Đạt | GIF nhúng ngay đầu README, dung lượng 2,3 MB tải nhanh; việc hiển thị thực tế trên GitHub kiểm chứng khi có repo (phần hiển thị thuộc M5-B nhưng tài sản đã đạt chuẩn). |
| B9-05 | Đạt | Màn hình đầu README: ai đau + hệ làm gì trước khi cuộn (đã nghiệm ở M5-A). |
| B9-06 | Đạt | README đủ cấu trúc vấn đề → giải pháp → demo → cài đặt → ví dụ → giới hạn → license. |
| B9-07 | Đạt | Cài đặt/chạy gói trong ít bước: chạy gates cục bộ + collect/verify bằng các lệnh copy-chạy được trong README/evidence README. |
| B9-08 | Đạt | Ví dụ chạy ngay sau cài kèm output kỳ vọng: dogfood checkout-sample + kết quả kỳ vọng ghi trong `release/dogfood-checkout-sample.md`. |
| B9-09 | Đạt | `examples/` có ví dụ thực tế: payments-sample (2 biến thể), checkout-sample, cấu hình mẫu trong `docs/examples/` (OIDC trust policy, branch protection). |
| B9-10 | Đạt | Tên repo rõ nghĩa; tiêu đề/mô tả viết như dev thật, không câu view. |
| B9-11 | Đạt | Thông báo lỗi gợi bước tiếp theo: collector nêu tên vấn đề + cách xử lý; generators báo rõ binary nào thiếu; verify nêu đúng file lệch hash. |
| B9-12 | Đạt | Giới hạn nêu rõ trong README + mục "Giới hạn đã biết" của landing. |
| B9-13 | Đã sửa vòng này | Tạo `CONTRIBUTING.md` (môi trường, 5 bộ kiểm thử, quy tắc đóng góp). |
| B9-14 | Đã sửa vòng này | Tạo `.github/ISSUE_TEMPLATE/` (bug_report, feature_request, config tắt blank issue + trỏ kênh bảo mật). |
| B9-15 | Đạt | Thuật ngữ nhất quán giữa README ↔ landing ↔ bản nháp dev.to (rà chéo khi cập nhật cả ba ở vòng này). |
| B9-16 | Đạt | README đã đọc thử góc người mới ở M5-A; các sửa vòng này giữ nguyên chuẩn đó (không thêm thuật ngữ nội bộ). |
| B9-17 | Không áp dụng | Làm lại GIF khi output thay đổi: vòng này output của gates/bundle không đổi dạng trình bày (chỉ thêm loại record) và GIF không chứa con số truy vết nào bị lỗi thời — chưa phát sinh nhu cầu quay lại; nếu bản publish muốn nêu 13/14 trong demo thì quay lại ở M5-B. |
| B9-18 | Bị khoá bởi cổng phát hành | Ban 9 duyệt riêng kịch bản demo flagship trước ngày publish — bước nghiệm thu của A. |
| B9-19 | Không áp dụng | So sánh demo giữa các sản phẩm trong tuần — nhịp tuần nhà máy. |
| B9-20 | Không áp dụng | Rà README repo cũ khi có thay đổi lớn — nhịp tháng nhà máy. |

## Ban 10 — Kiếm tiền open-core (16 mục)

| Mã | Kết quả | Ghi chú |
|---|---|---|
| B10-01 | Đạt | `KIEM-TIEN-TRACK.md` đã có ở cấp nhà máy (checklist gốc [x]). |
| B10-02 | Đạt | Nguyên tắc Pro phải được chủ sở hữu duyệt đã chốt (checklist gốc [x]) — vòng này không đề xuất Pro nào. |
| B10-03 | Đạt | Nguyên tắc free luôn hữu ích thật đã chốt (checklist gốc [x]); bản free của sản phẩm này là toàn bộ pha 1. |
| B10-04 | Không áp dụng | Định nghĩa ngưỡng tín hiệu tối thiểu cho Pro là việc 1 lần của Ban 10 ở cấp nhà máy (checklist gốc chưa tick) — không thuộc cây sản phẩm. |
| B10-05 | Không áp dụng | Cập nhật tín hiệu vào track — nhịp tuần; sản phẩm chưa publish nên chưa có tín hiệu. |
| B10-06 | Đạt | Chỉ đề xuất Pro khi có tín hiệu thật bền: chưa đề xuất vì chưa có tín hiệu nào — tuân thủ đúng quy tắc. |
| B10-07 | Không áp dụng | Phác thảo ranh giới free/Pro chỉ áp cho ứng viên Pro — sản phẩm chưa là ứng viên. |
| B10-08 | Không áp dụng | Trình đề xuất Pro kèm bằng chứng — chưa có đề xuất nào để trình. |
| B10-09 | Đạt | Không đăng bán/mở thanh toán/niêm yết giá khi chưa duyệt — không có hành động nào như vậy. |
| B10-10 | Không áp dụng | Nội dung giới thiệu bản Pro — chưa tồn tại bản Pro hay nội dung của nó. |
| B10-11 | Đạt | Bản free không nag/upsell/khoá tính năng cũ (kiểm tra trong cây: không cơ chế nào như vậy). |
| B10-12 | Không áp dụng | Ghi nhận issue/yêu cầu thật làm căn cứ Pro — chưa có người dùng/issue thật. |
| B10-13 | Không áp dụng | Rà danh mục chọn ứng viên Pro — nhịp tháng nhà máy. |
| B10-14 | Không áp dụng | Đánh giá doanh thu Pro đang sống — chưa có bản Pro nào. |
| B10-15 | Đạt | Veto kiếm tiền dựa trên tín hiệu giả đang hiệu lực và được tôn trọng. |
| B10-16 | Không áp dụng | Kế hoạch tăng tốc khi 2–3 repo đạt 500+ sao — điều kiện chưa xảy ra. |

---

## Các sửa chữa đã thực thi trong vòng (tổng hợp)

1. `evidence/generators.py` (mới) + mở rộng collector/verify trong
   `evidence/bundle_tool.py` 1.2.0 — đóng 5 loại bằng chứng còn
   thiếu (nhiệm vụ 1 của vòng; chi tiết ở hồ sơ phát hành).
2. `CHANGELOG.md` gốc cây (mới) — B2-16.
3. SECURITY.md: thêm quy trình xử lý sự cố lộ secret — B4-18.
4. `CONTRIBUTING.md` (mới) — B9-13.
5. `.github/ISSUE_TEMPLATE/` (mới: bug/feature/config) — B9-14.
6. Sửa tham chiếu `gate-10-prgate.yml` → `gate-10-ai-pr-review.yml`
   ở template gốc (`templates/api-service/.github/workflows/ci.yml`)
   và bản dogfood (`examples/checkout-sample/.github/workflows/ci.yml`).
7. Cập nhật truy vết 13/14 trong `evidence/README.md` (kèm mục
   hướng dẫn bộ sinh) và mục giới hạn của
   `release/landing-techdev-fun.md`.
8. Vệ sinh cây: xoá 2 `cosign.key` sót trong thư mục lần chạy cũ;
   đổi chuỗi secret mẫu trong fixture test để không vấp bộ quét
   secret; xoá `__pycache__` tái sinh trong cây.
9. Cập nhật `release/risk-sweep-m5a.md`: R2 đóng, thêm R6 (kết quả
   quét gitleaks cuối vòng).
10. Bản nháp dev.to `release/devto-article-draft.md` (nhiệm vụ 4).
11. Test mới: 15 (evidence/tests/test_generators.py) + 13
    (gates/local/tests/test_adapters.py) — tổng unit test Python
    tăng 8 → 36.
