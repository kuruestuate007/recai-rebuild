resource "aws_cognito_user_pool" "users" {
  name = local.name
  admin_create_user_config {
    allow_admin_create_user_only = true
  }
  username_attributes = ["email"]
}
resource "aws_cognito_user_pool_domain" "login" {
  domain       = "${local.name}-${var.account_id}"
  user_pool_id = aws_cognito_user_pool.users.id
}
resource "aws_cognito_resource_server" "recai" {
  identifier   = "recai"
  name         = "RecAI"
  user_pool_id = aws_cognito_user_pool.users.id
  scope {
    scope_name        = "evidence.read"
    scope_description = "Read authorized resume evidence"
  }
  scope {
    scope_name        = "documents.manage"
    scope_description = "Manage the signed-in user's documents"
  }
}
resource "aws_cognito_user_pool_client" "portal" {
  name                                 = "${local.name}-portal"
  user_pool_id                         = aws_cognito_user_pool.users.id
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", local.mcp_scope, "recai/documents.manage"]
  supported_identity_providers         = ["COGNITO"]
  callback_urls                        = [var.portal_callback]
  prevent_user_existence_errors        = "ENABLED"
  depends_on                           = [aws_cognito_resource_server.recai]
}
resource "aws_cognito_user_pool_client" "claude" {
  name                                 = "${local.name}-claude"
  user_pool_id                         = aws_cognito_user_pool.users.id
  generate_secret                      = true
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", local.mcp_scope]
  supported_identity_providers         = ["COGNITO"]
  callback_urls                        = ["https://claude.ai/api/mcp/auth_callback"]
  prevent_user_existence_errors        = "ENABLED"
  depends_on                           = [aws_cognito_resource_server.recai]
}
