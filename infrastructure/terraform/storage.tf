locals {
  buckets = {
    pictures = "${var.name}-pictures-${data.aws_caller_identity.current.account_id}"
    transfer = "${var.name}-ansible-${data.aws_caller_identity.current.account_id}" # files on their way to the server
  }
}

resource "aws_s3_bucket" "this" {
  for_each      = local.buckets
  bucket        = each.value
  force_destroy = each.key == "transfer" # never delete the pictures along with the bucket
}

resource "aws_s3_bucket_public_access_block" "this" {
  for_each                = aws_s3_bucket.this
  bucket                  = each.value.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  for_each = aws_s3_bucket.this
  bucket   = each.value.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "pictures" {
  bucket = aws_s3_bucket.this["pictures"].id

  versioning_configuration {
    status = "Enabled"
  }
}

# Removed pictures can be recovered for 30 days, then they are gone.
resource "aws_s3_bucket_lifecycle_configuration" "pictures" {
  bucket = aws_s3_bucket.this["pictures"].id

  rule {
    id     = "drop-old-versions"
    status = "Enabled"
    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }

  depends_on = [aws_s3_bucket_versioning.pictures]
}

# Ansible's files can hold secrets: keep them for a day at most.
resource "aws_s3_bucket_lifecycle_configuration" "transfer" {
  bucket = aws_s3_bucket.this["transfer"].id

  rule {
    id     = "expire"
    status = "Enabled"
    filter {}

    expiration {
      days = 1
    }
  }
}
