# A1 – Chronologische Konsolidierung Local EMS

**Methode:** Ältester erreichbarer Local-EMS-Kern aus „SG Ready erklärt“ zuerst, danach chronologisch neue Anforderungen/Änderungen, schließlich aktueller Chat. Technische Git-Quellen sind ein unabhängiger **Umsetzungsnachweis**, keine vollständige Rekonstruktion der ursprünglichen Begründungen. Die fortschreibbare Übersicht steht ausschließlich in `../gespraechskarte.md`; dieses Dokument ist Herkunfts- und Prüfnachweis.

## Vorlauf (nicht A1-Fortsetzung): frühere Konzepte [R]

- **04.07.2025 (P0):** Home-Assistant-EMS-Idee, PV, Batterie, Wallbox und Power Flow Card Plus; die verfügbare Quelle ist eine frühere Assistenten-Antwort, kein konkreter Local-EMS-Umsetzungsbeschluss.
- **21.07.2026 (P1):** Lastmanagement für österreichische 15-Minuten-Peaks mit vorgeschlagenem Titel „QuarterPeak“; `2,8 × 4` als Korrektur des Viertelstunden-Durchschnitts. Vorgeschlagene SoC-Prioritäten/Grenzen waren nicht bereits vom User freigegeben. Die konkrete Local-EMS-Umsetzung begann nach derzeitiger Quellensicht erst im S1-Chat.
- **14.10.2026 (Z1/P2):** Separater Sofar-Modbus-/Koordinationsfaden. Keine automatische Verschmelzung mit S1 oder Löschfreigabe.

## Stufe 0 – 01.11.2026: übergreifendes EMS, SG Ready und Parken von ISO Fault (S1) [R]

- **Benutzeranlass:** Einheitliches Konzept für Netzbetreiber-Steuerbefehle, Überschuss, Spitzenglättung und SG Ready; zugleich Sofar-Recovery/ISO-Fault-Fragen als weitere Teilfäden.
- **Assistenten-Architekturidee (nicht bereits freigegeben):** Netz-/Schutzvorgaben vor Anschlussgrenzen, Notstromreserve, Peak-Shaving, Überschuss und Wirtschaftlichkeit; geeignete externe Netzvorgabe-Schnittstellen sind von Home-Assistant-Automationen zu trennen.
- **Explizite Benutzerabgrenzung:** ISO-Fault-Thema vorerst zurückstellen und am EMS weiterarbeiten – kein Fehlernachweis oder Abschluss.
- **Wiedergefundener Artefakt-Kandidat:** `originale/sofar_modbus_coordinator_patch_2026_10.zip`; **separater** TCP-Verbindungs-Recovery-Entwurf, der eine offene Modbus-TCP-Sitzung nach wiederholten *vollständigen* Leseausfällen zurücksetzen soll. Er ist nicht hardwarevalidiert und behebt nicht automatisch den Write-Timeout.
- **Quellen:** `a1-wiedergefundene-fragmente.md`, `a1-anlagenregister.md`, D-10/D-12.

## Stufe 1 – 02.11.2026: ursprüngliches Problem und Grundarchitektur (S1)

- **Primärziel:** Zeitnahe Warnung vor einer Überschreitung der 15-Minuten-Netzbezugs-Spitze, nicht sofortige Netzregelung. Anfangs 10-kW-Grenzwert und 9-kW-Warnung. [R/G]
- **Festlegung:** HA-Custom-Integration Local EMS, herstellerneutral, vorhandene Entitäten/Recorder/Statistics statt eigenem Archiv oder SQL; KNG-Bezugsenergie für feste Viertelstunden. [R/G]
- **Warum:** Früher Kontext sollte ohne redundante Datenerhaltung und ohne gefährliche erste Aktorik in ein modular erweiterbares System münden. Sofar nur optionale Quelle. [R/G]
- **Zurückgestellt:** aktive Laststeuerung, Batterie-/Wallbox-Ansteuerung, Ersatz von Netzschutzfunktionen. [G]
- **Gegenargumente / Restrisiken:** Recorder-Datenlücken, Schätzungen an Zeitfenstergrenzen, Datenqualität und offizielle Viertelstundenwerte – Prognose niemals als amtlich verifizierte Messung ausgeben. [G]
- **Git-Prüfung:** `a5398f2e70` 02.11.2026 HA-Peakmonitor; `7cb8ca657b` Klassifikation `integration_type: hub`; `699f71df7b` herstellerneutrale Statuslogik; `54a9734829` Quarter-average und Gauge.
- **Quelle:** `a1-stufe-1-ursprung.md`, `../entscheidungen/entscheidungsprotokoll.md` D-01/D-02, `https://github.com/riederch/ha-apps/blob/3e3c3067b9206fc9ab8431fd0942f5d3a308612c/docs/local-ems.md`.

## Stufe 2 – 02.11.2026: Energiefluss-Dashboard, Darstellung und Sensorquellen (S1)

- **Erweiterter Bedarf:** Datenflusskarte mit vorhandenen W-/kW-Sensoren sowie Sofar-/EPS-/Netzstatus; voller Platz der Lovelace-Sections-Ansicht, feste Bubbles und verständliche Richtungen. [R/G]
- **Abwägung:** `power-sankey` entspricht nicht dem gewünschten visuellen Modell; Power-Flow-Card-Plus-Stil bevorzugt. Der damalige Nachbau war **noch nicht** die endgültige Entscheidung für Original-PFCP. [R]
- **Git-Prüfung:** `46679d06c8` integrierte Flow-Karte, `3e3447c852` PFCP-Stil, `37bc34eea2` Vollbreite und `7f6e16eedc` feste Bubbles.
- **Bewahrte Grenze:** keine echten zusätzlichen Energiefluss-Entities als Nebenarchiv, keine aktorische Netz-/EPS-Verantwortung der Karte. [G]

## Stufe 3 – 08.11.2026: direkte Flüsse und Original-PFCP (S1)

- **Neue Anforderung:** PV→Batterie, Netz→Batterie und PV→Netz darstellen. [R]
- **Entscheidungsgrund:** Aus aggregierten Messwerten lässt sich die physikalisch exakte Herkunft nicht generell herleiten; darum nur konservative **Mindestflüsse**, bei fehlenden Quellen oder EPS keine erfundenen Flüsse. [G]
- **UX-Kurskorrektur:** Nutzer verlangte vollständige **Original-Logik und Original-Darstellung** statt des früheren visuellen Nachbaus; Credits/Lizenz berücksichtigen. [R]
- **Neue Umsetzung:** Original-PFCP `0.4.0-beta.1` (statt stabilem `0.3.7`) mit Adapter, originalem Renderer/Rechner/Editor; MIT-Hinweise; Local EMS behält seinen Kartentyp und nutzt reine Browser-Sensoren. [G]
- **Nachteile:** Fremd-Bundle-Versionspflege und Adapter-Komplexität; konservative Mindestflüsse können tatsächliche, aber nicht beweisbare Transfers ausblenden. [G]
- **Git-Prüfung:** `aaa1e88058` Netz→Batterie/PV→Netz, `5b42ea5b2e` Flussmodell-Fix, `ab55fa813f` PV→Batterie, `d0b8839575` Original-PFCP.
- **Quelle:** `../entscheidungen/entscheidungsprotokoll.md` D-03/D-04; `https://github.com/riederch/ha-apps/blob/3e3c3067b9206fc9ab8431fd0942f5d3a308612c/docs/local-ems-flow.md`.

## Stufe 4 – 11.11.2026: Batterie-Invertierungsoptionen (fachliche Zwischenausführung)

- **Git-Befund:** `71105b5995` (**PR #46**) „correct battery polarity override in all auto source modes“ am 11.11.2026. [G]
- **Vorsicht:** Dies ist eine Git-Historienstufe; **kein separater Chat** mit belegten vollständigen Abwägungen. Sie darf nicht als neue Nutzerfreigabe interpretiert werden. Der spätere Fehler des impliziten Batteriequellwechsels blieb als Problem bis zum Fix vom 15.11. bestehen.

## Stufe 5 – 15.11.2026: aktueller Chat und Batteriequell-Fix (S2)

- **Problem:** Minimalkarte `type: custom:local-ems-flow-card` verwendete implizit die Energy-Dashboard-Batteriequelle, obwohl Local EMS die Batterieumkehr konfiguriert hatte. Dadurch wirkte `battery_power_invert` im Standardmodus nicht erwartungsgemäß. [C/G]
- **Entscheidung:** Bei konfiguriertem EMS-Batteriesensor hat er samt Invertierungsoption und SoC **im Auto-Modus** Vorrang; Netz/PV dürfen wie zuvor Energy Dashboard nutzen. `source_mode: energy`, `source_mode: ems`, manuelle `entities:` und expliziter YAML-Override bleiben möglich. [C/G]
- **Warum nicht einfach alle Quellen umstellen:** `source_mode: ems` würde mehr als den Batteriepfad ändern; doppelte YAML-Vorzeichenpflege ist anfällig und widerspricht zentraler EMS-Konfiguration. [C/G]
- **Umgesetzt:** PR #47 gemergt 15.11.2026 (`3e3c3067b9206fc9ab8431fd0942f5d3a308612c`), Manifest `0.5.0b7`, drei GitHub-Actions-Workflows erfolgreich. [G]
- **Nicht nachgewiesen:** produktive HACS-Installation, echte Ladung/Entladung, sämtliche PFCP-Pfade und EPS, Ursache des gemeldeten „Runner“-Fehlers. [C/G]
- **Quelle:** `../entscheidungen/entscheidungsprotokoll.md` D-05/D-06; `../nachweise/stand-und-abnahme.md`.

## Stufe 6 – 15.11.2026: Kontextkontinuität als neuer Nebenfaden im selben Chat (S2)

- **Ursprüngliches Problem der Arbeitsanweisung:** Lange Chats verlieren Entscheidungsgründe; Archiv und Übergabe sind Nebenfolgen, nicht Ziel. [C]
- **Entschieden:** Version 1.3 mit Begründungs- und Wiederaufnahmeregeln; Selbstanwendung; eine fortgeschriebene Karte und ein optionales Paket statt redundanter Projektverwaltung. [C]
- **Neues, ausdrücklich autorisiertes Experiment:** Addendum A1 soll **auf diese** Local-EMS-Fortsetzungskette angewendet werden, obwohl der Addendum-Entwurf OMT als geplanten Erprobungsfall erwähnt. Das ist eine **Anwendung**, keine Änderung an v1.3/A1 und keine Löschfreigabe. [C]
- **Neuer offener Punkt:** Vollständige Originalchat-Prüfung und unabhängiger Test nach A6 sind für die rückwirkende Konsolidierung noch erforderlich.

## Ausgeschlossene, aber relevante Chronologie – 14.10.–09.11.2026 (Z1)

- **„Sofar Home assistant patch“** behandelt Modbus-Schreibbefehle/Antwortfehler zu Register 4368. Der Chat begann früher als die Local-EMS-Entwicklung, ist aber **kein** ursprünglicher Local-EMS-Ursprung.
- **Kein stillschweigender Bedeutungswechsel:** Ein mit Readback beantworteter Modbus-Schreibfehler ist nicht dasselbe wie falsch visualisierte Batterie-Lade-/Entladeleistung.
- **Weiterhin separater Faden:** `../gespraechskarte.md` T4 und D-07; keine Änderung fremder Karten oder neue merge-/freigabebezogene Behauptung.

## Ergebnis der chronologischen Prüfung

**Nachvollziehbar gesichert:** Ziel, technische Architektur, spätere UX-Kurskorrektur, Sicherheitsgrenzen, explizite und implizite Quellentscheidungen, Fix-/CI-Stand sowie offene Praxistests.

**Nicht nachweisbar vollständig:** Gesamter Ursprungschat, jede ursprüngliche verworfene Alternative, die exakte Anzahl aller früheren Gespräche und der Grund eines etwaigen Kontextfenster-bedingten Wechsels. Eine vollständige chronologische Erfassung *aller* Originalaussagen wird ausdrücklich nicht behauptet.