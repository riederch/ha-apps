# A1 – Quellen- und Vollständigkeitsregister der Local-EMS-Gesprächskette

**Arbeitsvorschrift:** Addendum A1 zur Arbeitsanweisung 1.3, Erprobungsentwurf; keine Einführung einer Version 1.4.  
**Führende Karte:** `../gespraechskarte.md` (einziger fortzuschreibender Einstiegspunkt).  
**Quellenlage:** Von den älteren Chats sind derzeit nur selektive Gesprächsinhalte/Verlaufszusammenfassungen abrufbar. Die Originaltranskripte sind **nicht** vollständig eingesehen. Die hier verwendeten Quellencodes bedeuten `R` (rekonstruierter Chatkontext), `C` (im aktuellen Chat direkt belegbar), `G` (GitHub-Datei, PR oder Commit geprüft).

## Abgrenzungsentscheidung

Für die rückwirkende **eine logische Local-EMS-Fortsetzungskette** werden nur zwei bekannte Gesprächseinheiten geführt: der Ursprung **„SG Ready erklärt“** (Local-EMS-Entwicklung ab 02.11.2026 innerhalb dieses Chats) und **der aktuelle Chat** (Batterie-Vorzeichen-Fix und dessen Fortsetzung am 15.11.2026). Das dokumentiert eine fachliche Fortsetzung, **keinen abschließend nachgewiesenen durch Kontextfenster erzwungenen Chatwechsel**. Die Ursachen des Chatwechsels sind für Local EMS nicht belegt.

„Sofar Home assistant patch“ ist ein älterer, **unabhängiger Zulieferfaden**: sein Modbus-Schreibproblem ist wichtig, darf aber nicht mit dem Flow-Frontend-Fix oder dessen Entscheidungen gleichgesetzt werden. Auch andere projektähnliche oder methodische Chats werden nicht ohne Herkunftsbeleg in die logische Einheit verschmolzen.

## Vollständigkeitsregister nach A4

| ID / Quelle und Fundort | Zeitstellung und Rolle | Zugänglichkeit | Übernahme / Kontextnachweis | Abhängigkeiten | Prüfung | Löschbereitschaft |
| --- | --- | --- | --- | --- | --- | --- |
| **S1** „SG Ready erklärt“, ChatGPT, technische Chat-ID nicht verfügbar | Gesprächsbeginn laut Kontextübersicht **01.11.2026**, belastbare Local-EMS-Ausschnitte ab **02.11.** und **08.11.**; mutmaßlicher Ursprung | **Teilweise**: selektive frühere Gesprächsausschnitte, keine originale Vollfassung | **Mit Lücke konsolidiert:** Ursprung, SG-Ready-/Netzvorgabe-Frage, geparkter ISO Fault, Sofar-TCP-Recovery-Kandidat, Herstellerneutralität, Peakmonitor, HA-Datenhaltung, UX-Ablehnung von Sankey/Nachbau, Original-PFCP. Fundstellen `a1-stufe-1-ursprung.md`, `a1-chronologie.md`, `../entscheidungen/entscheidungsprotokoll.md` D-01 bis D-04 sowie D-10 bis D-13 | Git-Historie Nov 2/8, `docs/local-ems.md`, `docs/local-ems-flow.md`; UI-Screenshot und TCP-Recovery-ZIP jetzt als Originaldateien gefunden; Herkunft zu S1 nicht gesichert; weitere Anhänge unbekannt | **Intern abgeglichen** mit Git-Commit-Daten; Originaltext nicht vollgeprüft | **GESPERRT** |
| **S2** Aktueller Chat „Batterievorzeichen konfigurieren“ (historischer Arbeitstitel), derzeitiger Gesprächsverlauf, technische Chat-ID nicht verfügbar | **15.11.2026**; Fortsetzung des Flow-Card-Arbeitsstands plus eigenständiger methodischer Nebenfaden | **Teilweise**: aktuelle Folgebeiträge direkt verfügbar; frühe Fehlersuche/Runner-Meldung nur aus früherer Gesprächszusammenfassung | **Mit Lücke konsolidiert:** `0.5.0b7`, PR #47, Quellpriorität, Teststatus; Arbeitsanweisung 1.3 und A1-Nebenfaden. Fundstellen bestehende `../gespraechskarte.md`, D-05/D-08/D-09, `../nachweise/stand-und-abnahme.md` | PR #47 und CI vorhanden; Original-Runner-Log und reales HA-Livetestprotokoll fehlen | **Intern abgeglichen** mit GitHub; vollständige alte Chat-Eingangsphase nicht im Original geprüft | **GESPERRT** |
| **Z1** „Sofar Home assistant patch“, ChatGPT | Nach Verlauf **14.10.–09.11.2026**; **separater Zulieferfaden**, nicht S1/S2-Fortsetzung | **Teilweise**: rekonstruierte Fehlersymptome, kein Volltranskript | **Nur referenziert:** Modbus Register `4368`, Readback statt blindem Retry; D-07; unabhängige fachliche Fortsetzung bleibt offen | Original-Logs aus diesem anderen Chat nicht vollständig im Paket, tatsächlicher Upstream-Stand nicht geprüft | **Nicht unabhängig geprüft** | **GESPERRT** (für etwaige eigene spätere Konsolidierung) |
| **Z2** „Gesprächskarte prüfen“ und andere Chats zur Arbeitsanweisung | 15.11.2026; **methodische Quelle**, kein Local-EMS-Vorgängerchat | Inhalt über die finale Arbeitsanweisung und die in diesem Chat dokumentierte Diskussion teilweise gesichert | **Nur referenziert** für Regeln, nicht als zusätzliche Local-EMS-Entscheidungskette. `gespraechskarte-arbeitsanweisung-1.3.md`, `a1-addendum.md` | Verbindlicher Stand 1.3, A1 nur Erprobung | Dokumenteninhalt geprüft; kein eigener historischer Vollabgleich | **Nicht beurteilt**; kein Teil der Local-EMS-Löschbewertung |

**Weitere historische Hinweise:** P0 (Juli 2025, allgemeiner HA-EMS-Entwurf), P1 (21.07.2026, „QuarterPeak“ als Assistenten-Vorschlag) und P2/Z1 (14.10.2026, Sofar-Integration) sind **Vorlauf/andere Arbeitsstränge**, keine belegten technischen S1-Fortsetzungschats. Details in `a1-wiedergefundene-fragmente.md` und `a1-anlagenregister.md`.

**Reihenfolge:** S1 → S2 ist die bisher belegbare fachliche Fortsetzung. Eine lückenlose Liste *aller* möglicherweise verwandten oder ehemals eröffneten Chats ist **nicht** nachgewiesen. Z1 ist zeitlich teilweise älter, aber ausdrücklich **keine** Vorgängerstufe von S1. Die Chatnamen dienen zur Identifizierung, nicht als nachgewiesene technische Chat-IDs. **Einzelne übermittelte Nachrichtenhinweise sind nicht der vollständig durchsuchte Originalchat.**

## A1-Prüfgrenzen

- **Originalquelle gesichtet** bedeutet: vollständiger Chattranskript-Text gelesen. Für S1, S2 und Z1 ist dieses Kriterium derzeit **nicht** erfüllt.
- **Git geprüft** bedeutet lediglich: bestimmter Code oder dokumentierte Git-Historie nachgewiesen. Git ersetzt nicht die damaligen positiven/negativen Entscheidungskriterien.
- **Rekonstruktion** bedeutet nachvollziehbarer Arbeitsstand aus Ausschnitten und vorhandener Dokumentation, keine wortgetreue Vollständigkeit.
- **Keine automatische Löschfreigabe:** Bis Originalabdeckung und isolierter Wiederaufnahmetest nach A6 vorliegen, bleiben S1 und S2 gesperrt.
- Neue Vorgängerquelle: Erst als zusätzliche S-Quelle samt Zeit, Rolle, Originalabdeckung und Konfliktprüfung einarbeiten. Keine stillschweigende „jüngster Stand gewinnt“-Regel.

**Quellenzugriff-Nachtrag 15.11.2026:** Trotz weiterer gezielter Wiederauffindungsversuche konnten S1/S2 nicht als Volltranskript gelesen werden. Das Quellenregister ist inhaltlich ergänzt, jedoch weder mit dem Chatverlauf abzugleichen noch zur Löschfreigabe heranzuziehen. `a1-vollquellen-bedarf.md` beschreibt die verbleibenden Primärquellen.