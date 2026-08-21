#!/command/with-contenv bashio
# shellcheck shell=bash
# ==============================================================================
# Home Assistant App: Cloudflared Origin Auth overlay
# Adds inbound Basic/Bearer authentication to selected additional hosts.
# ==============================================================================

UPSTREAM_PREPARE="/etc/s6-overlay/s6-rc.d/prepare/run-upstream.sh"
AUTH_PROXY_CONFIG="/tmp/nginx-origin-auth.conf"
AUTH_PROXY_PORT_BASE=19080

if [[ ! -r "${UPSTREAM_PREPARE}" ]]; then
    bashio::exit.nok "Upstream Cloudflared prepare script not found: ${UPSTREAM_PREPARE}"
fi

# Load upstream functions without executing the upstream main() call.
# shellcheck disable=SC1090
source <(sed '/^main "\$@"$/d' "${UPSTREAM_PREPARE}")

# Preserve selected upstream functions before overriding them.
eval "$(
    declare -f validateConfigAndSetVars |
        sed '1s/validateConfigAndSetVars/validateConfigAndSetVars_upstream/' |
        sed 's/bashio::log.debug "Checking host ${additional_host}\.\.\."/bashio::log.debug "Checking configured additional host..."/'
)"

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
                *) bashio::exit.nok "Authentication for '${hostname}' requires an http:// or https:// service" ;;
            esac

            if ! [[ ${service} =~ ^https?://[^/]+/?$ ]]; then
                bashio::exit.nok "Authenticated service for '${hostname}' must not contain a URL path"
            fi

            if [[ "${service}" == *$'\n'* || "${service}" == *$'\r'* || \
                "${service}" == *';'* || "${service}" == *'{'* || "${service}" == *'}'* || \
                "${service}" == *'"'* || "${service}" == *"'"* || "${service}" == *'\\'* || \
                "${service}" == *'$'* || "${service}" == *$'\t'* || "${service}" == *' '* ]]; then
                bashio::exit.nok "Service URL for authenticated host '${hostname}' contains unsupported characters"
            fi
        fi

        if bashio::var.has_value "${bearer_token}" && \
            ! [[ ${bearer_token} =~ ^[A-Za-z0-9._~+/=-]+$ ]]; then
            bashio::exit.nok "bearer_token for '${hostname}' contains unsupported characters"
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
    local auth_type="$3"
    local expected_authorization="$4"
    local map_name="auth_ok_${port}"
    local challenge

    if [[ "${auth_type}" == "basic" ]]; then
        challenge='Basic realm="Cloudflared Origin Auth"'
    else
        challenge='Bearer realm="Cloudflared Origin Auth"'
    fi

    cat >>"${AUTH_PROXY_CONFIG}" <<NGINX

    map \$http_authorization \$${map_name} {
        default 0;
        "${expected_authorization}" 1;
    }

    map \$${map_name} \$auth_challenge_${port} {
        0 '${challenge}';
        1 "";
    }

    server {
        listen 127.0.0.1:${port};
        add_header WWW-Authenticate \$auth_challenge_${port} always;

        location / {
            if (\$${map_name} = 0) {
                return 401;
            }

            set \$origin_service "${service}";
            proxy_pass \$origin_service\$request_uri;
            proxy_http_version 1.1;
            proxy_buffering off;

            proxy_set_header Host \$http_host;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection \$http_connection;

            # Credentials authenticate the client at this proxy and are not
            # forwarded to the protected origin service.
            proxy_set_header Authorization "";

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
    local expected_authorization
    local auth_type
    local proxy_port
    local proxy_count=0

    rm -f "${AUTH_PROXY_CONFIG}"

    for additional_host in "${additional_hosts[@]}"; do
        hostname=$(bashio::jq "${additional_host}" '.hostname')
        service=$(bashio::jq "${additional_host}" '.service')
        basic_auth_username=$(bashio::jq "${additional_host}" '.basic_auth_username // ""')
        basic_auth_password=$(bashio::jq "${additional_host}" '.basic_auth_password // ""')
        bearer_token=$(bashio::jq "${additional_host}" '.bearer_token // ""')

        sanitized_host=$(bashio::jq "${additional_host}" \
            'del(.basic_auth_username, .basic_auth_password, .bearer_token)')

        expected_authorization=""
        auth_type=""
        if bashio::var.has_value "${bearer_token}"; then
            auth_type="bearer"
            expected_authorization="Bearer ${bearer_token}"
        elif bashio::var.has_value "${basic_auth_username}"; then
            auth_type="basic"
            expected_authorization="Basic $(printf '%s:%s' "${basic_auth_username}" "${basic_auth_password}" | base64 | tr -d '\n')"
        fi

        if bashio::var.has_value "${expected_authorization}"; then
            if [[ ${proxy_count} -eq 0 ]]; then
                writeAuthProxyHeader
            fi

            proxy_port=$((AUTH_PROXY_PORT_BASE + proxy_count))
            appendAuthProxyServer "${proxy_port}" "${service}" "${auth_type}" "${expected_authorization}"

            sanitized_host=$(bashio::jq "${sanitized_host}" \
                ".service = \"http://127.0.0.1:${proxy_port}\"")

            bashio::log.info "Enabled ${auth_type} access protection for ${hostname} via 127.0.0.1:${proxy_port}"
            proxy_count=$((proxy_count + 1))
        fi

        sanitized_hosts+=("${sanitized_host}")
    done

    if [[ ${proxy_count} -gt 0 ]]; then
        printf '%s\n' '}' >>"${AUTH_PROXY_CONFIG}"
        chmod 600 "${AUTH_PROXY_CONFIG}"
        nginx -t -c "${AUTH_PROXY_CONFIG}" >/dev/null || \
            bashio::exit.nok "Generated authentication proxy configuration is invalid"
        bashio::log.info "Prepared access protection for ${proxy_count} additional host(s)"
    else
        bashio::log.info "No Basic or Bearer protection configured for additional hosts"
    fi

    additional_hosts=("${sanitized_hosts[@]}")
}

validateConfigAndSetVars() {
    validateConfigAndSetVars_upstream
    validateOriginAuth
}

createConfig() {
    local -a original_additional_hosts=("${additional_hosts[@]}")
    local default_config="/tmp/config.json"

    prepareOriginAuthHosts
    createConfig_upstream

    if [[ -f "${AUTH_PROXY_CONFIG}" ]]; then
        local protected_ingress_count
        protected_ingress_count=$(jq '[.ingress[] | select(.service | startswith("http://127.0.0.1:190"))] | length' "${default_config}")
        if [[ "${protected_ingress_count}" == "0" ]]; then
            bashio::exit.nok "Authentication proxy was prepared but no protected ingress route was written to Cloudflared config"
        fi
        bashio::log.info "Verified ${protected_ingress_count} protected ingress route(s) in Cloudflared config"
    fi

    additional_hosts=("${original_additional_hosts[@]}")
}

main "$@"
