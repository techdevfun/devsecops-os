# kyverno/verify-image-signatures — chỉ nhận image đã ký + có provenance

- **File**: `../kyverno/verify-image-signatures.yaml` (ClusterPolicy
  dạng `verifyImages`) · **Cơ chế**: Kyverno admission + Sigstore
  (Cosign keyless qua OIDC của GitHub Actions, tra Rekor) · **Gate
  tiêu thụ**: điểm thực thi tầng đích của Gate 6; phía CI, quyết định
  tương ứng do `devsecops.provenance` (Rego) đảm nhiệm · **Bằng
  chứng**: `provenance-attestation` + `policy-decision`.

**Kiểm soát nào** (ánh xạ tham chiếu): SSDF PS.3 (provenance); ISO
27001 A.5.19–A.5.22, A.8.28; SOC 2 CC7.1 ở mức tham chiếu.

**Vì sao**: chữ ký kiểm chứng ở admission là chốt cuối — dù registry
hay pipeline bị tác động, image không có chữ ký của danh tính workflow
tổ chức và không có SLSA attestation khớp sẽ không được chạy. File này
chính thức hoá mẫu M1 ở `docs/examples/kyverno-verify-images.yaml`.

**Trạng thái kiểm chứng (nói thẳng)**: ở M2 chỉ kiểm chứng được bằng
Kyverno CLI ở mức parse/áp cấu trúc. Rule `verifyImages` cần cluster
thật + Rekor/Cosign để chạy — **chưa kiểm chứng runtime ở M2**, để lại
cho M3/M5 trên môi trường Actions/cluster thử nghiệm. Trước khi dùng
phải thay `<OWNER>/<REPO>`, registry và mẫu tên image.

**Vi phạm thì sửa thế nào**: build image qua pipeline có ký keyless +
attestation; không nới policy để nhận image ngoài pipeline.
