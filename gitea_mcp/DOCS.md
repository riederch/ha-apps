# Gitea MCP

Diese App ist ein schlanker Home-Assistant-Wrapper um den offiziellen Gitea MCP Server `1.8.0`.
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

Die App speichert selbst keinen Zustand. Beim Upgrade auf `1.8.0-rch1` bleiben `gitea_host`, `insecure`, `read_only`, `debug`, Port `8080`, `/mcp` und der Bearer-Token-Passthrough unverändert.

Gitea MCP 1.8.0 unterstützt neuere MCP-Protokollstände und hat Änderungen an der angebotenen Tool-Oberfläche. Nach dem Upgrade sollte ein MCP-Client die Verbindung einmal neu aufbauen bzw. seine Tool-Liste neu laden. Eine Datenmigration ist nicht erforderlich.

Weitere Rollback-Hinweise stehen in [`../MIGRATIONS.md`](../MIGRATIONS.md).

## Update auf 1.8.0

Von `1.7.0-rch1` auf `1.8.0-rch1` bleiben App-Optionen und Endpunkt unverändert. Nach dem Neustart muss der MCP-Client seine Tool-Liste neu abfragen; die Funktion der tatsächlich verwendeten Tools ist gegen die Gitea-Instanz zu prüfen.

## Architektur

```text
MCP-Client
    |
    | Authorization: Bearer <GITEA_TOKEN>
    v
Gitea MCP 1.8.0 :8080/mcp
    |
    v
Gitea
```

Die App enthält keinen eigenen Fork des MCP-Servers und kompiliert keinen fremden Quellcode. Das offizielle Multi-Arch-Image `docker.gitea.com/gitea-mcp-server:1.8.0` dient als Binärquelle; der lokale Wrapper ergänzt nur Home-Assistant-Konfiguration und Startparameter.

## ChatGPT

ChatGPT kann lokale IP-Adressen nicht direkt erreichen. Veröffentliche daher ausschließlich den MCP-Dienst über einen abgesicherten HTTPS-Reverse-Proxy oder Cloudflare Tunnel.

Beispiel:

```text
https://gitea-mcp.example.at/mcp
    -> http://HOME-ASSISTANT-IP:8080/mcp
```

Der Port `8080` sollte nicht direkt am Router freigegeben werden.

## ChatGPT-Kompatibilitätsfix 1.8.0-rch2

Der integrierte HTTP-Adapter auf Port 8080 leitet alle MCP-Anfragen mit unverändertem Authorization-Header an den lokalen offiziellen Gitea-MCP-Server auf 127.0.0.1:8081 weiter. Er ergänzt bei `get_file_contents` das MCP-`structuredContent` und ein `outputSchema`. Dadurch sollen Clients, die reine MCP-Textantworten verwerfen, Dateiinhalte lesen können.

Für größere Dateien stehen beim **selben Tool** die optionalen Parameter `start_line`, `end_line` und `max_bytes` bereit. Standardmaximum: 65536 Bytes pro Antwort. Bei abgeschnittenen Ergebnissen liefert `next_start_line` die Fortsetzung. Binärdateien werden in Base64 mit `start_byte` und `next_start_byte` übertragen. Die vollständige Antwort des Upstream-Servers wird vor der Abschnittsbildung intern eingelesen (maximal 16 MiB); dies ist **kein serverseitiges Range-Reading**.

Bestehender Endpunkt, Konfiguration, Tokens und Gitea-Daten bleiben erhalten. Der Proxy schreibt keine Tokens oder Datei-Inhalte ins Log. HTTP-Streaming wird transparent weitergegeben und nur für ausgewählte JSON-RPC-Antworten erweitert. Nach dem App-Upgrade den ChatGPT-MCP-Connector erneut verbinden, um die neue Toolschema-Definition abzurufen.

**Einschränkung:** Der Fix behebt eine vermutete Inkompatibilität des Rückgabeformats. Ein vollständiger Ende-zu-Ende-Test mit ChatGPT ist erst möglich, wenn die aktualisierte App installiert und die Verbindung neu hergestellt wurde. Falls ein Fehler auftritt: vorheriges App-Image `1.8.0-rch1` wiederherstellen.


## Binaerdatei-Upload (1.8.0-rch3)

Die bestehende Python-Bridge stellt zusaetzlich die MCP-Tools `upload_binary_file`
(ChatGPT-Datei mit `_meta["openai/fileParams"]`) und `upload_binary_base64`
(Base64-Fallback, maximal 2 MiB) bereit. Der offizielle Gitea-MCP-Server
bleibt auf 1.8.0. `read_only: true` entfernt beide Upload-Tools.

Home Assistant App-Optionen:

```yaml
upload_max_mb: 16
upload_allowed_hosts: ""
```

Das Limit ist auf 1 bis 50 MiB begrenzt. Aus Sicherheitsgruenden ist der
Download per ChatGPT-Datei standardmaessig deaktiviert, bis die **tatsaechlichen**
HTTPS-Dateihosts als kommagetrennte Liste freigegeben wurden. Beispiel
(nur verwenden, wenn dieser Host tatsaechlich im Dateiobjekt vorkommt):
`files.oaiusercontent.com`. Datei-URLs werden nicht geloggt.

Alle Uploads erfordern pro Request einen Bearer-Token, der direkt an die
Gitea-Contents-API uebergeben wird. Neue Dateien werden via POST angelegt;
bestehende Dateien nur mit explizit gesetzter aktueller Git-Blob-SHA via PUT
ersetzt. Die Originalbytes bleiben erhalten und eine SHA-256-Pruefsumme
wird zurueckgegeben. Der Bridge-Service speichert keine Datei und keinen Token.

Nach der Installation: App neu starten und den MCP-Connector in ChatGPT
aktualisieren, sodass die neue Tool-Liste abgerufen wird. Eine PDF in einem
privaten Testrepo hochladen, den Gitea-Download pruefen und SHA-256 vergleichen.
Falls ChatGPT diese File-Parameter nicht weiterreicht, bleibt die Base64-
Alternative als Fallback, aber ohne automatische Uebernahme grosser Anhaenge.
Fuer grosse Archive Git LFS oder Objektspeicher bevorzugen.

Rollback: zur vorherigen App-Version `1.8.0-rch2` wechseln. Keine
Migration von Gitea-Daten erforderlich.
