# Evidence automation — M4 (đã cài đặt, kiểm chứng cục bộ); ký Cosign + unit test bổ sung tại M5-A2

Evidence collector là "gate cuối" của pipeline (blueprint mục 5.2):
mỗi lần bộ gates chạy xong, collector gom toàn bộ bằng chứng vào một
**evidence bundle** có manifest SHA-256, kiểm chứng toàn vẹn được
bằng **một lệnh duy nhất** (tiêu chí nghiệm thu số 4 của blueprint
mục 3.2). Bằng chứng luôn nằm **trong hạ tầng của tổ chức sử dụng** —
repo này không lưu trữ bằng chứng của bất kỳ ai; `bundles/` và
`store/` đã được .gitignore.

## Công cụ

| File | Vai trò |
|---|---|
| `bundle_tool.py` | Toàn bộ logic: lệnh `collect` (thu thập + đóng bundle, tuỳ chọn `--sign` ký Cosign) và `verify` (kiểm chứng hash + schema + chữ ký khi bundle có khai báo). Python 3, chỉ thư viện chuẩn — không cần cài thêm gói trên runner |
| `verify_bundle.py` | Lối vào một lệnh cho việc kiểm chứng (gọi `bundle_tool.py verify`) |
| `tests/test_bundle_tool.py` | Unit test của bundle_tool (xem mục Kiểm thử ở cuối) |
| `mapping.phase1.json` | Dữ liệu ánh xạ pha 1 (khung → nhóm kiểm soát → policy → gate → loại bằng chứng), chép từ bản đồ pack v1 trong `../policies/README.md` — collector dùng để dựng bảng truy vết trong báo cáo tổng hợp |

## Cách dùng

```bash
# Đóng bundle từ một lần chạy gates (hợp đồng thư mục của M3:
# evidence/output/<lần chạy>/gate-NN-*/ kèm *.record.json +
# policy-decision-*.json + disabled-note.txt của gate 10 khi tắt)
python3 evidence/bundle_tool.py collect evidence/output/local-clean

# Đóng bundle CÓ ký mật mã (Cosign trên bundle.sha256; cần cosign —
# công cụ tự tìm qua PATH/COSIGN_BINARY hoặc truyền --cosign)
python3 evidence/bundle_tool.py collect evidence/output/local-clean --sign

# Kiểm chứng một bundle — MỘT lệnh duy nhất (tự kiểm thêm chữ ký
# khi bundle có khai báo chữ ký; thiếu cosign trên máy = FAIL ồn ào)
python3 evidence/verify_bundle.py evidence/bundles/<bundle-id>

# Hoặc chỉ kiểm hash bằng công cụ hệ thống:
cd evidence/bundles/<bundle-id> && sha256sum -c bundle.sha256
```

## Bộ sinh bằng chứng quyết định/định kỳ (M5-A3)

`generators.py` sinh các loại bằng chứng không thuộc một cổng CI —
từ dữ liệu thật của lần chạy và của cây — vào thư mục
`supplementary-records/` của lần chạy; collector thu chúng như mọi
record khác (kiểm schema, đưa vào truy vết):

```bash
# Sinh cả 4 loại cho một lần chạy (trước khi collect):
python3 evidence/generators.py all --run-dir evidence/output/<lần chạy>

# Từng loại: change-record | drift-report | access-review |
# config-baseline (xem --help). Khai/cập nhật baseline drift:
python3 evidence/generators.py write-baseline \
    --workload examples/payments-sample/clean
```

- `change-record`: tổng hợp kết quả cổng của chính lần chạy; quyết
  định do policy `change_record` chạy thật bằng OPA kết luận — lần
  chạy cục bộ không có phê duyệt PR nên quyết định là **deny** (bằng
  chứng trung thực, không phải lỗi của bộ sinh).
- `drift-report`: so cấu hình IaC hiện tại với baseline đã khai tại
  `baselines/payments-sample.tf-normalized.json`.
- `access-review-report` / `config-baseline-report`: rà soát quyền
  workflow + đánh giá policy IaC trên cấu hình hiện tại của cây.
- `ci-log` không do `generators.py` sinh: **collector tự phát hành**
  khi lần chạy có file `.log` thật — đóng gói log thành artefact zip
  tất định và ghi SHA-256 của nó vào record; verify đối chiếu lại.

Chế độ mặc định của `collect` là **nghiêm**: record nào sai schema
M2, gate nào thiếu thư mục/thiếu bằng chứng, lần quét nào có
`scan-error.json` — collect dừng, nêu tên từng vấn đề, không sinh
bundle. Cờ `--allow-incomplete` (job CI dùng, chế độ chỉ-thu-thập):
vẫn sinh bundle, record sai bị tách vào `rejected/` kèm lý do, mọi
vấn đề được ghi trong báo cáo và bundle mang cờ
`evidence-incomplete` trong manifest.

## Cấu trúc một bundle

```
<bundle>/
  bundle.json      metadata: định dạng, run id, thời gian, commit SHA
  summary.md/.json báo cáo tổng hợp: kết quả theo gate, quyết định
                   policy + lý do chặn nguyên văn, finding secret,
                   lỗ hổng đã xếp hạng (KEV/EPSS), bảng truy vết cả
                   14 hàng pha 1 (loại bằng chứng nào có/chưa có và
                   vì sao), danh sách file không đưa vào bundle
  records/         mọi evidence record khớp schema M2, giữ nguyên
                   đường dẫn gate-NN-*/ — cộng một record
                   control-evidence-index do chính collector sinh
                   từ dữ liệu thật của lần chạy
  artifacts/       file phụ trợ mà record tham chiếu (SARIF, tài
                   liệu SBOM/provenance, đầu vào của policy, ghi chú
                   gate tắt...) để bundle tự chứa, đọc được độc lập
  schemas/         bản sao 14 schema M2 — hợp đồng mà bundle đã
                   được kiểm theo, để verify không phụ thuộc repo
  rejected/        (chỉ khi --allow-incomplete) record sai schema,
                   giữ nguyên bản kèm lý do trong manifest
  manifest.json    từng file trong bundle (trừ manifest.json và
                   bundle.sha256): đường dẫn, SHA-256, kích thước,
                   vai trò; với record còn có loại bằng chứng, gate,
                   commit SHA, mốc thời gian và hàng ánh xạ liên quan;
                   khi bundle được ký, manifest có thêm trường
                   `signature` khai báo chữ ký + vân tay khoá công khai
  bundle.sha256    bao phủ MỌI file còn lại kể cả manifest.json —
                   tương thích `sha256sum -c`
  bundle.sigstore.json  (chỉ khi ký bằng --sign) chữ ký Cosign dạng
                   Sigstore bundle trên chính bundle.sha256
  cosign.pub       (chỉ khi ký bằng --sign) khoá công khai của chữ
                   ký trên — hai file này CỐ Ý đứng ngoài manifest
                   và ngoài bundle.sha256 vì chúng chứng thực
                   bundle.sha256
```

An toàn theo thiết kế: **vật liệu khoá riêng không bao giờ vào
bundle** (gate 6 sinh `cosign.key` tạm khi chạy cục bộ — collector
loại nó và ghi rõ trong báo cáo).

## Ký mật mã cho bundle (M5-A2)

`collect --sign` ký `bundle.sha256` bằng Cosign (`sign-blob`, định
dạng Sigstore bundle, signing-config offline của repo — cùng mẫu
với gate 6). Vì `bundle.sha256` bao phủ mọi file còn lại kể cả
manifest.json, chữ ký này gián tiếp trói toàn bộ nội dung bundle:
kẻ sửa một record *rồi tính lại cả hash lẫn manifest cho nhất
quán* vẫn bị verify bắt ở lớp chữ ký. Khai báo chữ ký (gồm vân tay
SHA-256 của khoá công khai) nằm trong `manifest.json` +
`bundle.json` — cả hai đều được `bundle.sha256` bao phủ — và
`verify` **bắt buộc** kiểm chữ ký khi có khai báo: thiếu file chữ
ký, thiếu khoá công khai, khoá bị thay, chữ ký sai, hoặc máy kiểm
không có cosign đều là FAIL ồn ào, không âm thầm hạ xuống kiểm hash.

**Giới hạn trung thực của chữ ký cục bộ** (khác với keyless OIDC
trên CI — việc thuộc M5-B):

- Khoá là khoá tạm theo lần chạy, sinh trong thư mục tạm **ngoài
  cây** và **huỷ ngay sau khi ký**; khoá riêng không vào bundle và
  không nằm lại trong cây. Hệ quả: chữ ký chứng minh "nội dung này
  khớp với thời điểm ký", nhưng danh tính người ký chỉ là
  `local:cosign-ephemeral-key` — chưa gắn với danh tính OIDC của
  workflow và **không có transparency log** (Rekor) như ký keyless
  trên CI.
- `cosign.pub` đi kèm trong bundle nên tự nó không phải neo tin
  cậy: kẻ sửa được *toàn bộ* bundle cũng có thể ký lại bằng khoá
  của họ và thay `cosign.pub`. Giá trị chống ký-lại chỉ có khi
  người kiểm **đối chiếu vân tay khoá công khai
  (`signature.public_key_sha256` trong manifest) với một bản ghi
  ngoài bundle** — ví dụ hồ sơ phát hành hoặc log CI — trước khi
  tin. Neo tin cậy đầy đủ (chứng thư OIDC + Rekor tra cứu công
  khai) là phần của ký keyless trên CI ở M5-B.

## Truy vết tuân thủ (ánh xạ tham chiếu, không phải chứng nhận)

Báo cáo tổng hợp của mỗi bundle cho thấy từng hàng pha 1 của pack
v1 có bằng chứng thật từ gate nào. Trạng thái sau vòng M5-A3
(2026-10-22): **13/14 hàng đầy đủ**. Bốn loại bằng chứng dạng quyết
định/định kỳ (`change-record`, `drift-report`,
`config-baseline-report`, `access-review-report`) được sinh bởi
`generators.py` từ dữ liệu thật của lần chạy/cây và `ci-log` do
chính collector phát hành kèm hash của log lần chạy — chứng minh
bằng bundle `local-clean-m5a3` (verify PASS, truy vết 13/14). Hàng
duy nhất còn một phần là `row-05`: `pr-review-report` chỉ có khi
gate 10 bật — gate 10 đang tắt theo thiết kế pha 1.

## Tích hợp CI

Job `evidence-bundle` trong `.github/workflows/all-gates.yml` chạy
sau cả 10 gate (`if: always()`): tải artefact của từng gate (không
gộp, giữ cấu trúc `gate-NN-*/`), dựng thư mục lần chạy, chạy
collector ở chế độ chỉ-thu-thập, tự kiểm chứng bundle bằng đúng một
lệnh ở trên, rồi tải bundle lên làm artefact. Job này **không đổi
quyết định chặn của bất kỳ gate nào** và gate 10 giữ mặc định tắt.

## Kiểm thử

Unit test cho `bundle_tool.py` nằm ở `tests/test_bundle_tool.py`,
cho bộ sinh ở `tests/test_generators.py` (fixture lần chạy tối
thiểu tự sinh, không cần chạy gates thật):

```bash
python3 -m unittest discover -s evidence/tests -v
```

23 test (sau M5-A3): 8 test gốc của collector — collect trên
fixture tối thiểu + verify PASS; gate 10 disabled không bị tính là
thiếu bằng chứng; record sai schema ở chế độ nghiêm (dừng + nêu
tên) và ở `--allow-incomplete` (vào `rejected/` + cờ
`evidence-incomplete`); verify FAIL khi sửa 1 byte; và 3 test chữ ký
bằng cosign thật (bundle ký verify PASS cả hash + chữ ký; sửa nội
dung kèm tính lại hash nhất quán vẫn FAIL ở lớp chữ ký; thay chữ ký
bằng chữ ký của bundle khác → FAIL) — cộng 15 test M5-A3: 4 bộ sinh
(record khớp schema, quyết định policy chạy thật bằng OPA, drift
phát hiện rule mở 0.0.0.0/0 so với baseline, rà soát quyền trên
chính cây repo) và 2 mở rộng collector (record phụ trợ được thu +
truy vết; ci-log phát hành kèm đối chiếu chéo hash — sửa record cho
"nhất quán giả" vẫn bị bắt). Nhóm test chữ ký tự bỏ qua khi máy
không có cosign.
