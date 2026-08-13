# Vaultwarden

This Home Assistant app is based on the Home Assistant Community App `hassio-addons/app-vaultwarden` release `v0.27.0` and packages Vaultwarden server `1.36.0`.

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

Vaultwarden stores persistent application data in `/data`.

## Upstream

- Home Assistant app: `hassio-addons/app-vaultwarden`, release `v0.27.0`
- Vaultwarden runtime: `vaultwarden/server:1.36.0`
- License of the imported Home Assistant app integration: MIT
