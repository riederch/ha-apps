# Local EMS – Entscheidungspaket (Stand 16.11.2026)

**Status:** fachlich konsolidierter, versionierter historischer Kontext; **kein** Abnahme- oder Löschfreigabenachweis.
**Modul:** `custom_components/local_ems` im Repository `riederch/ha-apps`.
**Ursprung:** Rekonstruktion der Chatkette vom 2.–15.11.2026 und vorangehender getrennt ausgewiesener Konzepte.
**Primärzweck:** Entscheidungen mitsamt damaligen Gründen, Gegenargumenten, Alternativen und fortgeltenden Randbedingungen vor Verlust bewahren.

## Einstieg und Verbindlichkeit

- **[13 Entscheidungseinträge D-01–D-13](entscheidungen/entscheidungsprotokoll.md)** – wesentliche Gründe, Alternativen, Grenzen und realer Umsetzungsstatus.
- [Historische Chronologie](quellen/a1-chronologie.md) – vom ältesten belegbaren Local-EMS-Ursprung bis zum Merge von PR #47.
- [Quellen- und Vollständigkeitsregister](quellen/a1-quellenregister.md) – Umfang und methodische Grenzen der Rückschau.
- [Gesprächskarte](gespraechskarte.md) – **eingefrorener Snapshot** zur Kontextwiederherstellung; die fortzuschreibende Gesprächskarte bleibt in der ChatGPT-Dateibibliothek.
- [Modul- und CI-Abnahmen](nachweise/stand-und-abnahme.md) – was umgesetzt, getestet und weiterhin ungeprüft ist.
- [Anlagenregister](quellen/a1-anlagenregister.md) – Originaldateien und bewusst nicht übernommene Binärdateien.
- [A1-Prüfung zur Löschbereitschaft](tests/a1-loeschbereitschaft.md) und [Blindtest-Auftrag](tests/a1-blindtest-auftrag.md) – Unabhängigkeitstest steht noch aus.

Die technische Dokumentation unter `docs/local-ems.md` und `docs/local-ems-flow.md` sowie der tatsächliche Code bleiben für Implementierung und Betriebsverhalten maßgeblich. Dieser Ordner ist eine **historische Entscheidungsquelle**, keine zweite Spezifikation, kein Live-Status und keine alternative Produktdatenbank. Änderungen an Produktregeln gehören in die reguläre Projektpflege; spätere Entscheidungsänderungen müssen bisherige Gründe ausdrücklich berücksichtigen.

## Tragende technische Entscheidungen

1. Herstellerneutrale HA-Integration, vorhandene Entitäten/Recorder/Statistics statt eigener Verbrauchsdatenbank.
2. Zunächst lesende 15-Minuten-Peaküberwachung; keine ungesicherte Schalt-/Netzschutzfunktion.
3. Original-Power-Flow-Card-Plus-Renderer statt Sankey oder dauerhaftem SVG-Nachbau, mit Lizenz-/Credits-Pflichten.
4. PV→Batterie, Netz→Batterie und PV→Netz nur als konservative Untergrenzen bei vollständiger Datenlage.
5. In der Standardkarte hat ein in Local EMS konfigurierter Batteriesensor samt Invertierung und SoC Vorrang vor der impliziten Energy-Dashboard-Batteriequelle; Netz/PV behalten ihre unabhängige Quellenwahl.
6. Frontend-Flüsse dürfen weder neue produktive HA-Entitäten schaffen noch Steuerung oder EPS-Sicherheitsentscheidungen auslösen.
7. Sofar-Modbus-Register-4368- und TCP-Recovery-Themen bleiben **getrennte, nicht vollständig abgenommene** Vorarbeiten.

## Historische Belege und Erkenntnisgrenzen

- **S1:** „SG Ready erklärt“ – erster belegbarer Local-EMS-Inhalt 02.11.2026, Originalchat nur selektiv zugänglich. Er enthielt außerdem SG Ready, Netzbetreiber-Steuerkonzepte, Sofar-Betriebsfragen und Recovery-Themen.
- **S2:** „Batterievorzeichen konfigurieren“ / der fortgesetzte Chat vom 15.11.2026 – PR #47 und Gesprächskarten-Arbeitsanweisung, nicht als vollständig eingesehener Originalchat belegt.
- **Z1:** „Sofar Home assistant patch“ – eigener Arbeitsstrang, **nicht** mit S1/S2 verschmolzen.
- 2025er und Juli-2026-Vorläufer enthalten **Vorschläge**, die nicht automatisch verbindliche Local-EMS-Entscheidungen sind.
- Die Codehistorie und CI sind **kein** Ersatz für komplette Chattranskripte oder reale HA-/Sofar-Praxistests.

**Nicht in dieses GitHub-Repository übernommen:** der Original-Screenshot der privaten Home-Assistant-Oberfläche, separate Sofar-Patch-Binärarchive und weitere potenziell sensible Originalanhänge. Ihre Herkunft ist im Anlagenregister dokumentiert; sie waren zum Konsolidierungszeitpunkt separat in der Nutzer-Dateibibliothek gesichert. Ohne Zugriff auf diese Ablage dürfen sie nicht als hier enthalten oder langfristig öffentlich abrufbar behauptet werden.

## Löschrisiko und Stand der A1-Prüfung

Die relevanten Entscheidungen sind fachlich weitgehend gesichert. **Der strenge A1-Nachweis ist weiterhin nicht bestanden**, weil vollständige Originalchat-Abdeckung und unabhängiger Wiederaufnahmetest fehlen. Die Benutzerpräferenz, keine aufwendige Volltextextraktion fortzuführen, ist keine nachträgliche Behauptung eines erfolgreichen A1-Tests und keine automatische Löschfreigabe. Jede spätere Chatlöschung ist eine **separate, bewusste Benutzerentscheidung** mit Restrisiko für nicht rekonstruierte Details und Anhänge.

Für Folgeänderungen prüfen: `entscheidungen/entscheidungsprotokoll.md` (Warum), `quellen/a1-chronologie.md` (Wann und Alternativen), `nachweise/stand-und-abnahme.md` (Was tatsächlich belegt ist).

**Letzter verifizierter Produkt-Merge im Quellmaterial:** PR #47 am 15.11.2026; `0.5.0b7`, `3e3c3067b9206fc9ab8431fd0942f5d3a308612c`. Der Commit dieses Entscheidungspakets allein bestätigt keine inzwischen erfolgte Produkt-/Hardwareabnahme.
