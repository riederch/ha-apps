#!/bin/sh
set -eu

OPTIONS_FILE="/data/options.json"

GITEA_HOST="$(jq -r '.gitea_host // "http://homeassistant.local:3000"' "$OPTIONS_FILE")"
GITEA_INSECURE="$(jq -r '.insecure // false' "$OPTIONS_FILE")"
DEBUG="$(jq -r '.debug // false' "$OPTIONS_FILE")"

export GITEA_HOST
export GITEA_INSECURE

set -- /usr/local/bin/gitea-mcp -t http --port 8080 --host "$GITEA_HOST"

if [ "$DEBUG" = "true" ]; then
  set -- "$@" -d
fi

echo "Starting Gitea MCP for ${GITEA_HOST} on port 8080"
exec "$@"
