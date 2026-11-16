# Local EMS – Entscheidungsprotokoll zum aktuellen und rekonstruierten Vorgängerstand

**Stand:** 15.11.2026. **Status:** fachliche Kontextkonsolidierung; keine neue Entwicklungsfreigabe. **Verbindlichkeit:** Entscheidungen aus dem Ursprungsgespräch und den Repo-Artefakten werden unterschieden; historische Nutzeraussagen sind soweit nicht vollständig erneut gelesen als `R` markiert (siehe `quellen/vorgaengerchats.md`). **Keine erfundenen Gründe oder nachträgliche Freigaben.**

## D-01 – HA-Custom-Integration und vorhandene Datenspeicherung

- **Ausgangsproblem:** 15-Minuten-Leistungsbezug überwachen, später ein modulares und herstellerneutrales EMS ermöglichen, ohne Daten doppelt zu führen.
- **Entscheidung:** `custom_components/local_ems` als HA-Custom-Integration in `riederch/ha-apps`; HA Recorder/Statistics sind die einzige dauerhafte Verbrauchsdatenhaltung; UI-konfigurierbare Entitäten; keine zusätzliche Datenbank, keine direkten SQL-Abfragen. [R/G]
- **Positive Kriterien (genannt bzw. dokumentiert):** Vorhandene HA-Sensoren und deren Historie wiederverwenden; keine zweite, driftende Verbrauchshistorie; Integration in HA-UI und HACS; später modular erweiterbar.
- **Negative Kriterien/Risiken:** HA-Recorder-Datenlücken und träge Smartmeter-Updates können genaue Rekonstruktion und Prognosen einschränken; Integration ist von den verfügbaren HA-Sensordaten abhängig. [G]
- **Verworfene Alternativen:** Separate Verbrauchsdatenbank und direkter SQL-Zugriff [R]; reine Energy-Dashboard-Daten statt geeignetem Importzähler für Peakmonitor nicht ausreichend [G].
- **Fortgeltende Bedingungen:** Keine zweite Verbrauchsdatenbank; fehlende Historie nicht durch angenommene Werte ersetzen; bei Änderungen weiterhin herstellerneutral und recorder-kompatibel.
- **Stand:** Repo-Dokumentation bestätigt, tatsächlicher umfassender Runtime-/Langzeittest nicht nachgewiesen.
- **Nachweis:** `https://github.com/riederch/ha-apps/blob/main/docs/local-ems.md`.

## D-02 – Zunächst nur lesender Viertelstundenmonitor statt aktiver Netzregelung

- **Problem/Ziel:** Nutzer soll kommende 15-Minuten-Netzspitzen rechtzeitig erkennen, ohne durch unreife Schaltlogik Netz-/EPS-Sicherheit zu beeinträchtigen.
- **Entscheidung:** Zunächst lesender Peakmonitor für feste Viertelstunden (00/15/30/45); 10 kW Grenzwert und anfänglich 9 kW Warnung; Bezugssensor `sensor.kng_p_in` als im Konzept genannte Quelle; Ist-Durchschnitt, `committed`, Endprognose, Restbudget und Minuten bis Schwelle getrennt; bei Qualitätslücken keine gültige Prognose. [R/G]
- **Positive Kriterien:** Frühzeitige Warnung, nachvollziehbare Kennzahlen, keine direkten Eingriffe; vorhandene HA-Recorder-Daten; klare Trennung von Beobachtung und Aktorik.
- **Negative Kriterien/Risiken:** Prognose ist keine Messung; Messlücken, Zählerresets, spärliche Updates und DST-Fälle können die Qualität beeinträchtigen; amtliche 15-Minuten-Werte müssen vor abrechnungsrelevanter Nutzung gegengeprüft werden.
- **Verworfene/zurückgestellte Alternativen:** Sofortiges Peak-Shaving mit Schreibbefehlen; direkte Netzschutzfunktion; PV-/Wallbox-/Batteriesteuerung als Bestandteil des ersten Monitorings. [R/G]
- **Fortgeltende Bedingungen:** Kein automatischer Schaltbetrieb oder vertragliche Grenzgarantie aus diesem reinen Monitoring; nur echte Netzbezugsenergie zählt; `unknown` ist kein Wert 0; reale Sensor- und Zeitfensterqualität prüfen.
- **Stand:** Berechnung, Warnentitäten und Peak-Gauge im Repository vorhanden, Produktionsabnahme/Netzbetreiberabgleich nicht belegt.
- **Nachweis:** `https://github.com/riederch/ha-apps/blob/main/docs/local-ems.md`.

## D-03 – Original Power Flow Card Plus statt Sankey oder eigener SVG-Karte

- **Problem/Ziel:** Originalgetreue Darstellung von Energieflüssen, Bubbles/Animationen, Vollbreite und Bedienungsoptionen, ohne funktional abweichende Nachbildung.
- **Entscheidung:** Vorhandenen Typ `custom:local-ems-flow-card` mit Original-PFCP-Renderer, Flussberechnung und Editor verbinden; vendorte Distribution `0.4.0-beta.1` von `flixlix` (statt stabiler `0.3.7`), eigenen Adapter dazwischen, Elementnamen gegen Kollisionen umbenennen; MIT-Urheber- und Lizenzhinweise erhalten. [R/G]
- **Positive Kriterien:** Gewünschtes originales Erscheinungsbild, responsive Darstellung, Bubbles, Animationen, vollständige Original-Optionen; weniger selbst entworfene parallele UI-Logik; Einbindung in bestehende Karte ohne neue HA-Entitäten.
- **Negative Kriterien/Risiken:** Eingebettetes Fremd-Bundle und Version-Fixierung erfordern Pflege bei künftigen Upstream-Updates; Adapter und unterschiedliche Vorzeichenkonventionen erzeugen Abhängigkeiten; visuelle Laufzeitabnahme weiterhin erforderlich.
- **Verworfene Alternativen:** `power-sankey` wurde wegen unpassender Darstellung abgelehnt [R]; eigener SVG-Nachbau entsprach nicht dem gewünschten Original [R]; älterer stabiler PFCP-Release `0.3.7` zugunsten der aktuelleren Distribution nicht verwendet [G].
- **Fortgeltende Bedingungen:** Originalberechnung/-darstellung nicht stillschweigend durch eigene Grafik ersetzen; Credits/Lizenz beibehalten; keine UI-Sicherheits- oder EMS-Schaltfunktion daraus ableiten.
- **Stand:** Quellcode und Credits im GitHub-Repo vorhanden; originale reale Renderings in HA für alle Pfade noch nicht abgenommen.
- **Nachweis:** `https://github.com/riederch/ha-apps/blob/main/docs/local-ems-flow.md`, `.../frontend/vendor/`.

## D-04 – Direkte Flüsse nicht als exakte Messung erfinden

- **Problem/Ziel:** Pfade PV→Batterie, Netz→Batterie, PV→Netz sichtbar machen, ohne falsche Aussage über die physikalische Herkunft zu erzeugen.
- **Entscheidung:** Flüsse nur als konservative, aus der Energiebilanz zwingend resultierende Mindestwerte ermitteln; bei unvollständigen PV-/Netz-/Batteriemessungen oder EPS `0` für erschlossene Direktflüsse; nicht als messbaren Einzelpfad ausgeben. [R/G]
- **Positive Kriterien:** Plausible Animationen ohne unbelegte Quellenzuschreibung; mit vorhandenen Summensensoren möglich, kein Extra-Sensor notwendig.
- **Negative Kriterien/Risiken:** Konservative Untergrenzen können tatsächlich vorhandene Flüsse absichtlich nicht anzeigen; dadurch wirkt die Grafik unter Umständen leerer als die reale Anlage.
- **Verworfene Alternative:** Exakte Verteilung aus unvollständigen Summenwerten ableiten oder bei fehlenden Informationen weiter animieren; im EPS könnte sonst ungemessene Generatorleistung fälschlich PV/Batterie zugeordnet werden.
- **Fortgeltende Bedingungen:** Nur Anzeige, nicht Grundlage für Lastabwurf/Abrechnung/Steuerung; im EPS keine ungemessene Erzeugerquelle behaupten.
- **Stand:** `inferDirectFlows` in `frontend/flow-model.mjs` implementiert; Live-Abnahme der Pfade offen.
- **Nachweis:** `https://github.com/riederch/ha-apps/blob/main/custom_components/local_ems/frontend/flow-model.mjs`.

## D-05 – Zentraler Batterie-Vorzeichenentscheid / Fix `0.5.0b7`

- **Problem:** Minimal-YAML `type: custom:local-ems-flow-card` zeigte Batterie-Richtung trotz EMS-Konfiguration falsch: HA-Energy-Dashboard-Batteriehelfer hatte Vorrang, daher wurde `battery_power_invert` ignoriert.
- **Entscheidung:** Bei automatisch konfigurierter Batterie Local-EMS-Sensor, dessen Invertierungsoption und gekoppelten SoC priorisieren; Netz- und PV-Quellen weiterhin nach Energy-Dashboard-Priorität; explizite Kartenmodi `energy`/`ems`, Override `invert_battery_power` und vollständig manueller PFCP-Modus bleiben möglich. [C/G]
- **Positive Kriterien:** Ein Ort für die Batterie-Polarität; Standardkarte ohne Doppelkonfiguration; richtige SoC-Quelle; vorhandene Energy-Dashboard-Netz-/PV-Abbildung bleibt erhalten; Rückwärtskompatibilität durch explizite Modi.
- **Negative Kriterien/Risiken:** Geänderte Default-Priorität kann bei abweichenden HA-Energy- und EMS-Sensoren das angezeigte Signal ändern; gemischte Quellen können nicht jede Bilanz automatisch physikalisch validieren; ohne reale Lade-/Entladeprobe keine belastbare Vorzeichenabnahme.
- **Betrachtete Alternativen:** `source_mode: ems` als per-Karte-Workaround [C/G] – löst Vorzeichenproblem nur bei manueller Konfiguration und schaltet **alle** Quellen um; `source_mode: energy` als bewusste Energy-Quelle; YAML-`invert_battery_power` als Override statt Standard; vollständig manuelle `entities.battery.invert_state` für Sonderfälle.
- **Signalkonvention:** Local EMS Batterie **+ = Entladung, − = Ladung**; PFCP erwartet **+ = Ladung, − = Entladung**, daher wendet Adapter das Vorzeichen. Netz **+ = Bezug, − = Einspeisung**; W/kW explizit konvertieren; fehlende Werte `unavailable`, nicht `0`.
- **Fortgeltende Bedingungen:** Kein stiller Quellwechsel gegen EMS-Vorzeichenentscheidung; keine neuen HA-Entitäten/Steuerbefehle; SoC derselben Quelle; das Standard-YAML bleibt einzeilig.
- **Umsetzung:** GitHub PR #47 gemergt 15.11.2026, Merge `3e3c3067b9206fc9ab8431fd0942f5d3a308612c`, `manifest.json` `0.5.0b7`, automatisierte Tests auf Merge-Commit grün.
- **Offen:** HACS-Update/Browser-Neuladung und reale Lade-/Entladephasen (bei gewünschtem Rohsensor `sensor.sofar_batterie_1_leistung`) nicht geprüft; tatsächliche Rohvorzeichen zuerst messen.
- **Quellen:** `https://github.com/riederch/ha-apps/pull/47`; `https://github.com/riederch/ha-apps/blob/main/docs/local-ems-flow.md`.

## D-06 – Trennung von UI und Netz-/EPS-Sicherheitslogik

- **Problem/Ziel:** Bei Netzausfall oder fehlerhaftem Smartmeter keine gefährliche/irreführende Flussdarstellung und keine unzulässige Aktorik.
- **Entscheidung:** Energy-Flow-Karte verwendet reine virtuelle Browser-Zustände ohne Recorder oder Steuerschreiben; `eps`/`grid_lost`/negativer Netzkontakt ergibt Outage-Anzeige, Netzleistung in Darstellung `0`, keine alten Flusspfeile; Generator ohne Messung nicht bilanziert. [G]
- **Positive Kriterien:** Anzeige bleibt vom EMS-Core und von EPS-Schutzeinrichtungen getrennt; keine zusätzlichen echten HA-Sensoren; falsche Smartmeter-Animation beim Ausfall vermieden.
- **Negative Kriterien/Risiken:** Die Anzeige kann ungemessene Generatorleistungen nicht darstellen und darf nicht als Sicherheitsdiagnose missverstanden werden.
- **Verworfene Alternative:** UI-Karte als Sicherheits- oder Schaltmechanismus verwenden; fehlende Quellen als reale Nullproduktion interpretieren.
- **Fortgeltende Bedingungen:** Nur zugelassener Sofar-Betriebsmodus „Self Consumption“ für EMS-Freigabe [R]; keine EPS-Sicherheits-/Generatorsteuerung durch die Karte.
- **Stand:** Adapter-/Dokumentationscode vorhanden; Live-EPS-Sichtprüfung nicht nachgewiesen.
- **Nachweis:** `https://github.com/riederch/ha-apps/blob/main/docs/local-ems-flow.md`.

## D-07 – Sofar-Modbus-Schreibfehler separat, keine blind wiederholten Aktionen

- **Problem:** FC16/Schreiben auf Register `4368` quittiert mit Timeout oder Antwortabweichung, obwohl das Gerät teilweise tatsächlich übernommen hat. [R]
- **Vorentscheidung:** Bestehende serialisierte Read/Write-Sperre reicht für Gleichzeitigkeit; keine zusätzliche Queue; bei Schreibfehlern den tatsächlichen Zustand per Readback verifizieren, statt blind zu wiederholen. [R]
- **Positive Kriterien:** Kein zusätzlicher Komplexitätslayer, geringeres Risiko doppelter Schaltungen; Zustand wichtiger als fehlerhafte Modbus-Quittung.
- **Negative Kriterien/Risiken:** Readback benötigt Zeit und kann selbst ausfallen; Recovery nach mehrfachen Lese-Timeouts/Cooldown wurde historisch besprochen, aber der aktuelle Produktivstand ist nicht geprüft.
- **Verworfene Alternativen:** Zusätzliche separate Queue trotz vorhandenem Lock; globale Lockerung der Modbus-Response-Validierung; blindes Retry nach vermeintlichem Fehler.
- **Fortgeltende Bedingungen:** Sofar-Schreibpfad ist ein getrenntes Integrationsproblem; dieser Stand bedeutet **keine** produktive Freigabe oder behobenen Schreibfehler.
- **Status:** Rekonstruierter Vorgängerchat, aktueller Patch/Upstream-PR/Live-Test nicht nachgewiesen.
- **Herkunft:** Vorgängerchat „Sofar Home assistant patch“; kein belegter aktueller Repo-Commit in diesem Gespräch.

## D-08 – Ein Chat, eine Karte, Gründe nicht nur als Commit-Liste

- **Problem/Ziel:** Die anfängliche Fokussierung auf Archivierung und Commit-Hashes drohte den ursprünglichen Gesprächskontextverlust zu verdecken.
- **Entscheidung:** Vorliegende Karte aus dem Selbstanwendungs-Paket **fortschreiben**, keine zweite Chatkarte; frühere thematische Entscheidungen mit Begründung, Alternativen und Status aufnehmen; andere Chats/Karten nur lesen und referenzieren. [C]
- **Positive Kriterien:** Kontinuierlicher Zustand je Chat, weniger konkurrierende Änderungen, Fäden über Themenwechsel hinweg wiederaufnehmbar; die umfangreiche Abwägung bleibt separat erreichbar.
- **Negative Kriterien/Risiken:** Historische Vorgängerchats nur teilweise als rekonstruierte Ausschnitte verfügbar; dieses Paket darf keine Belegvollständigkeit vortäuschen; Karten-/Paketpflege erfordert verifizierte Ablage.
- **Verworfene Alternativen:** Neue eigenständige Karte allein für Local EMS trotz bestehender Chatkarte; parallele Änderung fremder Karten; bloße chronologische Chat-Zusammenfassung ohne Entscheidungsgründe.
- **Fortgeltende Bedingungen:** Keine zweite Projektdokumentation und keine neue Steuerungsentscheidung allein durch Kartenpflege; `gespraechskarte.md` ist einziger führender Einstiegspunkt.
- **Stand:** Diese Karte erstellt; tatsächliche dauerhafte Ablage erst nach Upload und Lesetest gesichert.
- **Nachweis:** `quellen/gespraechskarte-arbeitsanweisung-1.3.md`, `quellen/gespraechskarte-vorheriger-snapshot.md`.

## D-09 – Addendum A1 kontrolliert auf die lokale Local-EMS-Fortsetzung anwenden

- **Ausgangsproblem:** Die erste Gesprächskarte rekonstruierte verfügbare Vorgänger, prüfte aber nicht chronologisch je Chat mit vollständigem Quellen- und Löschbereitschaftsregister. Späterer Kontextverlust könnte ursprüngliche Kriterien erneut verdrängen.
- **Entscheidung:** A1 als **Erprobungsentwurf** auf die bisher erkennbare fachliche Kette „SG Ready erklärt“ → aktueller Batterievorzeichen-Chat anwenden; mit der **einen bereits existierenden führenden Karte** fortfahren; chronologisch ab ältestem Ursprung prüfen, Quellenlücken dokumentieren. Keine generelle Regeländerung v1.3/1.4. [C/R]
- **Positive Kriterien:** Frühere Anforderungen und Ablehnungsgründe bleiben auch nach späteren Git-/UI-Änderungen sichtbar; kein unkontrolliertes Zusammenwerfen aller Chats eines Projekts; strukturierte Nachprüfbarkeit und Status je Quelle.
- **Negative Kriterien / bewusst akzeptiert:** Historische Volltranskripte sind hier nicht vollständig zugänglich; Rekonstruktion ist ein vorläufiges, nicht zur Löschung berechtigendes Ergebnis; zusätzliche Pflege verursacht Aufwand und parallel bearbeitete Themen bleiben getrennt.
- **Abgrenzung:** „Sofar Home assistant patch“ ist ein eigenständiger Zulieferfaden, kein historischer Local-EMS-Ursprung; Arbeitsanweisung ist methodischer Nebenfaden des aktuellen Chats. Ein Chatwechsel aufgrund eines *vollen Kontextfensters* ist im Local-EMS-Fall bislang nicht direkt belegt.
- **Verworfene Alternativen:** Alle thematisch verwandten Chats automatisch zu einer einzigen Projektkarte verschmelzen (überschreibt unabhängige Arbeitsstränge); ausschließlich jüngsten Code-/CI-Stand aufzeichnen (verliert Gründe); aus Rekonstruktionsannahmen nachträgliche Löschfreigabe ableiten.
- **Fortgeltende Bedingungen:** `gespraechskarte.md` bleibt führend; Git-/Projektquellen bleiben maßgeblich für Code; kein fremder Chat wird verändert; Quellennachweis muss zwischen direktem Original, Rekonstruktion und Git unterscheiden. Für A6-Löschbereitschaft sind Originalabdeckung, Speicherung mit Wiederlesen, unabhängiger Test und Benutzerfreigabe erforderlich.
- **Umsetzung:** `quellen/a1-stufe-1-ursprung.md` (ältester gesicherter Teil), `quellen/a1-chronologie.md`, `quellen/a1-quellenregister.md`, `tests/a1-loeschbereitschaft.md` sowie diese Karte; A1-Stufe 1 bereits separat in der Library gesichert und wieder gelesen.
- **Status:** **Erprobung mit dokumentierten Lücken**; nicht unabhängig bestanden, keine Löschfreigabe.

## D-10 – Netzbetreiber-/Schutzvorgaben vor lokaler EMS-Optimierung [R]

- **Ausgangsfrage:** „SG Ready erklärt“, 01.11.2026: Gibt es ein einheitliches Konzept, das Netzbetreiber-Signale, PV-Überschuss und Spitzenvermeidung koordiniert?
- **Belegter Nutzerwunsch:** Ein zusammenhängender Ansatz statt unabhängiger Automationen; Sofar, lokale Geräte und Netzvorgaben müssen zusammenspielen.
- **Damals vorgeschlagener Entwurf (nicht alles beschlossen):** Netz-/Schutzpflichten und Anschlussgrenzen zuerst; darunter Notstromreserve, Peak-Shaving, PV-Überschuss, Wirtschaftlichkeit. Schutz- und Netzbetreiber-Schnittstellen dürfen **nicht** durch gewöhnliche HA-Automationen fingiert werden.
- **Positive Kriterien:** Rechts-/Schutzvorrang, klare Sicherheitsgrenzen, Herstellerunabhängigkeit, Erweiterbarkeit des späteren EMS.
- **Negative Kriterien / Gegenargumente:** Nicht alle Geräte unterstützen SG Ready/EEBUS/OpenADR; keine bestätigte kombinierte Sofar-PCC-/Self-Use-Konfiguration. Höhere Komplexität und unklare Schnittstellenverfügbarkeit.
- **Zurückgestellte Alternativen:** SG-Ready-Kontakte als universelle vollständige Lösung behandeln; Home Assistant unmittelbar als zugelassenen Netzschutzregler verwenden.
- **Fortgeltende Grenze:** Konkrete Netzbetreiberanforderungen/gerätebezogene Funktionen vor Implementierung separat nachweisen. Bisher keine Freigabe zur externen Netzregelung.
- **Belegstatus:** Selektive Gesprächsfragmente/Assistentenmodell, vollständige historische Freigabe nicht nachgewiesen; siehe `quellen/a1-wiedergefundene-fragmente.md`.

## D-11 – Wiederverwendbare HA-Integration statt verstreuter YAML-Steuerlogik [R/G]

- **Problem:** KNG/Sofar/HA-Daten sollen für Peakmonitor und spätere Verbraucher-/Wallbox-Funktionen zentral bereitstehen.
- **Nutzerforderung vom 02.11.:** „Fertiges Paket“ statt dieselben Entitäten in jedem YAML; HA-Recorder/Statistics als Datenspeicher; HACS/UI-native Entitäten und keine zweite Verbrauchshistorie.
- **Umgesetzte Architektur:** `custom_components/local_ems` als Home-Assistant-Custom-Integration im `ha-apps`-Repository, mit Geräte-/Quelleneinrichtung über UI; spätere Module zunächst konzeptionell.
- **Positive Kriterien:** Zentrale Konfiguration, eindeutige Sensor- und Vorzeichenmetadaten, Weiterverwendung vorhandener Historie, keine YAML-Doppelpflege.
- **Alternativen und Grenzen:** Node-RED, n8n und andere Orchestrierung wurden im Ursprung **diskutiert**, aber nicht belegbar pauschal ausgeschlossen. HA-Funktionsumfang hängt von Sensorverfügbarkeit und Recorder-Qualität ab.
- **Status:** Grundarchitektur durch Code/Git nachgewiesen; kein Nachweis einer endgültigen Entscheidung gegen Node-RED/n8n für spätere Aktorik.
- **Quellen:** `quellen/a1-wiedergefundene-fragmente.md`, `https://github.com/riederch/ha-apps/blob/3e3c3067b9206fc9ab8431fd0942f5d3a308612c/docs/local-ems.md`.

## D-12 – Sofar TCP-Link-Recovery als unvalidierter Kandidat, getrennt von Modbus-Schreibquittungen [R/F]

- **Ausgangsproblem:** Modbus-TCP-Sitzung kann trotz offener Verbindung nicht mehr antworten; Integration-Neuladen stellt zeitweise Betrieb wieder her.
- **Technischer Testkandidat:** `quellen/originale/sofar_modbus_coordinator_patch_2026_10.zip` – im README ist die gezielte `disconnect()`-Wiederherstellung nach **drei vollständig fehlgeschlagenen Leseaktualisierungen** mit Timeout dokumentiert, mindestens **180 Sekunden** zwischen Resets. Teilweise erfolgreiche Abfragen setzen den Fehlerzähler zurück. Nur Readings-Coordinator, nicht Settings-Coordinator.
- **Begründung pro:** Kein ständiges manuelles Neuladen, keine Verbindungsreset-Stürme, keine Nebenwirkung bei einem einzelnen defekten Registerblock; keine Steuer-Registeränderung.
- **Nachteile/Gegenargumente:** Ursache der TCP-Stille unbekannt; vorschnelles Reconnect könnte bestehende Teilerfolge stören; Test nur unter passender HA-Core-Version und mit Hardwareabnahme sinnvoll.
- **Keine Gleichsetzung:** Fehler `write_registers(4368,...)` mit `Device response does not match request` ist ein **anderes** Problem. Die Recovery-ZIP enthält laut README keine bestätigte Reparatur für diesen Fehler.
- **Status:** Patchpaket und Tests vorhanden, **keine** erfolgreiche Hardwareinstallation / Upstream-Freigabe verifiziert; Herkunftszuordnung S1 aufgrund zeitlicher Nähe nur mutmaßlich.
- **Beleg:** `quellen/a1-anlagenregister.md`, Patch-README im Original-ZIP.

## D-13 – Historische Vorläufer wahren, ohne Vorschläge zu Beschlüssen umzudeuten [R]

- **Beobachtung:** Bereits 2025 wurde ein HA-EMS-Szenario skizziert; am 21.07.2026 schlug der Assistant „QuarterPeak“ für 15-Minuten-Lastmanagement vor, inklusive Energie-Budget und dynamischer Lastprioritäten.
- **Belegbarer Nutzerbeitrag:** Frage nach Sofar HYD20KTL und Korrektur der Viertelstunden-Interpretation `2,8 × 4`.
- **Abgrenzung:** Weder Name „QuarterPeak“ noch vorgeschlagene Grenzwerte, SoC-Ziele oder Node-RED-Regelstrategie sind dadurch automatisch verbindliche Local-EMS-Designentscheidungen. Das konkrete 2026er Local EMS hat später eigene explizite Nutzeranforderungen und Git-Historie erhalten.
- **Warum diese Abgrenzung:** Sonst könnten frühere Alternativentwürfe bei einer späteren Kontextverdichtung fälschlich als beschlossene Architektur übernommen werden.
- **Status:** Konzeptioneller Quellhinweis; ältere Originalchat-IDs/-Vollfassungen nicht verfügbar; für diese A1-Fortsetzung keine automatische Löschfreigabe.
- **Fundstellen:** `quellen/a1-wiedergefundene-fragmente.md` sowie spätere S1-Gesprächsrekonstruktion.