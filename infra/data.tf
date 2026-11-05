resource "aws_s3_bucket" "files" {
  for_each      = local.buckets
  bucket        = "${local.name}-${each.key}-${var.account_id}-${var.region}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "files" {
  for_each                = aws_s3_bucket.files
  bucket                  = each.value.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "files" {
  for_each = aws_s3_bucket.files
  bucket   = each.value.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_dynamodb_table" "documents" {
  name         = local.name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "tenant"
  range_key    = "document_id"
  attribute {
    name = "tenant"
    type = "S"
  }
  attribute {
    name = "document_id"
    type = "S"
  }
}

resource "aws_s3vectors_vector_bucket" "search" {
  vector_bucket_name = "${local.name}-${var.account_id}-${var.region}"
}
resource "aws_s3vectors_index" "evidence" {
  vector_bucket_name = aws_s3vectors_vector_bucket.search.vector_bucket_name
  index_name         = "evidence"
  data_type          = "float32"
  dimension          = 512
  distance_metric    = "cosine"
}

resource "aws_sqs_queue" "dead" {
  name                      = "${local.name}-dead"
  message_retention_seconds = 345600
  sqs_managed_sse_enabled   = true
}
resource "aws_sqs_queue" "ingest" {
  name                       = "${local.name}-ingest"
  visibility_timeout_seconds = 180
  sqs_managed_sse_enabled    = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dead.arn
    maxReceiveCount     = 3
  })
}
resource "aws_sqs_queue_policy" "notifications" {
  queue_url = aws_sqs_queue.ingest.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "s3.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.ingest.arn
      Condition = {
        ArnEquals    = { "aws:SourceArn" = aws_s3_bucket.files["quarantine"].arn }
        StringEquals = { "aws:SourceAccount" = var.account_id }
      }
    }]
  })
}
resource "aws_s3_bucket_notification" "ingest" {
  bucket = aws_s3_bucket.files["quarantine"].id
  queue {
    queue_arn     = aws_sqs_queue.ingest.arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "uploads/"
  }
  depends_on = [aws_sqs_queue_policy.notifications]
}
