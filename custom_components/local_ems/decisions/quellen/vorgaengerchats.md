# Herkunft und Abdeckung der Vorgängerchats

**Verwendungszweck:** Kontrollierte Übernahme von Entscheidungskontext gemäß Arbeitsanweisung 1.3. Dieses Dokument ist **kein vollständiges Chattranskript**. Die Inhalte wurden aus in dieser Unterhaltung vorhandenen Aussagen, vorhandenen Zusammenfassungen sowie erneut abgerufenen *selektiven* älteren Gesprächskontexten rekonstruiert. Für ältere Chats liegen keine vollständig gegengeprüften Originaltranskripte vor. Zitierbare Original-GitHub-Dateien stützen technische Fakten, aber nicht jedes damals genannte Entscheidungsargument.

## R1 – „SG Ready erklärt“ (November 2026; Local EMS / Monitoring / Karte)

**Bekannte Nutzervorgaben aus rekonstruierter Historie:**
- 02.11.: 15-Minuten-Spitzenmonitor und Vorwarnung vor Überschreiten von 10 kW, inklusive „in x Minuten“; `sensor.kng_p_in` als bevorzugte Messquelle im Konzept.
- 02.11.: Keine zweite Verbrauchsdatenbank und keine direkten SQL-Abfragen; Recorder/Statistics von Home Assistant verwenden.
- 02.11.: Local EMS muss herstellerneutral sein, Sofar ist optionale Quelle; EMS-Aktorik nur im geeigneten Self-Consumption-Modus.
- 02.11.: `power-sankey` abgelehnt; Power-Flow-Card-Plus-Stil verlangt, Vollbreite und feste Bubbles; Netzfrequenz, Wechselrichterzustand, Netzausfall mit darstellen.
- 08.11.: Direkte Pfade PV→Batterie, Netz→Batterie, Solar→Netz; bei unklarer Herkunft keine Animation.
- 08.11.: Original-Logik und Originaldarstellung vollständig übernehmen, Credits/Lizenz berücksichtigen.

**Aus Repository gegenprüfbar:** `docs/local-ems.md` (Monitor, Datenqualität, keine Steuerung), `docs/local-ems-flow.md` (Vendor-Renderer, MIT, Original-UI), `frontend/flow-model.mjs` (konservative Direktflüsse).

**Nicht als gesichert ausgeben:** Vollständige damalige Abwägung jedes einzelnen Designparameters, exakte Wortlaute aus dem gesamten Chat, erfolgreiche visuelle Live-Abnahme aller Pfade.

## R2 – „Sofar Home assistant patch“ (Oktober bis November 2026; separater Integrationsfehler)

**Rekonstruierte Nutzeraussagen:** `write_registers(4368,[0])` meldet Timeout oder `Device response does not match request` beim Moduswechsel trotz tatsächlicher Ausführung; gelegentlich Reload notwendig. HACS-Fix darf keine unbeabsichtigten neuen Entitäten erzeugen.

**Rekonstruierte technische Entscheidungen und Gründe:** Vorhandener Modbus-Lock serialisiert Zugriffe; keine weitere Queue notwendig. Bei Schreibquittungsfehlern verifizieren per Readback, statt blind zu wiederholen. Überlange FC16-Antwort als plausible Ursache erkannt; keine globale Aufweichung des Modbus-Protokollchecks. Geplante Coordinator-Recovery nur bei wiederholten vollständigen Lese-Timeouts, nicht bei Teilfehlern.

**Ungeprüft:** Repo-/Merge-Stand, tatsächliche Geräte- und Upstream-Abnahme, abschließende Freigabe. Sofar ISO-Fault/Generatorbetrieb ist weiterer separater Strang und gehört nicht zum Local-EMS-Flow-UI-Fix.

## R3 – Dieser Chat „Batterievorzeichen konfigurieren“ (15.11.2026)

**Im Gespräch direkt sichtbar:** Batteriesymbol/Vorzeichen wird von der Local-EMS-Config nicht richtig übernommen. Nach Antwort „Fehler“ präzisiert Nutzer „Beim runner“; ein originaler Runner-Log fehlt. Entwicklung PR #47, 0.5.0b7, Merge-Commit und erfolgreiche CI wurden anschließend überprüft. Die Praxisabnahme blieb aus.

**Späterer Themenfaden:** 1.3-Arbeitsanweisung wird entwickelt, begründete Entscheidungen als oberste Regel; ZIP nur unterstützendes Format, Primärziel Kontextkontinuität; Selbstanwendung auf denselben Chat. Der frühere Kartensnapshot aus dem 1.3-Paket wird hier weitergeführt und nicht als neue Karte verdoppelt.

## Herangezogene GitHub-Fundstellen (15.11.2026 erneut geprüft)

- PR #47: https://github.com/riederch/ha-apps/pull/47 – Merge und Detaildiff.
- `docs/local-ems-flow.md`: https://github.com/riederch/ha-apps/blob/3e3c3067b9206fc9ab8431fd0942f5d3a308612c/docs/local-ems-flow.md
- `docs/local-ems.md`: https://github.com/riederch/ha-apps/blob/3e3c3067b9206fc9ab8431fd0942f5d3a308612c/docs/local-ems.md
- `frontend/flow-model.mjs`: https://github.com/riederch/ha-apps/blob/3e3c3067b9206fc9ab8431fd0942f5d3a308612c/custom_components/local_ems/frontend/flow-model.mjs
- `frontend/pfcp-adapter.mjs`: https://github.com/riederch/ha-apps/blob/3e3c3067b9206fc9ab8431fd0942f5d3a308612c/custom_components/local_ems/frontend/pfcp-adapter.mjs
- `manifest.json`: https://github.com/riederch/ha-apps/blob/3e3c3067b9206fc9ab8431fd0942f5d3a308612c/custom_components/local_ems/manifest.json

**Versions- und Aktualitätshinweis:** Diese Links adressieren den geprüften Commit, nicht automatisch den späteren Entwicklungsstand. Vor weiteren Codeänderungen den dann aktuellen `main`-/Featurebranch-Stand lesen. Bei verlorenen oder unzugänglichen Quellen die historischen Begründungen aus `entscheidungen/` erhalten, Unverifiziertes markieren.

## Nachtrag 15.11.2026 – A1-Chronologie statt bloßer Themenliste

Die rückwirkende Sonderregel A1 ist für die Local-EMS-Fortsetzung S1 („SG Ready erklärt“) → S2 (aktueller Chat) **zur Erprobung autorisiert**. Die Quelle wurde nun tatsächlich beim ältesten rekonstruierbaren Local-EMS-Abschnitt begonnen; Einzelstufen und Entscheidungskorrekturen stehen in `a1-stufe-1-ursprung.md` und `a1-chronologie.md`, die vollständigen Quellstatus-Felder in `a1-quellenregister.md`. Die ältere Sofar-Modbus-Unterhaltung bleibt separater Zulieferfaden. **Die bisherigen Lücken sind nicht durch die neue Chronologie behoben.** Siehe `../tests/a1-loeschbereitschaft.md`.

## Nachtrag A1 (15.11.2026)

Die laufende A1-Aufarbeitung hat zusätzliche ältere Gesprächsfragmente, die zuerst übersehene **SG-Ready-/Netzvorgaben-/ISO-Fault-Seitenlinie**, zwei Originaldatei-Kandidaten sowie konzeptionelle Vorläufer von **2025 und Juli 2026** erschlossen. Der aktuelle Quellenstand steht ausschließlich in `a1-quellenregister.md`, `a1-wiedergefundene-fragmente.md` und `a1-anlagenregister.md`; dieser ältere Überblick ist keine Volltranskript-Prüfung.