# provenance — artefact phải có SBOM + chữ ký + SLSA khớp digest

- **Mã**: `devsecops.provenance` · **Cơ chế**: OPA/Rego tại điểm quyết
  định triển khai (dữ liệu do Gate 6 sinh); thực thi ở tầng đích bằng
  Kyverno `verifyImages` (xem `../kyverno/verify-image-signatures.yaml`)
  · **Gate tiêu thụ**: Gate 6 (SBOM + attestation) · **Bằng chứng**:
  `provenance-attestation` + `sbom`.

**Kiểm soát nào** (ánh xạ tham chiếu): SSDF PS.3 (bảo vệ mọi dạng của
phần mềm, provenance); ISO 27001 A.5.19–A.5.22 (nhà cung cấp — ở đây
là chính pipeline của tổ chức với vai trò nhà cung cấp nội bộ) và
A.8.28; SOC 2 CC7.1/CC8.1 ở mức tham chiếu.

**Vì sao**: digest khớp giữa artefact, chữ ký và provenance là cách
duy nhất trả lời được "image đang chạy có đúng là image pipeline đã
build từ commit đó không" — câu hỏi cốt lõi của an ninh chuỗi cung
ứng sau các vụ action/registry bị chiếm quyền.

**Vi phạm thì sửa thế nào**: build qua pipeline có bật Syft (SBOM) +
Cosign keyless (ký bằng OIDC) + slsa-github-generator (provenance);
không triển khai artefact build ngoài pipeline; nếu provenance không
khớp digest, điều tra như sự cố — không ghi đè bằng tay.
