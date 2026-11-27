data "aws_iam_policy_document" "server_trust" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "server" {
  name               = "${var.name}-server"
  assume_role_policy = data.aws_iam_policy_document.server_trust.json
}

# Lets Systems Manager reach the server, in place of SSH.
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.server.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# The app's own rights: picture files, nothing else.
data "aws_iam_policy_document" "pictures" {
  statement {
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.this["pictures"].arn}/*"]
  }
}

resource "aws_iam_role_policy" "pictures" {
  name   = "pictures"
  role   = aws_iam_role.server.id
  policy = data.aws_iam_policy_document.pictures.json
}

resource "aws_iam_instance_profile" "server" {
  name = "${var.name}-server"
  role = aws_iam_role.server.name
}
