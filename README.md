# Home Assistant Apps

Eigenes Home-Assistant-App-Repository von Christoph Rieder.

## Enthaltene Apps

| App | Zweck |
|---|---|
| **Gitea** | Selbst gehosteter Git-Server direkt unter Home Assistant OS |
| **Gitea MCP** | Schlanker Wrapper um den offiziellen Gitea-MCP-Server mit optionalem Read-only-Modus |
| **Gitea Runner** | Schlanker Host-Mode-Wrapper um den offiziellen Gitea Runner für vertrauenswürdige Actions-Jobs |
| **Vaultwarden** | Selbst gehosteter, Bitwarden-kompatibler Passwortmanager |
| **Cloudflared Origin Auth** | Cloudflare Tunnel mit optionalem Basic-/Bearer-Zugriffsschutz für zusätzliche Hosts |

## Repository in Home Assistant hinzufügen

1. **Einstellungen → Apps → App-Store** öffnen.
2. Rechts oben **⋮ → Repositories** wählen.
3. Folgende URL hinzufügen:

   ```text
   https://github.com/riederch/ha-apps
   ```

4. Den App-Store aktualisieren.
5. Danach die gewünschten Apps aus diesem Repository installieren.

## Sicherheit

Für Gitea MCP wird ein Gitea-Zugriffstoken nicht dauerhaft in der App gespeichert. Im HTTP-Modus sendet der jeweilige MCP-Client den Token als Bearer-Token. Für reine Wissensabfragen kann die MCP-App zusätzlich mit `read_only: true` gestartet werden.

Der Gitea Runner läuft standardmäßig im Host-Mode innerhalb seines eigenen Home-Assistant-App-Containers und erhält weder Docker-Socket noch privilegierte Host-Rechte. Er ist für vertrauenswürdige, leichte Workflows mit dem dedizierten Label `ha-runner` gedacht.

Vaultwarden generiert beim ersten Start einen temporären Admin-Token und zeigt ihn im App-Log an. Dieser sollte unmittelbar im Vaultwarden-Adminbereich gespeichert oder ersetzt werden.

Cloudflared Origin Auth verwendet für geschützte Zusatzhosts einen ausschließlich auf `127.0.0.1` gebundenen Nginx-Proxy im App-Container. Dieser prüft eingehende Basic- oder Bearer-Zugangsdaten, bevor der Request zum internen Origin-Dienst weitergeleitet wird. Die Zugangsdaten werden nicht an den Origin weitergereicht und nicht in die erzeugte Cloudflared-Ingress-Konfiguration geschrieben.

## Migrationen

Bestehende Installationen werden bei Versionswechseln nach Möglichkeit ohne manuelle Neukonfiguration übernommen. Versionsspezifische Hinweise, Rollback-Punkte und unveränderte Datenpfade sind in [`MIGRATIONS.md`](MIGRATIONS.md) dokumentiert.

## Aktuelle Runtime-Stände

- Gitea: `1.27.2`
- Gitea MCP: `1.8.0`
- Gitea Runner: `5.0.0` (App `5.0.0-rch3`, bereinigte Job-Prozessumgebung)
- Vaultwarden: `1.37.4`
- Cloudflared: `2026.10.3`

## Herkunft

Die Gitea-App verwendet die etablierte Gitea-App aus [`alexbelgium/hassio-addons`](https://github.com/alexbelgium/hassio-addons/tree/master/gitea) als Runtime-Image.

Gitea MCP verwendet den offiziellen Gitea-MCP-Server `1.8.0` aus `docker.gitea.com/gitea-mcp-server`; der lokale Code ist nur der Home-Assistant-Startwrapper.

Gitea Runner verwendet den offiziellen Runner `5.0.0` aus `docker.io/gitea/runner`; der lokale Code ergänzt nur Home-Assistant-Konfiguration, persistente Registrierung und einen bewusst unprivilegierten Host-Mode.

Die Vaultwarden-App basiert auf [`hassio-addons/app-vaultwarden`](https://github.com/hassio-addons/app-vaultwarden) und verwendet Vaultwarden `1.37.4`.

Cloudflared Origin Auth ist ein schlanker Overlay-Fork von [`homeassistant-apps/app-cloudflared`](https://github.com/homeassistant-apps/app-cloudflared), aktuell auf App-Basis `7.0.19` mit Cloudflared `2026.10.3`. Details zu den übernommenen Komponenten stehen in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Local EMS (HACS-Integration, Beta)

Zusätzlich zu den oben beschriebenen Apps enthält dieses Repository die **Home-Assistant-Integration Local EMS** unter `custom_components/local_ems/`. Der App-Store installiert weiterhin nur die Apps, die Integration wird **separat über HACS** installiert.

**Beta / Draft:** Der Rechenkern, das HA-Manifest und die technischen HACS-Prüfungen werden automatisiert validiert; optionale GitHub-Katalog-Metadaten sind noch nicht gesetzt, und der HA-Laufzeittest steht aus. **Erst nach Abschluss der Tests produktiv verwenden.** Auf dem Entwicklungsbranch `feature/local-ems-peak-monitor` befindet sich die erste lesende Beta für die Überwachung der 15-Minuten-Bezugsleistung.

### Geplante Einrichtung

1. HACS → benutzerdefinierte Repositories → `https://github.com/riederch/ha-apps` als Typ **Integration** hinzufügen.
2. Die Integration **Local EMS** installieren und Home Assistant neu starten.
3. Einstellungen → Geräte & Dienste → Integration hinzufügen → **Local EMS**.
4. Als Bezugssensor `sensor.kng_p_in` auswählen; 10 kW Grenzwert und 9 kW Warnschwelle sind die Startwerte.
5. Die erzeugten Sensoren und Warnentitäten in Dashboard/Automationen nutzen. Keine YAML-Konfiguration erforderlich.

Dokumentierte Architektur und Einschränkungen: [`docs/local-ems.md`](docs/local-ems.md).

**Wichtig:** Diese erste Fassung ist kein zugelassener Netzleistungsbegrenzer, sondern eine rein lesende Prognose. Bei unvollständigen Quelldaten werden Berechnungen ausdrücklich als ungültig markiert.

## Lizenzen

**Eigener Quellcode** dieses Repositories, insbesondere `custom_components/local_ems/`, steht unter der **GNU GPL-3.0-or-later**. Der vollständige Lizenztext liegt in [`LICENSE`](LICENSE). Die Abgrenzung gegenüber Fremdcode erläutert [`LICENSE_SCOPE.md`](LICENSE_SCOPE.md).

**Fremdkomponenten, übernommene MIT-lizenzierte App-Bestandteile und externe Runtime-Images** behalten ihre jeweiligen Lizenzbedingungen. Copyright-Hinweise und Herkunft sind unter [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) dokumentiert. Die GPL für unsere eigenen Teile ist keine Umlizenzierung fremder Werke.
