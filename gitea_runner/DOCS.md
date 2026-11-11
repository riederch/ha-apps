# Gitea Runner

Diese Home-Assistant-App stellt den offiziellen **Gitea Runner 5.4.1** als bewusst schlanken Host-Mode-Runner bereit.

Der Runner ist fuer vertrauenswuerdige, leichte Workflows gedacht, die direkt im App-Container ausgefuehrt werden. Er bekommt **keinen Docker-Socket, keinen Supervisor-Zugriff und keine privilegierten Rechte**.

## Warum Host-Mode?

Fuer die gemeinsamen Knowledge-Base-Workflows werden vor allem Git, Shell, Python 3 und der in Gitea Runner 5 enthaltene `builtin:checkout` benoetigt. Dafuer ist kein Docker-in-Docker erforderlich.

Der Standard-Label ist:

```text
ha-runner:host
```

Workflows muessen daher explizit

```yaml
runs-on: ha-runner
```

verwenden. Dadurch wird verhindert, dass allgemeine Workflows fuer `ubuntu-latest` versehentlich unsandboxed im Runner-Container ausgefuehrt werden.

## Installation

1. Diese App aus `riederch/ha-apps` installieren.
2. In Gitea **Benutzereinstellungen -> Actions -> Runner** oeffnen.
3. Einen **User-Level Registration Token** erzeugen bzw. kopieren.
4. Den Token in der App-Konfiguration als `registration_token` eintragen.
5. App starten.
6. In Gitea pruefen, ob der Runner online erscheint.

Beispielkonfiguration:

```yaml
gitea_instance_url: http://homeassistant.local:3000
registration_token: "<TOKEN>"
runner_name: homeassistant
labels:
  - ha-runner:host
```

Der Token muss nicht im Chat, in Git oder in einer Workflow-Datei abgelegt werden.

## Persistenz und Token

Die Runner-Registrierung wird unter `/data/.runner` gespeichert und ist Bestandteil der persistenten App-Daten.

Nach einer erfolgreichen Erstregistrierung kann `registration_token` in der Home-Assistant-App-Konfiguration wieder geleert werden. Bei spaeteren Starts verwendet die App die bestehende Registrierung.

Wenn die konfigurierte Gitea-Instanz nach einer Registrierung geaendert wird, startet die App absichtlich nicht weiter. Dadurch wird vermieden, dass eine bestehende Runner-Identitaet versehentlich gegen eine andere Instanz verwendet wird.

## Schutz gegen versehentliches Token-Logging

Vor dem Start von `tini` und `gitea-runner` entfernt `clean-env.sh` alle geerbten Umgebungsvariablen außer `PATH`, `HOME=/data` und `TZ`. Insbesondere erreichen die von Home Assistant injizierten `SUPERVISOR_TOKEN` und `HASSIO_TOKEN` keine Host-Mode-Jobprozesse. Dieser Schutz erfasst auch unerwartete künftige Variablen und verhindert unbeabsichtigte Lecks über Build-Tracebacks bzw. `os.environ`.

**Sicherheitsgrenze:** Der Runner ist weiterhin ein Host-Mode-Runner. Vertrauenswürdige Workflows können andere Credentials, etwa ihre ausdrücklich bereitgestellten CI-Secrets, selbst ausgeben oder lokale Runner-Registrierungsdaten lesen. Eine absolute Garantie gegen Secrets in beliebigen Logs besteht nicht. Nur vertrauenswürdige Repositories/Workflows zuweisen; für fremden Code getrennte, isolierte Runner verwenden. Bereits im alten Joblog veröffentlichte Supervisor-Tokens werden durch dieses Update **nicht** widerrufen: Tokens/Log-Zugriff unabhängig prüfen und Berechtigungen entziehen bzw. rotieren.

## Sicherheitsmodell

Host-Mode bedeutet: Workflow-Schritte laufen direkt **innerhalb des Runner-App-Containers**. Sie laufen nicht auf dem Home-Assistant-Host.

Diese App aktiviert bewusst nicht:

- `docker_api`
- `full_access`
- privilegierte Linux-Capabilities
- Host-Networking
- Supervisor- oder Home-Assistant-API-Zugriff

Trotzdem sollten nur vertrauenswuerdige Repositories diesen Runner verwenden. Ein Workflow kann auf Dateien innerhalb des Runner-App-Containers zugreifen, einschliesslich der persistenten Runner-Registrierung.

Fuer Workflows, die Docker-Container, Service-Container oder `docker://` Actions benoetigen, sollte spaeter ein separater containerisierter bzw. DinD-Runner eingesetzt werden.

## Update auf 5.4.1

Der Wechsel von `5.0.0-rch3` zu `5.4.1-rch1` tauscht nur die
offizielle Runner-Runtime aus. Das eigene `clean-env.sh` bleibt erhalten,
einschliesslich der Positivliste fuer `PATH`, `HOME` und `TZ`.
Die Registrierung in `/data/.runner`, die Instanzbindung
`/data/.ha-runner-instance` sowie Labels und Konfiguration werden
weiterverwendet, eine Neuregistrierung ist nicht geplant.

Vor dem App-Neustart sollten laufende Actions-Jobs beendet sein, da
der Upgrade-Neustart diese unterbrechen kann. Nach dem Neustart:
`ha-runner:host` in Gitea pruefen, einen kleinen vertrauenswuerdigen
`builtin:checkout`-Job starten und bei einem Testjob sicherstellen,
dass keine Home-Assistant-Supervisor-Tokens in den Job-Umgebungsvariablen
liegen. Ein CI-Container-Build ersetzt diesen Laufzeittest nicht.

## Runtime

- Home Assistant app: `5.4.1-rch1`
- Gitea Runner: `5.4.1`
- Python: `3.x` (Alpine package)
- Upstream image: `docker.io/gitea/runner:5.4.1`
- Architectures: `amd64`, `aarch64`
- Default label: `ha-runner:host`
- Persistent state: `/data/.runner`
