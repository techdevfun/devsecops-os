variable "aws_region" {
  description = "AWS region for the sample deployment."
  type        = string
  default     = "ap-southeast-1"
}

variable "project" {
  description = "Project name used as a prefix for all resources."
  type        = string
  default     = "example-service"
}

variable "environment" {
  description = "Environment name (demo, staging, ...)."
  type        = string
  default     = "demo"
}

variable "vpc_cidr" {
  description = "CIDR block for the sample VPC."
  type        = string
  default     = "10.42.0.0/16"
}

variable "app_port" {
  description = "Port the API listens on."
  type        = number
  default     = 8000
}

variable "container_image" {
  description = "Container image URI for the API (e.g. an ECR URI with an immutable tag or digest)."
  type        = string
  default     = "example-service:latest"
}

variable "allowed_ingress_cidrs" {
  description = <<-EOT
    CIDRs allowed to reach the ALB on 443. The default is a TEST-NET-3
    documentation range (RFC 5737) as a placeholder: replace it with your
    corporate egress / VPN ranges. Never put 0.0.0.0/0 here for a regulated
    workload — the planted variant shows what that looks like to the IaC gate.
  EOT
  type        = list(string)
  default     = ["203.0.113.0/24"]
}

variable "acm_certificate_arn" {
  description = "ARN of the ACM certificate for the ALB HTTPS listener. Placeholder in this sample; supply a real certificate before applying."
  type        = string
  default     = "arn:aws:acm:ap-southeast-1:123456789012:certificate/00000000-0000-0000-0000-000000000000"
}
