output "alb_dns_name" {
  description = "DNS name of the sample ALB."
  value       = aws_lb.main.dns_name
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster running the sample API."
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "Name of the ECS service running the sample API."
  value       = aws_ecs_service.app.name
}

output "artefacts_bucket" {
  description = "Private S3 bucket for evidence/log artefacts."
  value       = aws_s3_bucket.artefacts.bucket
}
