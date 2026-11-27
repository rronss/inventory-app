#!/usr/bin/env bash
# Deploys Crate with the Ansible playbook. If SECRET_KEY is missing or too short to be used, a new random one is
# stored first. Extra arguments go to ansible-playbook, for example --check.
set -euo pipefail
cd "$(dirname "$0")/ansible"
REGION="${AWS_REGION:-us-east-1}"

length=$(aws ssm get-parameter --region "$REGION" --name /crate/SECRET_KEY --with-decryption \
  --query 'length(Parameter.Value)' --output text 2>/dev/null || echo 0)
if ((length < 32)); then
  echo "SECRET_KEY is missing or too short: storing a new random one"
  aws ssm put-parameter --region "$REGION" --type SecureString --name /crate/SECRET_KEY \
    --value "$(openssl rand -hex 32)" --overwrite >/dev/null
fi

extra=()
if ! aws ssm get-parameter --region "$REGION" --name /crate/TURNSTILE_SECRET_KEY >/dev/null 2>&1; then
  echo "No Turnstile keys stored: deploying without the bot check"
  extra=(-e bot_check=false)
fi

if [[ $(uname) == Darwin ]]; then # or Ansible's workers crash on macOS
  export OS_ACTIVITY_MODE=disable OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES no_proxy='*'
fi

terraform -chdir=../terraform output -json ansible_vars >tf-outputs.json
ansible-playbook site.yml -e @tf-outputs.json ${extra[@]+"${extra[@]}"} "$@"
