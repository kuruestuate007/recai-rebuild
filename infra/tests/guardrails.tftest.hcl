mock_provider "aws" {}

variables {
  profile         = "mock-profile"
  account_id      = "123456789012"
  region          = "us-east-2"
  stack_id        = "fixture"
  monthly_cap_usd = 25
  budget_email    = "alerts@example.com"
  portal_callback = "http://localhost:5173/callback"
  connector_zip   = "variables.tf"
  ingest_zip      = "variables.tf"
}

run "disabled_by_default" {
  command = plan

  assert {
    condition     = alltrue([for fn in aws_lambda_function.function : fn.reserved_concurrent_executions == 0])
    error_message = "Runtime must be paused by default."
  }
  assert {
    condition     = !aws_lambda_event_source_mapping.ingest.enabled
    error_message = "Ingestion must be disabled by default."
  }
  assert {
    condition     = aws_apigatewayv2_route.mcp["POST /mcp"].authorization_type == "NONE"
    error_message = "The MCP handler must emit its own OAuth challenge."
  }
  assert {
    condition     = alltrue([for route in aws_apigatewayv2_route.portal : route.authorization_type == "JWT"])
    error_message = "Portal routes require JWT authorization."
  }
}

run "metered_work_budget_action" {
  command = plan
  variables {
    enable_budget_action = true
  }

  assert {
    condition     = aws_budgets_budget_action.pause[0].approval_model == "AUTOMATIC"
    error_message = "The enabled budget action must be automatic."
  }
}
