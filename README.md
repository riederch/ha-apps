# Home Assistant Apps

Eigenes Home-Assistant-App-Repository von Christoph Rieder.

## Enthaltene Apps

| App | Zweck |
|---|---|
| **Gitea** | Selbst gehosteter Git-Server direkt unter Home Assistant OS |
| **Gitea MCP** | Read-only-fähiger MCP-Zugang zu einer Gitea-Instanz, unter anderem für ChatGPT |
| **Vaultwarden** | Selbst gehosteter, Bitwarden-kompatibler Passwortmanager; übernommen aus `hassio-addons/app-vaultwarden` v0.27.0 |
| **Cloudflared Origin Auth** | Cloudflare Tunnel mit optionalem Basic-/Bearer-`Authorization` für zusätzliche Origin-Hosts |

## Repository in Home Assistant hinzufügen

1. **Einstellungen → Apps → App-Store** öffnen.
2. Rechts oben **⋮ → Repositories** wählen.
3. Folgende URL hinzufügen:

   ```text
   https://github.com/riederch/ha-apps
   ```

4. Den App-Store aktualisieren.
5. Danach die gewünschten Apps aus diesem Repository installieren.

## Sicherheit

Für Gitea MCP wird ein Gitea-Zugriffstoken nicht dauerhaft in der App gespeichert. Im HTTP-Modus sendet der jeweilige MCP-Client den Token als Bearer-Token. Für reine Wissensabfragen sollte in Gitea ein Token mit ausschließlich lesenden Rechten verwendet und die MCP-App im Read-only-Modus betrieben werden.

Vaultwarden generiert beim ersten Start einen temporären Admin-Token und zeigt ihn im App-Log an. Dieser sollte unmittelbar im Vaultwarden-Adminbereich gespeichert oder ersetzt werden.

Cloudflared Origin Auth verwendet für authentifizierte Zusatzhosts einen ausschließlich auf `127.0.0.1` gebundenen Nginx-Proxy im App-Container. Authentifizierungsdaten werden vor der Übergabe an Cloudflared aus dessen Ingress-Konfiguration entfernt und nicht in den Debug-Logs der Host-Konfiguration ausgegeben.

## Herkunft

Die Gitea-App orientiert sich an der Gitea-App aus [`alexbelgium/hassio-addons`](https://github.com/alexbelgium/hassio-addons/tree/master/gitea), wurde für dieses Repository jedoch eigenständig und reduziert umgesetzt.

Die Vaultwarden-App basiert auf [`hassio-addons/app-vaultwarden`](https://github.com/hassio-addons/app-vaultwarden) Release `v0.27.0` und verwendet Vaultwarden `1.36.0`.

Cloudflared Origin Auth ist ein schlanker Overlay-Fork von [`homeassistant-apps/app-cloudflared`](https://github.com/homeassistant-apps/app-cloudflared). Details zu den übernommenen Komponenten stehen in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
