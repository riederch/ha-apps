# GitHub-Quellenstand der A1-Konsolidierung

Repository: `riederch/ha-apps`. Die Daten wurden für den Stand **15.11.2026** über die verbundene GitHub-Quelle erneut geprüft.

- 02.11.2026 – `a5398f2e70` HA-nativer 15-Minuten-Peakmonitor; `3e3447c852` PFCP-Stil; `37bc34eea2` Vollbreite; `7f6e16eedc` feste Bubbles; `54a9734829` Gauge.
- 08.11.2026 – `aaa1e88058` Direktflüsse; `ab55fa813f` PV→Batterie; `d0b8839575` MIT-lizenzierte originale PFCP-Implementierung.
- 11.11.2026 – `71105b5995` Batterie-Invertierungs-Override (PR #46).
- 15.11.2026 – `3e3c3067b9206fc9ab8431fd0942f5d3a308612c` Batterie-Quellenpriorität (PR #47, gemergt), `custom_components/local_ems/manifest.json` = `0.5.0b7`.
- 15.11.2026 – drei GitHub Actions auf dem Merge-Commit `success`: 43715113353, 43715113316, 43715113304.

Präzise unveränderliche GitHub-Quellen:
- https://github.com/riederch/ha-apps/commit/3e3c3067b9206fc9ab8431fd0942f5d3a308612c
- https://github.com/riederch/ha-apps/pull/47
- https://github.com/riederch/ha-apps/blob/3e3c3067b9206fc9ab8431fd0942f5d3a308612c/docs/local-ems-flow.md
- https://github.com/riederch/ha-apps/blob/3e3c3067b9206fc9ab8431fd0942f5d3a308612c/docs/local-ems.md
- https://github.com/riederch/ha-apps/blob/3e3c3067b9206fc9ab8431fd0942f5d3a308612c/custom_components/local_ems/frontend/flow-model.mjs

**Quellengrenze:** Git-Commit-Historie beweist Entwicklungsdaten und Implementierung, nicht die vollständige ursprüngliche Gesprächsabwägung oder eine reale Home-Assistant-Laufzeitfreigabe. Keine Codeänderung erfolgt durch diese A1-Übernahme.