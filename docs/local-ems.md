# Local EMS: Architektur und Umsetzungsstand

## Ziel

Ein lokales, modular erweiterbares Home Energy Management System (HEMS) als
Home-Assistant-Custom-Integration. Es verwendet die vorhandenen
Home-Assistant-Integrationen und den Recorder, speichert **keine zweite
Verbrauchsdatenbank** und übernimmt **keine sicherheitskritische Netzregelung**.

### Module

1. **Peak Monitor (0.1):** feste lokale Viertelstunden, kumulativer
   Netzbezugszähler, aufgelaufene Leistung, Prognose und Warnung.
2. **PV-Überschuss (später):** gemeinsame Leistungs- und Energiebilanz.
3. **Wallbox (später):** Ladestrombegrenzung anhand verfügbarer Leistung.
4. **Batterie (später):** Entladebudgets und SoC-Reserve, koordinierte
   Schreibzugriffe auf Wechselrichter.
5. **Netzvorgaben (später):** getrennte, zugelassene netzseitige Schnittstelle;
   der EMS-Core darf keine Netzschutz-/Sicherheitseinrichtung ersetzen.

## Architekturprinzipien

- **Einheiten und Vorzeichen:** Bezug positiv, Einspeisung negativ; Batterie
  positiv beim Entladen, negativ beim Laden; Leistung in kW, Energie in kWh.
- **Datenquellen:** Über UI konfigurierte HA-Entitäten. Für Peak Monitor
  ausdrücklich ein monoton steigender, *nur Netzbezug* messender Wh/kWh-Zähler
  (am Hausanschluss z. B. \`sensor.kng_p_in\`). Keine saldierte Leistung und kein
  Energy-Dashboard-Datenfeed als Ersatz für Echtzeitwerte.
- **Datenhaltung:** Home Assistant Recorder liefert Rohhistorie.
  Lokale Berechnungen halten nur eine flüchtige Stichprobenmenge der laufenden
  Viertelstunde. Kein SQL, keine eigene Datenbank.
- **Zeit:** Feste Uhrzeitfenster 00, 15, 30, 45 Minuten, lokale HA-Zeitzone.
  DST-Sprünge werden als unterschiedliche UTC-Fenster behandelt.
- **Ausfallsicherheit:** Bei fehlendem Messwert, veraltetem Sample, unmöglichem
  Zählerreset oder nicht rekonstruierbarem Viertelstundenstart keine gültige
  Prognose. Keine stillschweigende Annahme "0 kWh".
- **Wirkungsbereich:** Die erste Version ist ausschließlich lesend.
  Keine Sofar-, Wallbox- oder Netzbetreiber-Schreibbefehle.

## Formeln

Mit \`E\` = seit Viertelstundenbeginn aus dem Netz bezogene kWh,
\`P_trend\` = kurzfristige durchschnittliche Bezugsleistung in kW und
\`t\` = verstrichene Minuten:

- \`E_budget = P_limit * 0.25 h\`
- \`P_committed = 4 * E\`
- \`P_forecast = 4 * [E + P_trend * (15 - t) / 60]\`
- \`P_allowed_remaining = (E_budget - E) / remaining_hours\`
- \`minutes_to_limit = 60 * (E_budget - E) / P_trend\`, sofern der
  Schwellenwert bei unverändertem Trend *innerhalb der laufenden Viertelstunde*
  erreicht wird. Andernfalls ist der Wert unbekannt.

\`P_committed\` ist eine bereits gesicherte Untergrenze für den
Viertelstundenmittelwert. Die Prognose ist ausdrücklich keine Messung.

## Datenqualität

Die viertelstundengenaue Zuordnung setzt einen bekannten Zählerstand am
Zeitfensterbeginn voraus. Wenn der Smartmeter dort keinen Messwert liefert,
kann die Grenze zwischen dem letzten davor und ersten danach gemeldeten Wert
linear interpoliert werden. Das wird als \`estimated_boundary\` ausgewiesen.
Bei zu großen Lücken wird kein zuverlässiger Viertelstundenwert behauptet.

**Validierung für abrechnungsrelevante Zwecke:** Die vom EMS errechneten
Viertelstundenwerte sind gegen die offiziellen Viertelstundenwerte von Kärnten
Netz zu prüfen. Solange dies nicht erfolgt ist, ist die Funktion nur eine
informative Warnung und darf keine Vertragserfüllung oder Netzgrenze
garantieren.

## Repository und Installation

Das Repository enthält bereits **Home-Assistant-Apps**; diese bleiben in
ihren bisherigen Unterverzeichnissen. Die zusätzliche Integration lebt unter
\`custom_components/local_ems/\`, mit \`hacs.json\` im Repository-Stamm.
HACS installiert nur die Integration, nicht die Apps. Der HA-App-Store
bleibt von der Integrationsverwendung getrennt.

## Abnahmekriterien für 0.1

- Einrichtung und Grenzwertänderung über die HA-Oberfläche (kein YAML).
- Keine SQL-Abfragen, kein zweites Verbrauchsarchiv.
- Auskunft über aktuelle Viertelstundenenergie, aufgelaufene Leistung,
  Endprognose, verbleibendes Budget, Restleistungsbudget und Minuten bis Limit.
- Warnung und Datenqualitätsstatus als native HA-Entitäten.
- Einheitstests für Zählerreset, Neustart-/Datenlücke, Viertelstundenende,
  Fortschreibung und DST-Wechsel.
- Testbetrieb mit dem KNG-Zähler, ohne Verbraucher zu schalten.

## Bekannte Grenzen von 0.1

- Geringe Zähleraktualisierungsraten können Kurzfristprognosen verfälschen.
- Datenlücken können nicht immer aus dem Recorder rekonstruierbar sein.
- Bereits abgerechnete historische Viertelstunden sind nur dann exakt
  rekonstruierbar, wenn die ursprünglichen Zeitreihendaten verfügbar sind.
- Selbstverbrauch und Einspeisung werden im Peak Monitor **nicht verrechnet**:
  nur der Zähler für echten Netzbezug zählt.
- Monats-Spitzenhistorie wird später als eigener, HA-Statistiken-kompatibler
  Messwert umgesetzt.

## Stille Messwerte / Aktualisierungen ohne Zähleränderung

Der Coordinator überwacht neben `state_changed` auch `state_reported` für den
gewählten Verbrauchszähler. Wenn der Zähler bei 0 W unverändert bleibt, ist
ein erneutes HA-Update dennoch ein Mess-Heartbeat. Die Integration führt
keine eigene dauerhafte Verbrauchshistorie, sondern hält nur aktuelle
Stichproben bis zum Ende der laufenden Viertelstunde.

## Integration im Test-Branch installieren

Die neue Custom-Integration liegt zunächst nur auf `feature/local-ems-peak-monitor`; `main`
und die produktive HA-Instanz bleiben unverändert. Bis zum Merge kann
die Test-HA-Instanz die Integrationsdateien aus diesem Branch
in `/config/custom_components/local_ems/` erhalten. Vor einem produktiven
Einsatz sind die HACS-Prüfung und ein HA-Laufzeittest abzuschließen.

**HACS-Validierung:** Das gemeinsame `ha-apps`-Repository enthält
gleichzeitig Home-Assistant-Apps und diese Custom-Integration. Der HACS-Check
prüft das ganze GitHub-Repository: Beschreibung, Topics und eine sauber
geklärte Repository-Lizenz sowie die Branding-Assets (`icon.png`).
Diese Metadaten sind derzeit noch offen; sie werden **nicht** durch das
Anlegen von `hacs.json` ersetzt. Eine pauschale Lizenz für vorhandenen
Fremdcode darf nicht ohne Prüfung hinzugefügt werden.

## Dokumentierter Validierungsstand

- Der reine Python-Rechenkern durchläuft die CI-Unittests.
- Die Manifestvalidierung erfolgt über HA `hassfest`.
- Die HACS-Publikationsvalidierung benötigt noch Repository-Metadaten.
- Ein vollständiger Integrationstest in einer realen Home-Assistant-Instanz
  steht aus. Die Software darf bis dahin nicht als produktionsbereit gelten.

## HACS: eigene Quelle vs. öffentlicher Katalog

Diese Integration wird als **benutzerdefiniertes Repository** in HACS
verwendet. Der CI-Lauf prüft die Integrationsstruktur, das Manifest,
Branding und HACS-Konfiguration.

Die **Katalog-Metadatenprüfungen** für `description` und `topics` sind
im HACS-Action-Workflow ausdrücklich als Ausnahme dokumentiert, weil
GitHub-Metadaten über den verbundenen Schreibzugang derzeit nicht editiert
werden können. Diese Angaben sind für eine öffentliche Katalog-Aufnahme
weiterhin erforderlich und **nicht als erledigt zu betrachten**.

Der `license`-Check wird nur auf PR-Branches übersprungen, da GitHubs
Lizenz-API die `LICENSE` auf dem Default-Branch auswertet. Auf `main`
wird der Lizenz-Check erneut vollständig durchgeführt. Falls die Lizenz
danach nicht erkannt wird, bleibt die HACS-Validierung offen.

Empfohlene GitHub-Metadaten: Beschreibung `Home Assistant apps and a local,
modular Home Energy Management System (EMS) integration`, Topics
`home-assistant`, `hacs`, `ems`, `energy-management`.

Der HACS-CI-Status mit konfigurierten Ausnahmen ist **keine Freigabe für
den öffentlichen HACS-Katalog**. Ein Laufzeittest mit der tatsächlichen
Home-Assistant-Version und KNG-Smartmeter-Daten ist zusätzlich notwendig.

## Fix 0.1.0b2: Anzeige unter Integrationen statt Helfern

Im ersten Release war `integration_type: helper` gesetzt. Dies führt
dazu, dass Home Assistant die Konfiguration unter **Helfer** einordnet.
Das ist für den modularen EMS-Core mit mehreren angebundenen Systemen
falsch. Ab `0.1.0b2` ist der Manifesttyp `hub`, sodass Home Assistant
die Integration unter **Einstellungen → Geräte & Dienste → Integrationen**
aufführt.

**Update:** HACS → Local EMS → aktualisieren, anschließend Home Assistant
neu starten. Die bestehende Config-Entry, die Quellsensor-Zuordnung und
die von HA vergebenen Entity-IDs werden durch die Typkorrektur nicht
automatisch gelöscht oder umbenannt. Keine manuelle Änderung in
`.storage` und keine neue YAML-Datei erforderlich.

Falls die Integration danach weiterhin fehlt, **Einstellungen → System →
Protokolle** nach `local_ems` bzw. `custom_components.local_ems` durchsuchen.
Der Laufzeittest ist getrennt von Manifest-/HACS-CI zu validieren.
