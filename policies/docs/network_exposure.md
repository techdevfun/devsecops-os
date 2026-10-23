# network_exposure — do not open ingress from the Internet to internal ports

- **Code**: `devsecops.network_exposure` · **Mechanism**: OPA/Rego over normalised
  security group data (from the Terraform plan at M3; the HCL extractor at
  M2) · **Consuming gate**: Gate 4 (IaC scanning) at the plan evaluation step,
  before apply · **Evidence generated**: `iac-assessment` + `policy-decision`.

**Which control** (reference mapping): NIST CSF PR.AC/PR.DS and SSDF
PW.9 (secure configuration); PCI DSS 4.0 Requirements 1/2 (firewall rules,
no dangerous default configurations); SOC 2 CC6.6 (system boundaries);
ISO 27001 A.8.20–A.8.22 (network security, network segregation).

**Why**: opening an application/administration port to `0.0.0.0/0` bypasses all
controls at the load balancer/WAF layer — exactly planted fault #3 of payments-sample
(the task's SG opens ports 8000 and 22 to the Internet).

**How to fix a violation**: remove the `cidr_blocks = ["0.0.0.0/0"]` rule on
the internal security group; receive traffic via the ALB's SG
(`security_groups = [aws_security_group.alb.id]`) or restrict to the organisation's internal CIDR.
The pack's only exception: an SG declared `public_web: true`
may open exactly port 443.
