# Cloudflared Origin Auth

This app is based on `homeassistant-apps/app-cloudflared` and adds optional inbound Basic or Bearer access protection for entries in `additional_hosts`.

Protected hosts are routed by Cloudflared to a loopback-only Nginx proxy inside the app container. The proxy validates the client's `Authorization` header before forwarding the request to the configured origin service.

## Bearer authentication

```yaml
external_hostname: ha.example.com
additional_hosts:
  - hostname: api.example.com
    service: http://192.168.1.20:8080
    bearer_token: "my-secret-token"
```

A client must send:

```text
Authorization: Bearer my-secret-token
```

Requests without the exact token are rejected with HTTP 401.

## Basic authentication

```yaml
external_hostname: ha.example.com
additional_hosts:
  - hostname: service.example.com
    service: https://192.168.1.30:8443
    basic_auth_username: "alice"
    basic_auth_password: "secret"
```

Browsers receive an HTTP Basic authentication challenge and prompt for the configured username and password. Requests without valid credentials are rejected with HTTP 401.

## Compatibility

Hosts without authentication options are passed through unchanged and use the same Cloudflared ingress path as upstream.

Protected hosts currently require an `http://` or `https://` origin URL consisting only of scheme, host and optional port. URL paths in `service` are rejected for protected hosts.

`bearer_token` and Basic authentication are mutually exclusive for a host. For Basic authentication both `basic_auth_username` and `basic_auth_password` are required.

As in the upstream app, setting `tunnel_token` selects Cloudflare remotely managed tunnel mode and causes the local ingress options to be ignored. Consequently, `additional_hosts` and the access-protection fields in this app are only effective for locally managed tunnel configuration.

## Security notes

- The authentication proxy listens only on `127.0.0.1` inside the app container.
- Client credentials are checked at the local proxy before access to the origin is allowed.
- The client `Authorization` header is removed before forwarding to the protected origin service.
- Authentication fields are removed before the generated Cloudflared configuration is written.
- The upstream debug statement that prints complete `additional_hosts` entries is redacted so configured credentials are not emitted to the app log.
- Password and token fields use the Home Assistant `password` schema type.

## Runtime verification

On startup the app verifies that:

1. the local authentication proxy configuration is valid,
2. protected additional hosts were rewritten to loopback proxy routes in `/tmp/config.json`, and
3. each configured loopback authentication proxy port is actually listening before Cloudflared starts.

The log therefore contains explicit lines such as:

```text
Enabled basic access protection for service.example.com via 127.0.0.1:19080
Verified 1 protected ingress route(s) in Cloudflared config
Verified authentication proxy listener on 127.0.0.1:19080
```

If any of these stages fails, the app stops instead of starting with an unprotected route.

## Upstream

Initial overlay base: `homeassistant-apps/app-cloudflared` 7.0.13.
