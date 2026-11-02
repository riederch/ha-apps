#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CLEAN_ENV="$SCRIPT_DIR/../clean-env.sh"

# Synthetic canaries; no real access tokens are used.
CANARY_SUPERVISOR='synthetic-supervisor-secret-canary-01'
CANARY_HASSIO='synthetic-hassio-secret-canary-02'
CANARY_GITEA='synthetic-gitea-secret-canary-03'
CANARY_OTHER='synthetic-unanticipated-secret-canary-04'

result=$(env \
  SUPERVISOR_TOKEN="$CANARY_SUPERVISOR" \
  HASSIO_TOKEN="$CANARY_HASSIO" \
  GITEA_RUNNER_REGISTRATION_TOKEN="$CANARY_GITEA" \
  OTHER_UNEXPECTED_CREDENTIAL="$CANARY_OTHER" \
  TZ='Europe/Vienna' \
  "$CLEAN_ENV" /usr/bin/env)

count=$(printf '%s\n' "$result" | grep -c '^[A-Za-z_][A-Za-z_0-9]*=' || :)
if [ "$count" -ne 3 ]; then
  echo 'FAILED: unexpected variables in runner child environment.' >&2
  exit 1
fi
for expected in \
  'PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' \
  'HOME=/data' \
  'TZ=Europe/Vienna'; do
  if ! printf '%s\n' "$result" | grep -Fxq "$expected"; then
    echo 'FAILED: required allowlisted variable missing.' >&2
    exit 1
  fi
done
for canary in "$CANARY_SUPERVISOR" "$CANARY_HASSIO" "$CANARY_GITEA" "$CANARY_OTHER"; do
  if printf '%s\n' "$result" | grep -Fq "$canary"; then
    echo 'FAILED: sensitive test value was inherited.' >&2
    exit 1
  fi
done
for name in SUPERVISOR_TOKEN HASSIO_TOKEN GITEA_RUNNER_REGISTRATION_TOKEN OTHER_UNEXPECTED_CREDENTIAL; do
  if printf '%s\n' "$result" | grep -q "^$name="; then
    echo 'FAILED: sensitive variable name was inherited.' >&2
    exit 1
  fi
done
if "$CLEAN_ENV" >/dev/null 2>&1; then
  echo 'FAILED: empty command should be rejected.' >&2
  exit 1
fi
echo 'PASS: Runner environment is restricted to the allowlist.'
