#!/command/with-contenv bashio
# shellcheck shell=bash
# ==============================================================================
# Home Assistant App: Cloudflared Origin Auth overlay runtime wrapper
# ==============================================================================

AUTH_PROXY_CONFIG="/tmp/nginx-origin-auth.conf"
UPSTREAM_RUN="/run-upstream.sh"

if [[ -f "${AUTH_PROXY_CONFIG}" ]]; then
    bashio::log.info "Starting local additional-host authentication proxy..."
    nginx -t -c "${AUTH_PROXY_CONFIG}" >/dev/null || \
        bashio::exit.nok "Authentication proxy configuration is invalid"
    nginx -c "${AUTH_PROXY_CONFIG}" || \
        bashio::exit.nok "Failed to start authentication proxy"

    while IFS= read -r proxy_port; do
        [[ -n "${proxy_port}" ]] || continue
        if ! nc -z -w 2 127.0.0.1 "${proxy_port}"; then
            bashio::exit.nok "Authentication proxy is not listening on 127.0.0.1:${proxy_port}"
        fi
        bashio::log.info "Verified authentication proxy listener on 127.0.0.1:${proxy_port}"
    done < <(grep -o '127\.0\.0\.1:[0-9]\+' "${AUTH_PROXY_CONFIG}" | cut -d: -f2 | sort -nu)
fi

if [[ ! -x "${UPSTREAM_RUN}" ]]; then
    bashio::exit.nok "Upstream Cloudflared run script not found: ${UPSTREAM_RUN}"
fi

exec "${UPSTREAM_RUN}" "$@"
