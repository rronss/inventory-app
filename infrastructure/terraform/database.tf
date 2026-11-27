resource "aws_db_subnet_group" "main" {
  name       = var.name
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_db_instance" "main" {
  identifier     = var.name
  engine         = "postgres"
  engine_version = "17" # the same major version as docker-compose.yml
  instance_class = var.db_instance_class

  allocated_storage = var.db_storage_gb
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = var.name
  username = var.name
  # RDS makes the password and keeps it in Secrets Manager, so it is in neither the code nor the Terraform state.
  manage_master_user_password = true

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]
  publicly_accessible    = false
  multi_az               = false

  backup_retention_period   = var.db_backup_days
  copy_tags_to_snapshot     = true
  deletion_protection       = !var.allow_destroy
  skip_final_snapshot       = !var.final_snapshot
  final_snapshot_identifier = "${var.name}-final"
}

# RDS would change the password every 7 days, and the server only reads it when deploying. Stretch it to the
# longest allowed. Run the playbook again after a rotation.
resource "aws_secretsmanager_secret_rotation" "database" {
  secret_id          = aws_db_instance.main.master_user_secret[0].secret_arn
  rotate_immediately = false

  rotation_rules {
    automatically_after_days = 1000
  }
}
