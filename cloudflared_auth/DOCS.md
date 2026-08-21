# Cloudflared Origin Auth

This app is based on `homeassistant-apps/app-cloudflared` and adds optional per-origin `Authorization` headers for entries in `additional_hosts`.

The upstream Cloudflared ingress configuration does not support arbitrary static HTTP request headers in `originRequest`. For authenticated origins this app therefore routes Cloudflared to a loopback-only Nginx proxy inside the same container. That proxy replaces any incoming `Authorization` header and forwards the request to the configured origin.

## Bearer authentication

```yaml
external_hostname: ha.example.com
additional_hosts:
  - hostname: api.example.com
    service: http://192.168.1.20:8080
    bearer_token: "my-secret-token"
```

The origin receives:

```text
Authorization: Bearer my-secret-token
```

## Basic authentication

```yaml
external_hostname: ha.example.com
additional_hosts:
  - hostname: service.example.com
    service: https://192.168.1.30:8443
    basic_auth_username: "alice"
    basic_auth_password: "secret"
```

The origin receives a standard HTTP Basic Authorization header generated from `alice:secret`.

## Compatibility

Hosts without authentication options are passed through unchanged and use the same Cloudflared ingress path as upstream.

Authenticated hosts currently require an `http://` or `https://` origin URL consisting only of scheme, host and optional port. URL paths in `service` are rejected for authenticated hosts.

`bearer_token` and Basic authentication are mutually exclusive for a host. For Basic authentication both `basic_auth_username` and `basic_auth_password` are required.

## Security notes

- The authentication proxy listens only on `127.0.0.1` inside the app container.
- Client-supplied `Authorization` headers are always replaced for authenticated hosts.
- Authentication fields are removed before the generated Cloudflared configuration is written.
- The upstream debug statement that prints complete `additional_hosts` entries is redacted so configured credentials are not emitted to the app log.
- Password and token fields use the Home Assistant `password` schema type.

## Upstream

Initial overlay base: `homeassistant-apps/app-cloudflared` 7.0.13 / Cloudflared 2026.8.2.
