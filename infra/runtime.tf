resource "aws_cloudwatch_log_group" "function" {
  for_each          = local.functions
  name              = "/aws/lambda/${local.name}-${each.key}"
  retention_in_days = 7
}
resource "aws_iam_role" "function" {
  for_each = local.functions
  name     = "${local.name}-${each.key}"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "sts:AssumeRole", Principal = { Service = "lambda.amazonaws.com" } }]
  })
}
locals {
  policies = {
    connector = [
      { Action = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"], Resource = aws_dynamodb_table.documents.arn },
      { Action = ["s3:GetObject"], Resource = "${aws_s3_bucket.files["originals"].arn}/*" },
      { Action = ["s3:PutObject"], Resource = "${aws_s3_bucket.files["quarantine"].arn}/uploads/*" },
      { Action = ["s3vectors:QueryVectors"], Resource = aws_s3vectors_index.evidence.index_arn }
    ]
    ingest = [
      { Action = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"], Resource = aws_dynamodb_table.documents.arn },
      { Action = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"], Resource = aws_sqs_queue.ingest.arn },
      { Action = ["s3:GetObject", "s3:DeleteObject"], Resource = "${aws_s3_bucket.files["quarantine"].arn}/uploads/*" },
      { Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"], Resource = "${aws_s3_bucket.files["originals"].arn}/*" },
      { Action = ["s3vectors:PutVectors", "s3vectors:DeleteVectors"], Resource = aws_s3vectors_index.evidence.index_arn }
    ]
  }
}
resource "aws_iam_role_policy" "function" {
  for_each = local.functions
  name     = "runtime"
  role     = aws_iam_role.function[each.key].name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      for statement in concat(local.policies[each.key], [
        { Action = ["logs:CreateLogStream", "logs:PutLogEvents"], Resource = "${aws_cloudwatch_log_group.function[each.key].arn}:*" },
        { Action = ["bedrock:InvokeModel"], Resource = local.model_arn }
      ]) : merge(statement, { Effect = "Allow" })
    ]
  })
}
resource "aws_lambda_function" "function" {
  for_each                       = local.functions
  function_name                  = "${local.name}-${each.key}"
  role                           = aws_iam_role.function[each.key].arn
  filename                       = each.value
  source_code_hash               = filebase64sha256(each.value)
  handler                        = "handler.lambda_handler"
  runtime                        = "python3.13"
  memory_size                    = each.key == "ingest" ? 1024 : 512
  timeout                        = each.key == "ingest" ? 30 : 10
  reserved_concurrent_executions = var.enable_runtime ? (each.key == "ingest" ? 2 : 5) : 0
  environment {
    variables = {
      DOCUMENT_TABLE    = aws_dynamodb_table.documents.name
      ORIGINALS_BUCKET  = aws_s3_bucket.files["originals"].id
      QUARANTINE_BUCKET = aws_s3_bucket.files["quarantine"].id
      VECTOR_BUCKET     = aws_s3vectors_vector_bucket.search.vector_bucket_name
      VECTOR_INDEX      = aws_s3vectors_index.evidence.index_name
      EMBEDDING_MODEL   = "amazon.titan-embed-text-v2:0"
      TOKEN_ISSUER      = "https://${aws_cognito_user_pool.users.endpoint}"
      MCP_CLIENT_ID     = aws_cognito_user_pool_client.claude.id
      PORTAL_CLIENT_ID  = aws_cognito_user_pool_client.portal.id
      MCP_RESOURCE      = "${aws_apigatewayv2_api.http.api_endpoint}/mcp"
    }
  }
  depends_on = [aws_iam_role_policy.function]
}
resource "aws_lambda_event_source_mapping" "ingest" {
  event_source_arn = aws_sqs_queue.ingest.arn
  function_name    = aws_lambda_function.function["ingest"].arn
  batch_size       = 1
  enabled          = var.enable_runtime
  scaling_config {
    maximum_concurrency = 2
  }
  depends_on = [aws_iam_role_policy.function]
}

resource "aws_apigatewayv2_api" "http" {
  name          = local.name
  protocol_type = "HTTP"
}
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true
  default_route_settings {
    throttling_burst_limit = 10
    throttling_rate_limit  = 5
  }
}
resource "aws_apigatewayv2_integration" "connector" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.function["connector"].invoke_arn
  payload_format_version = "2.0"
}
resource "aws_apigatewayv2_authorizer" "portal" {
  api_id           = aws_apigatewayv2_api.http.id
  name             = "portal-access-token"
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  jwt_configuration {
    audience = [aws_cognito_user_pool_client.portal.id]
    issuer   = "https://${aws_cognito_user_pool.users.endpoint}"
  }
}
resource "aws_apigatewayv2_route" "portal" {
  for_each             = toset(["PUT /documents/{id}", "GET /documents/{id}", "DELETE /documents/{id}"])
  api_id               = aws_apigatewayv2_api.http.id
  route_key            = each.key
  target               = "integrations/${aws_apigatewayv2_integration.connector.id}"
  authorization_type   = "JWT"
  authorizer_id        = aws_apigatewayv2_authorizer.portal.id
  authorization_scopes = ["recai/documents.manage"]
}
resource "aws_apigatewayv2_route" "mcp" {
  # Let the MCP handler emit the OAuth discovery challenge. It must verify tokens itself.
  for_each           = toset(["POST /mcp", "GET /mcp", "DELETE /mcp", "GET /.well-known/oauth-protected-resource/mcp"])
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = each.key
  authorization_type = "NONE"
  target             = "integrations/${aws_apigatewayv2_integration.connector.id}"
}
resource "aws_lambda_permission" "api" {
  for_each      = toset(["mcp", ".well-known/oauth-protected-resource/mcp", "documents/*"])
  statement_id  = "Gateway-${replace(replace(replace(each.key, "/", "-"), "*", "any"), ".", "")}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.function["connector"].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*/${each.key}"
}
output "endpoint" {
  value = "${aws_apigatewayv2_api.http.api_endpoint}/mcp"
}
output "target" {
  value = { account = var.account_id, region = var.region, stack = var.stack_id }
}


