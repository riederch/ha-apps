# Gesprächskarte – Kontextkontinuität / Local EMS

- **Chatkennung:** `gespraechskarte-arbeitsanweisung-2026-11-15` (bestehende lokale Kennung aus dem 1.3-Selbstanwendungs-Paket; technische Chat-ID nicht verfügbar)
- **Projekt/Thema:** Local EMS / Home Assistant, Energieflusskarte, Batterie-Vorzeichen; Arbeitsanweisung 1.3 als abgeschlossener Nebenfaden
- **Stand:** 2026-11-15 (A1-Vertiefung um historische Nebenfäden/Dateiquellen; Chat aktiv, keine Löschfreigabe)
- **Status:** aktiv; kein Abschluss oder Wechsel in ein anderes Gespräch erklärt
- **Betriebsmodus:** A – ChatGPT-Dateibibliothek; fortlaufende Speicherung und Wiederlesen verifizieren
- **Führende Ablage:** `/Gespraechskarten/gespraechskarte-arbeitsanweisung-2026-11-15/gespraechskarte.md`
- **Entscheidungsbegründungen:** `entscheidungen/entscheidungsprotokoll.md`; detaillierte Herkunft: `quellen/vorgaengerchats.md`
- **Ursprung der Karte:** Fortführung der **einen** Gesprächskarte aus dem 1.3-Selbstanwendungs-Paket (`quellen/gespraechskarte-vorheriger-snapshot.md`), keine zweite Chatkarte
- **Quellenklassen:** `G` = GitHub-Datei/PR/CI am 15.11.2026 geprüft; `C` = Aussagen dieses Chatverlaufs; `R` = rekonstruierte Vorgängerchat-Ausschnitte; `U` = ungeprüft/fehlend

## Fokus jetzt

1. **A1-Erprobung fortsetzen:** Die logische Local-EMS-Fortsetzung (S1 → S2) ist chronologisch aus erreichbaren Ausschnitten und Git-Evidenz aufgearbeitet. Originaltranskripte fehlen, die Originalverfügbarkeit ist weiterhin unvollständig; Löschbereitschaft **gesperrt**. Siehe A1-Register und Prüftabelle.
2. Local EMS `0.5.0b7` am realen Sofar/KNG-System abnehmen: HACS-Installation, Batterie-Vorzeichen, SoC und originale PFCP-Flüsse; CI allein genügt nicht.
3. „Runner“-Fehler mit Originalmeldung einem konkreten Job zuordnen; frühere Designgründe bei Folgeänderungen beachten.

## A1 – Quellen-/Vollständigkeitsregister (Erprobung, keine Löschfreigabe)

| Quelle | Rolle/Zeitstellung | Erreichbarkeit und Übernahme | A1-Prüfung / Löschbereitschaft |
| --- | --- | --- | --- |
| **S1 „SG Ready erklärt“** | Implementierungsursprung; Chat ab 01.11., Local-EMS-Inhalte 02./08.11.2026; ältere konzeptionelle Vorläufer getrennt | **Teilweise**, chronologisch rekonstruiert; keine vollständige Chat-Originalfassung; Quellen `quellen/a1-stufe-1-ursprung.md` und `quellen/a1-chronologie.md` | Intern gegen Git geprüft; weitere SG-Ready-/Sofar-Nebenfäden nur fragmentarisch; **gesperrt** |
| **S2 Dieser Chat** | fachliche Fortsetzung ab 15.11.2026; Batterie-Vorzeichen und methodischer Nebenfaden | Früher Chatabschnitt nur teilweise wiedergegeben, weitere Beiträge direkt zugänglich; PR #47 bestätigt | Intern abgeglichen, unabhängiger Test fehlt; **gesperrt** |
| **Z1 „Sofar Home assistant patch“** | seit 14.10.2026, **separater** Zulieferfaden | Nur rekonstruierte Ausschnitte, kein stilles Zusammenführen | Nicht vollständig geprüft; **gesperrt** |

- **A1-Ergebnis:** S1 → S2 ist die bisher bekannte fachliche Local-EMS-Fortsetzung; frühere allgemeine EMS-Vorläufer (2025/Juli 2026) sind gesonderte Referenzen, aber weder vollständige Chatkette noch Kontextfenster-Ursache des Wechsels sind nachgewiesen. Details und Herkunftsgrenzen in `quellen/a1-quellenregister.md`; A6-Prüfung in `tests/a1-loeschbereitschaft.md`.
- **Entscheidungsgründe:** Weiterhin nur im führenden `entscheidungen/entscheidungsprotokoll.md` (D-01 bis D-13); keine zweite Projektdokumentation.
- **Addendum-Status:** A1 ist ein Erprobungsentwurf, weder Version 1.4 noch automatische Löschung noch Aktivierung für alle Chats.

## Gesprächsfäden

### T1 – Batterie-Vorzeichen aus Local EMS (aktiv; Implementierung abgeschlossen, Praxisabnahme offen)
- **Ziel:** Die Standardkarte verwendet den zentral konfigurierten Batteriesensor inklusive Batterie-Umkehr und zugeordnetem SoC, ohne redundante YAML-Einstellungen.
- **Ausgangspunkt:** `custom:local-ems-flow-card` übernahm in der automatischen Quellenwahl den Energy-Dashboard-Batteriehelfer statt des EMS-Sensors; `invert_battery_power` aus der EMS-Konfiguration wirkte dadurch nicht wie erwartet. [C/G]
- **Entschieden:** Bei konfiguriertem EMS-Batteriesensor hat dessen Quelle samt Vorzeichen und SoC in Auto Vorrang; Netz/PV dürfen weiter die Energy-Dashboard-Quellen verwenden. Explizite `source_mode: energy`, `source_mode: ems` und manuelle Quellen bleiben möglich. [C/G; D-05]
- **Kerngrund:** Eine zentrale EMS-Batteriekonfiguration darf durch eine implizite, abweichende Dashboard-Quelle nicht überstimmt werden. Die vorhandenen Netz-/PV-Quellen sollen unverändert nutzbar bleiben.
- **Umgesetzt:** `riederch/ha-apps` PR #47, `0.5.0b7`, Merge `3e3c3067b9206fc9ab8431fd0942f5d3a308612c`; GitHub Actions auf `main` grün. [G]
- **Kontextnachweis:** `gesichert` – D-05 mit Alternativen, Code-/Dokumentverweisen; Umsetzungsnachweis unter `nachweise/stand-und-abnahme.md`.
- **Offen:** Version in HACS/HA tatsächlich installiert? Positives/negatives Rohsignal bei Laden und Entladen prüfen; SoC, Source-Mapping und Richtung der PFCP-Pfeile gegen Rohsensor testen.
- **Nächster Schritt:** Ist-Installation und je eine reale Lade-/Entladephase nach Abnahmeplan kontrollieren; Befunde mit Messwert und Zeitstempel festhalten.
- **Verweise:** https://github.com/riederch/ha-apps/pull/47; https://github.com/riederch/ha-apps/blob/main/docs/local-ems-flow.md

### T2 – Original-Power-Flow-Card-Plus und Direktflüsse (aktiv; Code vorhanden, visuelle Abnahme offen)
- **Ziel:** Originaldarstellung und -logik samt Animationen/Bubbles, volle Breite, Flüssen PV→Batterie, Netz→Batterie, Solar→Netz; korrektes Verhalten bei fehlenden Quellen/EPS.
- **Entschieden:** Original-Renderer/-Editor PFCP `0.4.0-beta.1` integriert statt `power-sankey` oder eigener SVG-Nachbildung; MIT-Credits und Lizenzhinweise. [R/G; D-03]
- **Kerngrund:** Der Nutzer lehnte Sankey-Darstellung und den visuellen Nachbau ab; Original-UI/-Berechnung entspricht dem geforderten Verhalten besser.
- **Entschieden:** Direkte Pfade nur als konservative Mindestflüsse aus bekannten Werten ableiten; bei unklarer Herkunft, Datenlücken oder EPS keine unbelegte Animation. [R/G; D-04]
- **Kerngrund:** Summenleistungen beweisen keine exakte Herkunft; ein unbeobachteter Generator im EPS-Fall verbietet sichere Quellenzuordnung.
- **Umgesetzt:** Upstream-Bundle mit Adapter im Repository; Werte für PFCP als reine Browser-Objekte, keine neuen HA-Entitäten. [G]
- **Kontextnachweis:** `gesichert` – D-03/D-04, Dokumentation und `flow-model.mjs`.
- **Offen:** Echte UI-Prüfung PV→Batterie, Netz→Batterie, PV→Netz, Leer-/Negativwerte und EPS; gewählte Darstellungsdetails mit dem Original vergleichen.
- **Nächster Schritt:** Reale PV-/Netz-/Batterieszenarien dokumentiert prüfen; bei Inkonsistenzen Code-/Datenursache trennen.

### T3 – Local-EMS-Grundarchitektur / Viertelstundenmonitor (wartet; getrennte Funktionsabnahme)
- **Ziel:** Herstellerneutrale, zunächst **nur lesende** Überwachung einer festen 15-Minuten-Netzbezugsspitze; 10-kW-Grenze, anfangs 9-kW-Warnung, Prognose und Datenqualität.
- **Entschieden:** HA-Custom-Integration in `riederch/ha-apps`, HA Recorder/Statistics statt eigener Verbrauchsdatenbank oder direkter SQL-Abfragen; KNG-Netzbezugsquelle über UI. [R/G; D-01/D-02]
- **Kerngrund:** Bereits vorhandene HA-Quellen wiederverwenden, keine parallele Datenhaltung und keine ungesicherte Netzregelung.
- **Entschieden:** `unknown`/Datenlücke nicht als null interpretieren; Peaks vor abrechnungsrelevanter Verwendung mit Kärnten-Netz-Viertelstundenwerten vergleichen. [G]
- **Umgesetzt:** Peak-Monitor, Statusentitäten, UI-Geräteverwaltung und Gauge im Repository dokumentiert; keine Bestätigung der vollständigen Live-Abnahme. [G]
- **Kontextnachweis:** `gesichert` – D-01/D-02 und verifizierte Repo-Dokumentation.
- **Offen:** Abgleich offizieller Viertelstundenwerte; HA-Laufzeit-/Langzeittest. Aktive Steuerung, Wallbox-/PV-Optimierung später, kein Teil dieses Vorzeichen-Fixes.
- **Nächster Schritt:** Bei Wiederaufnahme eigene Abnahmedaten und Datenqualitätsgrenzen prüfen, nicht aus erfolgreich durchgelaufener CI auf Netzvertragskonformität schließen.

### T4 – Sofar Modbus-Schreibfehler (geparkt; eigener Vorgängerchat)
- **Ziel:** Schreiben von Sofar-Moduswerten ohne falsche Fehleranzeige, Doppelbefehle oder unbeabsichtigte Folgeschaltungen.
- **Historischer Befund:** `write_registers(4368, [0])`/FC16 meldete Timeout bzw. `Device response does not match request`, obwohl Wert teilweise nachweislich geschrieben wurde. [R]
- **Vorentscheidung:** Bestehenden Read/Write-Lock statt zusätzlicher Queue nutzen; bei Schreibfehler Readback, nicht blind wiederholen oder Modbus-Antwortprüfung pauschal lockern. [R; D-07]
- **Kerngrund:** Ungültige/überlange Sofar-Antwort und tatsächlicher Schreibzustand sind getrennt; Retry birgt Doppelbefehlsrisiken.
- **Kontextnachweis:** `teilweise gesichert` – rekonstruierter Vorgängerchat, keine aktuelle Verifikation des Patch-/PR-Status.
- **Offen:** Praxisabnahme und tatsächlicher Repo-/Upstream-Stand in eigenem Faden; nicht mit Frontend-Batterievorzeichen gleichsetzen.
- **Verweis:** Vorgängerchat „Sofar Home assistant patch“; keine fremde Gesprächskarte verändert.

### T5 – Runner-Fehlermeldung (wartet; Ursache ungeklärt)
- **Ausgangspunkt:** Nutzer meldete „Fehler“ und präzisierte „Beim runner“. Keine konkrete Fehlermeldung, Job-ID oder eindeutige Runner-Zuordnung übermittelt. [C]
- **Bisheriger Befund:** Die GitHub-Actions-Läufe von PR #47 und dem `main`-Merge sind erfolgreich. Ein früherer CI-Versionsabgleich b6/b7 wurde korrigiert. [G/C]
- **Nicht entschieden:** Dass der Fehler den selbst gehosteten Gitea Runner betrifft, ist lediglich eine frühere Hypothese; keine Ursachenbestätigung.
- **Kontextnachweis:** `teilweise gesichert` – gemeldetes Symptom erhalten, Fehlerbeleg fehlt.
- **Offen/Nächster Schritt:** Betroffenen Runner/Job und Originalfehler zuordnen; keine Änderung oder „behoben“-Markierung ohne Log und Reproduktion.

### T6 – Arbeitsanweisung 1.3 und A1-Selbstanwendung (Version 1.3 fachlich erledigt; A1-Erprobung aktiv)
- **Ziel:** Ursprüngliche Entscheidungen und Gründe trotz langer Chats schützen; Archivierung/Übergabe ausdrücklich nachrangig.
- **Entschieden:** Eine Karte je Chat, vollständige wesentliche Abwägungen an einem maßgeblichen Ort, fortlaufende Sicherung, getrennte Statusachsen, logisches Paket, kontrollierte Selbstanwendung. [C]
- **Kerngrund:** Reine Beschluss- oder Commit-Listen lassen spätere Änderungen ohne Kenntnis ursprünglicher Anforderungen zu.
- **Umgesetzt:** Finale v1.3 und Selbstanwendungs-ZIP im vorangegangenen Gesprächsteil erzeugt; diese Karte setzt denselben Chatstand fort.
- **Kontextnachweis:** `gesichert` – Datei `quellen/gespraechskarte-arbeitsanweisung-1.3.md` und vorheriger Kartensnapshot; zuvor externe Bibliotheksablage noch unbestätigt.
- **A1-Erprobung:** Für S1 → S2 rückwirkende chronologische Quellenprüfung begonnen und nachvollziehbar konsolidiert; historische Originalchat-Abdeckung und unabhängiger Wiederaufnahmetest bleiben offen. [C/R/G; D-09]
- **Offen:** Globale KBF-/Hook-/Codex-Aktivierung sowie unabhängiger Kontext-Wiederaufnahmetest sind nicht nachgewiesen; gesonderter Arbeitsfaden, nicht Teil der Local-EMS-Praxisabnahme.

### T7 – SG Ready, Netzbetreiber-Steuerschnittstellen und EPS-Grenzen (geparkt, eigener Ursprungsteilfaden)
- **Ausgangsfrage S1 (01.11.):** Einheitlicher Ansatz für Netzbetreiber-Steuerung, PV-Überschuss und Peak-Shaving; nicht nur grafische Flüsse. [R; D-10]
- **Unterscheidung:** Verbindliche Schutz-/Netzvorgaben gehören nicht in ungesicherte Home-Assistant-Aktorik; Prioritätenhierarchie war ein Architekturvorschlag, keine abschließend getestete Lösung.
- **Fortgeltend:** EMS herstellerneutral, nur zulässiger Betriebsmodus, EPS-Aktorik sperren; Smartmeter-Ausfall nur ergänzendes Netzindiz. Sofar PCC/SG-Ready/EEBUS-Kompatibilität offen.
- **Nebenfaden:** ISO-Fault wurde im Ursprung ausdrücklich **zurückgestellt**, nicht gelöst. Keine provozierten Netz-/Schaltversuche allein zum UI-Test.
- **Quellen:** `quellen/a1-wiedergefundene-fragmente.md`, D-10, Git-Historie `699f71df7bfe`.

### T8 – Sofar-TCP-Link-Recovery (geparkt; getrennt von T4-Write-Quittung)
- **Beleg:** Originaldatei-Kandidat `quellen/originale/sofar_modbus_coordinator_patch_2026_10.zip` vom 01.11. vorhanden. [F; D-12]
- **Kandidat:** Bei wiederholten vollständigen Modbus-Lese-Timeouts gezielt Verbindung neu öffnen; nicht identisch mit Register-4368-Schreibfehler.
- **Status:** Patch-Dateien/Tests gesichert, **Hardwareprüfung, produktiver Einbau, Chat-Zuordnung und Upstream-Merge nicht nachgewiesen**.

## Parkplatz

- EPS/Generator-Laden und ISO-Fault-Diagnose sind getrennte Sofar-/Sicherheitsthemen; nicht mit dem UI-Fix verknüpfen.
- Modulares PV-/Wallbox-/Batterie-EMS mit aktiven Steuerbefehlen: Zukunftsplanung, aktuell keine Freigabe aus dem UI-Fix.
- Kontextsparsame Kurzfassung der Arbeitsanweisung 1.3: kein hier gefasster Architekturentscheid.

## Übergreifende offene Fragen

- **A1-Volltextblocker:** Für S1 („SG Ready erklärt“) reicht die aktuelle Wiederauffindung selektiver älterer Nachrichten nicht zur vollständigen Prüfung. Ein zusätzlicher früherer Sofar-/SG-Ready-/ISO-Fault-Kontext ist rekonstruiert; Original-Chattext fehlt. `quellen/a1-vollquellen-bedarf.md`.
- **Originaldateien gefunden:** UI-Vergleichsscreenshot vom 02.11. und Sofar-TCP-Recovery-ZIP vom 01.11. sind im Paket erhalten; Chat-Zuordnung nur als Kandidat, nicht als endgültiger Anhangnachweis. Siehe `quellen/a1-anlagenregister.md`.

- Reale HA-Installationsversion und Rohsensor-Vorzeichen am Sofar nicht aus den verfügbaren Nachweisen bestimmbar.
- Ursprüngliche vollständige Vorgängerchat-Transkripte und deren eigene Gesprächskarten nicht vollständig verfügbar; rekonstruierte Aussagen sind keine unabhängigen Primärnachweise. Für S1/S2 ist A1-Löschbereitschaft ausdrücklich **gesperrt**.
- „Runner“ nicht zweifelsfrei identifiziert; keine neuen Rückschlüsse aus erfolgreichen CI-Jobs ziehen.
- Keinen Vorgängerchat ohne ausdrücklichen Abschluss als abgeschlossen einstufen; keine fremden Karten überschreiben.

## Ergebnis / bestätigter Arbeitsstand

- **Belegter Repositorystand:** Local EMS `0.5.0b7` auf `main` nach PR #47; drei GitHub-CI-Workflows bestanden. [G]
- **Gesichertes Entscheidungswissen:** ausführliche D-01 bis D-13 in `entscheidungen/entscheidungsprotokoll.md`; Quellen und Status in Zusatzdateien.
- **Nicht nachgewiesen:** Produktive HACS-Installation, reeller Vorzeichen-/UI-Test, Funktion aller Direktflüsse, präzise Runner-Ursache, Sofar-Modbus-Upstream-Fix.
- **Ablagehinweis:** Maßgeblich ist die nachgewiesen gespeicherte und gelesene Library-Fassung dieses Dokuments; ZIP-Snapshots sind keine separat fortgeschriebenen Karten.
- **A1:** Inhaltliche Rekonstruktion S1→S2 mit dokumentierten Lücken; Originalabdeckung und unabhängiger Wiederaufnahmetest fehlen; **kein Ursprungschat zur Löschung bereit**.
- **Abschluss:** Dieser Chat bleibt aktiv; die Arbeitsanweisung 1.3 ist als Nebenfaden fachlich abgeschlossen, A1-Erprobung und Local EMS nicht.