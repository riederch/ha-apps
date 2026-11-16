# Umsetzungs-, CI- und Abnahmestand – Local EMS

**Stichtag:** 15.11.2026. **Achtung:** Ein CI-Erfolg ist keine Home-Assistant-Laufzeitabnahme.

## Verifizierter Quellstand

- Repository: `https://github.com/riederch/ha-apps`
- PR #47: `https://github.com/riederch/ha-apps/pull/47`; `merged=true`, Merge 15.11.2026 um 12:41:17 UTC.
- Merge-Commit: `3e3c3067b9206fc9ab8431fd0942f5d3a308612c`.
- Stand `custom_components/local_ems/manifest.json` auf `main`: `0.5.0b7`.
- Der Code priorisiert im automatischen Modus den EMS-Batteriesensor samt Invertierungsoption und SoC; `source_mode: energy` bzw. `source_mode: ems` weiterhin möglich.
- Die Frontend-Visualisierung basiert auf Power Flow Card Plus `0.4.0-beta.1` und einem eigenen Adapter; keine echten neuen HA-Entitäten durch den UI-Bridgecode.

## CI nach Merge auf `main` – alle erfolgreich

| Workflow | GitHub-Actions-Run | Ergebnis | Bedeutung |
| --- | --- | --- | --- |
| Local EMS tests | [43715113353](https://github.com/riederch/ha-apps/actions/runs/43715113353) | success | Automatisierte Python-/JavaScript-Tests |
| HA app release gate | [43715113316](https://github.com/riederch/ha-apps/actions/runs/43715113316) | success | Repository-spezifisches Gate |
| Local EMS integration validation | [43715113304](https://github.com/riederch/ha-apps/actions/runs/43715113304) | success | HACS-/Hassfest-Validierung |

**Frühere Zwischenstörung:** Ein älterer Branch-Lauf erwartete im Manifesttest noch `0.5.0b6`, nachdem auf `0.5.0b7` umgestellt worden war. Dieser Test wurde vor dem Merge korrigiert. Das ist **kein** Nachweis, welcher separate Runner mit „Fehler“ gemeint war.

## Tatsächlich noch fehlende Laufzeitnachweise

1. HACS/HA: installierte Local-EMS-Version `0.5.0b7`, HA-Neustart und Browser-Neuladen **nicht nachgewiesen**.
2. Test mit minimaler Karte `type: custom:local-ems-flow-card`, ohne zusätzlichen invert-Override **nicht nachgewiesen**.
3. Echte Ladephase und echte Entladephase: Zeit, Batteriesensor, Vorzeichen, SoC, Pfeilrichtung und Leistung vor/nach EMS-Umkehreinstellung **nicht nachgewiesen**.
4. Energiefluss-Plausibilität: PV→Batterie, Netz→Batterie, PV→Netz inkl. Quell-Sensoren, W/kW-Konversion und unbekannter Werte **nicht nachgewiesen**.
5. EPS/Netzausfall-Darstellung: Netzpfad 0 nur als UI-Outage, keine erfundene Generatorleistung; keine Live-Abnahme.
6. Runner-Meldung: Herkunft (GitHub Actions / Gitea Runner / anderer Runner) und originale Fehlermeldung **unbekannt**.
7. Viertelstunden-Monitor: Abgleich mit offiziellen Viertelstundenwerten und abschließende Live-Prüfung nicht belegt.

## Testprotokoll-Vorlage (noch nicht ausgefüllt)

| Prüffall | Zeitpunkt | Quellentity / Rohwert | Config/Modus | Modell-/UI-Wert | Erwartung | Ergebnis/Beleg |
| --- | --- | --- | --- | --- | --- | --- |
| Batterie lädt | offen | offen | Standardkarte | offen | Anzeige „Laden“ | offen |
| Batterie entlädt | offen | offen | Standardkarte | offen | Anzeige „Entladen“ | offen |
| PV → Batterie | offen | offen | Standardkarte | offen | konservativer Quellenfluss | offen |
| Netz → Batterie | offen | offen | Standardkarte | offen | konservativer Quellenfluss | offen |
| PV → Netz | offen | offen | Standardkarte | offen | konservativer Quellenfluss | offen |
| EPS/Netzausfall | offen | offen | Standardkarte | offen | kein unbewiesener Netzfluss | offen |

**Sicherheit:** Keine provozierten Netz-/EPS-Eingriffe allein für UI-Tests; echte vorhandene Betriebsphasen und vorhandene Zustandswerte verwenden.