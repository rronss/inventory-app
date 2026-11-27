output "public_ip" {
  description = "Point the domain's A record here."
  value       = aws_eip.server.public_ip
}

output "ansible_vars" {
  description = "What the playbook needs. None of it is secret."
  value = {
    crate_region   = var.region
    domain         = var.domain
    ssm_bucket     = aws_s3_bucket.this["transfer"].bucket
    picture_bucket = aws_s3_bucket.this["pictures"].bucket
    db_host        = aws_db_instance.main.address
    db_name        = aws_db_instance.main.db_name
    db_user        = aws_db_instance.main.username
    db_secret_arn  = aws_db_instance.main.master_user_secret[0].secret_arn
  }
}
