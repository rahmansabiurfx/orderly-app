# ════════════════════════════════════════════════════════════════
# Outputs
# ════════════════════════════════════════════════════════════════

output "repository_url" {
  description = "The full URL of the ECR repository"
  value       = aws_ecr_repository.app.repository_url
}

output "registry_url" {
  description = "The ECR registry URL (for docker login)"
  value       = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.name}.amazonaws.com"
}

output "repository_name" {
  description = "The name of the ECR repository"
  value       = aws_ecr_repository.app.name
}

output "aws_account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}
