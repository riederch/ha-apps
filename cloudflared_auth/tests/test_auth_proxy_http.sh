#!/usr/bin/env bash
# Live HTTP regression tests against the exact Nginx renderer used by the
# Cloudflared Origin Auth overlay. No Cloudflare credentials or network needed.
set -euo pipefail
for command in nginx python3 curl; do
    command -v "$command" >/dev/null || { echo "Missing $command" >&2; exit 1; }
done

SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/rootfs/etc/s6-overlay/s6-rc.d/prepare/run.sh"
# shellcheck disable=SC1090
source <(sed -n '/^writeAuthProxyHeader() {/,/^}/p' "$SCRIPT")
source <(sed -n '/^appendAuthProxyServer() {/,/^}/p' "$SCRIPT")
declare -F writeAuthProxyHeader appendAuthProxyServer >/dev/null

TEST_DIR="$(mktemp -d)"
AUTH_PROXY_CONFIG="$TEST_DIR/nginx.conf"
origin_pid=""
cleanup() {
    if [[ -f "$TEST_DIR/nginx.pid" ]]; then
        nginx -s quit -c "$AUTH_PROXY_CONFIG" >/dev/null 2>&1 || true
    fi
    if [[ -n "$origin_pid" ]]; then
        kill "$origin_pid" >/dev/null 2>&1 || true
        wait "$origin_pid" >/dev/null 2>&1 || true
    fi
    rm -rf "$TEST_DIR"
}
trap cleanup EXIT

bashio::var.is_empty() { [[ -z "${1:-}" ]]; }
origin_port=29972
basic_port=29970
bearer_port=29971

python3 -u - "$origin_port" <<'PY' &
import http.server
import sys

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        authorization = self.headers.get("Authorization", "")
        self.wfile.write(("received-authorization:" + authorization).encode("utf-8"))

    def log_message(self, *args):
        return

http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), Handler).serve_forever()
PY
origin_pid="$!"

writeAuthProxyHeader
basic_header="Basic $(printf 'alice:correct' | base64 | tr -d '\n')"
appendAuthProxyServer "$basic_port" "http://127.0.0.1:$origin_port" basic "$basic_header"
appendAuthProxyServer "$bearer_port" "http://127.0.0.1:$origin_port" bearer "Bearer test-ci-token"
printf '%s\n' '}' >>"$AUTH_PROXY_CONFIG"
# The production renderer uses /tmp; avoid a shared path in the CI runner.
sed -i "s|pid /tmp/nginx-origin-auth.pid;|pid $TEST_DIR/nginx.pid;|" "$AUTH_PROXY_CONFIG"
nginx -t -c "$AUTH_PROXY_CONFIG" >/dev/null
nginx -c "$AUTH_PROXY_CONFIG"

origin_ready=0
for i in {1..30}; do
    if curl --silent --max-time 1 "http://127.0.0.1:$origin_port/" >/dev/null; then
        origin_ready=1
        break
    fi
    sleep 0.1
done
test "$origin_ready" -eq 1 || { echo 'Origin did not start' >&2; exit 1; }

http_status() {
    curl --silent --show-error --max-time 4 -o /dev/null -w '%{http_code}' "$@"
}
assert_status() {
    local expected="$1"
    shift
    local got
    got="$(http_status "$@")"
    if [[ "$got" != "$expected" ]]; then
        echo "Expected HTTP $expected, got HTTP $got" >&2
        exit 1
    fi
}

# Auth must be enforced independently for both configured proxies.
assert_status 401 "http://127.0.0.1:$basic_port/"
assert_status 401 -u 'alice:wrong' "http://127.0.0.1:$basic_port/"
assert_status 200 -u 'alice:correct' "http://127.0.0.1:$basic_port/"
assert_status 401 "http://127.0.0.1:$bearer_port/"
assert_status 401 -H 'Authorization: Bearer wrong' "http://127.0.0.1:$bearer_port/"
assert_status 200 -H 'Authorization: Bearer test-ci-token' "http://127.0.0.1:$bearer_port/"

# The proxy must consume, not forward, the original client credentials.
basic_body="$(curl --silent --show-error --fail -u 'alice:correct' "http://127.0.0.1:$basic_port/")"
bearer_body="$(curl --silent --show-error --fail -H 'Authorization: Bearer test-ci-token' "http://127.0.0.1:$bearer_port/")"
test "$basic_body" = 'received-authorization:'
test "$bearer_body" = 'received-authorization:'

# The challenge header informs browsers and API clients of the auth scheme.
basic_headers="$(curl --silent --show-error -D - -o /dev/null "http://127.0.0.1:$basic_port/")"
bearer_headers="$(curl --silent --show-error -D - -o /dev/null "http://127.0.0.1:$bearer_port/")"
grep -qi 'WWW-Authenticate: Basic realm=' <<<"$basic_headers"
grep -qi 'WWW-Authenticate: Bearer realm=' <<<"$bearer_headers"

echo 'PASS: Basic/Bearer proxy 401, authorized 200, challenge and credential stripping'
