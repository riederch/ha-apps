#!/bin/sh
set -eu

OPTIONS_FILE="/data/options.json"

GITEA_HOST="$(jq -r '.gitea_host // "http://homeassistant.local:3000"' "$OPTIONS_FILE")"
GITEA_INSECURE="$(jq -r '.insecure // false' "$OPTIONS_FILE")"
READ_ONLY="$(jq -r '.read_only // false' "$OPTIONS_FILE")"
DEBUG="$(jq -r '.debug // false' "$OPTIONS_FILE")"

export GITEA_HOST
export GITEA_MCP_READ_ONLY="$READ_ONLY"
GITEA_MCP_UPLOAD_MAX_MB="$(jq -r '.upload_max_mb // 16' "$OPTIONS_FILE")"
GITEA_MCP_UPLOAD_ALLOWED_HOSTS="$(jq -r '.upload_allowed_hosts // ""' "$OPTIONS_FILE")"
export GITEA_MCP_UPLOAD_MAX_MB GITEA_MCP_UPLOAD_ALLOWED_HOSTS
export GITEA_INSECURE

set -- /usr/local/bin/gitea-mcp -t http --port 8081 --host "$GITEA_HOST"

if [ "$READ_ONLY" = "true" ]; then
  set -- "$@" --read-only
fi

if [ "$DEBUG" = "true" ]; then
  set -- "$@" -d
fi

echo "Starting Gitea MCP 1.8.0 for ${GITEA_HOST} behind structured file bridge on port 8080"
echo "Migration compatibility: endpoint, Home Assistant options and per-request bearer-token forwarding are unchanged"
exec python3 /usr/local/lib/gitea-mcp-bridge.py "$@"
