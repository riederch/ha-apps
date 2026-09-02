# Gitea MCP

Diese App ist ein schlanker Home-Assistant-Wrapper um den offiziellen Gitea MCP Server `1.7.0`.
Sie startet den Upstream-Server im Streamable-HTTP-Modus und reicht den vom MCP-Client gesendeten Bearer-Token pro Request an Gitea weiter. Der Token wird nicht in der Home-Assistant-App-Konfiguration gespeichert.

## Voraussetzungen

- Eine erreichbare Gitea-Instanz, beispielsweise die Gitea-App aus diesem Repository.
- Ein persönlicher Gitea-Zugriffstoken.
- Für externe MCP-Clients ein abgesicherter HTTPS-Endpunkt, beispielsweise über Cloudflare Tunnel.

## Konfiguration

```yaml
gitea_host: http://homeassistant.local:3000
insecure: false
read_only: false
debug: false
```

`read_only: true` startet den offiziellen Server mit `--read-only` und stellt nur lesende MCP-Tools bereit.

`insecure` darf nur bei einer HTTPS-Verbindung mit nicht vertrauenswürdigem Zertifikat aktiviert werden.

## MCP-Endpunkt

Nach dem Start ist der lokale Endpunkt:

```text
http://HOME-ASSISTANT-IP:8080/mcp
```

Der MCP-Client sendet den Gitea-Token als Header:

```http
Authorization: Bearer <GITEA_TOKEN>
```

Der Token wird dadurch nicht dauerhaft in der App gespeichert.

## Migration von 1.6.0

Die App speichert selbst keinen Zustand. Beim Upgrade auf `1.7.0-rch1` bleiben `gitea_host`, `insecure`, `read_only`, `debug`, Port `8080`, `/mcp` und der Bearer-Token-Passthrough unverändert.

Gitea MCP 1.7.0 unterstützt neuere MCP-Protokollstände und hat Änderungen an der angebotenen Tool-Oberfläche. Nach dem Upgrade sollte ein MCP-Client die Verbindung einmal neu aufbauen bzw. seine Tool-Liste neu laden. Eine Datenmigration ist nicht erforderlich.

Weitere Rollback-Hinweise stehen in [`../MIGRATIONS.md`](../MIGRATIONS.md).

## Architektur

```text
MCP-Client
    |
    | Authorization: Bearer <GITEA_TOKEN>
    v
Gitea MCP 1.7.0 :8080/mcp
    |
    v
Gitea
```

Die App enthält keinen eigenen Fork des MCP-Servers und kompiliert keinen fremden Quellcode. Das offizielle Multi-Arch-Image `docker.gitea.com/gitea-mcp-server:1.7.0` dient als Binärquelle; der lokale Wrapper ergänzt nur Home-Assistant-Konfiguration und Startparameter.

## ChatGPT

ChatGPT kann lokale IP-Adressen nicht direkt erreichen. Veröffentliche daher ausschließlich den MCP-Dienst über einen abgesicherten HTTPS-Reverse-Proxy oder Cloudflare Tunnel.

Beispiel:

```text
https://gitea-mcp.example.at/mcp
    -> http://HOME-ASSISTANT-IP:8080/mcp
```

Der Port `8080` sollte nicht direkt am Router freigegeben werden.
