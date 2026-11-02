# Local EMS – 15-Minuten-Gauge (0.5.0b1)

## Ziel

Ein Gauge für den **tatsächlichen bisherigen Durchschnitt des Netzbezugs
innerhalb der laufenden Viertelstunde**, mit separat gekennzeichneter
**Prognose zum Viertelstundenende**.

Die Grenzwerte stammen aus der bestehenden Local-EMS-Konfiguration
(\`number.*_demand_limit\` und \`number.*_warning_threshold\`).
Die Karte benötigt keine manuellen Grenzen oder doppelte Messwertdefinitionen.

## Berechnung und Bedeutung

* \`quarter_average_kw = energy_kwh / elapsed_hours\`
  – Ist-Durchschnitt des Netzbezugs seit Viertelstundenbeginn.
  Verwendet den Zeitstempel **des letzten gültigen Smartmeter-Samples**.
* \`committed_kw = energy_kwh × 4\`
  – schon sicher auf das komplette 15-Minuten-Fenster umgerechneter Bezug,
  **nicht** der Ist-Durchschnitt.
* \`forecast_kw\`
  – aus beobachtetem Bezug und kurzfristigem Trend prognostizierter
  Viertelstundenmittelwert bei unverändertem Verbrauchsverlauf.

Beispiel: In 6 Minuten wurden 0,8 kWh bezogen.

* Ist-Durchschnitt: \`0,8 / (6/60) = 8,0 kW\`.
* Gesicherter Viertelstundenwert: \`0,8 × 4 = 3,2 kW\`.
* Prognose: hängt vom verbleibenden Zeitfenster und kurzfristigen Trend ab.

Bei **exakt 0 Sekunden verstrichener Zeit** ist der Durchschnitt undefiniert
und wird als nicht verfügbar angezeigt, **nicht fälschlich als 0**. Bei
fehlendem Viertelstundenbeginn, Zählerreset, veralteten oder fehlerhaften
Messdaten zeigt der Gauge keinen verlässlichen Istwert an.

## Anzeige in der neuen Karte

- **Zeiger + große Zahl:** aktueller Ist-Durchschnitt in kW.
- **Grün:** kleiner als die Warnschwelle.
- **Gelb:** ab Warnschwelle bis zur Leistungsgrenze.
- **Rot:** ab Leistungsgrenze.
- **Darunter:** separate Werte für Prognose, Warnschwelle und Grenze.
- **Viertelstundenfenster:** lokale Uhrzeiten und Restzeit.
- **Datenqualität:** sichtbarer Hinweis z. B. bei interpoliertem
  Viertelstundenbeginn oder stale Smartmeter.
- **Alarmfarbe der Kopfzeile:** auf Basis der Prognose, damit drohende
  Grenzwertüberschreitungen bereits vor dem endgültigen Istwert sichtbar
  werden. Die Zahlen bleiben eindeutig beschriftet.

Der Gauge ist ausschließlich **lesend**. Es werden keine Lasten geschaltet.
Der native Recorder wird für Datenhistorie genutzt; es gibt keine
zusätzliche Datenbank.

## Dashboard-Einrichtung

Nach HACS-Update auf **0.5.0b1** und HA-Neustart:

\`\`\`yaml
type: custom:local-ems-peak-gauge-card
\`\`\`

Die Gauge-Karte wird über **dieselbe Dashboard-Ressource** wie
\`custom:local-ems-flow-card\` ausgeliefert. Eine zweite JS-Ressource
muss nicht angelegt werden.

Die Karte findet den bestehenden, immer verfügbaren
**Local EMS – Measurement quality**-Sensor über das Attribut
\`ems_peak_gauge_version: 1\` und liest die vom Coordinator
bereitgestellten Werte. Bei mehreren Local-EMS-Instanzen kannst du den
gewünschten Qualitäts-Sensor explizit wählen:

\`\`\`yaml
type: custom:local-ems-peak-gauge-card
entity: sensor.local_ems_measurement_quality
\`\`\`

Die tatsächlichen Entitäts-IDs können je nach Home-Assistant-Installation
abweichen. Der Sensor \`quarter_average_kw\` ist zusätzlich als eigener
nativer Home-Assistant-Power-Sensor verfügbar und lässt sich auch in
Standard-Gauge-, Statistik- oder Verlaufsdiagrammen verwenden.

**Installation:** Das vorhandene Lovelace-Modul
\`/local_ems/local-ems-flow-card.mjs?v=0.5.0b1\` muss einmal geladen sein
(wird normalerweise von Local EMS automatisch registriert). Bei selbst
verwalteten YAML-Lovelace-Ressourcen die Versionsabfrage aktualisieren.

## Sicherheit und Grenzen

Der Ist-Durchschnitt kann besonders zu Beginn eines Zeitfensters stark
schwanken. Für Warnungen **immer die gesonderte Prognose**
\`forecast_kw\` beachten. Die Prognose ist keine abrechnungsrelevante
Messung. Vor einem Einsatz zur Einhaltung vertraglicher Netzgrenzen
müssen die Viertelstundenwerte mit den Netzbetreiberwerten verglichen
werden. Die EMS-Sicherheitslogik für EPS bleibt davon unabhängig.
