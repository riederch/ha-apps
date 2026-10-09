#!/bin/sh
set -eu

OPTIONS_FILE="/data/options.json"
RUNNER_STATE_FILE="/data/.runner"
INSTANCE_STATE_FILE="/data/.ha-runner-instance"

GITEA_INSTANCE_URL="$(jq -r '.gitea_instance_url // "http://homeassistant.local:3000"' "$OPTIONS_FILE")"
REGISTRATION_TOKEN="$(jq -r '.registration_token // ""' "$OPTIONS_FILE")"
RUNNER_NAME="$(jq -r '.runner_name // "homeassistant"' "$OPTIONS_FILE")"
RUNNER_LABELS="$(jq -r '(.labels // ["ha-runner:host"]) | map(select(length > 0)) | join(",")' "$OPTIONS_FILE")"

if [ -z "$RUNNER_LABELS" ]; then
  RUNNER_LABELS="ha-runner:host"
fi

mkdir -p /data
cd /data

if [ -s "$RUNNER_STATE_FILE" ]; then
  if [ -s "$INSTANCE_STATE_FILE" ]; then
    REGISTERED_INSTANCE="$(cat "$INSTANCE_STATE_FILE")"
    if [ "$REGISTERED_INSTANCE" != "$GITEA_INSTANCE_URL" ]; then
      echo "Runner is already registered for $REGISTERED_INSTANCE."
      echo "Configured instance is $GITEA_INSTANCE_URL."
      echo "Remove the app data or restore the previous instance URL before starting again."
      exit 1
    fi
  else
    printf '%s\n' "$GITEA_INSTANCE_URL" > "$INSTANCE_STATE_FILE"
  fi

  echo "Using existing Gitea runner registration from $RUNNER_STATE_FILE"
else
  if [ -z "$REGISTRATION_TOKEN" ]; then
    echo "No runner registration exists yet and registration_token is empty."
    echo "Create a user-level runner registration token in Gitea and add it to the app configuration."
    exit 1
  fi

  umask 077
  TOKEN_FILE="$(mktemp /tmp/gitea-runner-token.XXXXXX)"
  trap 'rm -f "$TOKEN_FILE"' EXIT INT TERM HUP
  printf '%s' "$REGISTRATION_TOKEN" > "$TOKEN_FILE"

  echo "Registering Gitea runner '$RUNNER_NAME' at $GITEA_INSTANCE_URL"
  gitea-runner register \
    --no-interactive \
    --instance "$GITEA_INSTANCE_URL" \
    --token-file "$TOKEN_FILE" \
    --name "$RUNNER_NAME" \
    --labels "$RUNNER_LABELS"

  rm -f "$TOKEN_FILE"
  trap - EXIT INT TERM HUP
  printf '%s\n' "$GITEA_INSTANCE_URL" > "$INSTANCE_STATE_FILE"
fi

unset REGISTRATION_TOKEN

echo "Starting Gitea Runner 5.0.0"
echo "Instance: $GITEA_INSTANCE_URL"
echo "Labels: $RUNNER_LABELS"
echo "Execution mode: host inside the Home Assistant app container"
echo "Docker API access: disabled"

exec gitea-runner daemon --labels "$RUNNER_LABELS"
