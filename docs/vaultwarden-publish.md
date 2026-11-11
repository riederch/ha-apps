# Vaultwarden: getrennte Image-Veröffentlichung

Stand: 11.11.2026 · Gültig **nach** Freigabe dieses PRs

## Warum?

Bisher veröffentlichte `.github/workflows/vaultwarden-image.yaml` die Tags
`ghcr.io/riederch/ha-apps-vaultwarden:<app-version>` und `:latest` automatisch
nach einem Push auf `main` **und** nach jedem manuellen Workflow-Start,
auch wenn dieser auf einen anderen Branch zielte.

Das ist für einen zustandsbehafteten Passwortmanager eine ungewollte Kopplung:
Code-Review/Build, Veröffentlichung eines allgemein abrufbaren Images
und produktive Installation sind unterschiedliche Freigaben.

## Neuer Ablauf

1. **PR prüfen**: Die bestehenden Vaultwarden-Multi-Arch-Builds,
   Snapshot-/Runtime-Versionsabgleiche (ab PR #33) und funktionalen
   SQLite-Backup-Tests müssen grün sein. PR-Review und Branchschutz aus
   Issue #44 sind unabhängig notwendig.
2. **Nach dem Merge nach `main`**: GitHub Actions baut und testet das
   Image, aber **veröffentlicht es nicht**. Weder die App-Version noch
   `:latest` werden durch den Push verändert.
3. **Freigabe zur Veröffentlichung**: Vorher vollständiges Backup der
   Zielinstallation, Restore-Rehearsal und App-spezifische Testfreigabe
   nach `docs/ha-app-release-gates.md` dokumentieren.
4. **Manuell veröffentlichen**: GitHub → **Actions → Vaultwarden image →
   Run workflow**; Branch **`main`** auswählen, den booleschen
   Parameter **`publish` aktivieren**, Workflow starten.
   Ohne diese Option wird nur gebaut. Veröffentlichungen von anderen
   Branches sind selbst bei aktivem Parameter gesperrt.
5. **Freigabe der GitHub-Umgebung (Pflicht vor dem ersten Publish)**:
   Unter **Settings → Environments → `vaultwarden-release`**
   Required reviewers und Deployment-Branches nur `main` einrichten,
   soweit vom GitHub-Plan unterstützt. Zusätzlich eine
   **Environment-Variable** `VAULTWARDEN_RELEASE_ENABLED=true`
   setzen. Ohne diese explizite Aktivierung verweigert der Publish-Job
   den Start vor dem GHCR-Login (fail closed). Die Variable ersetzt
   **keine** unabhängige Reviewer-Freigabe; ein noch nicht bestehendes
   Environment wird bei GitHub sonst ohne Schutzregeln angelegt.
   Die manuelle Veröffentlichung prüft zusätzlich zweimal, dass der
   ausgelöste Commit noch dem aktuellen `main`-HEAD entspricht.
   Gleichzeitige Publisher-Jobs werden serialisiert.
6. **Release-Nachweis**: Das Publisher-Job-Summary enthält
   App-Version, Git-Commit und den unveränderlichen Container-Digest.
   Nach dem Publish den Digest sichern, `amd64`/`aarch64` prüfen
   und die App erst im vorgesehenen Wartungsfenster aktualisieren.
7. **Nach Installation**: Anmeldungen, 2FA, Organisationen, Anhänge,
   Emergency Access und die Datenbank-Migration prüfen. Bei Fehlern
   die konsistente Datensicherung wiederherstellen (nicht bloß das
   Container-Image zurücksetzen).

## Technische Eigenschaften

- `pull_request`: Build und Checks, kein Login und kein Push.
- `push main`: Build und Checks, kein Login und kein Push.
- `workflow_dispatch, publish=false`: Build, kein Push.
- `workflow_dispatch, publish=true, branch!=main`: Build, Publisher-Job
  wird übersprungen; kein Push.
- `workflow_dispatch, publish=true, branch=main`: Nur nach grünem
  Build und gesetzter Environment-Variable `VAULTWARDEN_RELEASE_ENABLED=true`,
  mit zweifacher Prüfung auf unveränderten `main`-HEAD. Nur der serialisierte
  Publish-Job besitzt `packages:write`. Unabhängige GitHub-Environment-
  Reviewer müssen zusätzlich administrativ eingerichtet werden.

Die Registry-Tags `:latest` und `:<app-version>` sind technisch
überschreibbar, die Freigabe basiert daher auf Commit und Digest.
Wenn immutable Tags gewünscht sind, ist eine eigenständige
Registry-Policy zu definieren. Keine Tokens oder Backups im Repository
ablegen.

## Reihenfolge mit laufenden Pull Requests

**Diesen Workflow-PR zuerst übernehmen, bevor Vaultwarden-PR #33
gemergt wird.** #33 verändert denselben Workflow; beim Rebase/Merge
seine Snapshot-Prüfungen und die manuelle Veröffentlichung gemeinsam
erhalten. Nur die Image-Version anzuheben, ohne die Freigabeabsicherung,
würde wieder eine automatische Veröffentlichung auf `main` auslösen.

PR #40 ist ausschließlich Staging und wird nicht produktiv gemergt.

## Nachvollziehbarkeit des Builds

Der Publisher baut das Container-Image **erneut**; er lädt kein bereits
geprüftes OCI-Image-Artefakt aus dem Validierungsjob hoch. Deshalb
beweisen gleiche Git-Commit-SHAs alleine **keine bitidentischen Images**:
die beiden `FROM`-Tags und Systempaket-Repositories können sich zwischen
den Builds ändern. Der erfolgreiche PR-/Staging-Build ist ein notwendiger
Test, keine Image-Provenienz-Garantie. Vor dem finalen Publish muss die
Version samt Quellcode/Abhängigkeiten überprüft werden; nach dem Push
werden der tatsächlich veröffentlichte Multi-Arch-Digest sowie die
Architekturen als unveränderlicher Nachweis protokolliert. Eine künftige
Verbesserung ist Digest-Pinning der beiden Base-Images und eine
separate überprüfbare Build-Provenienz.

**Achtung:** Nach dem Merge von PR #33 kann die neue App-Version im
HA-App-Store bereits angeboten werden, bevor das manuell freigegebene
GHCR-Image existiert. Daher PR #33 und die zugehörige Image-Veröffentlichung
als gemeinsames Wartungsfenster planen; bis zum Publish keine App-Aktualisierung
auf der produktiven HA-Instanz durchführen.
