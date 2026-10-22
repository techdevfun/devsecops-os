# Định danh & attestation (identity-first)

> **Trạng thái (M1)**: tài liệu thiết kế + cấu hình mẫu tĩnh trong
> `docs/examples/`. Việc áp các cấu hình này vào workflow thật thuộc M3.

Nguyên tắc xuyên suốt: **không credential tĩnh dài hạn** — không AWS access
key trong GitHub secrets, không token registry không hết hạn, không mật khẩu
dùng chung. Mọi quyền đều gắn với một danh tính kiểm chứng được và một
phiên làm việc ngắn hạn.

## 1. Con người: SSO/OIDC của tổ chức

- Repo, registry, evidence store và mọi hệ thống đích đều nằm sau SSO/OIDC
  của tổ chức (Entra ID, Okta, Keycloak… tuỳ tổ chức). Hệ này không tự làm
  IdP và không lưu mật khẩu người dùng.
- Quyền merge vào nhánh release gắn với phê duyệt PR của CODEOWNERS — phê
  duyệt đó đồng thời là bằng chứng thay đổi cho các khung kiểm soát (được
  evidence collector gom ở M4).

## 2. Workload: OIDC federation (GitHub Actions → cloud)

- Mỗi workflow khai báo `permissions: id-token: write` và dùng OIDC token
  do GitHub cấp (sống theo phút, gắn chặt với repo + branch + environment)
  để đổi lấy IAM role ngắn hạn phía cloud.
- Điều kiện tin cậy (trust policy) phía AWS phải ghim tới đúng
  `repo:<owner>/<repo>` và, với job deploy, tới đúng `environment`.
- **[cấu hình mẫu]** `docs/examples/github-actions-oidc-aws-trust-policy.json`
  — mẫu IAM trust policy cho GitHub OIDC provider, có placeholder cần thay
  trước khi dùng; kèm ghi chú tách role đọc (quét) khỏi role ghi (deploy).

Nguyên tắc tách quyền đi kèm: role cho job *quét* chỉ đọc; role cho job
*deploy* chỉ ghi đúng tài nguyên của service đó (least privilege theo
service, không dùng chung một role cho cả tổ chức).

## 3. Artefact: ký Cosign + SLSA provenance

- Image/artefact được ký bằng Cosign theo cơ chế keyless (danh tính OIDC
  của workflow chính là "chìa khoá") hoặc bằng KMS/HSM của tổ chức nếu tổ
  chức yêu cầu quản lý khoá tập trung.
- Mỗi artefact đính kèm **SLSA provenance attestation**: ai build, từ commit
  nào, qua workflow nào, với tham số gì. Tầng đích kiểm chứng attestation
  này trước khi nhận (Kyverno `verifyImages` — xem cấu hình mẫu).
- **[cấu hình mẫu]** `docs/examples/kyverno-verify-images.yaml` — mẫu
  ClusterPolicy: chỉ cho phép image đã ký keyless bởi workflow của tổ chức
  và có attestation provenance; image không đạt bị từ chối ở admission.
  File này là mẫu tĩnh tham chiếu, chưa được kiểm chứng trên cluster thật
  ở M1.

## 4. Những gì thiết kế này cố ý loại bỏ

- Không dùng chung một PAT/token cho nhiều repo (bài học vận hành của chính
  nhà máy: token tách theo tài khoản/vai trò, ghim scope tối thiểu).
- Không `pull_request_target` với checkout mã của PR theo mẫu nguy hiểm đã
  biết; workflow xử lý PR fork đi theo mẫu hai workflow (build không quyền /
  comment có quyền) — chi tiết khi cài gate ở M3.
- Không lưu trữ bí mật của người dùng ở bất kỳ đâu ngoài hạ tầng của chính
  tổ chức.
