# Local EMS – Geräteverwaltung (0.2.0b1)

## Zweck

Einmalige Konfiguration aller schaltbaren Flexverbraucher und Wallboxen über
**Einstellungen → Geräte & Dienste → Local EMS → Konfigurieren**.

Die Geräteverwaltung ist Teil derselben Home-Assistant-Integration wie der
bestehende Peak Monitor. Die Daten werden als Optionen des HA Config Entry
gespeichert. Ein weiterer Verbrauchszähler oder eine zusätzliche Datenbank
wird **nicht** betrieben.

## Bedienung

Das Konfigurationsmenü bietet:

- **Peak Monitor:** vorhandene Leistungsgrenzen und Messwertalter ändern.
- **Energie-Messwerte:** Netzleistung (positiv Bezug, negativ Einspeisung),
  PV-Leistung, Hauslast, Batterie-Leistung (positiv Entladung), SoC zuordnen.
- **Schaltverbraucher hinzufügen:** Heizstab, Heizlüfter oder sonstige
  Verbraucher mit `switch.*`-Entität hinterlegen.
- **Schaltverbraucher bearbeiten/entfernen:** beliebig viele Geräte verwalten.
- **Wallbox hinzufügen:** Ladeleistungssensor, Ladefreigabeschalter,
  Ladestrom-Zahlentität und Fahrzeug-Verbindungsstatus optional zuordnen.
  Mindestens eine Wallbox-Entität muss hinterlegt werden.
- **Wallbox bearbeiten/entfernen:** mehrere unabhängige Wallboxen möglich.

### Pro Schaltverbraucher

| Parameter | Verwendung |
|---|---|
| Bezeichnung | Eindeutiger Anzeigename, z.B. Heizstab Pufferspeicher |
| Typ | Heizstab, Heizlüfter, anderer |
| Schalter | Bestehende HA `switch.*`-Entität |
| Nennleistung (W) | Planungswert; optional echter Leistungssensor |
| Priorität 1–100 | Niedriger = früher berücksichtigt |
| Mindest-Einschaltdauer | Späterer Schutz gegen schnelles Abschalten |
| Mindest-Ausschaltdauer | Späterer Schutz gegen häufige Starts |
| Überschussreserve (W) | Planungs-Sicherheitszuschlag |
| Berücksichtigen | Markiert Gerät für spätere Planung |

### Pro Wallbox

| Parameter | Verwendung |
|---|---|
| Bezeichnung | z.B. go-e |
| Ladeleistung | Bestehende HA `sensor.*`-Entität (optional) |
| Ladefreigabe | Bestehende HA `switch.*`-Entität (optional) |
| Ladestrom | Bestehende HA `number.*`-Entität (optional) |
| Fahrzeug verbunden | Bestehende HA `binary_sensor.*`-Entität (optional) |
| Phasen | 1 oder 3, zunächst reine Planung |
| Maximalstrom | 6–80 A, zunächst reine Planung |
| Priorität und Berücksichtigen | Zukunftsplanung |

Die Eingaben sind keine Herstellerkommandos; insbesondere dürfen
Ladefreigabe- und Stromlimit-Entitäten nicht ohne Prüfung der
zugrunde liegenden go-e-Integration für spätere Schreibaktionen benutzt werden.

## Sichtbare Statuswerte in HA

Es werden fünf zusätzliche native Sensoren angelegt: registrierte
Schaltverbraucher, aktuell eingeschaltete Schaltverbraucher, nicht
verfügbare Schaltverbraucher, *geschätzte* aktive Verbraucherleistung und
registrierte Wallboxen. Die beiden Anzahl-Sensoren enthalten die jeweilige
Konfiguration und beobachteten Zustände als Attribute.

Ist ein Leistungssensor hinterlegt, wird dessen Wert für den angezeigten
Schätzwert verwendet; andernfalls die hinterlegte Nennleistung.
Die Schätzung ist **kein abrechnungsrelevanter Messwert**.

## Betriebsgrenze: read-only

**Version 0.2.0b1 schaltet niemals einen Verbraucher und setzt keine
Wallbox-Ladeparameter.** Es werden ausschließlich bekannte HA-Entitäten
ausgelesen und Konfigurationswerte im HA Config Entry verändert.

Vor einer automatischen Überschussregelung sind zu definieren und zu testen:
Verhalten bei unzuverlässigen Daten, Einspeisung und Batterieentladung,
Mindestlaufzeiten, Prioritäten, elektrische Schaltlasten der Relais und
manuelle Bedienung beziehungsweise Sicherheitsabschaltung. Für manche
Heizlüfter oder Heizstäbe muss geprüft werden, ob das externe Schalten über
ein Relais betrieblich und elektrisch zulässig ist.

## Upgrade von 0.1.x

In HACS `Local EMS` aktualisieren und HA neu starten. Die vorhandene
Peak-Monitor-Config-Entry und deren Einstellungen bleiben bestehen. Im
Integrationseintrag unter **Konfigurieren** erscheint ein neues Menü.
Für registrierte Verbraucher sind keine YAML-Einträge erforderlich.

Regulärer Status: `Beta`. HACS/Hassfest und Unit-Tests sichern die
Struktur, aber nicht das reale Schaltverhalten (da nicht implementiert).

## Einheitsspezifische Entitätsfilter (0.2.0b2)

Die Entitätsauswahl verwendet Home Assistants nativen `EntitySelector` mit
`filter.unit_of_measurement`. Statt alle `sensor.*`-Entitäten anzubieten,
werden die Dropdowns wie im Energie-Dashboard nach Messgröße gefiltert:

| Feld | Zugelassene Einheiten |
|---|---|
| Netzbezugszähler (Peak Monitor) | Wh, kWh |
| Netz-, PV-, Haus-, Batterie-Leistung | W, kW |
| Verbraucher-Leistungsmessung | W, kW |
| Wallbox-Ladeleistung | W, kW |
| Batterie-Ladezustand | % |
| Wallbox-Ladestrom-Limit | A |

Schalter bleiben nach Domain `switch` gefiltert; Ladefreigabe und
Fahrzeugstatus nach `switch` bzw. `binary_sensor`. Die Vorauswahl
kombiniert Domain und Einheit, um ungeeignete Entitäten auszublenden.
Zusätzlich wird beim Speichern geprüft, ob die Einheit vorhandener
Live-Entitäten wirklich zum Feld passt. Die Filter konvertieren keine
Einheiten; sie schränken die Auswahl ein. Nicht geladene/temporär offline
stehende Entitäten blockieren bestehende Zuordnungen nicht allein deshalb.

## Netzstatus und EPS-Sicherheit – herstellerneutral (0.3.0b1)

Unter **Einstellungen → Geräte & Dienste → Local EMS → Konfigurieren →
Netz-/EPS-Sicherheit und Betriebsmodus** können folgende Quellen unabhängig
voneinander zugeordnet werden:

| Quelle | Home-Assistant-Typ | Bedeutung |
|---|---|---|
| Wechselrichter-Betriebszustand | Sensor, Select oder Input Select | Statuswerte für Netzbetrieb und EPS frei zuordnen |
| Physischer Netzkontakt (optional) | Binary Sensor | `on` oder `off` bedeutet Netz vorhanden, per Schalter umkehrbar |
| Smartmeter-Heartbeat (optional) | Sensor oder Binary Sensor | Letzte Zustandsmeldung `last_reported`, z.B. alle 1 s |
| Wechselrichter-Betriebsmodus (optional) | Sensor, Select oder Input Select | Nur explizit erlaubte Modi geben EMS-Regelung frei |
| EMS-Hauptfreigabe | HA-Config-Entität `switch` + Konfigurationsoption | Standard AUS, keine physische Schaltaktion in dieser Version |

### Beispiel für einen Sofar (kein herstellerspezifischer Standard!)

- Betriebsstatus: `sensor.hyd20ktl_3p_systemzustand`.
- Lade-/Betriebsmodus: `select.hyd20ktl_3p_betriebsmodus_des_ladegerats`.
- Smartmeter-Heartbeat: passender KNG-Sensor, **wenn er tatsächlich bei jeder
  Meldung von HA neu geschrieben wird**, z.B. `sensor.kng_p_in`.
- Netzbetriebs-/EPS-Werte: **exakte Rohwerte** unter **Entwicklerwerkzeuge →
  Zustände** ablesen und kommagetrennt eintragen. Nicht blind `2` und `3`
  annehmen, weil Hersteller/Integration Zustände unterschiedlich benennen.
- Erlaubter Betriebsmodus: den tatsächlichen Zustandswert des Select für
  `Self Consumption` bzw. `Eigenverbrauch` ablesen und eintragen.

Andere Nutzer können Status- und Betriebsmoduswerte selbst festlegen.
Benötigt ein Wechselrichter keinen gesonderten Modus, kann die
Betriebsmoduszuordnung leer bleiben; bei einem einfachen Netzmeldekontakt ist
auch kein Wechselrichter-Betriebsstatus erforderlich. **Nur das Vorliegen
eines Smartmeter-Heartbeats beweist dagegen niemals Netzbetrieb.**

### Statusmodell / Sicherheitsregeln

- **EPS bestätigt:** Wechselrichter meldet einen als EPS konfigurierten
  Zustand → `eps`, sofortige Sperre.
- **Netzkontakt aus:** als Netzabwesenheit konfigurierter Kontaktsignalwert
  → `grid_lost`, Sperre, unabhängig von widersprechendem WR-Status.
- **Smartmeter meldet nicht:** wenn `last_reported` älter als z.B. 10 s
  oder die Quelle nicht verfügbar ist, bei sonst erkanntem Netzbetrieb →
  `suspect`, Sperre, **kein** behaupteter EPS-Zustand.
- **Unbekannter WR-Status:** `unknown`, Sperre.
- **WR im nicht erlaubten Betriebsmodus:** Netzstatus bleibt `on_grid`,
  Freigabe dennoch gesperrt.
- **Netzbetrieb stabil und zulässiger Modus:** Nach einer einstellbaren
  Stabilisierungszeit (Standard 120 s) `on_grid` und Freigabe, sofern
  EMS aktiviert ist.
- **Keine Statusquelle konfiguriert:** `unconfigured`, keine Freigabe.
- **EMS ausgeschaltet:** weiterhin Überwachung, aber keine Regelung und
  keine Lastabwurfanforderung durch das EMS.

### Smartmeter-Heartbeat: technische Einschränkung

Home Assistant aktualisiert `last_reported` nur dann, wenn eine Integration
erneut einen Zustand in Home Assistant schreibt. **Nicht jede MQTT-,
Modbus- oder Herstellerintegration reicht unveränderte Telegramme weiter.**
Deshalb vor Aktivierung anhand der gewählten Entität prüfen, ob
`last_reported` auch bei unverändertem Energiewert tatsächlich ca. alle
1 s aktualisiert wird. Ein veralteter Wert kann ebenso Netzwerk-, Geräte-
oder HA-Kommunikationsprobleme anzeigen und ist kein definitiver Stromausfall.

Die Altersprüfung läuft unabhängig vom Peak-Monitor auf dessen Ereignis-
und Zeitbasis. Die Analyse wird als native Status- und Binary-Sensor-Entitäten
veröffentlicht; keine zweite Messwertdatenbank.

### Wichtige Grenze: derzeit KEINE reale Notstromabschaltung

Die in 0.3.0b1 neu veröffentlichten Werte `control_allowed` und
`load_shed_requested` sind **nur Entscheidungen des Sicherheitskerns**.
Selbst wenn `load_shed_requested` an ist, werden noch **keine** Switches,
Heizstäbe, Heizlüfter oder Wallboxen tatsächlich ausgeschaltet.

Für reale Lastabwurf-Funktionen braucht es gesonderte aktivierbare
Aktorsteuerung, Schaltbestätigung, manuellen Override und elektrische
Überprüfung. Für kritische Lasten ist ein hardwareseitiger Verriegelungs-
oder Lastabwurfkontakt unabhängig von Home Assistant vorzuziehen.
