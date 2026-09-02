# Migrationen

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
