# Local EMS – Original Power Flow Card Plus (0.5.0b6)

## Herkunft und Architektur

Die integrierte Karte `custom:local-ems-flow-card` verwendet den
**originalen Renderer, Flussberechner und Editor von Power Flow Card Plus**.
Wir verwenden bewusst die aktuelle **0.4.0-beta.1-Distribution** aus
[flixlix/power-flow-card-plus](https://github.com/flixlix/power-flow-card-plus)
(Main-Commit `d9f3a9255776b3e1a270bf72b2c8039e22047104` vom
8. November 2026), **nicht** den älteren stabilen Release 0.3.7.

Der ursprüngliche Quellcode lebt im
[flixlix-cards-Monorepo](https://github.com/flixlix/flixlix-cards).
Die Hauptzweige können sich unabhängig von der zuletzt veröffentlichten
gebündelten JavaScript-Distribution weiterentwickeln. Die Datei wird bei
Local EMS deshalb bewusst auf einen genauen Commit fixiert.

Die Integration besteht aus drei getrennten Komponenten:

1. `frontend/vendor/power-flow-card-plus-v0.4.0-beta.1.mjs`: aktueller
   Upstream-Build mit originaler Berechnung, UI, responsivem Layout,
   Animationen und Original-Konfigurationseditor.
2. `frontend/pfcp-adapter.mjs`: eigenständiger Adapter zwischen
   Home Assistant Energy Dashboard / Local EMS und dem nativen PFCP-Datenformat.
3. `frontend/local-ems-flow-card.mjs`: bestehender Local-EMS-Kartentyp,
   Registrierung, Quellenübernahme und More-Info-Aufrufe.

An der Originaldatei wurden **nur die Elementnamen und die zugehörigen
Selektoren** umbenannt (`local-ems-pfcp-upstream` statt
`power-flow-card-plus`). Dadurch kollidiert unsere eingebettete
Version nicht mit einer separat installierten Originalkarte.
Die originale Energiebilanz, ihre PV-/Netz-/Batteriepfade
und deren Animationen bleiben erhalten. Es existiert keine
eigene Local-EMS-SVG-Nachbildung mehr.

## Einrichtung

Nach HACS-Update auf Local EMS `0.5.0b6`, HA-Neustart und
vollständigem Neuladen des Dashboards bleibt die Kartendeklaration:

```yaml
type: custom:local-ems-flow-card
```

Die Karte liest standardmäßig die Leistungssensoren aus den Einstellungen
des Home Assistant Energy Dashboards (`energy/get_prefs`) und verwendet
ansonsten die konfigurierten Local-EMS-Quellen. Für die explizite
Local-EMS-Sensorzuordnung:

```yaml
type: custom:local-ems-flow-card
source_mode: ems
```

### Batterie-Vorzeichen gezielt korrigieren (0.5.0b6)

**Fehlerursache in 0.5.0b5:** Bei automatischer Quellenwahl hatte das
Home-Assistant-Energie-Dashboard Vorrang. Die Integrationseinstellung
`Batterieleistung umkehren` wirkte nur, wenn wirklich der Local-EMS-Sensor
verwendet wurde. Eine Kartenoption `invert_battery_power` wurde bisher
unverändert an den Originalrenderer durchgereicht und dort ignoriert.

Ab 0.5.0b6 kann die Karte die **tatsächlich gewählte** Batteriesensor-
Richtung unabhängig von der Quelle explizit vorgeben:

```yaml
type: custom:local-ems-flow-card
source_mode: ems
invert_battery_power: false
```

- `source_mode: ems` verwendet die in **Local EMS** konfigurierten Quellen,
  nicht die Sensoren des Energie-Dashboards.
- `invert_battery_power: false` bedeutet: Batteriesensor **positiv =
  Entladung**; dies überschreibt auch eine bisherige Local-EMS-Option zum
  Invertieren der Batterieleistung.
- `invert_battery_power: true` bedeutet: Batteriesensor **positiv =
  Ladung**. Die Karte dreht das Vorzeichen zur internen Konvention um.
- Ohne `invert_battery_power` bleibt die bisherige Logik erhalten: Bei
  Local-EMS-Sensoren gilt die dortige Invertierung, bei
  Energie-Dashboard-Sensoren deren eigene `power_config`.
- Der Override funktioniert **auch ohne** `source_mode: ems`: In diesem Fall
  invertiert er bei Bedarf das bereits vom Energie-Dashboard aufbereitete
  Leistungssignal. Bei `power_config.stat_rate_inverted` muss deshalb
  berücksichtigt werden, dass der Helper das Rohsignal bereits invertiert.
- Bei **vollständig manuellen** `entities:`-Konfigurationen weiterhin die
  Originaloption `entities.battery.invert_state` verwenden. Nicht mit der
  Local-EMS-Option `invert_battery_power` mischen.

Für den Sofar-Sensor `sensor.sofar_batterie_1_leistung`, der zuvor in
Power Flow Card Plus mit `invert_state: true` genutzt wurde, ist bei
automatischer Local-EMS-Quellenwahl die Einstellung `false` der passende
Ausgangspunkt, **sofern** positive Rohwerte tatsächlich Entladung bedeuten.
Vorzeichen anhand einer echten Lade- und Entladephase verifizieren, nicht aus
dem momentanen SoC ableiten. Die Änderung betrifft ausschließlich die
Browserdarstellung; EPS-/Verbraucherschutz und Batterieansteuerung bleiben
unverändert.

Auch die erweiterten Original-Einstellungen (Farben, Flussgeschwindigkeit,
einzelne Verbraucher, Animationen, Linien, Layout) werden durchgereicht.
Der Original-Editor kann bei manueller PFCP-Konfiguration verwendet werden.

### Vollständig manuelle Konfiguration

Die Konfiguration unter `entities` wird an die Originalkarte übergeben,
ohne dass Local EMS deren Quellen überschreibt:

```yaml
type: custom:local-ems-flow-card
entities:
  grid:
    entity: sensor.kng_p
  solar:
    entity: sensor.hyd20ktl_3p_pv_leistung_gesamt
  battery:
    entity: sensor.sofar_batterie_1_leistung
    state_of_charge: sensor.sofar_batterie_1_ladezustand
    invert_state: true  # Vorzeichen des tatsächlichen Sensors prüfen
```

Diese Entity-IDs dienen nur als Beispiel. Im manuellen Modus ist
die Verantwortung für Einheit, Vorzeichen und Verfügbarkeit bei
der HA-Konfiguration; hier werden nicht automatisch zusätzliche
Local-EMS-Sicherheitsinformationen eingebunden.

### Adapter und Vorzeichen

Bei automatischer Quellenübernahme gilt:

- Netzleistung `+` = Bezug, `−` = Einspeisung.
- Local EMS Batterie `+` = Entladung, `−` = Ladung.
- Power Flow Card Plus Batterie `+` = Ladung, `−` = Entladung.
- Der Adapter invertiert daher die Batterie und liefert Werte in **W**.
- Fehlende/ungültige Originalmesswerte bleiben `unavailable`, nicht `0`.
- Optional `use_measured_home: true` zeigt den vorhandenen gemessenen
  Hausverbrauch statt der aus Original-PFCP-Flüssen berechneten Bilanz.
- Virtuelle Quell-Objekte existieren **nur im Browser**;
  sie erzeugen keine echten HA-Entitäten und keine Recorder-Einträge.

### Netz- und EPS-Betrieb

Der erkannte EMS-Status `eps`/`grid_lost` bzw. ein explizit negativer
Netzkontakt wird für die Originalkarte als Power Outage gemeldet.
Der angezeigte Netzleistungswert wird dann auf `0` gesetzt, um
keine alten Smartmeter-Netzflüsse zu animieren.
Ein Generator wird ohne eigene Messquelle nicht als zusätzlicher
Erzeuger bilanziert. **Diese Karte steuert keine Verbraucher und
ersetzt keine EPS-Sicherheitsfunktionen.**

## Caching und Aktualisierung

Nach dem Chrome-Android-Cachefehler in der Version 0.5.0b2
erhalten der Hauptkartenimport, der EMS-Adapter, das Messmodell
und die eingebettete Upstream-Datei getrennte Versionskennungen.
Die Ressource wird unter `/local_ems/local-ems-flow-card.mjs?v=0.5.0b6`
registriert. Ein Browser-Neuladen nach dem HA-Neustart wird empfohlen.

## Credits, Lizenz und Rückbau

- Original: [Power Flow Card Plus von flixlix](https://github.com/flixlix/power-flow-card-plus).
- Version: **0.4.0-beta.1**, Commit `d9f3a9255776b3e1a270bf72b2c8039e22047104`.
- Copyright (c) 2023–2026 flixlix, **MIT**.
- Vollständige Lizenz: [`vendor/LICENSE-PFCP`](../custom_components/local_ems/frontend/vendor/LICENSE-PFCP).
- Nachweise: [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md) und
  [`LICENSE_SCOPE.md`](../LICENSE_SCOPE.md).
- Eigener Local-EMS-Adapter und Backend: GPL-3.0-or-later.

Vor der produktiven Abnahme muss die tatsächliche Darstellung in der
laufenden Home-Assistant-Instanz mit KNG und Sofar getestet werden,
insbesondere PV→Batterie, Netz→Batterie, Solar→Netz, negative Messwerte
und EPS. Dieser UI-Test ist durch GitHub Actions nicht ersetzt.
Für Rollback die frühere Local EMS Version `0.5.0b4` nutzen;
die EMS-Konfiguration wird durch den UI-Austausch nicht verändert.
