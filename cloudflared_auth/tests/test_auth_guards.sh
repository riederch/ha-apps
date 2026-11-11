#!/usr/bin/env bash
# Test the exact fail-closed guards from the production prepare overlay.
set -euo pipefail
command -v jq >/dev/null || { echo 'jq is required' >&2; exit 1; }

SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/rootfs/etc/s6-overlay/s6-rc.d/prepare/run.sh"
TMPDIR_TEST="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_TEST"' EXIT

# Only import the production guard functions: the full script requires a
# Home Assistant Supervisor and the upstream tunnel prepare environment.
# shellcheck disable=SC1090
source <(sed -n '/^rejectRemoteManagedAuth() {/,/^}/p' "$SCRIPT")
source <(sed -n '/^validateProtectedIngressRoutes() {/,/^}/p' "$SCRIPT")
declare -F rejectRemoteManagedAuth validateProtectedIngressRoutes >/dev/null

bashio::config.has_value() {
    case "$1" in
        tunnel_token) [[ "${HAS_TOKEN:-0}" == "1" ]] ;;
        additional_hosts) [[ "${HAS_HOSTS:-0}" == "1" ]] ;;
        *) return 1 ;;
    esac
}
bashio::app.config() { printf '%s' "${OPTIONS_JSON:-}"; }
bashio::jq() { jq -cr "$2" <<<"$1"; }
bashio::exit.nok() { printf 'Rejected as expected: %s\n' "$*" >&2; exit 79; }

must_reject() {
    if ( "$@" >/dev/null 2>&1 ); then
        echo "FAIL: unsafe configuration was accepted" >&2
        exit 1
    fi
}

# A local tunnel may use Basic/Bearer credentials; a remote tunnel without
# local auth remains supported.
HAS_TOKEN=0 HAS_HOSTS=1 OPTIONS_JSON='{"additional_hosts":[{"basic_auth_username":"user","basic_auth_password":"test"}]}' rejectRemoteManagedAuth
HAS_TOKEN=1 HAS_HOSTS=0 rejectRemoteManagedAuth
HAS_TOKEN=1 HAS_HOSTS=1 OPTIONS_JSON='{"additional_hosts":[{"hostname":"other.example.test","service":"http://example.test"}]}' rejectRemoteManagedAuth

# Remote-managed mode must reject either local authentication mechanism and
# invalid JSON (otherwise credentials could be silently ignored).
must_reject env HAS_TOKEN=1 HAS_HOSTS=1 OPTIONS_JSON='{"additional_hosts":[{"basic_auth_username":"user","basic_auth_password":"test"}]}' bash -c 'source <(sed -n "/^rejectRemoteManagedAuth() {/,/^}/p" "$1"); bashio::config.has_value() { [[ "$1" == tunnel_token || "$1" == additional_hosts ]]; }; bashio::app.config() { printf "%s" "$OPTIONS_JSON"; }; bashio::jq() { jq -cr "$2" <<<"$1"; }; bashio::exit.nok() { exit 79; }; rejectRemoteManagedAuth' _ "$SCRIPT"
must_reject env HAS_TOKEN=1 HAS_HOSTS=1 OPTIONS_JSON='{"additional_hosts":[{"bearer_token":"secret"}]}' bash -c 'source <(sed -n "/^rejectRemoteManagedAuth() {/,/^}/p" "$1"); bashio::config.has_value() { [[ "$1" == tunnel_token || "$1" == additional_hosts ]]; }; bashio::app.config() { printf "%s" "$OPTIONS_JSON"; }; bashio::jq() { jq -cr "$2" <<<"$1"; }; bashio::exit.nok() { exit 79; }; rejectRemoteManagedAuth' _ "$SCRIPT"
must_reject env HAS_TOKEN=1 HAS_HOSTS=1 OPTIONS_JSON='{invalid json' bash -c 'source <(sed -n "/^rejectRemoteManagedAuth() {/,/^}/p" "$1"); bashio::config.has_value() { [[ "$1" == tunnel_token || "$1" == additional_hosts ]]; }; bashio::app.config() { printf "%s" "$OPTIONS_JSON"; }; bashio::jq() { jq -cr "$2" <<<"$1"; }; bashio::exit.nok() { exit 79; }; rejectRemoteManagedAuth' _ "$SCRIPT"

AUTH_EXPECTED_ROUTES='[{"hostname":"basic.example.test","service":"http://127.0.0.1:19080"},{"hostname":"bearer.example.test","service":"http://127.0.0.1:19081"}]'
cat >"$TMPDIR_TEST/good.json" <<'JSON'
{"ingress":[
  {"hostname":"basic.example.test","service":"http://127.0.0.1:19080"},
  {"hostname":"bearer.example.test","service":"http://127.0.0.1:19081"},
  {"service":"http_status:404"}
]}
JSON
validateProtectedIngressRoutes "$TMPDIR_TEST/good.json"

cat >"$TMPDIR_TEST/missing.json" <<'JSON'
{"ingress":[{"hostname":"basic.example.test","service":"http://127.0.0.1:19080"},{"service":"http_status:404"}]}
JSON
must_reject validateProtectedIngressRoutes "$TMPDIR_TEST/missing.json"

cat >"$TMPDIR_TEST/shadowed.json" <<'JSON'
{"ingress":[
  {"hostname":"basic.example.test","service":"http://internal-service:80"},
  {"hostname":"basic.example.test","service":"http://127.0.0.1:19080"},
  {"hostname":"bearer.example.test","service":"http://127.0.0.1:19081"}
]}
JSON
must_reject validateProtectedIngressRoutes "$TMPDIR_TEST/shadowed.json"

cat >"$TMPDIR_TEST/wrong.json" <<'JSON'
{"ingress":[
  {"hostname":"basic.example.test","service":"http://127.0.0.1:19081"},
  {"hostname":"bearer.example.test","service":"http://127.0.0.1:19080"}
]}
JSON
must_reject validateProtectedIngressRoutes "$TMPDIR_TEST/wrong.json"

printf '%s\n' '{}' >"$TMPDIR_TEST/empty.json"
must_reject validateProtectedIngressRoutes "$TMPDIR_TEST/empty.json"

echo 'PASS: remote-mode auth rejection and unique protected ingress route checks'
