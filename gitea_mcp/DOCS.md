# Gitea MCP

Diese App stellt den offiziellen Gitea-MCP-Server als HTTP-Dienst unter Home Assistant OS bereit.

## Voraussetzungen

- Eine erreichbare Gitea-Instanz, beispielsweise die Gitea-App aus diesem Repository.
- Ein persönlicher Gitea-Zugriffstoken.
- Für ChatGPT ein von außen erreichbarer HTTPS-Endpunkt, beispielsweise über Cloudflare Tunnel.

## Konfiguration

```yaml
gitea_host: http://homeassistant.local:3000
insecure: false
debug: false
```

Bei Problemen mit `homeassistant.local` kann statt dessen die lokale IP-Adresse verwendet werden, beispielsweise:

```yaml
gitea_host: http://192.168.1.50:3000
insecure: false
debug: false
```

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

Der Token wird dadurch nicht in der Home-Assistant-App-Konfiguration gespeichert.

## Empfohlene Token-Rechte

Für die rchkb zunächst:

- `repository`: Lesen
- `user`: Lesen
- `organization`: Lesen, falls das Repository einer Organisation gehört
- alle übrigen Bereiche: Kein Zugriff

Damit sind Änderungen zusätzlich auf Ebene der Gitea-API blockiert.

## ChatGPT

ChatGPT kann lokale IP-Adressen nicht direkt erreichen. Veröffentliche daher ausschließlich den MCP-Dienst über einen abgesicherten HTTPS-Reverse-Proxy oder Cloudflare Tunnel. Der Gitea-Webserver selbst muss dafür nicht öffentlich erreichbar sein.

Beispiel:

```text
https://gitea-mcp.example.at/mcp
    -> http://HOME-ASSISTANT-IP:8080/mcp
```

Der Port `8080` sollte nicht direkt am Router freigegeben werden.
