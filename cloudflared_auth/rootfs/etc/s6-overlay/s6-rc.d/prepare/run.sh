#!/command/with-contenv bashio
# shellcheck shell=bash
# ==============================================================================
# Home Assistant App: Cloudflared Origin Auth overlay
# Extends upstream app-cloudflared with per-additional-host Authorization headers.
# ==============================================================================

UPSTREAM_PREPARE="/etc/s6-overlay/s6-rc.d/prepare/run-upstream.sh"
AUTH_PROXY_CONFIG="/tmp/nginx-origin-auth.conf"
AUTH_PROXY_PORT_BASE=19080

if [[ ! -r "${UPSTREAM_PREPARE}" ]]; then
    bashio::exit.nok "Upstream Cloudflared prepare script not found: ${UPSTREAM_PREPARE}"
fi

# Load all upstream functions without executing upstream main().
# The upstream file guards main() with BASH_SOURCE, so sourcing is safe.
# shellcheck disable=SC1090
source "${UPSTREAM_PREPARE}"

# Keep the upstream validation implementation, but redact the one debug statement
# that would otherwise print the complete additional_hosts JSON including secrets.
eval "$(
    declare -f validateConfigAndSetVars |
        sed '1s/validateConfigAndSetVars/validateConfigAndSetVars_upstream/' |
        sed 's/bashio::log.debug "Checking host ${additional_host}\.\.\."/bashio::log.debug "Checking configured additional host..."/'
)"

# Keep the upstream config generator. Our wrapper sanitizes/re-writes
# additional_hosts before invoking it.
eval "$(
    declare -f createConfig |
        sed '1s/createConfig/createConfig_upstream/'
)"

validateOriginAuth() {
    local additional_host
    local hostname
    local service
    local basic_auth_username
    local basic_auth_password
    local bearer_token

    for additional_host in "${additional_hosts[@]}"; do
        hostname=$(bashio::jq "${additional_host}" '.hostname')
        service=$(bashio::jq "${additional_host}" '.service')
        basic_auth_username=$(bashio::jq "${additional_host}" '.basic_auth_username // ""')
        basic_auth_password=$(bashio::jq "${additional_host}" '.basic_auth_password // ""')
        bearer_token=$(bashio::jq "${additional_host}" '.bearer_token // ""')

        if bashio::var.has_value "${bearer_token}" && \
            { bashio::var.has_value "${basic_auth_username}" || bashio::var.has_value "${basic_auth_password}"; }; then
            bashio::exit.nok "additional_hosts entry '${hostname}' cannot use bearer_token and Basic Auth at the same time"
        fi

        if bashio::var.has_value "${basic_auth_username}" && bashio::var.is_empty "${basic_auth_password}"; then
            bashio::exit.nok "additional_hosts entry '${hostname}' has basic_auth_username but no basic_auth_password"
        fi
        if bashio::var.has_value "${basic_auth_password}" && bashio::var.is_empty "${basic_auth_username}"; then
            bashio::exit.nok "additional_hosts entry '${hostname}' has basic_auth_password but no basic_auth_username"
        fi

        if bashio::var.has_value "${basic_auth_username}" || bashio::var.has_value "${bearer_token}"; then
            case "${service}" in
                http://*|https://*) ;;
                *)
                    bashio::exit.nok "Origin authentication for '${hostname}' requires an http:// or https:// service"
                    ;;
            esac

            # Authenticated origins are intentionally limited to an origin URL
            # (scheme + host + optional port). cloudflared service URLs are origin
            # addresses as well, and this keeps proxy URI handling deterministic.
            if ! [[ ${service} =~ ^https?://[^/]+/?$ ]]; then
                bashio::exit.nok "Authenticated service for '${hostname}' must not contain a URL path"
            fi

            # The service is inserted into an nginx directive. Reject characters that
            # could alter nginx configuration. Normal HTTP(S) origin URLs are unaffected.
            if [[ "${service}" == *$'\n'* || "${service}" == *$'\r'* || \
                "${service}" == *';'* || "${service}" == *'{'* || "${service}" == *'}'* || \
                "${service}" == *'"'* || "${service}" == *"'"* || "${service}" == *'\\'* || \
                "${service}" == *'$'* || "${service}" == *$'\t'* || "${service}" == *' '* ]]; then
                bashio::exit.nok "Service URL for authenticated host '${hostname}' contains unsupported characters"
            fi
        fi

        if bashio::var.has_value "${bearer_token}" && \
            ! [[ ${bearer_token} =~ ^[A-Za-z0-9._~+/=-]+$ ]]; then
            bashio::exit.nok "bearer_token for '${hostname}' contains characters outside the Bearer token syntax"
        fi

        if bashio::var.has_value "${basic_auth_username}"; then
            if [[ "${basic_auth_username}" == *:* || "${basic_auth_username}" == *$'\n'* || "${basic_auth_username}" == *$'\r'* ]]; then
                bashio::exit.nok "basic_auth_username for '${hostname}' must not contain ':' or line breaks"
            fi
            if [[ "${basic_auth_password}" == *$'\n'* || "${basic_auth_password}" == *$'\r'* ]]; then
                bashio::exit.nok "basic_auth_password for '${hostname}' must not contain line breaks"
            fi
        fi
    done
}

writeAuthProxyHeader() {
    local resolver
    resolver=$(awk '$1 == "nameserver" && $2 ~ /^[0-9.]+$/ {print $2; exit}' /etc/resolv.conf)
    if bashio::var.is_empty "${resolver}"; then
        resolver="127.0.0.11"
    fi

    cat >"${AUTH_PROXY_CONFIG}" <<NGINX
worker_processes 1;
pid /tmp/nginx-origin-auth.pid;
error_log /dev/stderr warn;

events {
    worker_connections 1024;
}

http {
    access_log off;
    server_tokens off;
    client_max_body_size 0;
    resolver ${resolver} valid=30s;
NGINX
}

appendAuthProxyServer() {
    local port="$1"
    local service="${2%/}"
    local authorization_header="$3"

    cat >>"${AUTH_PROXY_CONFIG}" <<NGINX

    server {
        listen 127.0.0.1:${port};

        location / {
            set \$origin_service "${service}";
            proxy_pass \$origin_service\$request_uri;
            proxy_http_version 1.1;
            proxy_buffering off;

            # Preserve the request semantics cloudflared would normally pass through.
            proxy_set_header Host \$http_host;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection \$http_connection;

            # Always replace any client-provided Authorization header.
            proxy_set_header Authorization "${authorization_header}";

            # Match upstream app-cloudflared behavior, which disables origin TLS
            # verification for its generated ingress rules.
            proxy_ssl_server_name on;
            proxy_ssl_verify off;
        }
    }
NGINX
}

prepareOriginAuthHosts() {
    local -a sanitized_hosts=()
    local additional_host
    local sanitized_host
    local hostname
    local service
    local basic_auth_username
    local basic_auth_password
    local bearer_token
    local authorization_header
    local proxy_port
    local proxy_count=0

    rm -f "${AUTH_PROXY_CONFIG}"

    for additional_host in "${additional_hosts[@]}"; do
        hostname=$(bashio::jq "${additional_host}" '.hostname')
        service=$(bashio::jq "${additional_host}" '.service')
        basic_auth_username=$(bashio::jq "${additional_host}" '.basic_auth_username // ""')
        basic_auth_password=$(bashio::jq "${additional_host}" '.basic_auth_password // ""')
        bearer_token=$(bashio::jq "${additional_host}" '.bearer_token // ""')

        # Never pass our private extension keys into cloudflared itself.
        sanitized_host=$(bashio::jq "${additional_host}" \
            'del(.basic_auth_username, .basic_auth_password, .bearer_token)')

        authorization_header=""
        if bashio::var.has_value "${bearer_token}"; then
            authorization_header="Bearer ${bearer_token}"
        elif bashio::var.has_value "${basic_auth_username}"; then
            authorization_header="Basic $(printf '%s:%s' "${basic_auth_username}" "${basic_auth_password}" | base64 | tr -d '\n')"
        fi

        if bashio::var.has_value "${authorization_header}"; then
            if [[ ${proxy_count} -eq 0 ]]; then
                writeAuthProxyHeader
            fi

            proxy_port=$((AUTH_PROXY_PORT_BASE + proxy_count))
            appendAuthProxyServer "${proxy_port}" "${service}" "${authorization_header}"

            sanitized_host=$(bashio::jq "${sanitized_host}" \
                ".service = \"http://127.0.0.1:${proxy_port}\"")

            bashio::log.info "Configured origin Authorization proxy for ${hostname}"
            proxy_count=$((proxy_count + 1))
        fi

        sanitized_hosts+=("${sanitized_host}")
    done

    if [[ ${proxy_count} -gt 0 ]]; then
        printf '%s\n' '}' >>"${AUTH_PROXY_CONFIG}"
        chmod 600 "${AUTH_PROXY_CONFIG}"
        nginx -t -c "${AUTH_PROXY_CONFIG}" >/dev/null
        bashio::log.info "Prepared ${proxy_count} authenticated origin host(s)"
    fi

    additional_hosts=("${sanitized_hosts[@]}")
}

validateConfigAndSetVars() {
    validateConfigAndSetVars_upstream
    validateOriginAuth
}

createConfig() {
    local -a original_additional_hosts=("${additional_hosts[@]}")

    prepareOriginAuthHosts
    createConfig_upstream

    # createDNS() only needs the hostname, but restore the original data to keep
    # upstream behavior intact after config generation.
    additional_hosts=("${original_additional_hosts[@]}")
}

main "$@"
