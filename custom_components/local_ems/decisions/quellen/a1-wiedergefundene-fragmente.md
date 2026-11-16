# A1 – Neu erschlossene Gesprächsfragmente und konzeptionelle Vorläufer

**Stand:** 15.11.2026 · **Quelle:** selektiv wiederaufgefundene Nachrichtenhinweise aus früheren ChatGPT-Gesprächen; **kein vollständiger Originalchat-Export**. Die Angaben sind sinngemäß zusammengefasst, nicht als wörtliche Zitate aus einem geprüften Volltranskript zu verstehen. **[R]** = rekonstruiertes Nachrichtenfragment; **[G]** = GitHub-Commit/Dokument separat überprüft; **[F]** = in Dateibibliothek aufgefundenes Originalartefakt, Zuordnung zu einem Chat nur soweit geklärt.

## S1 – „SG Ready erklärt“ (Beginn 01.11.2026; Originalchat nicht vollständig zugänglich)

| Zeit (UTC, soweit überliefert) | Sprecher | Rekonstruierter Inhalt | A1-Konsequenz |
|---|---|---|---|
| 01.11. 12:33 | Assistant | Recovery-Patch für Sofar/TCP als lokaler Testkandidat; Fehler bei Write-Timeout trotz ausgeführter Aktion weiter offen. | **Eigener Faden** TCP-Link-Recovery, nicht mit Batterie-Flussanzeige verwechseln. Patch-ZIP als möglicher Originalbeleg vorhanden [R/F]. |
| 01.11. 14:54 | User | Frage nach einem einheitlichen Konzept für Netzbetreiber-Steuerbefehle, Überschussbetrieb, Lastspitzenglättung und SG Ready. | Ursprüngliche übergreifende EMS-Zielsetzung, nicht bloß Flow-Card-Projekt [R]. |
| 01.11. 17:45 | User | ISO-Fault-Thema vorerst ausklammern, am EMS weiterarbeiten. | ISO-Fault bewusst **geparkt**, nicht behoben [R]. |
| 02.11. 10:41 | User/Assistant | EMS-Weiterarbeit; vorgeschlagene Priorität Netz-/Schutzvorgaben → Anschlussgrenzen → Notstromreserve → Peak-Shaving → PV-Überschuss → Wirtschaftlichkeit. | Die Priorität ist im gefundenen Material eine **Assistenten-Architekturantwort**, keine unabhängig bestätigte Nutzerfreigabe jeder Stufe [R]. |
| 02.11. 10:45 | User | KNG-Smartmeter mit 14 Entitäten; vollständige Sensorprüfung vorgesehen. | Ursprüngliche Datenquellenwahl, nicht unbesehen jede Entity als aktuell bestätigt verwenden [R]. |
| 02.11. 11:02 | User | Schritt 1: rein lesende Entität für laufenden 15-Minuten-Spitzenwert; Warnschwelle, Prognose bis etwa 10 kW. | Zentrales fachliches Abnahmekriterium des Peakmonitors [R/G]. |
| 02.11. 11:08 | User | Fertiges Paket statt Entitäts-YAML in jeder Karte; Node-RED, n8n und andere Architekturen zur Diskussion. | Generische Integrationsentscheidung; nicht behaupten, der User habe Node-RED/n8n verbindlich ausgeschlossen [R]. |
| 02.11. 11:11 | User | HA Recorder/Statistics soll Verbrauchshistorie verwalten; keine zweite Verbrauchsdatenbank, keine direkten SQL-Abfragen. | Weiterhin harte Datenarchitektur-Anforderung [R/G]. |
| 02.11. 11:19 | User | Local EMS als Grundlage für späteres PV-/Wallbox-/Verbraucher-EMS, mit HACS/UI und nativen Entitäten; zunächst lesend. | Entwicklungsphasen unterscheiden, keine implizite Schaltfreigabe [R/G]. |
| 02.11. 12:59 | User | Bei EPS/Netzausfall EMS-Aktorik sperren; Netz-/Smartmeter-Ausfall berücksichtigen. | Sicherheitsvorbedingung, kein durch UI-Flow-Fix erledigter Test [R/G]. |
| 02.11. 13:06 | User | Herstellerunabhängig; Smartmeter sendet etwa sekündlich, dessen Ausfall ist nur ein zusätzliches Netzindiz; EMS nur im erlaubten Modus „Self Consumption“. | Fortgeltende Betriebsmodus- und Netzstatus-Bedingungen [R/G]. |
| 02.11. 14:09 | User | Vorhandene `custom:power-flow-card-plus` mit Sofar Batterie/SoC (`invert_state: true`), KNG-Netz, PV/Haus/Netz-/WR-Status; zentrale Quellen statt duplizierter Karten-YAML. | Referenzkonfiguration und Vorzeichenproblem erhalten [R]. |
| 02.11. 14:39 | User | `power-sankey` als ungeeignete Darstellung zurückgewiesen; PFCP-Stil verlangt. | Konkreter negativer Entscheidungsgrund [R]. |
| 02.11. 15:07–15:23 | Assistant | Vollbreite und 80-px-Bubbles als umgesetzte UI-Korrekturen berichtet; reale visuelle Prüfung zunächst offen. | Git-Bestätigung 02.11.; CI ist kein HA-Live-Test [R/G]. |
| 02.11. 18:08 | Assistant | Viertelstunden-Istdurchschnitt und automatischer Gauge berichtet. | Implementierung durch Git-Commit gegengeprüft [R/G]. |
| 08.11. 09:32 und 13:27 | User | Netz→Batterie, PV→Netz, PV→Batterie ergänzen und **Originaldarstellung/-logik vollständig** verwenden; Lizenz/Credits aufnehmen. | Spätere bewusste Kurskorrektur gegenüber PFCP-ähnlichem Nachbau [R/G]. |

**Quellengrenze:** Die aufgefundenen Einzelnachrichten liefern keine vollständige Reihenfolge sämtlicher Nachrichten, keine gesicherten Chat-IDs und keinen Nachweis, dass sämtliche Einwände, Bilder und Dateien erfasst sind.

## Frühere fachliche Vorläufer (keine automatisch verschmolzenen Chats)

- **P0 – 04.07.2025, Titel nicht belegt:** Allgemeines EMS-Konzept für Home Assistant mit PV, Batterie, Wallbox/Verbrauchern und Power Flow Card Plus. Der erfasste Beitrag war eine **Assistenten-Antwort**; keine Freigabe für die Implementierung 2026 ableiten [R].
- **P1 – 21.07.2026, Titel nicht belegt:** 15-Minuten-Leistungspreise/Lastmanagement; der Assistant bezeichnete einen Vorschlag als „QuarterPeak“. Energie-Budget `Limit × 0,25 h`, Wallbox-/Last-/Batterie-Prioritäten und Node-RED/HA waren **vorgeschlagene Lösungsbausteine**. Der User fragte nach der Rolle des Sofar HYD 20KTL und korrigierte die Interpretation `2,8 × 4` (2,8 kWh je Viertelstunde entspricht 11,2 kW Durchschnitt). **Kein damaliger Beschluss** für konkrete SoC-Reserven oder 6-/8-kW-Beispielgrenzen [R].
- **P2 – 14.10.2026, Titel „Sofar Home assistant patch“ laut späterer Chatliste:** Sofar-Modbus-/Coordinator-Fragen; weitere Vorschläge zu Lastkoordination wurden erörtert. Die später als Beispiel genannten 4-/6-/9-kW-Werte nicht als bestätigte aktuelle Local-EMS-Grenzwerte übernehmen [R].

**Schluss:** „SG Ready erklärt“ bleibt der **älteste für die konkrete Local-EMS-Implementierung belegte Gesprächsabschnitt**, ist aber **nicht der älteste gedankliche Vorläufer** eines 15-Minuten-HEMS. P0/P1/P2 sind Quellenhinweise, keine Löschfreigabe und keine automatisch konsolidierten A1-Ursprungschats.