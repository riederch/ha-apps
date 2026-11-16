# Gesprächskarte – Arbeitsanweisung und Kontextkontinuität (Selbstanwendung)

- **Projekt/Thema:** Arbeitsanweisung Gesprächskarte; laufender Chat mit Local-EMS-Nebenfaden
- **Chatkennung:** gespraechskarte-arbeitsanweisung-2026-11-15 (lokal; echte Chat-ID nicht verfügbar)
- **Stand:** 2026-11-15; exportierte Momentaufnahme
- **Betriebsmodus:** B für dieses Paket; verifizierte dauerhafte Ablage/automatische Aktualisierung nicht festgestellt
- **Status:** Chat läuft; kein Abschluss erklärt
- **Entscheidungsort:** `entscheidungen/entscheidungsprotokoll.md` (lokal; KBF-Übernahme offen)

## Fokus jetzt

Version 1.3 als fachlich finale Anweisung mit vollständigen Begründungen, Versionsverlauf und Testverfahren liefern; nachgelagert technische KBF-Aktivierung und unabhängige Wiederaufnahme prüfen. **Primärziel: Kontextverlust während laufender langer Chats verhindern, nicht Archivierung.**

## Gesprächsfäden

### T1 – Local EMS Energieflusskarte (wartet)
- **Ziel:** Konfiguriertes Batterie-Vorzeichen und SoC ohne redundante Karten-YAML korrekt anzeigen.
- **Umgesetzt:** GitHub `riederch/ha-apps`, PR #47 gemergt, `0.5.0b7`, Commit `3e3c3067`; CI erfolgreich.
- **Kerngrund:** Standardquelle aus Energy Dashboard überging die zentrale EMS-Batterie-Umkehr; EMS-Batterie hat darum im Standardmodus Vorrang; übrige Quellen behalten Priorität.
- **Kontextnachweis:** Kerngrund hier und PR; vollständiger Live-Test fehlt.
- **Offen:** HACS-Update, realer Lade-/Entladetest, Plausibilitätsprüfung; separate gemeldete Runner-Störung ohne konkrete Fehlermeldung.
- **Verweis:** https://github.com/riederch/ha-apps/pull/47

### T2 – Arbeitsanweisung Version 1.3 (Text fertig; Aktivierung offen)
- **Ziel:** Ursprüngliche Entscheidungen, Gründe, verworfene Alternativen und offene Fäden auch nach Kontextverdichtung bewahren.
- **Entschieden:** Je Chat eine Karte; frühe Begründungspflicht; laufende Sicherung; Quellen als logisches Paket; unabhängiger Wiederaufnahmetest.
- **Kerngrund:** Nur den Beschluss zu speichern schützt nicht vor späteren Änderungen, die ursprünglich ausschlaggebende Anforderungen verletzen.
- **Kontextnachweis:** `entscheidungen/entscheidungsprotokoll.md` (D-01 bis D-09), 1.2-Original, 1.3-Fassung und Rückmeldung.
- **Umgesetzt:** Lokale finale Markdown-Datei und prüfbares ZIP-Paket erstellt.
- **Offen:** Upload/Übernahme in KBF, Hook-/Codex-Aktivierung, eigenständiger Wiederaufnahmetest.

### T3 – Geschichtliche Begründungen und fremder Faden T5 (Sicherung lokal; externe Übernahme offen)
- **Ziel:** Historische Gründe nicht nur aus Commit-Hashes ableiten und bei Anpassungen verfügbar halten.
- **Kerngrund:** Rückblickend wurde berichtet, dass ein anderer Bearbeiter T5 als erledigt markierte, die Abwägung aber nur im dortigen Chat stand.
- **Kontextnachweis:** Historie in D-01 bis D-09 und `quellen/anmerkungen-zur-1.3.md`, Status rückblickend/nicht am fremden Original verifiziert.
- **Offen:** Fremde Karte und KBF-Entscheidungsregister durch deren verantwortlichen Arbeitskontext korrigieren, nicht hier überschreiben.

## Parkplatz
- Kontextsparsamer kurzer Regelkern statt vollständigem Web-Anweisungstext (kein freigegebener Architekturentscheid).

## Übergreifende offene Fragen
- KBF-Entscheidungseintrag und betroffener Branch: keine konkrete Übernahme bestätigt.
- Hook nach tatsächlicher Modell-Kontextverdichtung und Codex-Regel: noch nicht getestet.
- Test durch einen wirklich unabhängigen neuen Agenten nur mit Karte/Zusatzdateien: noch nicht durchgeführt.

## Ergebnis
- **Erstellt:** Finale 1.3, versioniertes Entscheidungskonzept, Selbstanwendungs-Karte, Wiederaufnahmetest und nachprüfbares ZIP-Manifest.
- **Belegt:** Volltext 1.2 und 1.3 liegen als Paketdateien vor; Kriterien wurden statisch abgeglichen.
- **Nicht belegt:** Externe Persistenz/Activation, produktive Wirkung des Hooks, KBF-Übernahme, unabhängige Kontextprobe.
- **Chatabschluss:** Nicht erklärt; aktive Karte darf nicht automatisch archiviert werden.