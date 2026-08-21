#!/command/with-contenv bashio
# shellcheck shell=bash
# ==============================================================================
# Home Assistant App: Cloudflared Origin Auth overlay runtime wrapper
# ==============================================================================

AUTH_PROXY_CONFIG="/tmp/nginx-origin-auth.conf"
UPSTREAM_RUN="/run-upstream.sh"

if [[ -f "${AUTH_PROXY_CONFIG}" ]]; then
    bashio::log.info "Starting local origin authentication proxy..."
    nginx -t -c "${AUTH_PROXY_CONFIG}" >/dev/null || \
        bashio::exit.nok "Origin authentication proxy configuration is invalid"
    nginx -c "${AUTH_PROXY_CONFIG}" || \
        bashio::exit.nok "Failed to start origin authentication proxy"
fi

if [[ ! -x "${UPSTREAM_RUN}" ]]; then
    bashio::exit.nok "Upstream Cloudflared run script not found: ${UPSTREAM_RUN}"
fi

exec "${UPSTREAM_RUN}" "$@"
