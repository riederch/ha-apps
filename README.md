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
- Gitea MCP: `1.11.0`
- Gitea Runner: `5.0.0` (App `5.0.0-rch3`, bereinigte Job-Prozessumgebung)
- Vaultwarden: `1.37.4`
- Cloudflared: `2026.10.3`

## Herkunft

Die Gitea-App verwendet die etablierte Gitea-App aus [`alexbelgium/hassio-addons`](https://github.com/alexbelgium/hassio-addons/tree/master/gitea) als Runtime-Image.

Gitea MCP verwendet den offiziellen Gitea-MCP-Server `1.11.0` aus `docker.gitea.com/gitea-mcp-server`; lokaler Wrapper und HTTP-Bridge ergänzen Home-Assistant-Konfiguration, strukturierte Dateiausgaben und Binär-Uploads.

Gitea Runner verwendet den offiziellen Runner `5.0.0` aus `docker.io/gitea/runner`; der lokale Code ergänzt nur Home-Assistant-Konfiguration, persistente Registrierung und einen bewusst unprivilegierten Host-Mode.

Die Vaultwarden-App basiert auf [`hassio-addons/app-vaultwarden`](https://github.com/hassio-addons/app-vaultwarden) und verwendet Vaultwarden `1.37.4`.

Cloudflared Origin Auth ist ein schlanker Overlay-Fork von [`homeassistant-apps/app-cloudflared`](https://github.com/homeassistant-apps/app-cloudflared), aktuell auf App-Basis `7.0.19` mit Cloudflared `2026.10.3`. Details zu den übernommenen Komponenten stehen in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Local EMS (HACS-Integration, Beta)

Zusätzlich zu den oben beschriebenen Apps enthält dieses Repository die **Home-Assistant-Integration Local EMS** unter `custom_components/local_ems/`. Der App-Store installiert weiterhin nur die Apps, die Integration wird **separat über HACS** installiert.

**Beta:** Der Rechenkern, das HA-Manifest und die technischen HACS-Prüfungen werden automatisiert validiert; optionale GitHub-Katalog-Metadaten sind noch nicht gesetzt. Ein tatsächlicher HA-Laufzeittest steht noch aus. **Vor produktiven Schaltfunktionen ist ein Funktionstest erforderlich.** Die bisherige Version 0.1 umfasst die lesende 15-Minuten-Spitzenüberwachung.

### Geplante Einrichtung

1. HACS → benutzerdefinierte Repositories → `https://github.com/riederch/ha-apps` als Typ **Integration** hinzufügen.
2. Die Integration **Local EMS** installieren und Home Assistant neu starten.
3. Einstellungen → Geräte & Dienste → Integration hinzufügen → **Local EMS**.
4. Als Bezugssensor `sensor.kng_p_in` auswählen; 10 kW Grenzwert und 9 kW Warnschwelle sind die Startwerte.
5. Die erzeugten Sensoren und Warnentitäten in Dashboard/Automationen nutzen. Keine YAML-Konfiguration erforderlich.

Dokumentierte Architektur und Einschränkungen: [`docs/local-ems.md`](docs/local-ems.md).

**Wichtig:** Diese erste Fassung ist kein zugelassener Netzleistungsbegrenzer, sondern eine rein lesende Prognose. Bei unvollständigen Quelldaten werden Berechnungen ausdrücklich als ungültig markiert.

### Local EMS 0.1.0b2 – Anzeige als Integration

Die erste Beta `0.1.0b1` wurde im Manifest versehentlich als
`integration_type: helper` eingestuft. Home Assistant zeigt solche
Config-Entries im Bereich **Helfer** statt als eigenständige Integration.
Version `0.1.0b2` verwendet `integration_type: hub`: Das Local EMS
erscheint nach HACS-Update und Neustart bei **Einstellungen →
Geräte & Dienste → Integrationen**. Eine bestehende Konfiguration und
die Entitäts-IDs werden dabei nicht geändert; vor einer etwaigen
Neuinstallation bitte zuerst Logeinträge zu `local_ems` prüfen.

## Lizenzen

**Eigener Quellcode** dieses Repositories, insbesondere `custom_components/local_ems/`, steht unter der **GNU GPL-3.0-or-later**. Der vollständige Lizenztext liegt in [`LICENSE`](LICENSE). Die Abgrenzung gegenüber Fremdcode erläutert [`LICENSE_SCOPE.md`](LICENSE_SCOPE.md).

**Fremdkomponenten, übernommene MIT-lizenzierte App-Bestandteile und externe Runtime-Images** behalten ihre jeweiligen Lizenzbedingungen. Copyright-Hinweise und Herkunft sind unter [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) dokumentiert. Die GPL für unsere eigenen Teile ist keine Umlizenzierung fremder Werke.

## Local EMS 0.2.0b1 – Geräteverwaltung

Im bestehenden Local-EMS-Integrationseintrag unter **Konfigurieren** können
mehrere **Schaltverbraucher** (Heizstäbe, Heizlüfter, sonstige Geräte) und
**Wallboxen** hinterlegt, geändert und entfernt werden. Ebenfalls
konfigurierbar sind die Datenquellen für Netzleistung, PV, Hausverbrauch,
Batterieleistung und SoC.

- Schaltverbraucher: `switch.*`, Nennleistung, optionaler Leistungssensor,
  Priorität, Mindestlauf-/Ausschaltzeit und Überschussreserve.
- Wallboxen: Ladeleistungssensor, optionale Ladefreigabe,
  optionale Ladestromzahl, Fahrzeugstatus, Phasen, Maximalstrom, Priorität.
- Übersicht: zusätzliche native Zähler- und Statussensoren im EMS-Gerät.
- Speicherung: ausschließlich HA-Config-Entry-Optionen, keine YAML-Datei.

**Wichtig:** Alle neuen Aktor-Entitäten werden in dieser Version nur
hinterlegt und gelesen; **kein automatisches Schalten und keine
Ladestromregelung**. Die spätere Überschussautomatik wird nach
Validierung der Messwerte und Schaltgrenzen entwickelt.

Details: [Geräteverwaltung](docs/local-ems-devices.md).

### Local EMS 0.2.0b2 – Einheitsspezifische Auswahl

Die Konfigurationsdialoge filtern HA-Entitäten jetzt nach Einheit: Wh/kWh
für importierte Energie, W/kW für Leistung, % für Batterie-SoC und A für
den Wallbox-Ladestrom. Es sind keine manuellen Änderungen an bestehenden
Gerätezuordnungen notwendig. Details stehen in
[`docs/local-ems-devices.md`](docs/local-ems-devices.md).

## Local EMS 0.3.0b1 – herstellerunabhängige Netzfreigabe

Neu: Über **Konfigurieren → Netz-/EPS-Sicherheit und Betriebsmodus**
lassen sich Statuswerte eines beliebigen Wechselrichters, optional ein
physischer Netzmeldekontakt, der Smartmeter-Heartbeat und erlaubte
Wechselrichter-Betriebsmodi zuordnen. Der Zustand wird als HA-Entitäten
veröffentlicht. Die Eingaben verwenden **keine** festen Sofar-Register oder
andere herstellerspezifische Werte.

**Sicherheit:** Die EMS-Hauptfreigabe steht nach einem Upgrade standardmäßig
auf AUS. Diese Version erzeugt eine *Lastabwurfanforderung*, führt aber
**keine physischen Schaltbefehle** aus. Damit ist die EPS-Abschaltung noch
nicht technisch umgesetzt. Details:
[`docs/local-ems-devices.md`](docs/local-ems-devices.md).

## Local EMS 0.4.0b1 – eigene Energieflusskarte

Local EMS liefert nun **eine eigene, integrierte Dashboard-Karte** mit
PV, Netz, Batterie und Hausverbrauch. Die bisherige `power-flow-card-plus`
ist dafür nicht mehr erforderlich. Die Geräte-/Sensor-Entitäten werden
einmalig im EMS hinterlegt; eine Dashboard-Karte benötigt nur:

```yaml
type: custom:local-ems-flow-card
```

Die Karte wird über die Integration ausgeliefert. In Storage-Dashboards
versucht das EMS die JS-Ressource automatisch zu registrieren; bei
YAML-Ressourcenverwaltung ist eine einmalige Ressourceneintragung nötig.

[Einrichtung, Sensorzuordnung und Grenzen](docs/local-ems-flow.md).

## Local EMS 0.4.0b2 – Power-Flow-Stil und Energy-Dashboard-Datenquellen

Die integrierte Karte `custom:local-ems-flow-card` zeigt nun **runde, farbig
umrandete Energiefluss-Knoten und animierte Punkte** in der vertrauten
Anordnung PV oben, Netz links, Haus rechts, Batterie unten. Kein Sankey.

Die Leistungsquellen werden standardmäßig **lesend aus den bestehenden
Energy-Dashboard-Einstellungen** (`stat_rate` und `power_config`) übernommen.
Eine fehlende Echtzeit-Leistung kann alternativ aus den EMS-Zuordnungen
kommen; `source_mode: ems` erzwingt diese Quellen. **Wh/kWh-Zähler werden
nicht als momentane W-Werte fehlinterpretiert.** Die Sicherheits-/EPS-Quellen
bleiben separat konfigurierbar.

[Details zur integrierten Energieflusskarte](docs/local-ems-flow.md).

## Local EMS 0.5.0b1 – 15-Minuten-Ist-Durchschnitt und Gauge

Der native Sensor **Quarter actual average demand** (`quarter_average_kw`)
berechnet den tatsächlich beobachteten Viertelstunden-Ist-Durchschnitt
aus seit Intervallbeginn bezogenen kWh geteilt durch die verstrichenen
Stunden. Er ist ausdrücklich von `committed_kw` (E × 4) und
`forecast_kw` (Endprognose) getrennt.

Zusätzlich ist ein eigener Gauge enthalten, der Ist-Durchschnitt,
Prognose, Warnschwelle, Grenze und Restzeit ohne manuelle Quellenzuordnung
anzeigt:

```yaml
type: custom:local-ems-peak-gauge-card
```

Die Karte nutzt die **bereits registrierte Local-EMS-JavaScript-Ressource**
und vorhandene Daten des HA Coordinators. Kein eigenes Messarchiv, kein
zusätzliches HACS-Card-Repository und keine neuen Steuerungsbefehle.
[Beschreibung und Grenzen](docs/local-ems-peak-gauge.md).

## Local EMS 0.5.0b5 – Original Power Flow Card Plus eingebettet

Unsere bisher selbst gezeichnete `custom:local-ems-flow-card` verwendet ab
0.5.0b5 den **originalen Renderer und die originale Energieflussberechnung**
der aktuellen Originaldistribution **Power Flow Card Plus v0.4.0-beta.1**.
Es handelt sich um den am 8. November 2026 veröffentlichten Build im
Upstream-Repository `flixlix/power-flow-card-plus` (Commit `d9f3a925`).
Die Datei ist lokal mitgeliefert; eine zweite HACS-Installation entfällt.
Bestehende `custom:local-ems-flow-card`-Dashboards behalten dieselbe Karten-ID.

Ein eigenständiger, überschaubarer Adapter übergibt die Energy-Dashboard-
oder EMS-Leistungswerte nach Normierung von Einheiten und Vorzeichen.
Die Originalkarte übernimmt Layout, Flussverteilung und Animationen.
Die eigene 15-Minuten-Auswertung sowie die EMS-Netz-/EPS-Sicherheitslogik
bleiben davon unabhängig. Für alle neuen Diagrammstände sind Tests mit
realen Home-Assistant-Daten erforderlich; Beta bleibt Beta.

**Credits und Lizenz:** [Power Flow Card Plus – flixlix](https://github.com/flixlix/power-flow-card-plus), MIT,
Copyright (c) 2023–2026 flixlix. Vollständiger Original-Lizenztext:
[vendor/LICENSE-PFCP](custom_components/local_ems/frontend/vendor/LICENSE-PFCP).
Details zur exakten Version und Anpassung:
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) und
[Flow-Card-Dokumentation](docs/local-ems-flow.md).
