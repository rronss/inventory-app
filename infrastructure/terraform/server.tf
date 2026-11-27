data "aws_ssm_parameter" "ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64" # includes the SSM agent
}

resource "aws_instance" "server" {
  ami                    = data.aws_ssm_parameter.ami.value
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.server.id]
  iam_instance_profile   = aws_iam_instance_profile.server.name

  # Needed to reach AWS during the first boot, before the fixed address below is attached.
  associate_public_ip_address = true

  metadata_options {
    http_tokens                 = "required"
    http_put_response_hop_limit = 2 # one more hop, so the backend container can use the server's role
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = var.server_disk_gb
    encrypted   = true
  }

  tags = { Name = var.name }

  lifecycle {
    ignore_changes = [ami] # a newer image from AWS must not replace the running server
  }

  depends_on = [aws_route_table_association.public]
}

resource "aws_eip" "server" {
  instance = aws_instance.server.id
  domain   = "vpc"
  tags     = { Name = var.name }

  depends_on = [aws_internet_gateway.main]
}
