# Gitea 1.27.2 → 28.3.0: Migrations- und Abnahmeplan

Stand: 2026-11-11 · Status: **Vorbereitung, kein freigegebenes Deployment**

## Anlass und Sicherheitspriorität

Das Repository `riederch/ha-apps` pinnt die Home-Assistant-Gitea-App derzeit auf `1.27.2`. Das betreuende Upstream-App-Repository (`alexbelgium/hassio-addons`) nennt bereits `28.3.0`. **Gitea 28** ist der direkte Nachfolger der Reihe `1.27`: Die historische Versionsnummer `1.28` wurde auf `28` verkürzt. Trotzdem sind Breaking Changes und irreversible Datenbankmigrationen möglich.

Gitea 28.0 und 28.3 haben sicherheitsrelevante Korrekturen, unter anderem bei Actions-Freigaben, SSH, Tokens und Berechtigungen. Zeitnahes Upgrade vorbereiten, aber **nicht allein durch Änderung des Feldes `gitea/config.yaml:version` produktiv auslösen**.

## Ist-Zustand im Repository

- `gitea/config.yaml`: HA-App `1.27.2`, Image `ghcr.io/alexbelgium/gitea-{arch}`, Ports 3000 (Web) und Host 2222 (SSH), Persistenz-Mapping `addon_config`, `share`, `ssl`.
- Default-Option `DOMAIN: homeassistant.local`, `ROOT_URL: ""`. **Die tatsächlich laufende `app.ini` und der echte externe Host sind unbekannt und müssen vor der Änderung gelesen werden.**
- Verknüpfte Dienste: `gitea_mcp` (HTTP/API, Token), `gitea_runner` (Actions mit `ha-runner:host`). Die separat vorbereiteten Runtime-PRs werden nicht durch diesen Plan gemergt.

## Vorbereitende Prüfungen (Pflicht vor jedem Runtime-PR)

- [ ] In laufender Gitea-Instanz **tatsächlich aktive** Version, Datenbanktyp/Version, Gitea-Datenpfade und aktive Konfiguration ermitteln (keine Vermutungen aus App-Defaults).
- [ ] Alle betroffenen `app.ini`-Optionen auf veraltete Optionen und Warnungen der Adminoberfläche prüfen. Insbesondere `[server] ROOT_URL` explizit auf die korrekte URL setzen: **`DOMAIN` wird in Gitea 28 ignoriert**. Externes HTTPS, Host, Web-URL, SSH-Domain und Clone-URLs testen.
- [ ] `[migrations]`- und `[security]`-Egress-Konfiguration überprüfen. Ab 28.x gelten neue Egress-Modi, Host-Listen und Port-Regeln. Bestehende `ALLOWED_DOMAINS`, `BLOCKED_DOMAINS`, `ALLOW_LOCALNETWORKS` / `ALLOWED_HOST_LIST` / `BLOCKED_HOST_LIST` ausdrücklich vergleichen; keine ungewollte Öffnung oder Blockade interner Dienste zulassen.
- [ ] Aufbewahrung von Actions-Historie **entscheiden**: Gitea 28 löscht abgeschlossene Actions-Läufe standardmäßig nach **400 Tagen**. Wenn revisions-/auditrelevante Historie unverändert benötigt wird, vor Upgrade `[actions] RUN_RETENTION_DAYS = 0` setzen; ansonsten Aufbewahrungsfrist bewusst beschließen und dokumentieren.
- [ ] Prüfen, ob Benutzer-Selbstregistrierung gewünscht ist: 28.x deaktiviert sie standardmäßig; falls benötigt, explizit `[service] DISABLE_REGISTRATION = false` setzen.
- [ ] Git-Version im tatsächlich verwendeten Image verifizieren (Gitea 28 setzt Git ≥ 2.25 voraus); Abgleich von `ghcr.io/alexbelgium/gitea-{arch}` für AMD64/AArch64 und Version `28.3.0`.
- [ ] Eventuelle individuelle Templates, Webhooks, Mirroring, CI-Secrets und Proxy-Regeln dokumentieren. Live-Benachrichtigungen benötigen künftig den WebSocket-Pfad `/-/ws`; Weiterleitung von Upgrade-/Connection-Headern am Reverse Proxy prüfen.

## Zwischenmaßnahmen bis zum Gitea-28-Upgrade

Die Security-Fixes von 28.0.0 schließen unter anderem
`CVE-2026-104632` und `CVE-2026-104626` in der Freigabelogik
von Fork-Pull-Request-Actions. Der Host-Mode-Runner in diesem
Repository ist **nur für vertrauenswürdige Workflows** gedacht;
der bereits implementierte `clean-env.sh`-Filter ersetzt keine
Freigabe-/Isolation für fremden Quellcode.

- [ ] Bis zum Upgrade **keine** ungeprüften Fork-PR-Actions oder fremden
  Repository-Workflows auf `ha-runner:host` ausführen lassen. Nur
  kontrollierte Repositories, Branches und Workflows zuweisen und
  Runner-Zugriffe beziehungsweise Registrierungsrechte prüfen.
- [ ] Vor Upgrade laufende und ausstehende Actions-Jobs mit unbekannter
  Herkunft kontrollieren; ein Host-Mode-Job kann die lokale
  `/data/.runner`-Registrierung und ausdrücklich bereitgestellte
  CI-Secrets lesen. Keine fremden Workflow-Dateien als Test verwenden.
- [ ] Nach Upgrade die geänderte Evaluierung von Job-Level-`if`
  vor Matrix-Expansion prüfen. Zugriffe auf `matrix` gehören künftig
  in Step-Level-`if` bzw. die `strategy.matrix`-Definition.
- [ ] Über die neue Auditfunktion entscheiden: optional
  `[audit] RECORD_OUTPUT = database`. Die Ereignisse werden
  standardmäßig nach **30 Tagen** gelöscht; eine länger benötigte
  revisions-/ISO-relevante Aufbewahrung mittels
  `[audit] RETENTION_DAYS` explizit dokumentieren. Das ist getrennt
  von den **400 Tagen** für abgeschlossene Actions-Runs.

Quellen: [Offizielle Gitea 28.0.0 Release-Notes](https://blog.gitea.com/release-of-28.0.0/)
und [Gitea 28.3.0](https://blog.gitea.com/release-of-28.3.0/).

## Backup und Wiederherstellung (Gate 1)

1. Wartungsfenster definieren; aktive Pushes, Webhooks, Mirrors und Actions-Jobs pausieren.
2. Gitea ordentlich stoppen.
3. **Konsistentes vollständiges Backup** von Datenbank, App-Konfiguration, Git-Repositories, Anhängen/LFS, Customizations und ggf. externem Storage anfertigen. HA-App-Backup allein reicht bei externer Datenbank oder Storage nicht.
4. Prüfsummen, Versionen und Speicherorte dokumentieren. Zugangsdaten und Sicherungen nicht im Git-Repository ablegen.
5. Restore auf eine **isolierte Testinstanz** erfolgreich durchführen. Testumgebung darf weder produktive Webhooks, Runner, E-Mails noch Push-Mirrors auslösen.

**Kein Runtime-Upgrade ohne nachgewiesenen Restore.** Eine bereits durch 28.x migrierte Datenbank darf nicht ohne Restore mit der alten 1.27.x-Version gestartet werden.

## Vorabtests auf wiederhergestellter Testinstanz (Gate 2)

| Bereich | Abnahmetest |
|---|---|
| Anmeldung/Rechte | Admin- und Standardbenutzer, Organisationen, Private Repositories, 2FA/Token-Scopes |
| Git | Clone, Fetch, Push über HTTPS und SSH; Branchschutz, Hooks und Deploy Keys |
| Web UI | Externe URL, Login, Issues/PR, Benachrichtigungen einschließlich `/-/ws` |
| Daten/Integrität | Repository-Anzahl, Datenbank-Migration, Anhänge, LFS, Packages und ggf. Spiegel |
| API/MCP | Gitea-Token, `tools/list`, strukturierte Dateiantworten, `read_only`, kontrollierter Schreibtest |
| Actions | Runner-Registrierung bleibt nutzbar, `ha-runner:host`, `builtin:checkout`, Joblogs/Artefakte, Freigabe untrusted PRs |
| Netz | Egress-Migration/Mirror/Webhooks gegen zulässige und bewusst unzulässige Hosts |
| Historie | Aufbewahrungseinstellung und Archiv-/Audit-Anforderungen verifiziert |

Tests mit echten externen Integrationen nur in isolierter oder kontrolliert freigegebener Umgebung. Ist eine Abnahme offen, bleibt der Runtime-PR Draft.

## Durchführung (Gate 3)

1. Änderungsprotokoll, Release-Notes und Abnahmeergebnisse zum geplanten Ziel-Tag aktualisieren; Image für beide Architekturen im Test prüfen.
2. Eigenen Runtime-PR **mit ausschließlich nötigen Gitea-Änderungen** erstellen; separierte PRs für MCP und Runner nicht ungeprüft mitziehen.
3. Vor produktivem Stop erneut konsistentes Backup erstellen und Restore-Punkt markieren.
4. Gitea-App auf Zielversion heben; Datenbankmigration vollständig abwarten; Logs auf Fehler prüfen.
5. Abnahmetests wiederholen, insbesondere Push, SSH, Login, MCP, Actions und neue WebSocket-Route.
6. Versions-/Konfigurationsstand und Abnahme im Migrationsprotokoll dokumentieren.

## Rollback

Bei fehlgeschlagener Migration: neue Instanz stoppen; das **vor** dem Upgrade angefertigte Datenbank-/Data-/Konfigurations-Backup geschlossen wiederherstellen; auf 1.27.2 bzw. freigegebenes altes Image zurückwechseln. Externen Storage und Credentials konsistent halten. Bei Datenbank-Schemaänderungen ist ein bloßer Wechsel des Image-Tags **kein** Rollback.

## Quellen

- Gitea 28.0.0 Breaking Changes: https://blog.gitea.com/release-of-28.0.0/
- Gitea 28.3.0 Sicherheitskorrekturen: https://blog.gitea.com/release-of-28.3.0/
- Offizieller Upgrade-/Backup-Leitfaden: https://docs.gitea.com/installation/upgrade-from-gitea/
- HA-Upstream-App: https://github.com/alexbelgium/hassio-addons/tree/master/gitea
- Gitea Runner 5.x: https://docs.gitea.com/runner/

**Absichtlich noch keine Entscheidung getroffen:** reale `ROOT_URL`, Egress-Ausnahmelisten, Actions-Aufbewahrungsfrist und produktiver Migrationszeitpunkt müssen an der laufenden Installation geprüft beziehungsweise entschieden werden.
