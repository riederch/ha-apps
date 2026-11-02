#!/bin/sh
set -eu

# Home Assistant injects SUPERVISOR_TOKEN / HASSIO_TOKEN into app containers,
# regardless of whether the app requests Supervisor API permissions.
# Run as PID 1 and replace the process environment BEFORE starting tini.
# With env -i, even unexpected future credentials cannot reach host-mode jobs
# through inherited environment variables or /proc/1/environ.
# Do not print the incoming environment or any token value.
if [ "$#" -eq 0 ]; then
  echo 'Runner command not specified.' >&2
  exit 64
fi

exec env -i \
  PATH='/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' \
  HOME='/data' \
  TZ="${TZ:-UTC}" \
  "$@"
