# Local EMS – eigene Power-Flow-Karte (0.4.0b2)

## Idee und Grenzen

**Local EMS** liefert eine eigene, integrierte Lovelace-Karte
`custom:local-ems-flow-card`. Die bisher separate Community-Karte
`power-flow-card-plus` ist dafür **nicht erforderlich**.

**Standard: Energy-Dashboard als Datenquelle.** Die Karte liest die
Einstellungen über Home Assistants lesende WebSocket-API
`energy/get_prefs` und verwendet deren `stat_rate` bzw.
`power_config` für Netz, PV, Haus und Batterie, einschließlich
getrenntem Netzbezug/Einspeisung, Laden/Entladen, mehreren Quellen und
Batterie-SoC. Die im EMS hinterlegten Leistungsquellen dienen als
**Fallback**, falls im Energy-Dashboard kein Echtzeit-Leistungssensor
konfiguriert ist. Die Karte liest aktuelle HA-Zustände direkt.
Dadurch werden **keine zweiten Leistungszeitreihen im HA Recorder** erzeugt.

Die Karte nutzt bewusst die **runde Energiefluss-Topologie** in Anlehnung an
die Home-Assistant-Energieverteilung und Power Flow Card Plus:
PV **oben**, Netz **links**, Haus **rechts**, Batterie **unten**.
Gebogene Verbindungslinien, animierte farbige Punkte, Live-Leistungswerte,
Batterieladestand, Netzfrequenz, WR-Rohzustand und EPS-Status gehören dazu.
Die Darstellung ist eine **eigene Implementierung**, ohne fremde JavaScript-
Bibliothek oder Abhängigkeit von Power Flow Card Plus.

Die zusätzliche Metadaten-Entität **Local EMS Energy flow** enthält
Konfiguration und Sicherheitsstatus, **nicht** kontinuierliche Kopien der
Leistungsmesswerte. Bestehende EMS-Entitäten bleiben erhalten.

## Konfiguration mit der vorhandenen Sofar/KNG-Anlage (Beispiel, nicht fest verdrahtet)

Unter **Einstellungen → Geräte & Dienste → Integrationen → Local EMS →
Konfigurieren → Energie-Messwerte zuordnen**:

| Feld | Beispiel-Entität |
|---|---|
| Netzleistung | `sensor.kng_p` |
| PV-Leistung | `sensor.hyd20ktl_3p_pv_leistung_gesamt` |
| Hausleistung | `sensor.hyd20ktl_3p_wirkleistungslast_system` |
| Batterieleistung | `sensor.sofar_batterie_1_leistung` |
| Batterie-SoC | `sensor.sofar_batterie_1_ladezustand` |
| Netzfrequenz | `sensor.hyd20ktl_3p_netzfrequenz` |
| Netzleistung umkehren | AUS (sofern positive Werte Netzbezug bedeuten) |
| Batterieleistung umkehren | EIN, entsprechend dem bisher verwendeten `invert_state: true` |

Unter **Netz-/EPS-Sicherheit und Betriebsmodus**:

- Wechselrichterzustand: `sensor.hyd20ktl_3p_systemzustand`
- Physischer Netzkontakt: `binary_sensor.kng_netzversorgung` **nur wenn dessen
  Bedeutung bei on/off überprüft wurde**.
- Exakte erlaubte Netz-/EPS-Zustandswerte und WR-Betriebsmodus aus den
  HA-Entwicklerwerkzeugen übernehmen; **nicht** pauschal Herstellerwerte
  annehmen.

Für andere Wechselrichter dürfen vollständig andere HA-Entitäten gewählt
werden. Die Karte enthält **keinen Herstelleradapter**.

## Dashboard-Karte verwenden

Nach HACS-Update auf 0.4.0b2 und Neustart von Home Assistant:

```yaml
type: custom:local-ems-flow-card
```

Das ist die gesamte Dashboard-Konfiguration für einen EMS-Eintrag.
Die Karte zeigt **momentane Leistungen in W/kW**. Die Energiezähler in
Wh/kWh übernimmt unser EMS weiterhin für Peak- und Verbrauchsanalysen; die
Karte darf aus einem kumulativen kWh-Zähler **keine scheinbar sekundengenaue
Leistung** ableiten.

Falls die Leistungs-Sensoren des Energy-Dashboards nicht verwendet werden
sollen (z. B. wegen Spezialmessungen), ist ein Dashboard-Override möglich:

```yaml
type: custom:local-ems-flow-card
source_mode: ems
```

Damit verwendet die Karte wieder die zentral im EMS hinterlegten Sensoren,
ohne diese im Dashboard erneut angeben zu müssen.

Bei mehreren Local-EMS-Instanzen kann die passende Metadaten-Entität explizit
gewählt werden:

```yaml
type: custom:local-ems-flow-card
entity: sensor.local_ems_energy_flow
title: Haus-Energiefluss
```

Der Name der Entität kann durch HA bei Namenskonflikten variieren. Ohne
Angabe sucht die Karte automatisch nach einer HA-Entität mit
`ems_flow_version: 1`.

Klick auf einen Knoten öffnet die normale HA-Mehr-Info-Ansicht des
zugeordneten Quellsensors. Alle Symbole nutzen HA-eigene Material-Icons und
die HA-Farbvariablen, einschließlich Dark Mode.

## Installation der Dashboard-Ressource

In HA-Dashboards mit Speicherung über die Oberfläche versucht Local EMS,
sein eigenes Modul **automatisch** als Lovelace-Ressource zu registrieren
(nachdem bereits vorhandene Ressourcen geladen wurden).

Wenn die Registrierung nicht möglich ist, unter **Einstellungen →
Dashboards → Ressourcen → Ressource hinzufügen** einmalig anlegen:

- URL: `/local_ems/local-ems-flow-card.mjs?v=0.4.0b2`
- Typ: **JavaScript-Modul**

Bei YAML-Ressourcenverwaltung stattdessen entsprechend im Lovelace-Abschnitt
eintragen:

```yaml
lovelace:
  resource_mode: yaml
  resources:
    - url: /local_ems/local-ems-flow-card.mjs?v=0.4.0b2
      type: module
```

Das ist **nur** eine Dashboard-Ressource und keine erneute Zuordnung der
Leistungsmesswerte. Nach Ressourcenänderungen die Dashboard-Seite
vollständig neu laden (ggf. Browsercache leeren).

## Physikalisches Vorzeichenmodell

- Netz: **+ = Bezug**, **– = Einspeisung**.
- Batterie: **+ = Entladen**, **– = Laden**.
- PV und Haus: positive Leistungswerte.
- Quellwerte können in W oder kW gemeldet werden; die Karte rechnet
  intern in W um, Frequenz in Hz und SoC in Prozent.
- Nicht verfügbare oder unpassende Messwerte werden als **—** angezeigt,
  nicht stillschweigend als 0.
- Das Haus wird mit dem zugeordneten Hausleistungs-Sensor dargestellt.
  Es wird **keine fiktive Bilanz** erfunden, wenn eine Größe fehlt.

Die Karte zeigt reale **momentane Leistungen**, nicht Viertelstundenenergie
oder garantierte Leistungsflüsse zu einzelnen Verbrauchern. Animationen
geben die Richtung der vorzeichenbehafteten Größen wieder; sie ersetzen
keine elektroenergetische Lastflussberechnung.

## Warum nicht einfach power-flow-card-plus?

Die eigene Local-EMS-Karte hat jetzt den **vertrauten Kreis-/Punktfluss-Stil**,
bleibt aber schlanker als Power Flow Card Plus: noch kein vollständiger
grafischer Editor und noch keine zusätzlichen individuellen
Wallbox-/Heizstab-Knoten. Sie verwendet native HA-Themenfarben und ist
**keine pixelgenaue Kopie** der Fremdkarte. Native Power-Sankey-Diagramme
sind ausdrücklich **nicht** das gewählte Layout.

Bis die Darstellung und alle Richtungen in der eigenen HA-Instanz
verifiziert wurden, die bisherige Karte bitte als Referenz behalten.
Die EMS-Integration steuert in diesem Release weiterhin keine Verbraucher.
