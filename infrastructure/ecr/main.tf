# ════════════════════════════════════════════════════════════════
# ECR Repository for orderly-app
# ════════════════════════════════════════════════════════════════

resource "aws_ecr_repository" "app" {
  name                 = "orderly-app"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }

  force_delete = true

  tags = {
    Name = "orderly-app"
  }
}


# ════════════════════════════════════════════════════════════════
# ECR Lifecycle Policy
# ════════════════════════════════════════════════════════════════

resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep only the last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}


# ════════════════════════════════════════════════════════════════
# Data source: Get current AWS account ID and region
# ════════════════════════════════════════════════════════════════

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
