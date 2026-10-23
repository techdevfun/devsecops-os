# kyverno/workload-baseline — minimum runtime baseline on Kubernetes

- **File**: `../kyverno/workload-baseline.yaml` (ClusterPolicy,
  `validationFailureAction: Enforce`) · **Mechanism**: Kyverno admission
  — **reason Kyverno is needed alongside OPA**: control at the
  admission time of the cluster (when a person/system submits a manifest directly,
  outside the pipeline) can only be enforced by an admission controller; OPA
  in this pack evaluates at the CI/plan layer · **Consuming gate**: the enforcement point
  at the target layer (runtime), paired with Gate 4/6 on the CI side · **Evidence**:
  `policy-decision` (from Kyverno PolicyReports collected by the collector).

**Which control** (reference mapping): ISO 27001 A.8.9 (configuration
management — minimum configuration baseline); PCI DSS 4.0 Requirement 2 (do not use
vendor default configurations); SOC 2 CC6.6 (system boundaries) and
CC7.1.

**Contents**: (1) Pods/containers run non-root, forbid `runAsUser: 0`;
(2) every container has CPU + memory requests/limits; (3)
`allowPrivilegeEscalation: false` and drop capability `ALL`.

**Local verification (M2)**: with the Kyverno CLI — the clean workload manifest
passes 3/3 rules; the fixture `../fixtures/k8s-bad-pod.yaml` (root,
privilege escalation, no limits) fails 3/3. See
`../harness/kyverno_check.sh`.

**How to fix a violation**: set `securityContext` on the pod and container
as in the workload's sample manifest; add `resources.requests/limits`
according to the service's real sizing.
