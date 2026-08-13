# Vaultwarden

This Home Assistant app is maintained in `riederch/ha-apps` and packages Vaultwarden server `1.37.1`.

The Home Assistant integration is derived from `hassio-addons/app-vaultwarden` and is built as a multi-architecture image for `amd64` and `aarch64` in this repository.

## Installation

1. Install **Vaultwarden** from this Home Assistant app repository.
2. Start the app and inspect its log.
3. On the first start, copy the temporary admin token shown in the log.
4. Open the Web UI.
5. Open `/admin` and use the temporary token.
6. Save or replace the admin token in the Vaultwarden admin settings.

## Configuration

```yaml
log_level: info
ssl: false
certfile: fullchain.pem
keyfile: privkey.pem
request_size_limit: 10485760
```

The Web UI is exposed on TCP port `7277`. If SSL is enabled, the certificate and key must exist below `/ssl`.

## Data

Vaultwarden stores persistent application data in `/data`. Updating the app image does not replace this persistent data directory.

## Runtime

- Home Assistant app version: `0.28.0`
- Vaultwarden server: `1.37.1`
- Image: `ghcr.io/riederch/ha-apps-vaultwarden`
- Architectures: `amd64`, `aarch64`

## Upstream

- Home Assistant integration base: `hassio-addons/app-vaultwarden`
- Vaultwarden runtime: `vaultwarden/server:1.37.1`
- License of the imported Home Assistant app integration: MIT
