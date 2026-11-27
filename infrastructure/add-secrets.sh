#!/usr/bin/env bash
# Puts the app's secrets into Parameter Store, once. You type them here; they are not shown, and nothing is written
# to a file. A value that is already stored is left as it is.
set -euo pipefail
REGION="${AWS_REGION:-us-east-1}"

store() { # name value
  local answer
  if answer=$(aws ssm put-parameter --region "$REGION" --type SecureString --name "/crate/$1" --value "$2" 2>&1); then
    echo "  stored /crate/$1"
  elif [[ $answer == *ParameterAlreadyExists* ]]; then
    echo "  /crate/$1 already exists: left as it is"
  else
    echo "$answer" >&2
    exit 1
  fi
}

store SECRET_KEY "$(openssl rand -hex 32)" # signs the sign-in tokens; nobody needs to know it

read -rp "Admin email: " email
[[ $email == *@*.* ]] || { echo "That is not an email address" >&2; exit 1; }
store ADMIN_EMAIL "$email"

read -rsp "Admin password (12 to 72 characters): " password; echo
read -rsp "Repeat it: " again; echo
[[ $password == "$again" ]] || { echo "The two do not match" >&2; exit 1; }
((${#password} >= 12 && ${#password} <= 72)) || { echo "Use 12 to 72 characters" >&2; exit 1; }
store ADMIN_PASSWORD "$password"

echo "Cloudflare Turnstile keys (press Enter to skip; then deploy with -e bot_check=false)"
read -rp "Site key: " site
if [[ -n $site ]]; then
  read -rsp "Secret key: " secret; echo
  [[ -n $secret ]] || { echo "The secret key is empty" >&2; exit 1; }
  store TURNSTILE_SITE_KEY "$site"
  store TURNSTILE_SECRET_KEY "$secret"
fi
echo "Done."
