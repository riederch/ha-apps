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
