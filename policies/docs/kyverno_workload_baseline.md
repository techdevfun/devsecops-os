# kyverno/workload-baseline — chuẩn runtime tối thiểu trên Kubernetes

- **File**: `../kyverno/workload-baseline.yaml` (ClusterPolicy,
  `validationFailureAction: Enforce`) · **Cơ chế**: Kyverno admission
  — **lý do cần Kyverno bên cạnh OPA**: kiểm soát tại thời điểm
  admission của cluster (khi có người/kệ thống nộp manifest trực tiếp,
  ngoài pipeline) chỉ thực thi được bằng admission controller; OPA
  trong pack này đánh giá ở tầng CI/plan · **Gate tiêu thụ**: điểm thực
  thi ở tầng đích (runtime), cặp với Gate 4/6 phía CI · **Bằng chứng**:
  `policy-decision` (từ PolicyReport của Kyverno do collector gom).

**Kiểm soát nào** (ánh xạ tham chiếu): ISO 27001 A.8.9 (quản lý cấu
hình — chuẩn cấu hình tối thiểu); PCI DSS 4.0 Yêu cầu 2 (không dùng
cấu hình mặc định của vendor); SOC 2 CC6.6 (ranh giới hệ thống) và
CC7.1.

**Nội dung**: (1) Pod/container chạy non-root, cấm `runAsUser: 0`;
(2) mọi container có requests/limits CPU + memory; (3)
`allowPrivilegeEscalation: false` và drop capability `ALL`.

**Kiểm chứng cục bộ (M2)**: bằng Kyverno CLI — manifest clean của
workload đạt 3/3 rule; fixture `../fixtures/k8s-bad-pod.yaml` (root,
privilege escalation, không limits) rớt 3/3. Xem
`../harness/kyverno_check.sh`.

**Vi phạm thì sửa thế nào**: đặt `securityContext` ở pod và container
như manifest mẫu của workload; bổ sung `resources.requests/limits`
theo sizing thật của service.
