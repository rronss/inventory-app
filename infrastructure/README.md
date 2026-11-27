# Deploying Crate to AWS

**Terraform** creates the AWS resources. **Ansible** sets up the server and runs the app.

```
Internet --HTTPS--> EC2: Caddy -> frontend -> backend -> RDS PostgreSQL (private)
                                                    \--> S3 (private): picture files
```

No SSH: Ansible reaches the server through AWS Systems Manager. The server runs
[docker-compose.prod.yml](../docker-compose.prod.yml).

## Before the first deployment

- **Public sign-up:** sign-in and sign-up attempts are limited, and new accounts can change only the items they
  add. They can still see public items and people, and send messages.
- A Cloudflare **Turnstile** widget for the domain (free), for the bot check on sign-up.
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
so Caddy can get its certificate directly. Before turning Cloudflare's proxy on, set SSL/TLS to **Full (strict)** and
tell Caddy to trust Cloudflare's addresses: otherwise every visitor seems to come from Cloudflare and they share
one attempt limit.
The state file stays on your computer and is not committed.

## 2. Add the secrets (once)

Terraform never sees these. The database password is made by RDS itself.

```bash
infrastructure/add-secrets.sh
```

It makes `SECRET_KEY`, asks for the admin email and password, and for the Turnstile widget's keys, and stores them
under `/crate/` in Parameter Store. Without the Turnstile keys, deploy with `-e bot_check=false`.

## 3. Deploy

```bash
infrastructure/deploy.sh
```

or step by step:

```bash
cd infrastructure/ansible
terraform -chdir=../terraform output -json ansible_vars > tf-outputs.json
ansible-playbook site.yml -e @tf-outputs.json
```

Run the playbook again to deploy a new version. `--check` shows what would change.

**On macOS**, set these first, or Ansible's workers crash ("A worker was found in a dead state"):

```bash
export OS_ACTIVITY_MODE=disable OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES no_proxy='*'
```

## What it costs

An estimate for us-east-1 with little traffic, about USD 27 a month: server, address and disk about 11, database
about 14, the rest (pictures, database password in Secrets Manager, domain) about 2 to 3. Check the AWS Pricing
Calculator before applying.

## Removing it

This deletes the database and every picture. Delete the domain's DNS record first, so it does not point at an
address you have given up. Then lift the protections, and destroy:

```bash
cd infrastructure/terraform
terraform apply -var allow_destroy=true -var final_snapshot=false
terraform destroy -var allow_destroy=true -var final_snapshot=false
```

Leave `-var final_snapshot=false` out to keep a last database snapshot, `crate-final`; it is billed until you delete
it, and it must be gone before another one can be made. The secrets in Parameter Store are not Terraform's: they stay
for next time.
