# Gitea

Diese App stellt einen vollständigen Gitea-Server unter Home Assistant OS bereit.

## Installation

1. App installieren.
2. Standardmäßig werden die Ports `3000` für die Weboberfläche und `2222` für Git über SSH verwendet.
3. App starten.
4. Die Weboberfläche öffnen und den Gitea-Einrichtungsassistenten abschließen.
5. Die App danach einmal neu starten.

## Standardkonfiguration

```yaml
ssl: false
certfile: fullchain.pem
keyfile: privkey.pem
APP_NAME: Gitea for Home Assistant
DOMAIN: homeassistant.local
ROOT_URL: ""
env_vars: []
```

Wird `ROOT_URL` leer gelassen, ermittelt die zugrunde liegende App die URL aus Protokoll, Domain und veröffentlichtem Port.

## Daten und Sicherung

Die Gitea-Daten sind Bestandteil der Home-Assistant-App-Daten und müssen in vollständige Home-Assistant-Backups aufgenommen werden. Wichtige Repositories sollten zusätzlich auf ein zweites System gespiegelt werden.

Die Gitea-Konfiguration `app.ini` wird durch die zugrunde liegende App im App-Konfigurationsverzeichnis bereitgestellt.

## Herkunft

Diese Definition verwendet das von AlexBelgium gepflegte Gitea-App-Image. Dadurch kann die App ausschließlich über dieses Repository installiert werden, während Build- und Laufzeitpflege weiterhin vom etablierten Upstream-Projekt stammen.
