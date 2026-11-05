terraform {
  required_version = ">= 1.7, < 2.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

variable "profile" {
  type = string
  validation {
    condition     = length(trimspace(var.profile)) > 0
    error_message = "Set an explicit AWS profile."
  }
}
variable "account_id" {
  type = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "Set the expected 12-digit AWS account ID."
  }
}
variable "region" {
  type = string
  validation {
    condition     = contains(["us-east-2", "eu-central-2"], var.region)
    error_message = "Choose Ohio (us-east-2) or Zurich (eu-central-2) explicitly."
  }
}
variable "stack_id" {
  type = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,11}$", var.stack_id))
    error_message = "Use 3–12 lowercase letters, digits or hyphens, starting with a letter."
  }
}
variable "monthly_cap_usd" {
  type = number
  validation {
    condition     = var.monthly_cap_usd > 0
    error_message = "Set a positive monthly cost cap."
  }
}
variable "budget_email" {
  type = string
  validation {
    condition     = can(regex("^[^@ ]+@[^@ ]+\\.[^@ ]+$", var.budget_email))
    error_message = "Set an address for budget alerts."
  }
}
variable "portal_callback" { type = string }
variable "connector_zip" { type = string }
variable "ingest_zip" { type = string }
variable "enable_runtime" {
  type    = bool
  default = false
}
variable "enable_budget_action" {
  type    = bool
  default = false
}

provider "aws" {
  profile             = var.profile
  region              = var.region
  allowed_account_ids = [var.account_id]
  default_tags {
    tags = {
      project = "recai-rebuild"
      stack   = "${var.region}-${var.stack_id}"
    }
  }
}

locals {
  name      = "recai-${var.region}-${var.stack_id}"
  model_arn = "arn:aws:bedrock:${var.region}::foundation-model/amazon.titan-embed-text-v2:0"
  functions = { connector = var.connector_zip, ingest = var.ingest_zip }
  buckets   = toset(["originals", "quarantine"])
  mcp_scope = "recai/evidence.read"
}

