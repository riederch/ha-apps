# Vaultwarden

This Home Assistant app is maintained in `riederch/ha-apps` and packages Vaultwarden server `1.37.2`.

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

## Data and migration

Vaultwarden stores persistent application data in `/data`. Updating the app image does not replace this persistent data directory.

When upgrading this app from Vaultwarden 1.37.1 to 1.37.2 and `/data/db.sqlite3` exists, the startup wrapper creates a one-time backup at:

```text
/data/migration-backups/db.sqlite3.pre-1.37.2
```

The source database and the backup are checked with SQLite `PRAGMA quick_check`. Vaultwarden then performs its own required database schema migrations when the new server starts. For external PostgreSQL or MariaDB databases, create a database-server backup before upgrading because those databases are not stored inside the app container.

For rollback details see [`../MIGRATIONS.md`](../MIGRATIONS.md).

## Runtime

- Home Assistant app version: `0.29.0`
- Vaultwarden server: `1.37.2`
- Image: `ghcr.io/riederch/ha-apps-vaultwarden`
- Architectures: `amd64`, `aarch64`

## Upstream

- Home Assistant integration base: `hassio-addons/app-vaultwarden`
- Vaultwarden runtime: `vaultwarden/server:1.37.2`
- License of the imported Home Assistant app integration: MIT
