resource "aws_budgets_budget" "sandbox" {
  name         = local.name
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_cap_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  cost_filter {
    name   = "TagKeyValue"
    values = ["user:stack$${var.region}-${var.stack_id}"]
  }
  dynamic "notification" {
    for_each = [50, 80, 100]
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = [var.budget_email]
    }
  }
}

resource "aws_iam_policy" "pause_metered_work" {
  count = var.enable_budget_action ? 1 : 0
  name  = "${local.name}-pause-metered-work"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Deny"
      Action   = ["bedrock:InvokeModel", "s3vectors:QueryVectors", "s3vectors:PutVectors"]
      Resource = [local.model_arn, aws_s3vectors_index.evidence.index_arn]
    }]
  })
}
resource "aws_iam_role" "budget" {
  count = var.enable_budget_action ? 1 : 0
  name  = "${local.name}-budget"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "sts:AssumeRole", Principal = { Service = "budgets.amazonaws.com" } }]
  })
}
resource "aws_iam_role_policy" "budget" {
  count = var.enable_budget_action ? 1 : 0
  role  = aws_iam_role.budget[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = ["iam:AttachRolePolicy", "iam:DetachRolePolicy"]
      Resource  = [for role in aws_iam_role.function : role.arn]
      Condition = { ArnEquals = { "iam:PolicyARN" = aws_iam_policy.pause_metered_work[0].arn } }
    }]
  })
}
resource "aws_budgets_budget_action" "pause" {
  count              = var.enable_budget_action ? 1 : 0
  budget_name        = aws_budgets_budget.sandbox.name
  action_type        = "APPLY_IAM_POLICY"
  approval_model     = "AUTOMATIC"
  notification_type  = "ACTUAL"
  execution_role_arn = aws_iam_role.budget[0].arn
  action_threshold {
    action_threshold_type  = "PERCENTAGE"
    action_threshold_value = 100
  }
  definition {
    iam_action_definition {
      policy_arn = aws_iam_policy.pause_metered_work[0].arn
      roles      = [for role in aws_iam_role.function : role.name]
    }
  }
  subscriber {
    address           = var.budget_email
    subscription_type = "EMAIL"
  }
  depends_on = [aws_iam_role_policy.budget]
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each            = aws_lambda_function.function
  alarm_name          = "${each.value.function_name}-errors"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  dimensions          = { FunctionName = each.value.function_name }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 3
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}
resource "aws_sns_topic" "alerts" {
  name = "${local.name}-alerts"
}
resource "aws_sns_topic_subscription" "alerts" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.budget_email
}

