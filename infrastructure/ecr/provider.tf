terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  required_version = ">= 1.0"


  backend "s3" {
    bucket         = "rahmansabiurfx-terraform-state"
    key            = "orderly-app/ecr/terraform.tfstate" # Different path from Project 1
    region         = "us-east-1"
    dynamodb_table = "rahmansabiurfx-state-locks"
    encrypt        = true
  }
}
provider "aws" {
  region = "us-east-1"

  # Default tags applied to ALL resources created by this Terraform config
  default_tags {
    tags = {
      Project   = "orderly-app"
      ManagedBy = "terraform"
      Component = "ecr"
    }
  }
}
