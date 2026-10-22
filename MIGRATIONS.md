# Migrationen

## 2026-10-22 – Security and compatibility update

### Vaultwarden `0.29.0` → `0.29.1` / Server `1.37.2` → `1.37.4`

- Security release 1.37.4 addresses organization revocation, 2FA, invitations, attachments and other vulnerabilities; see upstream release notes.
- The Debian base moves to `9.5.0`; s6 user-service declarations move to `/etc/s6-overlay/user-bundles.d/user/contents.d` per upstream.
- App data stays under `/data`. On first start with SQLite, a verified one-time snapshot is created at `/data/migration-backups/db.sqlite3.pre-1.37.4` before server startup. Existing `pre-1.37.2` backups are preserved.
- For external PostgreSQL/MariaDB databases, create a database-server backup before upgrading.
- Reverse proxy operators: when `IP_HEADER=X-Forwarded-For`, check `IP_HEADER_TRUSTED_PROXIES`; changed trusted-proxy address selection can affect rate limiting and logging.

**Rollback:** Stop the app, restore the matching pre-upgrade database snapshot when the server has already applied schema changes, then use the previous app image. Do not start an older server against a newer migrated database.

### Cloudflared Origin Auth `7.0.14-rch1` → `7.0.19-rch1`

- Upstream HA app base 7.0.19 includes cloudflared `2026.10.3` and its eMudhra certificate-trust security fix. No separate binary download is required.
- Fixes an incorrect attempt to strip the guarded `main` call while sourcing the upstream prepare script, which could leave an empty Bash `if` block. The import now checks the upstream guard and uses `source` safely.
- Local tunnel credential paths `/data/cert.pem` and `/data/tunnel.json`, app options and protected-host authentication remain unchanged.
- After updating, explicitly test protected Basic/Bearer hosts (401 without credentials, normal access with credentials), unprotected hosts, and tunnel reconnects.

**Rollback:** Previous `7.0.14-rch1` app version, preserving /data. Due to the certificate-trust fix, avoid rolling back cloudflared to a vulnerable binary.

### Gitea MCP `1.7.0-rch1` → `1.8.0-rch1`

- Official upstream MCP binary 1.8.0; unchanged local options, TCP port 8080, endpoint `/mcp` and per-request Bearer token forwarding.
- The app is stateless. Reconnect clients to refresh the advertised MCP tools; validate actual Gitea operations before relying on them.

**Rollback:** Previous `1.7.0-rch1` image, no data migration.

### Unchanged components

- **Gitea** remains at `1.27.2`: current upstream HA image tracks the 28.x release line, requiring a separate server/database migration review and verified backup before enabling an update.
- **Gitea Runner** stays at `5.0.0-rch2`, already on the current 5.0.0 release.

## 2026-10-09

### Gitea Runner `5.0.0-rch1` → `5.0.0-rch2`

- Die persistente Runner-Registrierung unter `/data/.runner` bleibt unverändert.
- Runner-Name, Labels und Gitea-Instanzkonfiguration bleiben unverändert.
- Das App-Image enthält zusätzlich Python 3 für deterministische Knowledge-Base-Tools und deren Tests.
- Docker-Socket, Supervisor-Zugriff und privilegierte Rechte bleiben weiterhin deaktiviert.

Ein Rollback auf `5.0.0-rch1` benötigt keine Datenmigration.

Dieses Dokument beschreibt zustandsbehaftete Updates und die dafür vorgesehenen Rollback-Punkte. Ziel ist, bestehende Home-Assistant-App-Installationen ohne Neuinstallation oder Verlust der App-Konfiguration weiterzuführen.

## 2026-09-02

### Vaultwarden `0.28.1` → `0.29.0` / Server `1.37.1` → `1.37.2`

- Der persistente Datenpfad bleibt `/data`.
- `config.json`, Anhänge und sonstige Vaultwarden-Daten werden nicht verschoben oder neu angelegt.
- Wenn die Standard-SQLite-Datenbank `/data/db.sqlite3` existiert, erstellt die App **vor dem ersten Start von 1.37.2** einmalig eine konsistente SQLite-Sicherung unter `/data/migration-backups/db.sqlite3.pre-1.37.2`.
- Vor und nach der Sicherung wird `PRAGMA quick_check` ausgeführt. Bei einem Fehler wird der Start abgebrochen, bevor Vaultwarden die Datenbank öffnen und interne Schema-Migrationen anwenden kann.
- Vaultwarden selbst führt notwendige Datenbank-Schema-Migrationen beim Serverstart aus.
- Bei PostgreSQL oder MariaDB liegt die Datenbank außerhalb des App-Containers. Die App verändert die Verbindungsparameter nicht und kann dafür keinen lokalen Datenbank-Snapshot erstellen. Vor dem Upgrade sollte deshalb zusätzlich ein Backup des externen DB-Servers vorhanden sein.

**Rollback:** App stoppen, bei SQLite die gesicherte Datei als `/data/db.sqlite3` wiederherstellen und anschließend die vorherige App-Version starten. Ein Downgrade sollte nicht gegen eine bereits von einer neueren Vaultwarden-Version migrierte Datenbank erfolgen.

### Gitea MCP `1.6.0-rch1` → `1.7.0-rch1`

- Die App ist zustandslos; es gibt keine lokale Datenbank oder persistente MCP-Konfiguration zu migrieren.
- Die bestehenden Optionen `gitea_host`, `insecure`, `read_only` und `debug` bleiben unverändert.
- Der Endpunkt bleibt `/mcp` auf Port `8080`.
- Bearer-Token-Passthrough bleibt unverändert; Tokens werden weiterhin pro Request vom Client geliefert und nicht in der App gespeichert.
- Gitea MCP 1.7.0 erweitert bzw. konsolidiert die angebotenen Tools und unterstützt neuere MCP-Protokollstände. MCP-Clients sollten nach dem Upgrade die Verbindung einmal neu aufbauen bzw. die Tool-Liste neu laden.

Ein Rollback auf `1.6.0-rch1` benötigt keine Datenmigration.

### Cloudflared Origin Auth `7.0.13-rch6` → `7.0.14-rch1`

- Die Upstream-App-Basis wechselt von `7.0.13` auf `7.0.14`.
- Die Cloudflared-Binärdatei wechselt von `2026.8.2` auf `2026.8.3`.
- Persistente Tunnel-Daten bleiben unverändert in `/data`, insbesondere `cert.pem` und `tunnel.json`.
- Alle bestehenden Optionen für `external_hostname`, `additional_hosts`, Tunnel-Konfiguration sowie Basic-/Bearer-Schutz bleiben schema-kompatibel.
- Der Overlay-Code übernimmt weiterhin die Upstream-Funktionen und ergänzt ausschließlich die lokale Authentifizierungsschicht. Die 7.0.14-Upstream-Initialisierung unterstützt die aktuelle Home-Assistant-HTTP-Storage-Struktur; dafür ist keine manuelle Anpassung an bestehenden Tunnel-Daten erforderlich.

Ein Rollback auf `7.0.13-rch6` benötigt keine Datenkonvertierung, solange Tunnel-Zertifikat und Credentials nicht manuell ersetzt wurden.

### Gitea

Gitea bleibt vorerst auf `1.27.2`, weil das verwendete Home-Assistant-Runtime-Image von `alexbelgium/hassio-addons` noch auf diesem Stand liegt. Deshalb findet in diesem Update keine Gitea-Datenbankmigration statt.
