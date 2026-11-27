# Deploying Crate to AWS

**Terraform** creates the AWS resources. **Ansible** sets up the server and runs the app. Nothing here has been
applied to an AWS account yet.

```
Internet --HTTPS--> EC2: Caddy -> frontend -> backend -> RDS PostgreSQL (private)
                                                    \--> S3 (private): picture files
```

No SSH: Ansible reaches the server through AWS Systems Manager. The server runs
[docker-compose.prod.yml](../docker-compose.prod.yml).

## Before the first deployment

- **Not ready for the public yet:** anyone can register, and sign-in attempts are not limited.
- **Images:** the playbook pulls `ghcr.io/rronss/inventory-app-backend` and `-frontend` (arm64), which the
  `images` workflow publishes after `ci` passes on `main`. Both packages must be public, or the server cannot pull
  them. To deploy an earlier version, pass `-e image_tag=<commit>`.
- On your computer: Terraform, Ansible, the AWS CLI and the
  [Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html).
  `ansible-galaxy collection install -r ansible/requirements.yml`. Ansible's Python needs `boto3`.
- A domain, with its DNS at Cloudflare (the free plan is enough).

## 1. Create the resources

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars   # set the domain
terraform init
terraform plan -out=tfplan                     # read it
terraform apply tfplan
```

Then, in Cloudflare, add an `A` record for the domain with the `public_ip` output, set to **DNS only** (grey cloud),
so Caddy can get its certificate directly. If you later turn Cloudflare's proxy on, set SSL/TLS to **Full (strict)**.
The state file stays on your computer and is not committed.

## 2. Add the secrets (once)

Terraform never sees these. The database password is made by RDS itself.

```bash
aws ssm put-parameter --region us-east-1 --type SecureString --name /crate/SECRET_KEY --value "$(openssl rand -hex 32)"
```

Add `/crate/ADMIN_EMAIL` and `/crate/ADMIN_PASSWORD` the same way, or in the console under Systems Manager >
Parameter Store, which keeps the password out of your shell history.

## 3. Deploy

```bash
cd infrastructure/ansible
terraform -chdir=../terraform output -json ansible_vars > tf-outputs.json
ansible-playbook site.yml -e @tf-outputs.json
```

Run the playbook again to deploy a new version. `--check` shows what would change.

## What it costs

An estimate for us-east-1 with little traffic, about USD 27 a month: server, address and disk about 11, database
about 14, the rest (pictures, database password in Secrets Manager, domain) about 2 to 3. Check the AWS Pricing
Calculator before applying.

## Removing it

The database has deletion protection, and the picture bucket is not emptied by Terraform. Turn the protection off in
`database.tf`, apply, empty the bucket, then `terraform destroy`. A last database snapshot named `crate-final` is kept
and billed until you delete it.
