# Gitea Runner

Diese Home-Assistant-App stellt den offiziellen **Gitea Runner 5.0.0** als bewusst schlanken Host-Mode-Runner bereit.

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

## Runtime

- Home Assistant app: `5.0.0-rch2`
- Gitea Runner: `5.0.0`
- Python: `3.x` (Alpine package)
- Upstream image: `docker.io/gitea/runner:5.0.0`
- Architectures: `amd64`, `aarch64`
- Default label: `ha-runner:host`
- Persistent state: `/data/.runner`
